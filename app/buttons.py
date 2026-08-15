from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.i18n import t

KEYS = [
    "btn_menu",
    "btn_profile",
    "btn_deal",
    "btn_inventory",
    "btn_history",
    "btn_about",
    "active_deal_btn",
    "btn_req",
    "deposit",
    "withdraw",
    "change_lang",
    "lang_ru",
    "lang_en",
    "req_card",
    "req_phone",
    "req_ton",
    "btn_back",
    "btn_cancel",
    "btn_yes",
    "btn_no",
    "deposit_check",
    "deal_buyer",
    "deal_seller",
    "deal_send",
    "deal_reviews",
    "deal_accept",
    "deal_decline",
    "deal_set_price",
    "deal_set_nft",
    "deal_set_desc",
    "deal_pay",
    "deal_confirm",
    "deal_dispute",
    "deal_cancel",
    "deal_agree",
    "deal_refuse",
    "deal_review_skip",
    "admin_stats",
    "admin_disputes",
    "admin_deposits",
    "admin_withdraws",
    "admin_ban",
    "admin_unban",
    "admin_balance",
    "admin_mail",
    "admin_buttons",
    "admin_buyer",
    "admin_seller",
    "admin_confirm",
    "admin_reject",
]

DEFAULT_STYLE = {
    "btn_deal": "primary",
    "btn_menu": "primary",
    "deposit": "success",
    "withdraw": "primary",
    "deal_send": "primary",
    "deal_accept": "success",
    "deal_decline": "danger",
    "deal_pay": "success",
    "deal_confirm": "success",
    "deal_dispute": "danger",
    "deal_cancel": "danger",
    "btn_yes": "success",
    "btn_no": "danger",
    "deal_agree": "success",
    "deal_refuse": "danger",
    "btn_cancel": "danger",
    "admin_ban": "danger",
    "admin_confirm": "success",
    "admin_reject": "danger",
    "admin_buyer": "success",
    "admin_seller": "primary",
    "admin_buttons": "primary",
}

STYLES = ("primary", "success", "danger")
PAGE_SIZE = 7


class Theme:
    def __init__(self, rows: dict[str, dict]) -> None:
        self.rows = rows

    def text(self, key: str, lang: str, **fmt) -> str:
        row = self.rows.get(key) or {}
        custom = row.get(f"label_{lang}") or row.get("label_ru") or row.get("label_en")
        raw = custom or t(lang, key)
        if fmt:
            try:
                return raw.format(**fmt)
            except (KeyError, IndexError, ValueError):
                return raw
        return raw

    def style(self, key: str) -> str | None:
        row = self.rows.get(key)
        if row is not None and row.get("style") is not None:
            return row["style"] or None
        return DEFAULT_STYLE.get(key)

    def emoji(self, key: str) -> str | None:
        row = self.rows.get(key) or {}
        return row.get("emoji_id") or None

    def add(self, kb: InlineKeyboardBuilder, key: str, lang: str, **kwargs) -> None:
        fmt = kwargs.pop("fmt", None) or {}
        kb.button(
            text=self.text(key, lang, **fmt),
            style=self.style(key),
            icon_custom_emoji_id=self.emoji(key),
            **kwargs,
        )
