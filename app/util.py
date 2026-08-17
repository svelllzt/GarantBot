import re
from html import escape

from aiogram.types import CallbackQuery, Message

from app.i18n import t
from app.storage import DEAL_CANCELLED, DEAL_CLOSED, DEAL_LISTED, DEAL_PENDING, KIND_TON_RUB

_AMOUNT = re.compile(r"^\d+([.,]\d{1,2})?$")
_TON_AMT = re.compile(r"^\d+([.,]\d{1,9})?$")
_CARD = re.compile(r"^\d{13,19}$")
_PHONE = re.compile(r"^\+\d{10,15}$")
_TON = re.compile(r"^(UQ|EQ|0:|kQ)[A-Za-z0-9_-]{20,}$")


def money(value) -> str:
    if value is None:
        return "—"
    return f"{float(value):.2f}"


def parse_amount(text: str) -> float | None:
    raw = (text or "").strip().replace(" ", "").replace(",", ".")
    if not _AMOUNT.match(raw):
        return None
    value = round(float(raw), 2)
    if value <= 0 or value > 1_000_000:
        return None
    return value


def parse_ton(text: str) -> float | None:
    raw = (text or "").strip().replace(" ", "").replace(",", ".")
    if not _TON_AMT.match(raw):
        return None
    value = round(float(raw), 9)
    if value <= 0 or value > 1_000_000:
        return None
    return value


def valid_card(text: str) -> bool:
    return bool(_CARD.match(re.sub(r"\s+", "", text or "")))


def valid_phone(text: str) -> bool:
    return bool(_PHONE.match((text or "").strip()))


def valid_ton(text: str) -> bool:
    return bool(_TON.match((text or "").strip()))


def h(value) -> str:
    return escape(str(value), quote=False)


def username_of(row) -> str:
    return row["username"] or "-"


def dash(value, lang: str) -> str:
    if value:
        return h(value)
    return t(lang, "not_set")


def nft_title(nft) -> str:
    if nft is None:
        return ""
    title = nft["title"]
    if nft["num"]:
        return f"{title} #{nft['num']}"
    return title


def deal_status_key(status: str) -> str:
    return f"deal_status_{status}"


def seller_payout(amount: float, commission: float) -> float:
    return round(float(amount) * (100 - commission) / 100, 2)


def money_ton(value) -> str:
    if value is None:
        return "—"
    text = f"{float(value):.9f}".rstrip("0").rstrip(".")
    return text or "0"


def is_ton_deal(deal) -> bool:
    try:
        if deal["kind"] == KIND_TON_RUB:
            return True
        return deal["category"] == "ton"
    except (KeyError, IndexError, TypeError):
        return False


def is_nft_deal(deal) -> bool:
    try:
        return (deal["category"] or "") == "nft"
    except (KeyError, IndexError, TypeError):
        return False


def listing_owner(deal) -> int:
    try:
        return int(deal["seller_id"] or 0) or int(deal["buyer_id"] or 0)
    except (KeyError, IndexError, TypeError):
        return 0


def listing_is_buy(deal) -> bool:
    try:
        return int(deal["seller_id"] or 0) == 0 and int(deal["buyer_id"] or 0) != 0
    except (KeyError, IndexError, TypeError):
        return False


def deal_currency(deal, fallback: str) -> str:
    if is_nft_deal(deal):
        return "₽"
    return fallback


def is_pdf_document(message) -> bool:
    doc = getattr(message, "document", None)
    if doc is None:
        return False
    mime = (doc.mime_type or "").lower()
    name = (doc.file_name or "").lower()
    if mime == "application/pdf":
        return True
    return name.endswith(".pdf") and not mime.startswith("image/")


def has_rub_req(user) -> bool:
    if user is None:
        return False
    if user["card"]:
        return True
    return bool(user["phone"] and user["bank_name"])


def seller_req_text(user, lang: str) -> str:
    if user is None:
        return t(lang, "not_set")
    return (
        f"{t(lang, 'req_card')}: {dash(user['card'], lang)}\n"
        f"{t(lang, 'req_phone')}: {dash(user['phone'], lang)}\n"
        f"{t(lang, 'req_bank_short')}: {dash(user['bank_name'], lang)}"
    )


def is_cancel(text: str) -> bool:
    value = (text or "").strip().lower()
    return value in {"/cancel", "отмена", "cancel", "❌ отмена", "❌ cancel"}


def profile_text(user, lang: str, currency: str) -> str:
    return t(
        lang,
        "profile",
        id=user["user_id"],
        nick=h(user["nick"] or user["first_name"] or "-"),
        username=username_of(user),
        deals=user["deals_count"],
        balance=money(user["balance"]),
        currency=currency,
        card=dash(user["card"], lang),
        phone=dash(user["phone"], lang),
        bank=dash(user["bank_name"], lang),
        ton=dash(user["ton_address"], lang),
    )


async def render_deal(db, deal, lang: str, currency: str, escrow: str = "") -> str:
    from app.catalog import label as cat_label

    buyer = await db.get_user(deal["buyer_id"]) if deal["buyer_id"] else None
    seller = await db.get_user(deal["seller_id"])
    cat = cat_label(deal["category"] if "category" in deal.keys() else None, lang)
    title = deal["title"] if "title" in deal.keys() else ""
    if is_ton_deal(deal):
        req = "—"
        if deal["status"] in {"funded", "rub_sent", "dispute", "closed"}:
            req = seller_req_text(seller, lang)
        return t(
            lang,
            "deal_opened_ton",
            id=deal["id"],
            buyer=username_of(buyer) if buyer else "-",
            buyer_id=deal["buyer_id"],
            seller=username_of(seller) if seller else "-",
            seller_id=deal["seller_id"],
            ton=money_ton(deal["ton_amount"]),
            rub=money(deal["rub_amount"]),
            buyer_ton=dash(deal["buyer_ton"], lang),
            escrow=escrow or "—",
            comment=deal["ton_comment"] or "—",
            received=money_ton(deal["ton_received"]) if deal["ton_received"] else "—",
            req=req,
            desc=h(deal["description"]) if deal["description"] else "—",
            status=t(lang, deal_status_key(deal["status"])),
            payout=deal["payout_hash"] or "—",
        )
    nft = await db.get_nft(deal["nft_id"]) if deal["nft_id"] else None
    pay = deal_currency(deal, currency)
    amount = f"{money(deal['amount'])} {pay}" if deal["amount"] is not None else "—"
    if is_nft_deal(deal):
        show_req = deal["status"] not in {DEAL_PENDING, DEAL_LISTED, DEAL_CANCELLED}
        req = seller_req_text(seller, lang) if show_req and seller else t(lang, "not_set")
        receipt = t(lang, "deal_receipt_yes") if deal["receipt_id"] else t(lang, "deal_receipt_none")
        return t(
            lang,
            "deal_opened_nft",
            id=deal["id"],
            cat=cat,
            title=h(title) if title else cat,
            buyer=username_of(buyer) if buyer else "-",
            buyer_id=deal["buyer_id"] or "—",
            seller=username_of(seller) if seller else "-",
            seller_id=deal["seller_id"] or "—",
            amount=amount,
            nft=nft_title(nft) if nft else t(lang, "deal_nft_none"),
            req=req,
            receipt=receipt,
            desc=h(deal["description"]) if deal["description"] else "—",
            status=t(lang, deal_status_key(deal["status"])),
        )
    return t(
        lang,
        "deal_opened",
        id=deal["id"],
        cat=cat,
        title=h(title) if title else cat,
        buyer=username_of(buyer) if buyer else "-",
        buyer_id=deal["buyer_id"] or "—",
        seller=username_of(seller) if seller else "-",
        seller_id=deal["seller_id"],
        amount=amount,
        nft=nft_title(nft) if nft else t(lang, "deal_nft_none"),
        desc=h(deal["description"]) if deal["description"] else "—",
        status=t(lang, deal_status_key(deal["status"])),
    )


def history_line(deal, user_id: int, peer_name: str, lang: str, currency: str) -> str:
    seller = user_id == deal["seller_id"]
    if is_ton_deal(deal):
        amount = f"{money_ton(deal['ton_amount'])} TON / {money(deal['rub_amount'])} ₽"
    elif is_nft_deal(deal):
        amount = f"{money(deal['amount'])} ₽" if deal["amount"] else "—"
    else:
        amount = f"{money(deal['amount'])} {currency}" if deal["amount"] else "—"
    return t(
        lang,
        "history_line",
        id=deal["id"],
        role=t(lang, "deal_seller" if seller else "deal_buyer"),
        amount=amount,
        status=t(lang, deal_status_key(deal["status"] if deal["status"] != DEAL_PENDING else DEAL_CLOSED)),
        peer=peer_name,
    )


async def paint(event: Message | CallbackQuery, text: str, markup=None, screen: str | None = None, settings=None) -> None:
    from app.media import paint as send

    await send(event, text, markup, screen=screen, settings=settings)


def extract_emoji_id(message: Message) -> str | None:
    for ent in message.entities or []:
        if getattr(ent, "custom_emoji_id", None):
            return ent.custom_emoji_id
    for ent in message.caption_entities or []:
        if getattr(ent, "custom_emoji_id", None):
            return ent.custom_emoji_id
    raw = (message.text or message.caption or "").strip()
    if raw.isdigit() and len(raw) >= 15:
        return raw
    return None


def ban_notice(lang: str, reason: str | None, support: str) -> str:
    extra = ""
    clean = (reason or "").strip()
    if clean:
        extra = t(lang, "banned_reason", reason=h(clean))
    return t(lang, "banned", reason=extra, support=(support or "").lstrip("@") or "—")
