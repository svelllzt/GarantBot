from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.buttons import Theme
from app.config import Settings
from app.i18n import t
from app.storage import Storage
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
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
        if user is None or user.is_bot:
            return await handler(event, data)

        row = await self.db.upsert_user(user.id, user.username, user.first_name or "")
        data["db"] = self.db
        data["settings"] = self.settings
        data["bank"] = self.bank
        data["ton"] = self.ton
        data["db_user"] = row
        data["lang"] = row["lang"] or "ru"
        data["theme"] = Theme(await self.db.button_map())
        ctx.screen_ids.set(await self.db.screen_map())
        ctx.support_url.set(support_link(self.settings))

        if row["banned"] and not self.settings.is_admin(user.id):
            text = t(data["lang"], "banned")
            reason = ""
            try:
                reason = (row["ban_reason"] or "").strip()
            except (KeyError, IndexError, TypeError):
                reason = ""
            if reason:
                text = f"{text}\n{reason}"
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            return None

        return await handler(event, data)
