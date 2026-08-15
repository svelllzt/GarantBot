from __future__ import annotations

import logging
from typing import Any, Optional

from pyrogram import Client
from pyrogram.handlers import RawUpdateHandler
from pyrogram.raw import functions, types

from app.config import Settings
from app.i18n import t
from app.storage import Storage
from app.util import nft_title

log = logging.getLogger("bank")


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


class BankAccount:
    def __init__(self, settings: Settings, db: Storage, bot) -> None:
        self.settings = settings
        self.db = db
        self.bot = bot
        self.client: Optional[Client] = None
        self.me = None

    @property
    def mention(self) -> str:
        if self.settings.bank_username:
            return "@" + self.settings.bank_username.lstrip("@")
        if self.me and self.me.username:
            return "@" + self.me.username
        return "—"

    def enabled(self) -> bool:
        return bool(
            self.settings.bank_api_id
            and self.settings.bank_api_hash
            and self.settings.bank_session
        )

    async def start(self) -> None:
        if not self.enabled():
            log.warning("bank account skipped: empty BANK_SESSION")
            return
        self.client = Client(
            name="bank",
            api_id=self.settings.bank_api_id,
            api_hash=self.settings.bank_api_hash,
            session_string=self.settings.bank_session,
            in_memory=True,
        )
        self.client.add_handler(RawUpdateHandler(self._on_raw))
        await self.client.start()
        self.me = await self.client.get_me()
        log.info("bank account @%s id=%s", self.me.username, self.me.id)

    async def stop(self) -> None:
        if self.client is not None:
            await self.client.stop()
            self.client = None

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

    async def transfer(self, nft, to_user_id: int) -> bool:
        if self.client is None or not nft["msg_id"]:
            return False
        gift_cls = getattr(types, "InputSavedStarGiftUser", None)
        transfer_fn = getattr(functions.payments, "TransferStarGift", None)
        if gift_cls is None or transfer_fn is None:
            return False
        try:
            peer = await self.client.resolve_peer(to_user_id)
            stargift = gift_cls(msg_id=int(nft["msg_id"]))
            try:
                await self.client.invoke(transfer_fn(stargift=stargift, to_id=peer))
                return True
            except Exception as exc:
                if "PAYMENT_REQUIRED" not in str(exc):
                    raise
                invoice_cls = getattr(types, "InputInvoiceStarGiftTransfer", None)
                get_form = getattr(functions.payments, "GetPaymentForm", None)
                send_form = getattr(functions.payments, "SendStarsForm", None)
                if not invoice_cls or not get_form or not send_form:
                    return False
                invoice = invoice_cls(stargift=stargift, to_id=peer)
                form = await self.client.invoke(get_form(invoice=invoice))
                await self.client.invoke(send_form(form_id=form.form_id, invoice=invoice))
                return True
        except Exception:
            log.exception("gift transfer failed msg_id=%s to=%s", nft["msg_id"], to_user_id)
            return False
