from aiogram.fsm.state import State, StatesGroup


class Requisites(StatesGroup):
    card = State()
    phone = State()
    bank = State()
    ton = State()


class Wallet(StatesGroup):
    deposit_amount = State()
    withdraw_amount = State()


class DealFlow(StatesGroup):
    username = State()
    price = State()
    description = State()
    review = State()
    ton_amount = State()
    rub_amount = State()
    buyer_ton = State()
    listing_title = State()
    listing_price = State()
    receipt_pdf = State()
    dispute_reason = State()
    dispute_evidence = State()


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
