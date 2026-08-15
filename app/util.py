import re
from html import escape

from app.i18n import t
from app.storage import DEAL_CLOSED, DEAL_PENDING

_AMOUNT = re.compile(r"^\d+([.,]\d{1,2})?$")
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


def is_cancel(text: str) -> bool:
    value = (text or "").strip().lower()
    return value in {"/cancel", "отмена", "cancel", "❌ отмена", "❌ cancel"}


def profile_text(user, lang: str, currency: str) -> str:
    return t(
        lang,
        "profile",
        id=user["user_id"],
        username=username_of(user),
        deals=user["deals_count"],
        balance=money(user["balance"]),
        currency=currency,
        card=dash(user["card"], lang),
        phone=dash(user["phone"], lang) if not user["bank_name"] else f"{dash(user['phone'], lang)}",
        bank=dash(user["bank_name"], lang),
        ton=dash(user["ton_address"], lang),
    )


async def render_deal(db, deal, lang: str, currency: str) -> str:
    buyer = await db.get_user(deal["buyer_id"])
    seller = await db.get_user(deal["seller_id"])
    nft = await db.get_nft(deal["nft_id"]) if deal["nft_id"] else None
    amount = f"{money(deal['amount'])} {currency}" if deal["amount"] is not None else "—"
    return t(
        lang,
        "deal_opened",
        id=deal["id"],
        buyer=username_of(buyer) if buyer else "-",
        buyer_id=deal["buyer_id"],
        seller=username_of(seller) if seller else "-",
        seller_id=deal["seller_id"],
        amount=amount,
        nft=nft_title(nft) if nft else t(lang, "deal_nft_none"),
        desc=h(deal["description"]) if deal["description"] else "—",
        status=t(lang, deal_status_key(deal["status"])),
    )


def history_line(deal, user_id: int, peer_name: str, lang: str, currency: str) -> str:
    seller = user_id == deal["seller_id"]
    return t(
        lang,
        "history_line",
        id=deal["id"],
        role=t(lang, "deal_seller" if seller else "deal_buyer"),
        amount=f"{money(deal['amount'])} {currency}" if deal["amount"] else "—",
        status=t(lang, deal_status_key(deal["status"] if deal["status"] != DEAL_PENDING else DEAL_CLOSED)),
        peer=peer_name,
    )
