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


class AdminFlow(StatesGroup):
    ban_id = State()
    unban_id = State()
    balance_id = State()
    balance_amount = State()
    mail = State()
    btn_name_ru = State()
    btn_name_en = State()
    btn_emoji = State()
