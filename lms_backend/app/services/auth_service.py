from datetime import datetime, date
from bson import ObjectId
from fastapi import HTTPException
import re
from ..database.mongo import get_db
from ..core.security import hash_password, verify_password, create_access_token
from ..core.config import settings
from ..models.enums import Roles
from ..utils.sequences import next_customer_id
from ..services.audit_service import write_audit_log


async def register_customer(payload: dict) -> dict:
    db = await get_db()

    # 🔴 ADD: normalize PAN to uppercase early
    if payload.get("pan_number"):
        payload["pan_number"] = payload["pan_number"].upper()

    # Existing email check (unchanged)
    existing = await db.users.find_one({"email": payload["email"]})
    existing_staff = await db.staff_users.find_one({"email": payload["email"]})
    if existing or existing_staff:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🔴 MODIFIED: PAN uniqueness check (now case-safe)
    if payload.get("pan_number"):
        pan_exists = await db.users.find_one(
            {"pan_number": payload["pan_number"]}
        )
        if pan_exists:
            raise HTTPException(
                status_code=400,
                detail="PAN number already registered with another user"
            )

    # assign a numeric customer id
    customer_id = await next_customer_id()

    # Convert DOB to string (unchanged logic, cleaner placement)
    dob = payload.get("dob")
    if dob is not None:
        dob = dob.isoformat() if hasattr(dob, "isoformat") else str(dob)

    user_doc = {
        "full_name": payload["full_name"],
        "email": payload["email"],
        "password": hash_password(payload["password"]),
        "phone": payload.get("phone"),
        "dob": dob,
        "gender": payload.get("gender"),
        "pan_number": payload.get("pan_number"),  # always uppercase now
        "customer_id": customer_id,
        "_id": customer_id,
        "role": Roles.CUSTOMER,
        "is_active": True,
        "is_kyc_verified": False,
        "created_at": datetime.utcnow(),
    }

    res = await db.users.insert_one(user_doc)

    from ..utils.serializers import normalize_doc
    out = {"_id": customer_id, **user_doc}
    return normalize_doc(out)


async def login(email: str, password: str) -> dict:
    db = await get_db()
    user = await db.users.find_one({"email": email})
    if user:
        user_collection = db.users
    else:
        user = await db.staff_users.find_one({"email": email})
        user_collection = db.staff_users
    if not user:
        await write_audit_log(
            action="login_failed",
            actor_role=None,
            actor_id=None,
            entity_type="user",
            entity_id=None,
            details={"email": email, "reason": "user_not_found"},
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_active", True):
        await write_audit_log(
            action="login_blocked",
            actor_role=user.get("role"),
            actor_id=user.get("_id"),
            entity_type="user",
            entity_id=user.get("_id"),
            details={"reason": "inactive_account"},
        )
        raise HTTPException(status_code=403, detail="Account disabled")

    now = datetime.utcnow()
    locked_until = user.get("locked_until")
    if locked_until and locked_until > now:
        await write_audit_log(
            action="login_blocked",
            actor_role=user.get("role"),
            actor_id=user.get("_id"),
            entity_type="user",
            entity_id=user.get("_id"),
            details={"reason": "account_locked", "locked_until": locked_until.isoformat()},
        )
        raise HTTPException(status_code=403, detail="Account locked. Try again later.")

    if not verify_password(password, user.get("password", "")):
        failed = int(user.get("failed_login_attempts") or 0) + 1
        update = {"failed_login_attempts": failed, "last_failed_login_at": now}
        if failed >= 5:
            update["locked_until"] = now.replace(microsecond=0)  # normalize
            # lock for 15 minutes
            from datetime import timedelta
            update["locked_until"] = now + timedelta(minutes=15)
        await user_collection.update_one({"_id": user["_id"]}, {"$set": update})
        await write_audit_log(
            action="login_failed",
            actor_role=user.get("role"),
            actor_id=user.get("_id"),
            entity_type="user",
            entity_id=user.get("_id"),
            details={"reason": "invalid_password", "failed_login_attempts": failed},
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # success: reset counters
    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"failed_login_attempts": 0, "locked_until": None, "last_login_at": now}},
    )
    await write_audit_log(
        action="login_success",
        actor_role=user.get("role"),
        actor_id=user.get("_id"),
        entity_type="user",
        entity_id=user.get("_id"),
        details={},
    )

    token = create_access_token(
        {"user_id": str(user["_id"]), "role": user["role"]}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "user_id": str(user["_id"]),
        "mpin_set": bool(user.get("mpin_hash")),
    }


async def reset_password_with_pan(
    email: str,
    pan_number: str,
    new_password: str,
    confirm_password: str,
) -> dict:
    db = await get_db()
    clean_email = str(email or "").strip()
    clean_pan = str(pan_number or "").strip().upper()

    if not clean_email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not re.fullmatch(r"^[A-Z]{5}[0-9]{4}[A-Z]$", clean_pan):
        raise HTTPException(status_code=400, detail="Invalid PAN format")
    if len(new_password or "") < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")

    user = await db.users.find_one({"email": {"$regex": f"^{re.escape(clean_email)}$", "$options": "i"}})
    if not user:
        await write_audit_log(
            action="password_reset_failed",
            actor_role="customer",
            actor_id=None,
            entity_type="user",
            entity_id=None,
            details={"email": clean_email, "reason": "user_not_found"},
        )
        raise HTTPException(status_code=400, detail="Invalid email or PAN number")

    stored_pan = str(user.get("pan_number") or "").strip().upper()
    if not stored_pan or stored_pan != clean_pan:
        await write_audit_log(
            action="password_reset_failed",
            actor_role="customer",
            actor_id=user.get("_id"),
            entity_type="user",
            entity_id=user.get("_id"),
            details={"email": clean_email, "reason": "pan_mismatch"},
        )
        raise HTTPException(status_code=400, detail="Invalid email or PAN number")

    if verify_password(new_password, str(user.get("password") or "")):
        raise HTTPException(status_code=400, detail="New password must be different from current password")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password": hash_password(new_password),
                "updated_at": datetime.utcnow(),
                "failed_login_attempts": 0,
                "locked_until": None,
            }
        },
    )

    await write_audit_log(
        action="password_reset_with_pan",
        actor_role="customer",
        actor_id=user.get("_id"),
        entity_type="user",
        entity_id=user.get("_id"),
        details={"email": clean_email},
    )

    return {"message": "Password reset successful. Please log in with your new password."}
