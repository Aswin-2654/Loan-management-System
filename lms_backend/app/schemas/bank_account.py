
from pydantic import BaseModel

class BankAccountOut(BaseModel):
    id: str
    account_number: int
    ifsc_code: str
    balance: float
