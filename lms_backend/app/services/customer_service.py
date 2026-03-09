
from ..database.mongo import get_db


async def profile_dashboard(customer_id: str):
    db = await get_db()
    customer_filters = [{"customer_id": customer_id}]
    if isinstance(customer_id, str) and customer_id.isdigit():
        customer_filters.append({"customer_id": int(customer_id)})
    elif isinstance(customer_id, int):
        customer_filters.append({"customer_id": str(customer_id)})

    query = {"$or": customer_filters} if len(customer_filters) > 1 else customer_filters[0]

    # customer_id is the numeric identifier assigned at registration
    user = await db.users.find_one(query)
    acc = await db.bank_accounts.find_one(query)
    kyc = await db.kyc_details.find_one(query)
    pan_number = await db.users.find_one(query, {"pan_number": 1})

    cibil_score = kyc.get("cibil_score") if kyc else None
    # Backfill legacy/manual approvals where KYC is approved but cibil_score was never stored.
    if kyc and cibil_score is None and str(kyc.get("kyc_status") or "").lower() == "approved":
        total_score = kyc.get("total_score")
        if total_score is None:
            total_score = int(kyc.get("employment_score") or 0) + int(kyc.get("income_score") or 0) + int(kyc.get("emi_score") or 0) + int(kyc.get("experience_score") or 0)
        cibil_score = max(300, min(900, 300 + round(int(total_score or 0) * 6)))
        await db.kyc_details.update_one({"_id": kyc["_id"]}, {"$set": {"total_score": int(total_score or 0), "cibil_score": int(cibil_score), "loan_eligible": int(cibil_score) >= 650}})

    # active loans
    active_personal = await db.personal_loans.find({"$and": [query, {"status": {"$in": ["active", "admin_approved", "manager_approved"]}}]}).to_list(length=50)
    active_vehicle = await db.vehicle_loans.find({"$and": [query, {"status": {"$in": ["active", "admin_approved", "manager_approved"]}}]}).to_list(length=50)
    def agg(loans):
        remaining_tenure = sum([int(l.get("remaining_tenure", 0)) for l in loans])
        remaining_amount = sum([float(l.get("remaining_amount", 0)) for l in loans])
        return remaining_tenure, remaining_amount
    rt1, ra1 = agg(active_personal)
    rt2, ra2 = agg(active_vehicle)
    profile = {
        "name": user.get("full_name") if user else None,
        "email": user.get("email") if user else None,
        "account_number": acc.get("account_number") if acc else None,
        "ifsc": acc.get("ifsc_code") if acc else None,
        "pan_number": pan_number.get("pan_number") if pan_number else None,
        "balance": acc.get("balance") if acc else 0.0,
        "cibil_score": cibil_score if kyc else None,
        "kyc_status": kyc.get("kyc_status") if kyc else "not_submitted",
        "active_loans": len(active_personal) + len(active_vehicle),
        "remaining_tenure": rt1 + rt2,
        "remaining_amount": ra1 + ra2,
    }
    return profile
