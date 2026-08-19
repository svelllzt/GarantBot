from __future__ import annotations

from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message

from app import ctx
from app.config import ROOT

EXTS = (".jpg", ".jpeg", ".png", ".webp")
SCREENS = (
    "menu",
    "profile",
    "deal",
    "faq",
    "support",
    "inventory",
    "about",
    "history",
    "requisites",
    "deposit",
    "listing",
)


def assets_dir(settings=None) -> Path:
    raw = "assets"
    if settings is not None:
        raw = getattr(settings, "assets_dir", None) or raw
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def photo_path(screen: str | None, settings=None) -> Path | None:
    if not screen:
        return None
    folder = assets_dir(settings)
    stem = screen.strip().lower()
    for ext in EXTS:
        candidate = folder / f"{stem}{ext}"
        if candidate.is_file():
            return candidate
    return None


def _media(screen: str | None, settings=None, text: str = ""):
    if not screen or len(text) > 1024:
        return None
    file_id = (ctx.screen_ids.get() or {}).get(screen)
    if file_id:
        return file_id
    path = photo_path(screen, settings)
    if path:
        return FSInputFile(path)
    return None


async def paint(event: Message | CallbackQuery, text: str, markup=None, screen: str | None = None, settings=None) -> None:
    file = _media(screen, settings, text)
    if isinstance(event, CallbackQuery):
        msg = event.message
        if msg is None:
            try:
                await event.answer()
            except TelegramBadRequest:
                pass
            return
        sent = False
        if file is not None:
            try:
                if msg.photo:
                    await msg.edit_media(InputMediaPhoto(media=file, caption=text), reply_markup=markup)
                else:
                    try:
                        await msg.delete()
                    except TelegramBadRequest:
                        pass
                    await msg.answer_photo(file, caption=text, reply_markup=markup)
                sent = True
            except TelegramBadRequest:
                sent = False
        if not sent:
            try:
                if msg.photo:
                    await msg.delete()
                    await msg.answer(text, reply_markup=markup)
                else:
                    await msg.edit_text(text, reply_markup=markup)
            except TelegramBadRequest:
                await msg.answer(text, reply_markup=markup)
        try:
            await event.answer()
        except TelegramBadRequest:
            pass
        return
    if file is not None:
        try:
            await event.answer_photo(file, caption=text, reply_markup=markup)
            return
        except TelegramBadRequest:
            pass
    await event.answer(text, reply_markup=markup)


async def send_screen(bot, chat_id: int, text: str, markup=None, screen: str | None = None, settings=None) -> None:
    file = _media(screen, settings, text)
    if file is not None:
        await bot.send_photo(chat_id, file, caption=text, reply_markup=markup)
        return
    await bot.send_message(chat_id, text, reply_markup=markup)
