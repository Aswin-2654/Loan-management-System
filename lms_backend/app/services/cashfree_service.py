from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from ..core.config import settings


def _cashfree_base_url() -> str:
    env = (settings.CASHFREE_ENV or "sandbox").lower().strip()
    if env == "production":
        return "https://api.cashfree.com/pg"
    return "https://sandbox.cashfree.com/pg"


def _cashfree_headers() -> dict[str, str]:
    if not settings.CASHFREE_CLIENT_ID or not settings.CASHFREE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Cashfree is not configured (missing CASHFREE_CLIENT_ID / CASHFREE_CLIENT_SECRET)",
        )
    return {
        "x-client-id": settings.CASHFREE_CLIENT_ID,
        "x-client-secret": settings.CASHFREE_CLIENT_SECRET,
        "x-api-version": settings.CASHFREE_API_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def cashfree_create_order(payload: dict[str, Any]) -> dict[str, Any]:
    base = _cashfree_base_url()
    url = f"{base}/orders"
    timeout = httpx.Timeout(float(settings.CASHFREE_HTTP_TIMEOUT_SECONDS))
    async with httpx.AsyncClient(timeout=timeout) as client:
        res = await client.post(url, headers=_cashfree_headers(), json=payload)

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Cashfree create order failed",
                "status_code": res.status_code,
                "body": res.text,
            },
        )

    try:
        return res.json()
    except Exception:
        return {"raw": res.text}


async def cashfree_get_order(order_id: str) -> dict[str, Any]:
    base = _cashfree_base_url()
    url = f"{base}/orders/{order_id}"
    timeout = httpx.Timeout(float(settings.CASHFREE_HTTP_TIMEOUT_SECONDS))
    async with httpx.AsyncClient(timeout=timeout) as client:
        res = await client.get(url, headers=_cashfree_headers())

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Cashfree get order failed",
                "status_code": res.status_code,
                "body": res.text,
            },
        )

    try:
        return res.json()
    except Exception:
        return {"raw": res.text}

