from __future__ import annotations

import logging
from typing import Optional

import aiohttp

from app.config import Settings

log = logging.getLogger("ton")


async def incoming_by_comment(settings: Settings, comment: str) -> Optional[float]:
    if not settings.ton_address:
        return None
    address = settings.ton_address
    params = {"address": address, "limit": 30}
    headers = {}
    if settings.ton_api_key:
        headers["X-API-Key"] = settings.ton_api_key
    url = "https://toncenter.com/api/v2/getTransactions"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=20) as resp:
                payload = await resp.json()
    except Exception:
        log.exception("toncenter request failed")
        return None
    if not payload.get("ok"):
        return None
    for tx in payload.get("result") or []:
        inn = tx.get("in_msg") or {}
        msg = (inn.get("message") or inn.get("comment") or "").strip()
        if msg != comment:
            continue
        nano = int(inn.get("value") or 0)
        if nano <= 0:
            continue
        return nano / 1_000_000_000
    return None


def ton_to_currency(ton_amount: float, settings: Settings, requested: float) -> Optional[float]:
    if settings.ton_rate > 0:
        credited = round(ton_amount * settings.ton_rate, 2)
        if credited + 0.01 >= requested:
            return requested
        return None
    if ton_amount > 0:
        return requested
    return None
