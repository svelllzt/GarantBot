from __future__ import annotations

import logging
import time

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, TelegramObject, Update
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.catalog import label
from app.config import Settings
from app.i18n import t
from app.util import deal_asset, h, is_nft_deal, listing_is_buy, money_asset, username_of

log = logging.getLogger("channel")
_sub_ok: dict[int, float] = {}
_SUB_TTL = 90.0


def _raw_channel(settings: Settings, attr: str = "deals_channel") -> str:
    return str(getattr(settings, attr, "") or "").strip()


def public_url(settings: Settings, attr: str = "deals_channel") -> str:
    raw = _raw_channel(settings, attr)
    if not raw:
        return ""
    if raw.startswith("http"):
        return raw.split("?")[0]
    raw = raw.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "")
    raw = raw.split("?")[0].strip("/")
    if raw.startswith("+") or raw.lower().startswith("joinchat/"):
        return f"https://t.me/{raw}"
    if raw.startswith("@"):
        return f"https://t.me/{raw[1:]}"
    if raw.lstrip("-").isdigit():
        return ""
    if raw:
        return f"https://t.me/{raw}"
    return ""


def chat_id(settings: Settings, attr: str = "deals_channel") -> str | int | None:
    raw = _raw_channel(settings, attr)
    if not raw:
        return None
    if raw.startswith("http") and ("+" in raw or "joinchat" in raw.lower()):
        return None
    raw = raw.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "")
    raw = raw.split("?")[0].strip("/")
    if raw.startswith("+") or raw.lower().startswith("joinchat/"):
        return None
    if raw.startswith("@"):
        return raw
    if raw.lstrip("-").isdigit():
        return int(raw)
    if raw:
        return "@" + raw
    return None


def required_chat(settings: Settings) -> str | int | None:
    return chat_id(settings, "required_channel")


def required_url(settings: Settings) -> str:
    return public_url(settings, "required_channel")


def sub_cached(user_id: int) -> bool:
    exp = _sub_ok.get(int(user_id) or 0, 0)
    return exp > time.monotonic()


def remember_sub(user_id: int) -> None:
    _sub_ok[int(user_id)] = time.monotonic() + _SUB_TTL


def forget_sub(user_id: int | None = None) -> None:
    if user_id is None:
        _sub_ok.clear()
        return
    _sub_ok.pop(int(user_id), None)


async def is_subscribed(bot, settings: Settings, user_id: int) -> bool:
    raw = (settings.required_channel or "").strip()
    if not raw:
        return True
    uid = int(user_id or 0)
    if uid <= 0:
        return True
    if settings.is_admin(uid):
        return True
    if sub_cached(uid):
        return True
    chat = required_chat(settings)
    if chat is None or bot is None:
        return False
    try:
        member = await bot.get_chat_member(chat, uid)
        status = getattr(member, "status", None)
        status = getattr(status, "value", status)
        ok = str(status or "") not in {"left", "kicked"}
    except Exception as exc:
        text = str(exc).lower()
        if any(word in text for word in ("participant", "not a member", "user not found", "kicked", "left")):
            ok = False
        else:
            log.exception("subscribe check failed")
            ok = True
    if ok:
        remember_sub(uid)
    else:
        forget_sub(uid)
    return ok


async def channel_link(bot, settings: Settings) -> str:
    url = required_url(settings)
    if url:
        return url
    chat = required_chat(settings)
    if chat is None or bot is None:
        return ""
    try:
        info = await bot.get_chat(chat)
        username = getattr(info, "username", None) or ""
        if username:
            return f"https://t.me/{username.lstrip('@')}"
        invite = getattr(info, "invite_link", None) or ""
        if invite:
            return invite
        return await bot.export_chat_invite_link(chat)
    except Exception:
        log.exception("subscribe link failed")
        return ""


def subscribe_markup(lang: str, url: str) -> InlineKeyboardMarkup:
    from app.buttons import Theme
    from app.keyboards import NavCB

    theme = Theme({})
    kb = InlineKeyboardBuilder()
    if url:
        kb.button(
            text=theme.text("sub_open", lang),
            style=theme.style("sub_open"),
            icon_custom_emoji_id=theme.emoji("sub_open"),
            url=url,
        )
    theme.add(kb, "sub_check", lang, callback_data=NavCB(a="subchk").pack())
    kb.adjust(1)
    return kb.as_markup()


def _gate_inner(event: TelegramObject):
    if isinstance(event, Update):
        return event.event
    return event


async def send_sub_gate(event, lang: str, settings: Settings, bot=None) -> None:
    target = _gate_inner(event)
    bot = bot or getattr(event, "bot", None) or getattr(target, "bot", None)
    url = await channel_link(bot, settings) if bot else required_url(settings)
    text = t(lang, "sub_need")
    markup = subscribe_markup(lang, url)
    if isinstance(target, CallbackQuery):
        try:
            await target.answer()
        except Exception:
            pass
        msg = target.message
        if msg is None:
            return
        try:
            await msg.edit_text(text, reply_markup=markup)
            return
        except Exception:
            pass
        try:
            await msg.edit_caption(caption=text, reply_markup=markup)
            return
        except Exception:
            pass
        try:
            await msg.answer(text, reply_markup=markup)
        except Exception:
            pass
        return
    if isinstance(target, Message):
        try:
            await target.answer(text, reply_markup=markup)
        except Exception:
            pass


def listing_text(deal, poster, lang: str, currency: str) -> str:
    cat = label(deal["category"] if "category" in deal.keys() else None, lang)
    title = (deal["title"] if "title" in deal.keys() else "") or cat
    desc = h(deal["description"]) if deal["description"] else "—"
    asset = deal_asset(deal)
    amount = f"{money_asset(deal['amount'], asset)} {asset}" if deal["amount"] is not None else "—"
    name = username_of(poster) if poster else "-"
    buy = listing_is_buy(deal)
    if is_nft_deal(deal):
        key = "channel_listing_nft_buy" if buy else "channel_listing_nft"
    else:
        key = "channel_listing_buy" if buy else "channel_listing"
    return t(
        lang,
        key,
        id=deal["id"],
        cat=cat,
        title=h(title),
        seller=name,
        buyer=name,
        amount=amount,
        desc=desc,
    )


def listing_kb(settings: Settings, deal_id: int, lang: str) -> InlineKeyboardMarkup | None:
    user = (settings.bot_username or "").lstrip("@")
    if not user:
        return None
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "channel_open"), style="success", url=f"https://t.me/{user}?start=d{deal_id}")
    return kb.as_markup()


async def publish(bot, settings: Settings, db, deal, seller) -> int | None:
    chat = chat_id(settings)
    if chat is None:
        return None
    deal = await db.get_deal(deal["id"])
    text = listing_text(deal, seller, "ru", settings.currency)
    markup = listing_kb(settings, deal["id"], "ru")
    try:
        msg = await bot.send_message(chat, text, reply_markup=markup)
    except Exception:
        log.exception("channel publish failed")
        return None
    await db.touch_deal(deal["id"], channel_msg_id=msg.message_id)
    return msg.message_id


async def mark(bot, settings: Settings, deal, key: str) -> None:
    chat = chat_id(settings)
    msg_id = None
    try:
        msg_id = deal["channel_msg_id"]
    except (KeyError, IndexError, TypeError):
        msg_id = None
    if chat is None or not msg_id:
        return
    try:
        text = listing_text(deal, None, "ru", settings.currency)
        text = text + "\n\n" + t("ru", key)
        await bot.edit_message_text(text, chat_id=chat, message_id=int(msg_id), reply_markup=None)
    except Exception:
        log.exception("channel edit failed")
