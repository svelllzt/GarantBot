from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.buttons import Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import NavCB, WalletCB, cancel_kb, deposit_kb, lang_kb, requisites_kb
from app.services.deposits import DepositWatch, user_memo
from app.states import Requisites, Wallet
from app.storage import Storage
from app.util import is_cancel, money_asset, paint, parse_amount, parse_ton, valid_ton

router = Router()


def _min_dep(settings: Settings, asset: str) -> float:
    if asset == "TON":
        return float(settings.min_deposit_ton or settings.min_ton_deal or 0.1)
    return float(settings.min_deposit)


def _min_wd(settings: Settings, asset: str) -> float:
    if asset == "TON":
        return float(settings.min_withdraw_ton or settings.min_ton_deal or 0.1)
    return float(settings.min_withdraw)


def _parse(text: str, asset: str) -> float | None:
    if asset == "TON":
        return parse_ton(text)
    return parse_amount(text)


@router.callback_query(NavCB.filter(F.a == "req"))
async def requisites(call: CallbackQuery, lang: str, theme: Theme, settings: Settings):
    await paint(call, t(lang, "req_menu"), requisites_kb(lang, theme), screen="requisites", settings=settings)


@router.callback_query(NavCB.filter(F.a == "lang"))
async def change_lang(call: CallbackQuery, theme: Theme, settings: Settings):
    await paint(call, t("ru", "choose_lang"), lang_kb(theme), screen="profile", settings=settings)


@router.callback_query(NavCB.filter(F.a == "req_ton"))
async def ask_ton(call: CallbackQuery, state: FSMContext, lang: str, theme: Theme):
    await state.set_state(Requisites.ton)
    await call.message.answer(t(lang, "req_ask_ton"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(Requisites.ton)
async def save_ton(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    address = (message.text or "").strip()
    if not valid_ton(address):
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_requisite(message.from_user.id, "ton_address", address)
    await state.clear()
    await message.answer(t(lang, "req_saved"), reply_markup=requisites_kb(lang, theme))


@router.callback_query(NavCB.filter(F.a == "dep"))
async def show_deposit(call: CallbackQuery, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    await state.clear()
    comment = user_memo(call.from_user.id)
    if settings.ton_address:
        extra = t(
            lang,
            "deposit_auto_extra",
            address=settings.ton_address,
        )
    else:
        extra = t(lang, "deposit_manual", support=settings.support_username.lstrip("@"))
    await paint(
        call,
        t(
            lang,
            "deposit_auto",
            comment=comment,
            extra=extra,
            min_usdt=money_asset(_min_dep(settings, "USDT"), "USDT"),
            min_ton=money_asset(_min_dep(settings, "TON"), "TON"),
        ),
        deposit_kb(lang, theme),
        screen="deposit",
        settings=settings,
    )


@router.callback_query(WalletCB.filter(F.a == "chk"))
async def check_deposit(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme, watch: DepositWatch | None = None):
    if watch is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    credited = await watch.apply(call.from_user.id)
    if not credited:
        await call.answer(t(lang, "deposit_wait"), show_alert=True)
        return
    parts = []
    totals: dict[str, float] = {}
    for asset, amount in credited:
        totals[asset] = totals.get(asset, 0) + amount
    for asset, amount in totals.items():
        parts.append(t(lang, "deposit_ok", amount=money_asset(amount, asset), currency=asset))
    from app.keyboards import home_kb

    await paint(
        call,
        "\n".join(parts),
        await home_kb(db, call.from_user.id, lang, theme),
        screen="menu",
        settings=settings,
    )


@router.callback_query(NavCB.filter(F.a == "wd"))
async def pick_withdraw_asset(call: CallbackQuery, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    await state.clear()
    await paint(call, t(lang, "withdraw_pick"), asset_pick_kb(lang, theme, "wasset"), screen="profile", settings=settings)


@router.callback_query(WalletCB.filter(F.a == "wasset"))
async def ask_withdraw(call: CallbackQuery, callback_data: WalletCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    asset = "TON" if callback_data.m == "TON" else "USDT"
    await state.update_data(asset=asset)
    await state.set_state(Wallet.withdraw_amount)
    await call.message.answer(
        t(lang, "withdraw_ask", currency=asset, min=money_asset(_min_wd(settings, asset), asset)),
        reply_markup=cancel_kb(lang, theme),
    )
    await call.answer()


@router.message(Wallet.withdraw_amount)
async def withdraw_amount(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    asset = "TON" if data.get("asset") == "TON" else "USDT"
    amount = _parse(message.text or "", asset)
    minimum = _min_wd(settings, asset)
    if amount is None or amount < minimum:
        await message.answer(t(lang, "min_amount", min=money_asset(minimum, asset), currency=asset))
        return
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer(t(lang, "error"))
        await state.clear()
        return
    available = db.available(user, asset)
    if available + 1e-12 < amount:
        frozen = db.frozen_of(user, asset)
        if frozen > 0:
            await message.answer(t(lang, "withdraw_frozen", have=money_asset(available, asset), frozen=money_asset(frozen, asset), currency=asset))
        else:
            await message.answer(t(lang, "withdraw_low"))
        await state.clear()
        return
    dest = (user["ton_address"] or "").strip()
    await state.update_data(amount=amount, asset=asset)
    if dest and valid_ton(dest):
        await _place_withdraw(message, state, db, lang, settings, theme, dest)
        return
    await state.set_state(Wallet.withdraw_ton)
    await message.answer(t(lang, "req_ask_ton"), reply_markup=cancel_kb(lang, theme))


@router.message(Wallet.withdraw_ton)
async def withdraw_ton_addr(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    address = (message.text or "").strip()
    if not valid_ton(address):
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_requisite(message.from_user.id, "ton_address", address)
    await _place_withdraw(message, state, db, lang, settings, theme, address)


async def _place_withdraw(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, dest: str) -> None:
    data = await state.get_data()
    asset = "TON" if data.get("asset") == "TON" else "USDT"
    amount = float(data.get("amount") or 0)
    if amount <= 0:
        await message.answer(t(lang, "error"))
        await state.clear()
        return
    try:
        await db.spend_available(message.from_user.id, asset, amount)
    except ValueError:
        await message.answer(t(lang, "withdraw_low"))
        await state.clear()
        return
    try:
        wid = await db.create_withdraw(message.from_user.id, amount, "ton", dest, asset)
    except ValueError:
        await db.credit_asset(message.from_user.id, asset, amount)
        await message.answer(t(lang, "withdraw_busy"))
        await state.clear()
        return
    await state.clear()
    from app.keyboards import home_kb

    await message.answer(
        t(lang, "withdraw_ok", id=wid, amount=money_asset(amount, asset), currency=asset, details=dest),
        reply_markup=await home_kb(db, message.from_user.id, lang, theme),
    )
