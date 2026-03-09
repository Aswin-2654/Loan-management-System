"""Quick test to verify loan creation and lookup."""
import asyncio
from datetime import datetime
from ..database.mongo import get_db
from ..utils.id import loan_id_filter


async def check_loan(customer_id: int = 1, loan_id: int = 1):
    """Check if a loan exists and what its status is."""
    db = await get_db()
    
    print(f"\n=== Checking Loan ID={loan_id}, Customer ID={customer_id} ===")
    
    # Check personal_loans
    filt = loan_id_filter(str(loan_id))
    filt["customer_id"] = customer_id
    print(f"Filter: {filt}")
    
    loan = await db.personal_loans.find_one(filt)
    if loan:
        print(f"✓ Found in personal_loans:")
        print(f"  _id: {loan.get('_id')}")
        print(f"  loan_id: {loan.get('loan_id')}")
        print(f"  status: {loan.get('status')}")
        print(f"  customer_id: {loan.get('customer_id')}")
        print(f"  emi_per_month: {loan.get('emi_per_month')}")
        return loan
    else:
        loan = await db.vehicle_loans.find_one(filt)
        if loan:
            print(f"✓ Found in vehicle_loans:")
            print(f"  _id: {loan.get('_id')}")
            print(f"  loan_id: {loan.get('loan_id')}")
            print(f"  status: {loan.get('status')}")
            print(f"  customer_id: {loan.get('customer_id')}")
            print(f"  emi_per_month: {loan.get('emi_per_month')}")
            return loan
        else:
            print(f"✗ Loan not found in either collection")
            # List all loans for this customer
            print(f"\nAll loans for customer_id={customer_id}:")
            p_loans = await db.personal_loans.find({"customer_id": customer_id}).to_list(None)
            v_loans = await db.vehicle_loans.find({"customer_id": customer_id}).to_list(None)
            for l in p_loans:
                print(f"  personal: _id={l.get('_id')}, loan_id={l.get('loan_id')}, status={l.get('status')}")
            for l in v_loans:
                print(f"  vehicle: _id={l.get('_id')}, loan_id={l.get('loan_id')}, status={l.get('status')}")
            return None


async def main():
    """Test scenario: check loan 1 for customer 1."""
    loan = await check_loan(customer_id=1, loan_id=1)
    if loan and loan.get("status") == "applied":
        print("\n⚠️  Loan is still in 'applied' status. To pay EMI, loan must be 'active'.")
        print("   Steps to activate:")
        print("   1. Manager assigns verification: PUT /api/manager/assign-verification/personal_loans/1/<verifier_id>")
        print("   2. Verifier approves: PUT /api/verification/verify-loan/personal_loans/1?approved=true")
        print("   3. Manager approves: PUT /api/manager/approve/personal_loans/1")
        print("   4. Admin approves (if loan > 15L): PUT /api/admin/approve-loan/personal_loans/1")
        print("   5. Disburse: PUT /api/admin/disburse/personal_loans/1")


if __name__ == "__main__":
    asyncio.run(main())
