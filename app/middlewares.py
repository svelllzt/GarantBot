from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, TelegramObject, Update

from app.buttons import Theme
from app.config import Settings
from app.storage import Storage
from app.util import ban_notice
from app import ctx


def support_link(settings: Settings) -> str:
    chat = (settings.support_chat or "").strip()
    if chat.startswith("http"):
        return chat
    if chat.startswith("@"):
        return f"https://t.me/{chat[1:]}"
    if chat.lstrip("-").isdigit():
        return ""
    if chat:
        return f"https://t.me/{chat.lstrip('@')}"
    user = (settings.support_username or "").lstrip("@")
    if user:
        return f"https://t.me/{user}"
    return ""


def _from_user(event: TelegramObject, data: dict[str, Any]):
    user = data.get("event_from_user")
    if user is not None:
        return user
    if isinstance(event, Update):
        return event.event_from_user
    inner = event.event if isinstance(event, Update) else event
    return getattr(inner, "from_user", None) or getattr(event, "from_user", None)


def _inner(event: TelegramObject):
    if isinstance(event, Update):
        return event.event
    return event


class ContextMiddleware(BaseMiddleware):
    def __init__(self, db: Storage, settings: Settings, bank, ton) -> None:
        self.db = db
        self.settings = settings
        self.bank = bank
        self.ton = ton

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        data["settings"] = self.settings
        data["bank"] = self.bank
        data["ton"] = self.ton
        data.setdefault("lang", "ru")
        data.setdefault("theme", Theme({}))

        user = _from_user(event, data)
        if user is None or getattr(user, "is_bot", False):
            return await handler(event, data)

        row = await self.db.upsert_user(user.id, user.username, user.first_name or "")
        data["db_user"] = row
        data["lang"] = row["lang"] or "ru"
        data["theme"] = Theme(await self.db.button_map())
        ctx.screen_ids.set(await self.db.screen_map())
        ctx.support_url.set(support_link(self.settings))

        banned = False
        try:
            banned = bool(int(row["banned"] or 0))
        except (KeyError, IndexError, TypeError, ValueError):
            banned = False
        if banned and not self.settings.is_admin(user.id):
            text = ban_notice(data["lang"], row["ban_reason"] if "ban_reason" in row.keys() else "", self.settings.support_username)
            await _send_ban(event, text)
            return None

        return await handler(event, data)


async def _send_ban(event: TelegramObject, text: str) -> None:
    target = _inner(event)
    if isinstance(target, CallbackQuery):
        try:
            await target.answer()
        except Exception:
            pass
        msg = target.message
        if msg is None:
            return
        try:
            await msg.edit_text(text, reply_markup=None)
            return
        except Exception:
            pass
        try:
            await msg.edit_caption(caption=text, reply_markup=None)
            return
        except Exception:
            pass
        try:
            await msg.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        try:
            await msg.answer(text, reply_markup=ReplyKeyboardRemove())
        except Exception:
            pass
        return
    if isinstance(target, Message):
        try:
            await target.answer(text, reply_markup=ReplyKeyboardRemove())
        except Exception:
            pass


def install(dp: Dispatcher, mw: ContextMiddleware) -> None:
    dp.update.outer_middleware(mw)
