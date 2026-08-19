from aiogram.fsm.state import State, StatesGroup


class Requisites(StatesGroup):
    ton = State()


class Wallet(StatesGroup):
    deposit_amount = State()
    withdraw_amount = State()
    withdraw_ton = State()


class DealFlow(StatesGroup):
    username = State()
    price = State()
    secret = State()
    description = State()
    review = State()
    dispute_reason = State()
    dispute_evidence = State()
    chat = State()


class AdminFlow(StatesGroup):
    ban_id = State()
    ban_reason = State()
    unban_id = State()
    balance_id = State()
    balance_amount = State()
    mail = State()
    btn_name_ru = State()
    btn_name_en = State()
    btn_emoji = State()
    faq_title_ru = State()
    faq_title_en = State()
    faq_body_ru = State()
    faq_body_en = State()
    faq_photo = State()
    screen_photo = State()
    dispute_reply = State()
    verdict_note = State()
    cfg_value = State()
    adm_add = State()
