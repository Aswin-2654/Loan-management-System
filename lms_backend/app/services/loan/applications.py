from datetime import datetime

from fastapi import HTTPException

from ...database.mongo import get_db
from ...models.enums import LoanStatus
from ...utils.dates import next_month_date
from ...utils.sequences import next_loan_id

from .calculations import compute_emi


# =========================
# APPLY LOAN (CUSTOMER)
# =========================
async def apply_loan(collection: str, customer_id: str, payload: dict, interest_rate: float):
    db = await get_db()

    # KYC must be approved
    kyc = await db.kyc_details.find_one(
        {"customer_id": customer_id, "kyc_status": "approved"}
    )
    if not kyc:
        raise HTTPException(status_code=400, detail="KYC not approved")

    # Check if customer has any ACTIVE loans
    active_loan = await db.personal_loans.find_one(
        {"customer_id": customer_id, "status": {"$in": [LoanStatus.ACTIVE, LoanStatus.DISBURSED]}}
    )
    if not active_loan:
        active_loan = await db.vehicle_loans.find_one(
            {"customer_id": customer_id, "status": {"$in": [LoanStatus.ACTIVE, LoanStatus.DISBURSED]}}
        )
    if not active_loan:
        active_loan = await db.education_loans.find_one(
            {"customer_id": customer_id, "status": {"$in": [LoanStatus.ACTIVE, LoanStatus.DISBURSED]}}
        )
    if not active_loan:
        active_loan = await db.home_loans.find_one(
            {"customer_id": customer_id, "status": {"$in": [LoanStatus.ACTIVE, LoanStatus.DISBURSED]}}
        )
    if active_loan:
        raise HTTPException(
            status_code=400,
            detail="You have an active loan. Please repay it completely before applying for a new loan."
        )

    # ðŸ”½ ADDED VALIDATION (REGISTERED USER + ACCOUNT)
    user = await db.users.find_one({"customer_id": customer_id})
    if not user:
        raise HTTPException(status_code=404, detail="Customer not found")

    account = await db.bank_accounts.find_one({"customer_id": customer_id})
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    mismatches = {}

    if payload.get("full_name") != user.get("full_name"):
        mismatches["full_name"] = "Full name does not match registered details"

    if payload.get("pan_number") != user.get("pan_number"):
        mismatches["pan_number"] = "PAN number does not match registered details"

    if str(payload.get("bank_account_number")) != str(account.get("account_number")):
        mismatches["bank_account_number"] = "Account number does not match registered account"

    if mismatches:
        raise HTTPException(status_code=400, detail=mismatches)
    # ðŸ”¼ END VALIDATION

    amount = float(payload["loan_amount"])
    tenure = int(payload["tenure_months"])

    emi = compute_emi(amount, interest_rate, tenure)
    loan_id = await next_loan_id()

    doc = {
        **payload,
        "_id": loan_id,
        "loan_id": loan_id,
        "customer_id": customer_id,
        "remaining_tenure": tenure,
        "emi_per_month": emi,
        "remaining_amount": round(emi * tenure, 2),
        "total_paid": 0.0,
        "cibil_score_at_apply": int(kyc.get("cibil_score") or 0),
        "status": LoanStatus.APPLIED,
        "manager_id": None,
        "verification_id": None,
        "admin_id": None,
        "next_emi_date": next_month_date(),
        "applied_at": datetime.utcnow(),
        "approved_at": None,
        "disbursed_at": None,
    }

    await db[collection].insert_one(doc)

    return {
        "message": "Loan application submitted and under review",
        "loan_id": loan_id,
        "status": LoanStatus.APPLIED,
        "emi_per_month": emi,
        "tenure_months": tenure
    }

