from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from app.pyro import Client, RawUpdateHandler, functions, types

from app.config import Settings
from app.i18n import t
from app.storage import DEAL_CLOSED, DEAL_PAID, DEAL_REVIEW, NFT_TRANSFERRED, Storage
from app.services.fragment import StarsBuyer
from app.util import nft_title

log = logging.getLogger("bank")

WATCH_SEC = 180
STARS_TTL = 20


def _user_id(peer: Any) -> Optional[int]:
    if peer is None:
        return None
    return getattr(peer, "user_id", None)


def _gift_meta(gift: Any) -> dict[str, Any]:
    unique = gift.__class__.__name__ == "StarGiftUnique" or getattr(gift, "slug", None)
    title = getattr(gift, "title", None)
    if not title:
        title = "Collectible gift" if unique else "Gift"
    return {
        "gift_id": str(getattr(gift, "id", "") or getattr(gift, "slug", "") or ""),
        "slug": getattr(gift, "slug", None),
        "title": title,
        "num": getattr(gift, "num", None),
        "is_unique": bool(unique),
    }


def _err_text(exc: BaseException) -> str:
    return str(exc).upper()


def _stars_int(balance: Any) -> Optional[int]:
    if balance is None:
        return None
    if isinstance(balance, int):
        return int(balance)
    amount = getattr(balance, "amount", None)
    if amount is None:
        return None
    return int(amount)


def _stargift(nft) -> Any:
    slug = str(nft["slug"] or "").strip()
    slug_cls = getattr(types, "InputSavedStarGiftSlug", None)
    if slug and slug_cls is not None:
        return slug_cls(slug=slug)
    gift_cls = getattr(types, "InputSavedStarGiftUser", None)
    if gift_cls is None or not nft["msg_id"]:
        return None
    return gift_cls(msg_id=int(nft["msg_id"]))


def _invoice_stars(form: Any) -> Optional[int]:
    invoice = getattr(form, "invoice", None)
    if invoice is None:
        return None
    currency = (getattr(invoice, "currency", "") or "").upper()
    if currency and currency != "XTR":
        return None
    total = 0
    for price in getattr(invoice, "prices", None) or []:
        total += int(getattr(price, "amount", 0) or 0)
    return total if total > 0 else None


class BankAccount:
    def __init__(self, settings: Settings, db: Storage, bot) -> None:
        self.settings = settings
        self.db = db
        self.bot = bot
        self.client: Optional[Client] = None
        self.me = None
        self._stars: Optional[int] = None
        self._stars_at = 0.0
        self._low_alerted = False
        self._watch_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self.stars_buyer = StarsBuyer(settings)
        self.stars_buyer.on_event = self._notify_admins

    @property
    def mention(self) -> str:
        if self.settings.bank_username:
            return "@" + self.settings.bank_username.lstrip("@")
        if self.me and self.me.username:
            return "@" + self.me.username
        return "—"

    @property
    def online(self) -> bool:
        return self.client is not None

    @property
    def fee(self) -> int:
        n = int(self.settings.bank_transfer_stars or 0)
        return n if n > 0 else 25

    @property
    def min_stars(self) -> int:
        n = int(self.settings.bank_min_stars or 0)
        return n if n > 0 else 50

    def enabled(self) -> bool:
        return bool(
            self.settings.bank_api_id
            and self.settings.bank_api_hash
            and self.settings.bank_session
        )

    async def _ask(self, prompt: str) -> str:
        return (await asyncio.to_thread(input, prompt)).strip()

    async def _first_login(self) -> bool:
        print("\nПервый вход банковского аккаунта (NFT). Код придёт в Telegram/SMS.")
        print("api_id / api_hash: https://my.telegram.org\n")
        try:
            if not self.settings.bank_api_id:
                raw = await self._ask("api_id: ")
                if not raw.isdigit():
                    print("api_id должен быть числом. Банк пропущен, бот всё равно запустится.")
                    return False
                self.settings.patch("bank_api_id", raw)
            if not self.settings.bank_api_hash:
                raw = await self._ask("api_hash: ")
                if len(raw) < 8:
                    print("api_hash пустой. Банк пропущен, бот всё равно запустится.")
                    return False
                self.settings.patch("bank_api_hash", raw)
            workdir = Path(self.settings.db_path).expanduser().resolve().parent
            workdir.mkdir(parents=True, exist_ok=True)
            client = Client(
                name="bank_login",
                api_id=self.settings.bank_api_id,
                api_hash=self.settings.bank_api_hash,
                workdir=str(workdir),
                workers=1,
            )
            await client.start()
            me = await client.get_me()
            session = await client.export_session_string()
            await client.stop()
            for leftover in (workdir / "bank_login.session", workdir / "bank_login.session-journal"):
                try:
                    if leftover.exists():
                        leftover.unlink()
                except OSError:
                    pass
            if not session:
                print("Не удалось получить session. Банк пропущен.")
                return False
            self.settings.patch("bank_session", session)
            if me.username:
                self.settings.patch("bank_username", me.username)
            print(f"Банк сохранён: @{me.username or '-'} id={me.id}\n")
            return True
        except Exception:
            log.exception("bank first login failed")
            print("Банк не вошёл. Бот всё равно запустится без NFT.")
            return False

    async def start(self) -> None:
        if not self.enabled():
            if sys.stdin.isatty():
                await self._first_login()
            if not self.enabled():
                log.warning("bank account skipped: empty [bank] session (run python main.py in a console to log in)")
                await self.stars_buyer.start()
                return
        self.client = Client(
            name="bank",
            api_id=self.settings.bank_api_id,
            api_hash=self.settings.bank_api_hash,
            session_string=self.settings.bank_session,
            in_memory=True,
            workers=4,
        )
        self.client.add_handler(RawUpdateHandler(self._on_raw))
        await self.client.start()
        self.me = await self.client.get_me()
        try:
            fresh = await self.client.export_session_string()
        except Exception:
            fresh = ""
        if fresh and fresh != self.settings.bank_session:
            try:
                self.settings.patch("bank_session", fresh)
            except Exception:
                log.exception("failed to write [bank] session")
        if self.me.username:
            try:
                self.settings.patch("bank_username", self.me.username)
            except Exception:
                log.exception("failed to write [bank] username")
        log.info("bank account @%s id=%s", self.me.username, self.me.id)
        await self.refresh_stars()
        await self.stars_buyer.start()
        await self._maybe_alert_stars()
        self._watch_task = asyncio.create_task(self._watch(), name="bank-stars")

    async def stop(self) -> None:
        task = self._watch_task
        self._watch_task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if self.client is not None:
            await self.client.stop()
            self.client = None

    async def stars(self, force: bool = False) -> Optional[int]:
        if (
            not force
            and self._stars is not None
            and (asyncio.get_running_loop().time() - self._stars_at) < STARS_TTL
        ):
            return self._stars
        return await self.refresh_stars()

    async def refresh_stars(self) -> Optional[int]:
        if self.client is None:
            return None
        try:
            status = await self.client.invoke(functions.payments.GetStarsStatus(peer=types.InputPeerSelf()))
            amount = _stars_int(getattr(status, "balance", None))
            if amount is None:
                return self._stars
            self._stars = amount
            self._stars_at = asyncio.get_running_loop().time()
            log.info("bank stars=%s", amount)
            return amount
        except Exception:
            log.exception("stars status failed")
            return self._stars

    async def _on_raw(self, client, update, users, chats) -> None:
        msg = None
        if isinstance(update, types.UpdateNewMessage):
            msg = update.message
        elif isinstance(update, types.UpdateNewChannelMessage):
            msg = update.message
        if not isinstance(msg, types.MessageService):
            return
        action = msg.action
        gift_types = tuple(
            cls
            for name in ("MessageActionStarGift", "MessageActionStarGiftUnique")
            if (cls := getattr(types, name, None)) is not None
        )
        if not gift_types or not isinstance(action, gift_types):
            return
        if getattr(msg, "out", False):
            return
        await self._ingest(msg, action)

    async def _ingest(self, msg, action) -> None:
        gift = getattr(action, "gift", None)
        if gift is None:
            return
        sender = _user_id(getattr(action, "from_id", None)) or _user_id(getattr(msg, "from_id", None))
        if sender is None:
            sender = _user_id(getattr(msg, "peer_id", None))
        if sender is None:
            return
        meta = _gift_meta(gift)
        if not meta["is_unique"]:
            log.info("skip non-unique gift from %s", sender)
            return
        nft_id = await self.db.add_nft(
            sender,
            gift_id=meta["gift_id"],
            slug=meta["slug"],
            title=meta["title"],
            num=meta["num"],
            msg_id=getattr(msg, "id", None),
            from_user_id=sender,
            is_unique=meta["is_unique"],
        )
        if nft_id is None:
            return
        user = await self.db.get_user(sender)
        if user is None or self.bot is None:
            return
        title = meta["title"]
        if meta["num"]:
            title = f"{title} #{meta['num']}"
        try:
            await self.bot.send_message(sender, t(user["lang"] or "ru", "inv_new", title=title))
        except Exception:
            log.exception("failed to notify %s about gift", sender)

    async def transfer(self, nft, to_user_id: int) -> str:
        async with self._lock:
            return await self._transfer(nft, to_user_id)

    async def _transfer(self, nft, to_user_id: int) -> str:
        if nft is None:
            return "fail"
        if self.client is None:
            return "offline"
        transfer_fn = getattr(functions.payments, "TransferStarGift", None)
        stargift = _stargift(nft)
        if transfer_fn is None or stargift is None:
            return "fail"
        try:
            peer = await self.client.resolve_peer(to_user_id)
            try:
                await self.client.invoke(transfer_fn(stargift=stargift, to_id=peer))
                return "ok"
            except Exception as exc:
                if "PAYMENT_REQUIRED" not in _err_text(exc):
                    raise
                invoice_cls = getattr(types, "InputInvoiceStarGiftTransfer", None)
                get_form = getattr(functions.payments, "GetPaymentForm", None)
                send_form = getattr(functions.payments, "SendStarsForm", None)
                if not invoice_cls or not get_form or not send_form:
                    return "fail"
                invoice = invoice_cls(stargift=stargift, to_id=peer)
                form = await self.client.invoke(get_form(invoice=invoice))
                fee = _invoice_stars(form) or self.fee
                stars = await self.stars()
                if stars is not None and stars < fee:
                    if await self._ensure_stars(fee):
                        stars = self._stars
                        form = await self.client.invoke(get_form(invoice=invoice))
                        fee = _invoice_stars(form) or fee
                if stars is not None and stars < fee:
                    await self._alert_no_stars(fee, stars)
                    return "no_stars"
                try:
                    await self.client.invoke(send_form(form_id=form.form_id, invoice=invoice))
                except Exception as pay_exc:
                    if "BALANCE_TOO_LOW" in _err_text(pay_exc):
                        if await self._ensure_stars(fee):
                            form = await self.client.invoke(get_form(invoice=invoice))
                            await self.client.invoke(send_form(form_id=form.form_id, invoice=invoice))
                        else:
                            await self.refresh_stars()
                            await self._alert_no_stars(fee, self._stars)
                            return "no_stars"
                    else:
                        raise
                if self._stars is not None:
                    self._stars = max(0, self._stars - fee)
                asyncio.create_task(self._refresh_silent())
                return "ok"
        except Exception:
            log.exception("gift transfer failed msg_id=%s to=%s", nft["msg_id"], to_user_id)
            return "fail"

    async def _ensure_stars(self, need: int) -> bool:
        stars = await self.stars(force=True)
        if stars is not None and stars >= need:
            return True
        if not self.stars_buyer.enabled():
            return False
        bought = await self.stars_buyer.buy_for_bank()
        if not bought:
            return False
        await asyncio.sleep(8)
        stars = await self.refresh_stars()
        return stars is not None and stars >= need

    async def _refresh_silent(self) -> None:
        try:
            await self.refresh_stars()
            await self._maybe_alert_stars()
        except Exception:
            log.exception("silent stars refresh")

    async def _watch(self) -> None:
        while True:
            try:
                await asyncio.sleep(WATCH_SEC)
                if self.client is None:
                    continue
                await self.refresh_stars()
                if self._stars is not None and self._stars < self.fee:
                    await self._ensure_stars(self.fee)
                await self._maybe_alert_stars()
                await self._retry_pending()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("bank watcher")

    async def _retry_pending(self) -> None:
        if self.client is None:
            return
        stars = await self.stars()
        if stars is not None and stars < self.fee:
            if not await self._ensure_stars(self.fee):
                return
        pending = await self.db.pending_nft_sends()
        for deal in pending:
            fresh = await self.db.get_deal(deal["id"])
            if fresh is None or fresh["nft_sent"] or not fresh["nft_id"] or not fresh["buyer_id"]:
                continue
            if fresh["status"] not in {DEAL_PAID, DEAL_REVIEW, DEAL_CLOSED}:
                continue
            nft = await self.db.get_nft(fresh["nft_id"])
            result = await self.transfer(nft, fresh["buyer_id"])
            if result == "ok":
                await self.db.touch_deal(fresh["id"], nft_sent=1)
                if fresh["status"] in {DEAL_CLOSED, DEAL_REVIEW}:
                    await self.db.set_nft_status(
                        fresh["nft_id"],
                        NFT_TRANSFERRED,
                        owner_id=fresh["buyer_id"],
                        deal_id=fresh["id"],
                    )
                await self._notify_nft_sent(fresh, nft)
            elif result == "no_stars":
                break

    async def _notify_nft_sent(self, deal, nft) -> None:
        if self.bot is None:
            return
        title = nft_title(nft) if nft is not None else ""
        for uid in (deal["buyer_id"], deal["seller_id"]):
            if not uid:
                continue
            user = await self.db.get_user(uid)
            if user is None:
                continue
            try:
                await self.bot.send_message(
                    uid,
                    t(user["lang"] or "ru", "deal_nft_retry_ok", id=deal["id"], title=title),
                )
            except Exception:
                log.exception("failed to notify %s about nft retry", uid)

    async def _maybe_alert_stars(self) -> None:
        stars = self._stars
        if stars is None:
            return
        if stars >= self.min_stars:
            self._low_alerted = False
            return
        pending = await self.db.pending_nft_sends()
        await self._alert_no_stars(self.fee, stars, pending=len(pending))

    async def _alert_no_stars(self, fee: int, stars: Optional[int], pending: Optional[int] = None) -> None:
        if self._low_alerted:
            return
        self._low_alerted = True
        if pending is None:
            rows = await self.db.pending_nft_sends()
            pending = len(rows)
        await self._notify_admins(
            "admin_stars_low",
            stars=stars if stars is not None else "—",
            min=self.min_stars,
            fee=fee,
            pending=pending,
            pack=self.stars_buyer.pack(),
        )

    async def _notify_admins(self, key: str, **kwargs: Any) -> None:
        if self.bot is None:
            return
        text = t("ru", key, **kwargs)
        for aid in self.settings.admins:
            try:
                await self.bot.send_message(aid, text)
            except Exception:
                log.exception("failed to alert admin %s", aid)
