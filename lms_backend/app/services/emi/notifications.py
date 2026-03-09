from __future__ import annotations

from datetime import datetime

from ...database.mongo import get_db
from ...utils.serializers import normalize_doc


async def create_customer_notification(
    customer_id: str | int,
    *,
    title: str,
    message: str,
    kind: str = "info",
    meta: dict | None = None,
) -> dict:
    db = await get_db()
    doc = {
        "customer_id": customer_id,
        "title": str(title),
        "message": str(message),
        "kind": str(kind or "info"),
        "meta": meta or {},
        "read": False,
        "created_at": datetime.utcnow(),
    }
    res = await db.customer_notifications.insert_one(doc)
    doc["_id"] = res.inserted_id
    return normalize_doc(doc)


async def list_customer_notifications(customer_id: str | int, limit: int = 100) -> list[dict]:
    db = await get_db()
    limit = max(1, min(int(limit or 100), 500))
    rows = await db.customer_notifications.find({"customer_id": customer_id}).sort("created_at", -1).limit(limit).to_list(length=limit)
    return [normalize_doc(r) for r in rows]
