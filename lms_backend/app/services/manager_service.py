
from ..database.mongo import get_db
from ..models.enums import LoanStatus
from ..utils.serializers import normalize_doc


async def get_loans_for_manager():
    db = await get_db()
    # Manager console needs both pending queues and recently processed items.
    # Return a broader set of statuses; the UI will group them into sections.
    manager_statuses = [
        LoanStatus.APPLIED,
        LoanStatus.VERIFICATION_DONE,
        LoanStatus.MANAGER_APPROVED,
        LoanStatus.PENDING_ADMIN_APPROVAL,
        LoanStatus.ADMIN_APPROVED,
        LoanStatus.SANCTION_SENT,
        LoanStatus.SIGNED_RECEIVED,
        LoanStatus.READY_FOR_DISBURSEMENT,
        LoanStatus.ACTIVE,
        LoanStatus.COMPLETED,
        LoanStatus.FORECLOSED,
        LoanStatus.DISBURSED,
        LoanStatus.REJECTED,
    ]

    loans = await db.personal_loans.find({"status": {"$in": manager_statuses}}).sort("applied_at", -1).to_list(length=400)
    loans += await db.vehicle_loans.find({"status": {"$in": manager_statuses}}).sort("applied_at", -1).to_list(length=400)
    loans += await db.education_loans.find({"status": {"$in": manager_statuses}}).sort("applied_at", -1).to_list(length=400)
    loans += await db.home_loans.find({"status": {"$in": manager_statuses}}).sort("applied_at", -1).to_list(length=400)
    return [normalize_doc(l) for l in loans]


async def list_pending_signature_verifications():
    db = await get_db()
    loans = await db.personal_loans.find({"status": LoanStatus.SIGNED_RECEIVED}).to_list(length=200)
    loans += await db.vehicle_loans.find({"status": LoanStatus.SIGNED_RECEIVED}).to_list(length=200)
    loans += await db.education_loans.find({"status": LoanStatus.SIGNED_RECEIVED}).to_list(length=200)
    loans += await db.home_loans.find({"status": LoanStatus.SIGNED_RECEIVED}).to_list(length=200)
    return [normalize_doc(l) for l in loans]


async def list_verification_team(active_only: bool = True):
    db = await get_db()
    query: dict = {"role": "verification"}
    if active_only:
        query["is_active"] = True

    members = await db.staff_users.find(query, {"password": 0}).sort("full_name", 1).to_list(length=300)
    return [normalize_doc(m) for m in members]
