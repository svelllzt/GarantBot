from __future__ import annotations

from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message

from app.config import ROOT

EXTS = (".jpg", ".jpeg", ".png", ".webp")
SCREENS = (
    "menu",
    "profile",
    "deal",
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


async def paint(event: Message | CallbackQuery, text: str, markup=None, screen: str | None = None, settings=None) -> None:
    path = photo_path(screen, settings)
    file = FSInputFile(path) if path and len(text) <= 1024 else None
    if isinstance(event, CallbackQuery):
        msg = event.message
        if file is not None:
            if msg.photo:
                try:
                    await msg.edit_media(InputMediaPhoto(media=file, caption=text), reply_markup=markup)
                except TelegramBadRequest:
                    await msg.answer_photo(file, caption=text, reply_markup=markup)
            else:
                try:
                    await msg.delete()
                except TelegramBadRequest:
                    pass
                await msg.answer_photo(file, caption=text, reply_markup=markup)
        else:
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
        await event.answer_photo(file, caption=text, reply_markup=markup)
        return
    await event.answer(text, reply_markup=markup)


async def send_screen(bot, chat_id: int, text: str, markup=None, screen: str | None = None, settings=None) -> None:
    path = photo_path(screen, settings)
    if path and len(text) <= 1024:
        await bot.send_photo(chat_id, FSInputFile(path), caption=text, reply_markup=markup)
        return
    await bot.send_message(chat_id, text, reply_markup=markup)
