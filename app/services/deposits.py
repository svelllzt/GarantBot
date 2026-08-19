from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from app.config import Settings
from app.i18n import t
from app.services.ton import fetch_ton_incoming, fetch_usdt_incoming
from app.storage import Storage
from app.util import money_asset

log = logging.getLogger("deposits")

WATCH_SEC = 25
_MEMO = re.compile(r"^G(\d{1,16})$")


def user_memo(user_id: int) -> str:
    return f"G{int(user_id)}"


def memo_user_id(comment: str) -> Optional[int]:
    text = (comment or "").strip()
    if not text:
        return None
    match = _MEMO.match(text)
    if match:
        return int(match.group(1))
    for part in text.replace(",", " ").split():
        match = _MEMO.match(part)
        if match:
            return int(match.group(1))
    return None


class DepositWatch:
    def __init__(self, settings: Settings, db: Storage, bot) -> None:
        self.settings = settings
        self.db = db
        self.bot = bot
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop(), name="deposit-watch")

    async def stop(self) -> None:
        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(WATCH_SEC)
                await self.apply()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("deposit watch")

    async def apply(self, user_id: int | None = None) -> list[tuple[str, float]]:
        async with self._lock:
            return await self._apply(user_id)

    async def _apply(self, user_id: int | None) -> list[tuple[str, float]]:
        if not (self.settings.ton_address or "").strip():
            return []
        want = user_memo(user_id) if user_id else None
        credited: list[tuple[str, float]] = []
        for asset, rows in (
            ("TON", await fetch_ton_incoming(self.settings)),
            ("USDT", await fetch_usdt_incoming(self.settings)),
        ):
            for row in rows:
                comment = (row.get("comment") or "").strip()
                hashed = (row.get("hash") or "").strip()
                amount = float(row.get("amount") or 0)
                if not hashed or amount <= 0:
                    continue
                if want and want not in comment.split() and comment != want:
                    pending = await self.db.pending_by_comment(comment)
                    if pending is None or int(pending["user_id"]) != int(user_id):
                        continue
                got = await self._credit_row(asset, comment, hashed, amount)
                if got:
                    credited.append(got)
        return credited

    async def _credit_row(self, asset: str, comment: str, tx_hash: str, amount: float) -> Optional[tuple[str, float]]:
        if await self.db.deposit_by_tx(tx_hash):
            return None
        pending = await self.db.pending_by_comment(comment)
        known = await self.db.deposit_by_comment(comment)
        uid = None
        if pending is not None:
            uid = int(pending["user_id"])
        else:
            uid = memo_user_id(comment)
            if uid is None and known is not None:
                uid = int(known["user_id"])
        if not uid:
            return None
        user = await self.db.get_user(uid)
        if user is None:
            return None
        used_pending = False
        rec_id = None
        if pending is not None:
            if not await self.db.claim_deposit(pending["id"], "done", tx_hash):
                return None
            rec_id = pending["id"]
            used_pending = True
        else:
            rec_id = await self.db.record_deposit(uid, amount, comment or user_memo(uid), asset, tx_hash)
            if not rec_id:
                return None
        try:
            await self.db.credit_asset(uid, asset, amount)
        except Exception:
            log.exception("credit failed tx=%s", tx_hash)
            try:
                if used_pending:
                    await self.db.finish_deposit(rec_id, "pending")
                else:
                    await self.db.execute("DELETE FROM deposits WHERE id = ?", (rec_id,))
            except Exception:
                pass
            return None
        lang = user["lang"] or "ru"
        try:
            await self.bot.send_message(
                uid,
                t(lang, "deposit_ok", amount=money_asset(amount, asset), currency=asset),
            )
        except Exception:
            pass
        return asset, amount
