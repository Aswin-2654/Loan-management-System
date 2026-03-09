
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import hashlib
from ..core.config import settings

client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client

async def get_db():
    return get_client()[settings.MONGODB_DB]

async def init_indexes():
    db = await get_db()
    # Unique index on user email
    await db.users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
    await db.staff_users.create_index([("email", ASCENDING)], unique=True, name="uniq_staff_email")
    await db.staff_users.create_index([("role", ASCENDING)], name="staff_role_idx")
    # Unique account number
    await db.bank_accounts.create_index([("account_number", ASCENDING)], unique=True, name="uniq_account")
    # Common indexes
    await db.personal_loans.create_index([("customer_id", ASCENDING)], name="pl_cust_idx")
    await db.vehicle_loans.create_index([("customer_id", ASCENDING)], name="vl_cust_idx")
    await db.education_loans.create_index([("customer_id", ASCENDING)], name="el_cust_idx")
    await db.home_loans.create_index([("customer_id", ASCENDING)], name="hl_cust_idx")
    await db.transactions.create_index([("customer_id", ASCENDING)], name="txn_cust_idx")
    await db.transactions.create_index([("loan_id", ASCENDING)], name="txn_loan_idx")
    await db.kyc_details.create_index([("customer_id", ASCENDING)], unique=True, name="uniq_kyc_customer")
    await db.users.create_index(
    [("pan_number", ASCENDING)],
    unique=True,
    sparse=True,
    name="uniq_pan_number"
    )

    # Unique Aadhaar hash in KYC (raw Aadhaar is not stored)
    await db.kyc_details.create_index(
        [("aadhaar_hash", ASCENDING)],
        unique=True,
        sparse=True,
        name="uniq_aadhaar_hash"
    )

    # One-time migration: move plaintext PAN/Aadhaar to hashed + masked fields.
    cursor = db.kyc_details.find(
        {
            "$or": [
                {"pan_number": {"$exists": True}},
                {"aadhaar_number": {"$exists": True}},
                {"aadhar_number": {"$exists": True}},
            ]
        }
    )
    rows = await cursor.to_list(length=5000)
    for row in rows:
        pan = str(row.get("pan_number") or "").strip().upper()
        aadhaar = "".join(ch for ch in str(row.get("aadhaar_number") or row.get("aadhar_number") or "") if ch.isdigit())
        set_doc = {}
        unset_doc = {}
        if pan:
            set_doc["pan_hash"] = hashlib.sha256(pan.encode("utf-8")).hexdigest()
            set_doc["pan_last4"] = pan[-4:]
            set_doc["pan_masked"] = f"{pan[:2]}******{pan[-2:]}" if len(pan) == 10 else pan
            unset_doc["pan_number"] = ""
        if aadhaar:
            set_doc["aadhaar_hash"] = hashlib.sha256(aadhaar.encode("utf-8")).hexdigest()
            set_doc["aadhaar_last4"] = aadhaar[-4:]
            set_doc["aadhaar_masked"] = f"XXXX-XXXX-{aadhaar[-4:]}" if len(aadhaar) >= 4 else aadhaar
            unset_doc["aadhaar_number"] = ""
            unset_doc["aadhar_number"] = ""
        if set_doc or unset_doc:
            update = {}
            if set_doc:
                update["$set"] = set_doc
            if unset_doc:
                update["$unset"] = unset_doc
            await db.kyc_details.update_one({"_id": row["_id"]}, update)

    # Audit logs (append-only)
    await db.audit_logs.create_index([("created_at", ASCENDING)], name="audit_created_at")
    await db.audit_logs.create_index([("actor_id", ASCENDING)], name="audit_actor_id")
    await db.audit_logs.create_index([("action", ASCENDING)], name="audit_action")
    await db.audit_logs.create_index([("entity_id", ASCENDING)], name="audit_entity_id")

    # EMI schedules
    await db.emi_schedules.create_index([("loan_id", ASCENDING)], name="emi_loan_id")
    await db.emi_schedules.create_index([("customer_id", ASCENDING)], name="emi_customer_id")
    await db.emi_schedules.create_index([("due_date", ASCENDING)], name="emi_due_date")
    await db.emi_schedules.create_index([("status", ASCENDING)], name="emi_status")

    # EMI escalations
    await db.emi_escalations.create_index([("loan_id", ASCENDING)], name="esc_loan_id")
    await db.emi_escalations.create_index([("customer_id", ASCENDING)], name="esc_customer_id")
    await db.emi_escalations.create_index([("status", ASCENDING)], name="esc_status")
    await db.emi_escalations.create_index([("opened_at", ASCENDING)], name="esc_opened_at")

    # Customer notifications
    await db.customer_notifications.create_index([("customer_id", ASCENDING)], name="cust_note_customer_id")
    await db.customer_notifications.create_index([("created_at", ASCENDING)], name="cust_note_created_at")
    await db.customer_notifications.create_index([("read", ASCENDING)], name="cust_note_read")

    # Support tickets
    await db.support_tickets.create_index([("ticket_id", ASCENDING)], unique=True, name="uniq_support_ticket_id")
    await db.support_tickets.create_index([("customer_id", ASCENDING)], name="support_customer_id")
    await db.support_tickets.create_index([("status", ASCENDING)], name="support_status")
    await db.support_tickets.create_index([("created_at", ASCENDING)], name="support_created_at")

    # Cashfree payments (gateway orders + processing state)
    await db.cashfree_payments.create_index(
        [("order_id", ASCENDING)],
        unique=True,
        name="uniq_cashfree_order_id",
    )
    await db.cashfree_payments.create_index([("customer_id", ASCENDING)], name="cf_customer_id")
    await db.cashfree_payments.create_index([("loan_id", ASCENDING)], name="cf_loan_id")

    # API idempotency records
    await db.idempotency_requests.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="idempotency_ttl",
    )
    await db.idempotency_requests.create_index(
        [("method", ASCENDING), ("path", ASCENDING), ("idempotency_key", ASCENDING), ("auth_hash", ASCENDING)],
        unique=True,
        name="uniq_idempotency_request",
    )

    # One-time migration path: move legacy staff rows out of users collection
    staff_roles = ["admin", "manager", "verification"]
    legacy_staff = await db.users.find({"role": {"$in": staff_roles}}).to_list(length=5000)
    for row in legacy_staff:
        email = row.get("email")
        if not email:
            continue
        await db.staff_users.update_one(
            {"email": email},
            {"$setOnInsert": row},
            upsert=True,
        )
        await db.users.delete_one({"_id": row.get("_id")})

    # Staff accounts do not use customer KYC status fields
    await db.staff_users.update_many(
        {"is_kyc_verified": {"$exists": True}},
        {"$unset": {"is_kyc_verified": ""}},
    )
