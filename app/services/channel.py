from __future__ import annotations

import logging

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.catalog import label
from app.config import Settings
from app.i18n import t
from app.util import h, is_nft_deal, listing_is_buy, money, username_of

log = logging.getLogger("channel")


def public_url(settings: Settings) -> str:
    raw = (settings.deals_channel or "").strip()
    if not raw:
        return ""
    if raw.startswith("http"):
        return raw.split("?")[0]
    raw = raw.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "")
    raw = raw.split("?")[0].strip("/")
    if raw.startswith("@"):
        return f"https://t.me/{raw[1:]}"
    if raw.lstrip("-").isdigit():
        return ""
    if raw:
        return f"https://t.me/{raw}"
    return ""


def chat_id(settings: Settings) -> str | int | None:
    raw = (settings.deals_channel or "").strip()
    if not raw:
        return None
    raw = raw.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "")
    raw = raw.split("?")[0].strip("/")
    if raw.startswith("@"):
        return raw
    if raw.lstrip("-").isdigit():
        return int(raw)
    if raw:
        return "@" + raw
    return None


def listing_text(deal, poster, lang: str, currency: str) -> str:
    cat = label(deal["category"] if "category" in deal.keys() else None, lang)
    title = (deal["title"] if "title" in deal.keys() else "") or cat
    desc = h(deal["description"]) if deal["description"] else "—"
    pay = "₽" if is_nft_deal(deal) else currency
    amount = f"{money(deal['amount'])} {pay}" if deal["amount"] is not None else "—"
    name = username_of(poster) if poster else "-"
    if is_nft_deal(deal) and listing_is_buy(deal):
        key = "channel_listing_nft_buy"
        return t(lang, key, id=deal["id"], cat=cat, title=h(title), buyer=name, amount=amount, desc=desc)
    if is_nft_deal(deal):
        return t(
            lang,
            "channel_listing_nft",
            id=deal["id"],
            cat=cat,
            title=h(title),
            seller=name,
            amount=amount,
            desc=desc,
        )
    if listing_is_buy(deal):
        return t(
            lang,
            "channel_listing_buy",
            id=deal["id"],
            cat=cat,
            title=h(title),
            buyer=name,
            amount=amount,
            desc=desc,
        )
    return t(
        lang,
        "channel_listing",
        id=deal["id"],
        cat=cat,
        title=h(title),
        seller=name,
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
