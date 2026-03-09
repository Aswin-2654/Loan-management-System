from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SupportCategory = Literal["kyc", "payment", "loan", "wallet", "documents", "other"]
SupportStatus = Literal["open", "closed"]


class SupportAttachment(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    size: int = Field(..., ge=0)
    type: str | None = Field(default=None, max_length=128)


class SupportTicketCreate(BaseModel):
    category: SupportCategory
    subject: str = Field(..., min_length=3, max_length=180)
    message: str = Field(..., min_length=5, max_length=5000)
    attachment: SupportAttachment | None = None


class SupportTicketAdminResolve(BaseModel):
    reply_message: str = Field(..., min_length=2, max_length=5000)
    close_ticket: bool = True


class SupportTicketOut(BaseModel):
    ticket_id: str
    customer_id: str
    category: SupportCategory
    subject: str
    message: str
    attachment: SupportAttachment | None = None
    status: SupportStatus
    admin_reply: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    created_at: datetime
    updated_at: datetime
