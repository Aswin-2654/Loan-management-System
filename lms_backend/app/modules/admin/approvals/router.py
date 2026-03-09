import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ....core.security import require_roles
from ..service import get_db
from ....models.enums import LoanCollection, LoanStatus, Roles
from ....schemas.settings import SystemSettingsUpdate
from ..service import (
    find_loan_any,
    get_admin_approvals_dashboard,
    list_high_value_pending,
    list_pending_admin_approvals,
    list_ready_for_disbursement,
    get_document_binary,
    admin_final_approve,
    admin_reject,
    disburse,
    mark_signed_received,
    send_sanction,
    get_settings,
    update_settings,
)
from ....utils.id import loan_id_filter
from ....utils.serializers import normalize_doc
from ..schemas import AdminApprovePayload, AdminRejectPayload

router = APIRouter()


@router.get("/pending-approvals")
async def pending(user=Depends(require_roles(Roles.ADMIN))):
    return await list_pending_admin_approvals()


@router.get("/approvals-dashboard")
async def approvals_dashboard(days: int = 30, user=Depends(require_roles(Roles.ADMIN))):
    return await get_admin_approvals_dashboard(days=days)


@router.get("/dashboard")
async def dashboard(user=Depends(require_roles(Roles.ADMIN))):
    db = await get_db()
    high_value_pending = await db.personal_loans.count_documents(
        {"status": LoanStatus.PENDING_ADMIN_APPROVAL, "loan_amount": {"$gt": 1500000}}
    )
    high_value_pending += await db.vehicle_loans.count_documents(
        {"status": LoanStatus.PENDING_ADMIN_APPROVAL, "loan_amount": {"$gt": 1500000}}
    )
    high_value_pending += await db.education_loans.count_documents(
        {"status": LoanStatus.PENDING_ADMIN_APPROVAL, "loan_amount": {"$gt": 1500000}}
    )
    high_value_pending += await db.home_loans.count_documents(
        {"status": LoanStatus.PENDING_ADMIN_APPROVAL, "loan_amount": {"$gt": 1500000}}
    )

    ready_for_disbursement = await db.personal_loans.count_documents({"status": LoanStatus.READY_FOR_DISBURSEMENT})
    ready_for_disbursement += await db.vehicle_loans.count_documents({"status": LoanStatus.READY_FOR_DISBURSEMENT})
    ready_for_disbursement += await db.education_loans.count_documents({"status": LoanStatus.READY_FOR_DISBURSEMENT})
    ready_for_disbursement += await db.home_loans.count_documents({"status": LoanStatus.READY_FOR_DISBURSEMENT})

    active_loans = await db.personal_loans.count_documents({"status": LoanStatus.ACTIVE})
    active_loans += await db.vehicle_loans.count_documents({"status": LoanStatus.ACTIVE})
    active_loans += await db.education_loans.count_documents({"status": LoanStatus.ACTIVE})
    active_loans += await db.home_loans.count_documents({"status": LoanStatus.ACTIVE})

    from datetime import datetime, timedelta

    now = datetime.utcnow()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    disb_today = await db.transactions.find(
        {"type": "disbursement", "created_at": {"$gte": day_start, "$lt": day_end}}
    ).to_list(length=5000)
    total_disbursed_today = float(sum(float(t.get("amount") or 0) for t in disb_today))

    db_ping = True
    try:
        await db.command("ping")
    except Exception:
        db_ping = False

    return {
        "high_value_pending": high_value_pending,
        "ready_for_disbursement": ready_for_disbursement,
        "active_loans": active_loans,
        "total_disbursements_today": len(disb_today),
        "total_disbursed_amount_today": total_disbursed_today,
        "system_health": {"db_ping": db_ping},
    }


@router.get("/loans/high-value-pending")
async def high_value_pending(user=Depends(require_roles(Roles.ADMIN))):
    return await list_high_value_pending()


@router.get("/loans/ready-for-disbursement")
async def ready_for_disbursement_queue(user=Depends(require_roles(Roles.ADMIN))):
    return await list_ready_for_disbursement()


@router.get("/loans/{loan_id}/review")
async def review_any_loan(loan_id: str, user=Depends(require_roles(Roles.ADMIN))):
    loan_collection, loan = await find_loan_any(loan_id)
    if not loan_collection or not loan:
        return {"error": "Loan not found"}
    return normalize_doc(loan)


@router.get("/loans/{loan_id}/documents/{doc_type}")
async def download_loan_document_for_admin(loan_id: str, doc_type: str, user=Depends(require_roles(Roles.ADMIN))):
    loan_collection, loan = await find_loan_any(loan_id)
    if not loan_collection or not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    field_map = {
        "pay_slip": "pay_slip",
        "vehicle_price_doc": "vehicle_price_doc",
        "home_property_doc": "home_property_doc",
        "fees_structure": "fees_structure",
        "bonafide_certificate": "bonafide_certificate",
        "collateral_doc": "collateral_doc",
    }
    field = field_map.get(doc_type)
    if not field:
        raise HTTPException(status_code=400, detail="Unsupported document type")

    raw_value = loan.get(field)
    if not raw_value:
        raise HTTPException(status_code=404, detail="Document not uploaded")

    if isinstance(raw_value, str) and (
        raw_value.startswith("http://") or raw_value.startswith("https://") or raw_value.startswith("/")
    ):
        raise HTTPException(status_code=404, detail="Document binary not available")

    doc = await get_document_binary(str(raw_value))
    return StreamingResponse(
        io.BytesIO(doc["data"]),
        media_type=doc["content_type"],
        headers={"Content-Disposition": f'inline; filename="{doc["filename"]}"'},
    )


@router.post("/loans/{loan_id}/approve")
async def approve_high_value(
    loan_id: str,
    payload: AdminApprovePayload | None = None,
    user=Depends(require_roles(Roles.ADMIN)),
):
    loan_collection, loan = await find_loan_any(loan_id)
    if not loan_collection or not loan:
        return {"error": "Loan not found"}
    approved_amount = payload.approved_amount if payload else None
    interest_rate = payload.interest_rate if payload else None
    return await admin_final_approve(
        loan_collection,
        loan_id,
        user["_id"],
        approved_amount=approved_amount,
        interest_rate=interest_rate,
    )


@router.post("/loans/{loan_id}/reject")
async def reject_high_value(loan_id: str, payload: AdminRejectPayload, user=Depends(require_roles(Roles.ADMIN))):
    loan_collection, loan = await find_loan_any(loan_id)
    if not loan_collection or not loan:
        return {"error": "Loan not found"}
    return await admin_reject(loan_collection, loan_id, user["_id"], payload.reason)


@router.post("/loans/{loan_id}/sanction-letter/generate")
async def generate_sanction_letter(loan_id: str, user=Depends(require_roles(Roles.ADMIN))):
    loan_collection, loan = await find_loan_any(loan_id)
    if not loan_collection or not loan:
        return {"error": "Loan not found"}
    res = await send_sanction(loan_collection, loan_id, user["_id"])
    return {**res, "download_url": f"/api/customer/loans/{loan.get('loan_id')}/sanction-letter"}


@router.post("/loans/{loan_id}/disburse")
async def disburse_any(loan_id: str, user=Depends(require_roles(Roles.ADMIN))):
    loan_collection, loan = await find_loan_any(loan_id)
    if not loan_collection or not loan:
        return {"error": "Loan not found"}
    return await disburse(loan_collection, loan_id, user["_id"])


@router.put("/approve/{loan_collection}/{loan_id}")
async def approve_route(
    loan_collection: LoanCollection,
    loan_id: str,
    payload: AdminApprovePayload | None = None,
    user=Depends(require_roles(Roles.ADMIN)),
):
    approved_amount = payload.approved_amount if payload else None
    interest_rate = payload.interest_rate if payload else None
    return await admin_final_approve(
        loan_collection.value,
        loan_id,
        user["_id"],
        approved_amount=approved_amount,
        interest_rate=interest_rate,
    )


@router.put("/sanction/{loan_collection}/{loan_id}")
async def sanction_route(
    loan_collection: LoanCollection,
    loan_id: str,
    user=Depends(require_roles(Roles.ADMIN)),
):
    return await send_sanction(loan_collection.value, loan_id, user["_id"])


@router.put("/signed/{loan_collection}/{loan_id}")
async def signed_route(
    loan_collection: LoanCollection,
    loan_id: str,
    user=Depends(require_roles(Roles.ADMIN)),
):
    return await mark_signed_received(loan_collection.value, loan_id, user["_id"])


@router.put("/disburse/{loan_collection}/{loan_id}")
async def disburse_route(
    loan_collection: LoanCollection,
    loan_id: str,
    user=Depends(require_roles(Roles.ADMIN)),
):
    return await disburse(loan_collection.value, loan_id, user["_id"])


@router.put("/settings")
async def settings_update(
    payload: SystemSettingsUpdate,
    user=Depends(require_roles(Roles.ADMIN)),
):
    return await update_settings(user["_id"], payload.dict())


@router.get("/settings")
async def settings_get(user=Depends(require_roles(Roles.ADMIN))):
    return await get_settings()


@router.get("/loan/{loan_collection}/{loan_id}")
async def get_loan(
    loan_collection: LoanCollection,
    loan_id: str,
    user=Depends(require_roles(Roles.ADMIN)),
):
    db = await get_db()
    loan = await db[loan_collection.value].find_one(loan_id_filter(loan_id))
    if not loan:
        return {"error": "Loan not found"}
    return normalize_doc(loan)



