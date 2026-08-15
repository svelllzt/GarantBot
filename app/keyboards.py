from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.i18n import t
from app.storage import DEAL_OPEN, DEAL_PAID, DEAL_PENDING, DEAL_REVIEW


class LangCB(CallbackData, prefix="lang"):
    code: str


class NavCB(CallbackData, prefix="nav"):
    a: str


class DealCB(CallbackData, prefix="deal"):
    a: str
    i: int = 0
    x: int = 0


class WalletCB(CallbackData, prefix="wal"):
    a: str
    i: int = 0
    m: str = ""


class AdminCB(CallbackData, prefix="adm"):
    a: str
    i: int = 0
    x: int = 0


def main_menu(lang: str, deal_id: int | None = None) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t(lang, "btn_profile"))
    kb.button(text=t(lang, "btn_deal"))
    kb.button(text=t(lang, "btn_inventory"))
    kb.button(text=t(lang, "btn_history"))
    kb.button(text=t(lang, "btn_about"))
    if deal_id:
        kb.button(text=t(lang, "active_deal_btn", id=deal_id))
    kb.adjust(2, 2, 1 if not deal_id else 2)
    return kb.as_markup(resize_keyboard=True)


def cancel_kb(lang: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t(lang, "btn_cancel"))
    return kb.as_markup(resize_keyboard=True)


def lang_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Русский", callback_data=LangCB(code="ru").pack())
    kb.button(text="English", callback_data=LangCB(code="en").pack())
    kb.adjust(2)
    return kb.as_markup()


def profile_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "btn_req"), callback_data=NavCB(a="req").pack())
    kb.button(text=t(lang, "deposit"), callback_data=NavCB(a="dep").pack())
    kb.button(text=t(lang, "withdraw"), callback_data=NavCB(a="wd").pack())
    kb.button(text=t(lang, "change_lang"), callback_data=NavCB(a="lang").pack())
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def requisites_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "req_card"), callback_data=NavCB(a="req_card").pack())
    kb.button(text=t(lang, "req_phone"), callback_data=NavCB(a="req_phone").pack())
    kb.button(text=t(lang, "req_ton"), callback_data=NavCB(a="req_ton").pack())
    kb.button(text=t(lang, "btn_back"), callback_data=NavCB(a="profile").pack())
    kb.adjust(1)
    return kb.as_markup()


def role_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "deal_buyer"), callback_data=DealCB(a="role", x=1).pack())
    kb.button(text=t(lang, "deal_seller"), callback_data=DealCB(a="role", x=0).pack())
    kb.adjust(2)
    return kb.as_markup()


def preview_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "deal_send"), callback_data=DealCB(a="send").pack())
    kb.button(text=t(lang, "deal_reviews"), callback_data=DealCB(a="rev_peer").pack())
    kb.button(text=t(lang, "btn_cancel"), callback_data=DealCB(a="abort").pack())
    kb.adjust(1)
    return kb.as_markup()


def offer_kb(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "deal_accept"), callback_data=DealCB(a="acc", i=deal_id).pack())
    kb.button(text=t(lang, "deal_decline"), callback_data=DealCB(a="dec", i=deal_id).pack())
    kb.button(text=t(lang, "deal_reviews"), callback_data=DealCB(a="rev", i=deal_id).pack())
    kb.adjust(2, 1)
    return kb.as_markup()


def deal_kb(lang: str, deal, user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    status = deal["status"]
    seller = user_id == deal["seller_id"]
    if status == DEAL_PENDING and seller:
        kb.button(text=t(lang, "deal_cancel"), callback_data=DealCB(a="can", i=deal["id"]).pack())
    if status == DEAL_OPEN:
        if seller:
            kb.button(text=t(lang, "deal_set_price"), callback_data=DealCB(a="price", i=deal["id"]).pack())
            kb.button(text=t(lang, "deal_set_nft"), callback_data=DealCB(a="nft", i=deal["id"]).pack())
            kb.button(text=t(lang, "deal_set_desc"), callback_data=DealCB(a="desc", i=deal["id"]).pack())
        else:
            kb.button(text=t(lang, "deal_pay"), callback_data=DealCB(a="pay", i=deal["id"]).pack())
        kb.button(text=t(lang, "deal_cancel"), callback_data=DealCB(a="can", i=deal["id"]).pack())
    if status == DEAL_PAID:
        if not seller:
            kb.button(text=t(lang, "deal_confirm"), callback_data=DealCB(a="ok", i=deal["id"]).pack())
        kb.button(text=t(lang, "deal_dispute"), callback_data=DealCB(a="dis", i=deal["id"]).pack())
    if status == DEAL_REVIEW and not seller:
        kb.button(text=t(lang, "deal_review_skip"), callback_data=DealCB(a="skip", i=deal["id"]).pack())
    kb.adjust(2)
    return kb.as_markup()


def confirm_kb(lang: str, action: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "btn_yes"), callback_data=DealCB(a=action, i=deal_id, x=1).pack())
    kb.button(text=t(lang, "btn_no"), callback_data=DealCB(a=action, i=deal_id, x=0).pack())
    kb.adjust(2)
    return kb.as_markup()


def peer_cancel_kb(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "deal_agree"), callback_data=DealCB(a="canok", i=deal_id).pack())
    kb.button(text=t(lang, "deal_refuse"), callback_data=DealCB(a="canno", i=deal_id).pack())
    kb.adjust(2)
    return kb.as_markup()


def nft_pick_kb(lang: str, deal_id: int, items) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for item in items:
        label = item["title"]
        if item["num"]:
            label = f"{label} #{item['num']}"
        kb.button(text=label[:60], callback_data=DealCB(a="nftset", i=deal_id, x=item["id"]).pack())
    kb.button(text=t(lang, "btn_back"), callback_data=DealCB(a="open", i=deal_id).pack())
    kb.adjust(1)
    return kb.as_markup()


def history_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "deal_seller"), callback_data=NavCB(a="hist_s").pack())
    kb.button(text=t(lang, "deal_buyer"), callback_data=NavCB(a="hist_b").pack())
    kb.adjust(2)
    return kb.as_markup()


def deposit_kb(lang: str, deposit_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "deposit_check"), callback_data=WalletCB(a="chk", i=deposit_id).pack())
    kb.adjust(1)
    return kb.as_markup()


def withdraw_method_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "req_card"), callback_data=WalletCB(a="wdm", m="card").pack())
    kb.button(text=t(lang, "req_phone"), callback_data=WalletCB(a="wdm", m="phone").pack())
    kb.button(text=t(lang, "req_ton"), callback_data=WalletCB(a="wdm", m="ton").pack())
    kb.adjust(1)
    return kb.as_markup()


def admin_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "admin_stats"), callback_data=AdminCB(a="stats").pack())
    kb.button(text=t(lang, "admin_disputes"), callback_data=AdminCB(a="disp").pack())
    kb.button(text=t(lang, "admin_deposits"), callback_data=AdminCB(a="deps").pack())
    kb.button(text=t(lang, "admin_withdraws"), callback_data=AdminCB(a="wds").pack())
    kb.button(text=t(lang, "admin_ban"), callback_data=AdminCB(a="ban").pack())
    kb.button(text=t(lang, "admin_unban"), callback_data=AdminCB(a="unban").pack())
    kb.button(text=t(lang, "admin_balance"), callback_data=AdminCB(a="bal").pack())
    kb.button(text=t(lang, "admin_mail"), callback_data=AdminCB(a="mail").pack())
    kb.adjust(2)
    return kb.as_markup()


def dispute_admin_kb(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "admin_buyer"), callback_data=AdminCB(a="win_b", i=deal_id).pack())
    kb.button(text=t(lang, "admin_seller"), callback_data=AdminCB(a="win_s", i=deal_id).pack())
    kb.adjust(2)
    return kb.as_markup()


def skip_review_kb(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "deal_review_skip"), callback_data=DealCB(a="skip", i=deal_id).pack())
    return kb.as_markup()


def ticket_kb(action: str, ticket_id: int, lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "admin_confirm"), callback_data=AdminCB(a=f"{action}_ok", i=ticket_id).pack())
    kb.button(text=t(lang, "admin_reject"), callback_data=AdminCB(a=f"{action}_no", i=ticket_id).pack())
    kb.adjust(2)
    return kb.as_markup()
