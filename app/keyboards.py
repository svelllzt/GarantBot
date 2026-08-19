from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.buttons import KEYS, PAGE_SIZE, STYLES, Theme
from app.i18n import t
from app.storage import DEAL_DISPUTE, DEAL_LISTED, DEAL_OPEN, DEAL_PENDING, DEAL_REVIEW, Storage
from app import ctx
from app.util import is_nft_deal


class LangCB(CallbackData, prefix="lang"):
    code: str


class NavCB(CallbackData, prefix="nav"):
    a: str


class DealCB(CallbackData, prefix="deal"):
    a: str
    i: int = 0
    x: int = 0


class CatCB(CallbackData, prefix="cat"):
    k: str = "goods"
    g: int = 0


class WalletCB(CallbackData, prefix="wal"):
    a: str
    i: int = 0
    m: str = ""


class AdminCB(CallbackData, prefix="adm"):
    a: str
    i: int = 0
    x: int = 0
    k: str = "-"


class FaqCB(CallbackData, prefix="faq"):
    a: str
    i: int = 0


class BtnCB(CallbackData, prefix="ub"):
    a: str
    k: str = "-"
    p: int = 0
    s: str = "-"


async def home_kb(db: Storage, user_id: int, lang: str, theme: Theme) -> InlineKeyboardMarkup:
    active = await db.active_deal(user_id)
    from app.config import get_settings
    admin = get_settings().is_admin(user_id)
    return main_menu(lang, theme, active["id"] if active else None, admin=admin)


def main_menu(lang: str, theme: Theme, deal_id: int | None = None, admin: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_deal", lang, callback_data=NavCB(a="deal").pack())
    theme.add(kb, "btn_faq", lang, callback_data=NavCB(a="faq").pack())
    theme.add(kb, "btn_profile", lang, callback_data=NavCB(a="profile").pack())
    url = ctx.support_url.get() or ""
    if url:
        kb.button(
            text=theme.text("btn_support", lang),
            style=theme.style("btn_support"),
            icon_custom_emoji_id=theme.emoji("btn_support"),
            url=url,
        )
    else:
        theme.add(kb, "btn_support", lang, callback_data=NavCB(a="support").pack())
    rows = [1, 2, 1]
    if admin:
        theme.add(kb, "btn_admin", lang, callback_data=NavCB(a="admin").pack())
        rows.append(1)
    if deal_id:
        theme.add(kb, "active_deal_btn", lang, callback_data=DealCB(a="open", i=deal_id).pack(), fmt={"id": deal_id})
        rows.append(1)
    kb.adjust(*rows)
    return kb.as_markup()


def cancel_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_cancel", lang, callback_data=NavCB(a="fsmx").pack())
    return kb.as_markup()


def lang_kb(theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "lang_ru", "ru", callback_data=LangCB(code="ru").pack())
    theme.add(kb, "lang_en", "en", callback_data=LangCB(code="en").pack())
    kb.adjust(2)
    return kb.as_markup()


def profile_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_req", lang, callback_data=NavCB(a="req").pack())
    theme.add(kb, "deposit", lang, callback_data=NavCB(a="dep").pack())
    theme.add(kb, "withdraw", lang, callback_data=NavCB(a="wd").pack())
    theme.add(kb, "btn_inventory", lang, callback_data=NavCB(a="inv").pack())
    theme.add(kb, "btn_history", lang, callback_data=NavCB(a="hist").pack())
    theme.add(kb, "change_lang", lang, callback_data=NavCB(a="lang").pack())
    theme.add(kb, "btn_about", lang, callback_data=NavCB(a="about").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1, 2, 2, 1, 1, 1)
    return kb.as_markup()


def requisites_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "req_ton", lang, callback_data=NavCB(a="req_ton").pack())
    theme.add(kb, "btn_back", lang, callback_data=NavCB(a="profile").pack())
    kb.adjust(1)
    return kb.as_markup()


def currency_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_cur_usdt", lang, callback_data=DealCB(a="cur", x=0).pack())
    theme.add(kb, "deal_cur_ton", lang, callback_data=DealCB(a="cur", x=1).pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    return kb.as_markup()


def asset_pick_kb(lang: str, theme: Theme, action: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deposit_asset_usdt", lang, callback_data=WalletCB(a=action, m="USDT").pack())
    theme.add(kb, "deposit_asset_ton", lang, callback_data=WalletCB(a=action, m="TON").pack())
    theme.add(kb, "btn_cancel", lang, callback_data=NavCB(a="fsmx").pack())
    kb.adjust(1)
    return kb.as_markup()


def deal_mode_kb(lang: str, theme: Theme, channel_url: str = "", public: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_private", lang, callback_data=DealCB(a="mode", x=0).pack())
    if public:
        theme.add(kb, "deal_public", lang, callback_data=DealCB(a="mode", x=1).pack())
    if channel_url:
        kb.button(text=t(lang, "deal_channel"), style="primary", url=channel_url)
    theme.add(kb, "btn_feed", lang, callback_data=NavCB(a="feed").pack())
    theme.add(kb, "btn_back", lang, callback_data=NavCB(a="deal").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    return kb.as_markup()


def group_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    from app.catalog import GROUPS, group_label

    kb = InlineKeyboardBuilder()
    styles = {"acc": "primary", "nft": "success", "goods": "primary", "other": "primary"}
    for key, _ in GROUPS:
        kb.button(
            text=group_label(key, lang),
            style=styles.get(key, "primary"),
            callback_data=CatCB(k=key, g=1).pack(),
        )
    theme.add(kb, "btn_feed", lang, callback_data=NavCB(a="feed").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    return kb.as_markup()


def category_kb(lang: str, theme: Theme, group: str | None = None) -> InlineKeyboardMarkup:
    from app.catalog import CATS, group_cats, label

    kb = InlineKeyboardBuilder()
    keys = group_cats(group) if group else CATS
    for key in keys:
        style = "success" if key == "nft" else "primary"
        kb.button(text=label(key, lang), style=style, callback_data=CatCB(k=key, g=0).pack())
    theme.add(kb, "btn_back", lang, callback_data=NavCB(a="deal").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    return kb.as_markup()


def take_kb(lang: str, theme: Theme, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_take", lang, callback_data=DealCB(a="take", i=deal_id).pack())
    theme.add(kb, "deal_manual_btn", lang, callback_data=DealCB(a="memo", i=deal_id).pack())
    theme.add(kb, "btn_back", lang, callback_data=NavCB(a="feed").pack())
    kb.adjust(1)
    return kb.as_markup()


def preview_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_send", lang, callback_data=DealCB(a="send").pack())
    theme.add(kb, "deal_reviews", lang, callback_data=DealCB(a="rev_peer").pack())
    theme.add(kb, "btn_cancel", lang, callback_data=DealCB(a="abort").pack())
    kb.adjust(1)
    return kb.as_markup()


def offer_kb(lang: str, theme: Theme, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_accept", lang, callback_data=DealCB(a="acc", i=deal_id).pack())
    theme.add(kb, "deal_decline", lang, callback_data=DealCB(a="dec", i=deal_id).pack())
    theme.add(kb, "deal_reviews", lang, callback_data=DealCB(a="rev", i=deal_id).pack())
    kb.adjust(2, 1)
    return kb.as_markup()


def deal_kb(lang: str, theme: Theme, deal, user_id: int, seller_row=None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    status = deal["status"]
    is_seller = user_id == deal["seller_id"]
    owner = int(deal["seller_id"] or 0) or int(deal["buyer_id"] or 0)
    sent = bool(deal["nft_sent"])
    nft = is_nft_deal(deal)
    if status == DEAL_PENDING and is_seller:
        theme.add(kb, "deal_cancel", lang, callback_data=DealCB(a="can", i=deal["id"]).pack())
    if status == DEAL_PENDING and user_id == deal["buyer_id"]:
        theme.add(kb, "deal_accept", lang, callback_data=DealCB(a="acc", i=deal["id"]).pack())
        theme.add(kb, "deal_decline", lang, callback_data=DealCB(a="dec", i=deal["id"]).pack())
    if status == DEAL_LISTED and user_id == owner:
        theme.add(kb, "deal_set_price", lang, callback_data=DealCB(a="price", i=deal["id"]).pack())
        theme.add(kb, "deal_set_desc", lang, callback_data=DealCB(a="desc", i=deal["id"]).pack())
        theme.add(kb, "deal_cancel", lang, callback_data=DealCB(a="can", i=deal["id"]).pack())
    if status == DEAL_OPEN and not is_seller:
        theme.add(kb, "deal_manual_btn", lang, callback_data=DealCB(a="memo", i=deal["id"]).pack())
        if not nft or sent:
            theme.add(kb, "deal_confirm", lang, callback_data=DealCB(a="ok", i=deal["id"]).pack())
        theme.add(kb, "deal_dispute", lang, callback_data=DealCB(a="dis", i=deal["id"]).pack())
        if not sent:
            theme.add(kb, "deal_cancel", lang, callback_data=DealCB(a="can", i=deal["id"]).pack())
    if status == DEAL_OPEN and is_seller:
        theme.add(kb, "deal_dispute", lang, callback_data=DealCB(a="dis", i=deal["id"]).pack())
        if not sent:
            theme.add(kb, "deal_cancel", lang, callback_data=DealCB(a="can", i=deal["id"]).pack())
    if status == DEAL_DISPUTE:
        theme.add(kb, "deal_dispute_thread", lang, callback_data=DealCB(a="disth", i=deal["id"]).pack())
        theme.add(kb, "deal_dispute_evidence", lang, callback_data=DealCB(a="disev", i=deal["id"]).pack())
    if status == DEAL_REVIEW and not is_seller:
        theme.add(kb, "deal_review_skip", lang, callback_data=DealCB(a="skip", i=deal["id"]).pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(2)
    return kb.as_markup()


def confirm_kb(lang: str, theme: Theme, action: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_yes", lang, callback_data=DealCB(a=action, i=deal_id, x=1).pack())
    theme.add(kb, "btn_no", lang, callback_data=DealCB(a=action, i=deal_id, x=0).pack())
    kb.adjust(2)
    return kb.as_markup()


def peer_cancel_kb(lang: str, theme: Theme, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_agree", lang, callback_data=DealCB(a="canok", i=deal_id).pack())
    theme.add(kb, "deal_refuse", lang, callback_data=DealCB(a="canno", i=deal_id).pack())
    kb.adjust(2)
    return kb.as_markup()


def nft_pick_kb(lang: str, theme: Theme, deal_id: int, items, action: str = "nftset") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for item in items:
        label = item["title"]
        if item["num"]:
            label = f"{label} #{item['num']}"
        kb.button(text=label[:60], style="primary", callback_data=DealCB(a=action, i=deal_id, x=item["id"]).pack())
    if deal_id:
        theme.add(kb, "btn_back", lang, callback_data=DealCB(a="open", i=deal_id).pack())
    else:
        theme.add(kb, "btn_cancel", lang, callback_data=DealCB(a="abort").pack())
    kb.adjust(1)
    return kb.as_markup()


def history_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_seller", lang, callback_data=NavCB(a="hist_s").pack())
    theme.add(kb, "deal_buyer", lang, callback_data=NavCB(a="hist_b").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(2, 1)
    return kb.as_markup()


def deposit_kb(lang: str, theme: Theme, deposit_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deposit_check", lang, callback_data=WalletCB(a="chk", i=deposit_id).pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    return kb.as_markup()


def admin_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "admin_stats", lang, callback_data=AdminCB(a="stats").pack())
    theme.add(kb, "admin_disputes", lang, callback_data=AdminCB(a="disp").pack())
    theme.add(kb, "admin_deposits", lang, callback_data=AdminCB(a="deps").pack())
    theme.add(kb, "admin_withdraws", lang, callback_data=AdminCB(a="wds").pack())
    theme.add(kb, "admin_bans", lang, callback_data=AdminCB(a="bans").pack())
    theme.add(kb, "admin_ban", lang, callback_data=AdminCB(a="ban").pack())
    theme.add(kb, "admin_unban", lang, callback_data=AdminCB(a="unban").pack())
    theme.add(kb, "admin_faq", lang, callback_data=AdminCB(a="faq").pack())
    theme.add(kb, "admin_screens", lang, callback_data=AdminCB(a="scr").pack())
    theme.add(kb, "admin_balance", lang, callback_data=AdminCB(a="bal").pack())
    theme.add(kb, "admin_mail", lang, callback_data=AdminCB(a="mail").pack())
    theme.add(kb, "admin_wallets", lang, callback_data=AdminCB(a="wal").pack())
    theme.add(kb, "admin_sessions", lang, callback_data=AdminCB(a="sess").pack())
    theme.add(kb, "admin_admins", lang, callback_data=AdminCB(a="adms").pack())
    theme.add(kb, "admin_buttons", lang, callback_data=BtnCB(a="list", p=0).pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(2)
    return kb.as_markup()


def admin_bal_asset_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deposit_asset_usdt", lang, callback_data=AdminCB(a="balcur", k="USDT").pack())
    theme.add(kb, "deposit_asset_ton", lang, callback_data=AdminCB(a="balcur", k="TON").pack())
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="home").pack())
    kb.adjust(1)
    return kb.as_markup()


def cfg_fields_kb(lang: str, theme: Theme, fields: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key in fields:
        kb.button(text=t(lang, f"admin_cfg_{key}"), style="primary", callback_data=AdminCB(a="cfgset", k=key).pack())
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="home").pack())
    kb.adjust(1)
    return kb.as_markup()


def admins_kb(lang: str, theme: Theme, ids: list[int]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "admin_adm_add", lang, callback_data=AdminCB(a="admadd").pack())
    for uid in ids:
        kb.button(text=f"✕ {uid}", style="danger", callback_data=AdminCB(a="admrm", i=uid).pack())
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="home").pack())
    kb.adjust(1)
    return kb.as_markup()


def dispute_admin_kb(lang: str, theme: Theme, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "admin_buyer", lang, callback_data=AdminCB(a="win_b", i=deal_id).pack())
    theme.add(kb, "admin_seller", lang, callback_data=AdminCB(a="win_s", i=deal_id).pack())
    theme.add(kb, "admin_reply", lang, callback_data=AdminCB(a="disr", i=deal_id).pack())
    theme.add(kb, "deal_dispute_thread", lang, callback_data=DealCB(a="disth", i=deal_id).pack())
    theme.add(kb, "admin_ban", lang, callback_data=AdminCB(a="ban").pack())
    kb.adjust(2, 1, 1, 1)
    return kb.as_markup()


def faq_user_kb(lang: str, theme: Theme, items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for item in items:
        title = item["title_ru"] if lang == "ru" else (item["title_en"] or item["title_ru"])
        kb.button(text=title[:60], style="primary", callback_data=FaqCB(a="open", i=item["id"]).pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    return kb.as_markup()


def faq_item_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_back", lang, callback_data=NavCB(a="faq").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    return kb.as_markup()


def faq_admin_kb(lang: str, theme: Theme, items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "admin_faq_add", lang, callback_data=AdminCB(a="faqadd").pack())
    for item in items:
        title = item["title_ru"] if lang == "ru" else (item["title_en"] or item["title_ru"])
        kb.button(text=f"#{item['id']} {title[:40]}", style="primary", callback_data=AdminCB(a="faqo", i=item["id"]).pack())
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="home").pack())
    kb.adjust(1)
    return kb.as_markup()


def faq_admin_item_kb(lang: str, theme: Theme, faq_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "admin_faq_photo", lang, callback_data=AdminCB(a="faqph", i=faq_id).pack())
    theme.add(kb, "admin_faq_del", lang, callback_data=AdminCB(a="faqdel", i=faq_id).pack())
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="faq").pack())
    kb.adjust(1)
    return kb.as_markup()


def screens_admin_kb(lang: str, theme: Theme) -> InlineKeyboardMarkup:
    from app.media import SCREENS

    kb = InlineKeyboardBuilder()
    for key in SCREENS:
        kb.button(text=key, style="primary", callback_data=AdminCB(a="scrset", k=key).pack())
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="home").pack())
    kb.adjust(2)
    return kb.as_markup()


def bans_kb(lang: str, theme: Theme, rows) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for row in rows:
        name = row["username"] or row["nick"] or str(row["user_id"])
        kb.button(
            text=f"{name} · {row['user_id']}",
            style="danger",
            callback_data=AdminCB(a="unbani", i=row["user_id"]).pack(),
        )
    theme.add(kb, "admin_ban", lang, callback_data=AdminCB(a="ban").pack())
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="home").pack())
    kb.adjust(1)
    return kb.as_markup()


def evidence_kb(lang: str, theme: Theme, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_dispute_done", lang, callback_data=DealCB(a="disdone", i=deal_id).pack())
    return kb.as_markup()


def skip_review_kb(lang: str, theme: Theme, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "deal_review_skip", lang, callback_data=DealCB(a="skip", i=deal_id).pack())
    return kb.as_markup()


def ticket_kb(action: str, ticket_id: int, lang: str, theme: Theme) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, "admin_confirm", lang, callback_data=AdminCB(a=f"{action}_ok", i=ticket_id).pack())
    theme.add(kb, "admin_reject", lang, callback_data=AdminCB(a=f"{action}_no", i=ticket_id).pack())
    kb.adjust(2)
    return kb.as_markup()


def buttons_list_kb(lang: str, theme: Theme, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    start = page * PAGE_SIZE
    chunk = KEYS[start : start + PAGE_SIZE]
    for key in chunk:
        kb.button(
            text=theme.text(key, lang, id=0),
            style=theme.style(key) or "primary",
            icon_custom_emoji_id=theme.emoji(key),
            callback_data=BtnCB(a="open", k=key, p=page).pack(),
        )
    nav = []
    if page > 0:
        nav.append(("‹", BtnCB(a="list", p=page - 1).pack()))
    if start + PAGE_SIZE < len(KEYS):
        nav.append(("›", BtnCB(a="list", p=page + 1).pack()))
    for text, data in nav:
        kb.button(text=text, style="primary", callback_data=data)
    theme.add(kb, "btn_back", lang, callback_data=AdminCB(a="home").pack())
    kb.adjust(1)
    return kb.as_markup()


def button_edit_kb(lang: str, theme: Theme, key: str, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    theme.add(kb, key, lang, callback_data=BtnCB(a="open", k=key, p=page).pack(), fmt={"id": 0})
    kb.button(text=t(lang, "admin_btn_name"), style="primary", callback_data=BtnCB(a="name", k=key, p=page).pack())
    kb.button(text=t(lang, "admin_btn_color"), style="primary", callback_data=BtnCB(a="color", k=key, p=page).pack())
    kb.button(text=t(lang, "admin_btn_emoji"), style="primary", callback_data=BtnCB(a="emoji", k=key, p=page).pack())
    kb.button(text=t(lang, "admin_btn_reset"), style="danger", callback_data=BtnCB(a="reset", k=key, p=page).pack())
    kb.button(text=t(lang, "btn_back"), style="primary", callback_data=BtnCB(a="list", p=page).pack())
    kb.adjust(1, 2, 2, 1)
    return kb.as_markup()


def button_style_kb(lang: str, theme: Theme, key: str, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    labels = {
        "primary": t(lang, "admin_btn_style_primary"),
        "success": t(lang, "admin_btn_style_success"),
        "danger": t(lang, "admin_btn_style_danger"),
    }
    for style in STYLES:
        kb.button(
            text=labels[style],
            style=style,
            callback_data=BtnCB(a="setst", k=key, p=page, s=style).pack(),
        )
    kb.button(text=t(lang, "admin_btn_style_none"), style="primary", callback_data=BtnCB(a="setst", k=key, p=page, s="none").pack())
    kb.button(text=t(lang, "btn_back"), style="primary", callback_data=BtnCB(a="open", k=key, p=page).pack())
    kb.adjust(1)
    return kb.as_markup()
