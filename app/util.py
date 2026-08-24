import re
from html import escape

from aiogram.types import CallbackQuery, Message

from app.i18n import t
from app.storage import DEAL_CANCELLED, DEAL_CLOSED, DEAL_LISTED, DEAL_PENDING

_AMOUNT = re.compile(r"^\d+([.,]\d{1,6})?$")
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
    value = round(float(raw), 6)
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


def clean_ton(text: str) -> str:
    raw = (text or "").strip()
    raw = raw.replace("ton://transfer/", "")
    raw = raw.replace("https://tonviewer.com/", "")
    raw = raw.replace("https://tonscan.org/", "")
    raw = raw.replace("https://ton.app/transfer/", "")
    raw = raw.split("?")[0].split("/")[-1].strip()
    return raw


def valid_ton(text: str) -> bool:
    return bool(_TON.match(clean_ton(text)))


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


def seller_payout(amount: float, commission: float, asset: str = "USDT") -> float:
    raw = float(amount) * (100 - commission) / 100
    if (asset or "").upper() == "TON":
        return round(raw, 9)
    return round(raw, 6)


def money_ton(value) -> str:
    if value is None:
        return "—"
    text = f"{float(value):.9f}".rstrip("0").rstrip(".")
    return text or "0"


def money_asset(value, asset: str) -> str:
    if value is None:
        return "—"
    if (asset or "").upper() == "TON":
        return money_ton(value)
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return text or "0"


def deal_asset(deal) -> str:
    try:
        cur = (deal["currency"] or "USDT").upper()
    except (KeyError, IndexError, TypeError):
        cur = "USDT"
    return "TON" if cur == "TON" else "USDT"


def is_ton_deal(deal) -> bool:
    return deal_asset(deal) == "TON"


def is_nft_deal(deal) -> bool:
    try:
        return (deal["category"] or "") == "nft"
    except (KeyError, IndexError, TypeError):
        return False


def pays_requisites(deal, seller=None) -> bool:
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


def deal_creator(deal) -> int:
    try:
        cid = int(deal["created_by"] or 0)
    except (KeyError, IndexError, TypeError, ValueError):
        cid = 0
    if cid:
        return cid
    try:
        return int(deal["seller_id"] or 0)
    except (KeyError, IndexError, TypeError, ValueError):
        return 0


def fmt_plain(value) -> str:
    return h(value).replace("{", "").replace("}", "")


def deal_currency(deal, fallback: str, seller=None) -> str:
    return deal_asset(deal) or fallback


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


def profile_text(user, lang: str, currency: str, db=None) -> str:
    usdt = 0.0
    ton_bal = 0.0
    frozen_usdt = 0.0
    frozen_ton = 0.0
    if db is not None:
        usdt = db.available(user, "USDT")
        ton_bal = db.available(user, "TON")
        frozen_usdt = db.frozen_of(user, "USDT")
        frozen_ton = db.frozen_of(user, "TON")
    else:
        usdt = max(float(user["balance"] or 0) - float(user["frozen_usdt"] or 0 if "frozen_usdt" in user.keys() else 0), 0)
        try:
            ton_bal = max(float(user["balance_ton"] or 0) - float(user["frozen_ton"] or 0), 0)
            frozen_usdt = float(user["frozen_usdt"] or 0)
            frozen_ton = float(user["frozen_ton"] or 0)
        except (KeyError, IndexError, TypeError):
            ton_bal = 0.0
    return t(
        lang,
        "profile",
        id=user["user_id"],
        nick=h(user["nick"] or user["first_name"] or "-"),
        username=username_of(user),
        deals=user["deals_count"],
        usdt=money_asset(usdt, "USDT"),
        frozen_usdt=money_asset(frozen_usdt, "USDT"),
        ton_bal=money_asset(ton_bal, "TON"),
        frozen_ton=money_asset(frozen_ton, "TON"),
        currency=currency,
        ton=dash(user["ton_address"], lang),
    )


async def render_deal(db, deal, lang: str, currency: str, escrow: str = "", viewer_id: int = 0, reveal_secret: bool = False) -> str:
    from app.catalog import label as cat_label

    buyer = await db.get_user(deal["buyer_id"]) if deal["buyer_id"] else None
    seller = await db.get_user(deal["seller_id"]) if deal["seller_id"] else None
    cat = cat_label(deal["category"] if "category" in deal.keys() else None, lang)
    title = deal["title"] if "title" in deal.keys() else ""
    asset = deal_asset(deal)
    amount = f"{money_asset(deal['amount'], asset)} {asset}" if deal["amount"] is not None else "—"
    nft = await db.get_nft(deal["nft_id"]) if deal["nft_id"] else None
    live = deal["status"] not in {DEAL_PENDING, DEAL_LISTED, DEAL_CANCELLED, DEAL_CLOSED}
    secret_raw = ""
    try:
        secret_raw = (deal["secret"] or "").strip()
    except (KeyError, IndexError, TypeError):
        secret_raw = ""
    party = False
    try:
        party = int(viewer_id or 0) in (int(deal["seller_id"] or 0), int(deal["buyer_id"] or 0))
    except (TypeError, ValueError):
        party = False
    if live and secret_raw and (party or reveal_secret):
        secret = h(secret_raw)
    elif secret_raw:
        secret = t(lang, "deal_secret_hidden")
    else:
        secret = "—"
    key = "deal_opened_nft" if is_nft_deal(deal) else "deal_opened"
    raw_amount = float(deal["amount"] or 0) if deal["amount"] is not None else 0.0
    fee = 2.0
    try:
        from app.config import get_settings
        fee = float(get_settings().commission_percent)
    except Exception:
        fee = 2.0
    seller_get = f"{money_asset(seller_payout(raw_amount, fee, asset), asset)} {asset}" if raw_amount else "—"
    return t(
        lang,
        key,
        id=deal["id"],
        cat=cat,
        title=h(title) if title else cat,
        buyer=username_of(buyer) if buyer else "-",
        buyer_id=deal["buyer_id"] or "—",
        seller=username_of(seller) if seller else "-",
        seller_id=deal["seller_id"] or "—",
        amount=amount,
        fee=f"{fee:g}",
        seller_get=seller_get,
        nft=nft_title(nft) if nft else t(lang, "deal_nft_none"),
        secret=secret,
        desc=h(deal["description"]) if deal["description"] else "—",
        status=t(lang, deal_status_key(deal["status"])),
    )


def history_line(deal, user_id: int, peer_name: str, lang: str, currency: str) -> str:
    seller = user_id == deal["seller_id"]
    asset = deal_asset(deal)
    amount = f"{money_asset(deal['amount'], asset)} {asset}" if deal["amount"] else "—"
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
