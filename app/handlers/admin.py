import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.buttons import KEYS, Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import AdminCB, BtnCB, admin_kb, button_edit_kb, button_style_kb, buttons_list_kb, cancel_kb, dispute_admin_kb, ticket_kb
from app.services import deals as svc
from app.services.deals import DealError
from app.states import AdminFlow
from app.storage import WALLET_DONE, WALLET_REJECTED, Storage
from app.util import extract_emoji_id, is_cancel, money, parse_amount, paint

router = Router()


def _admin(settings: Settings, user_id: int) -> bool:
    return settings.is_admin(user_id)


@router.message(Command("admin"))
async def admin_entry(message: Message, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, message.from_user.id):
        await message.answer(t(lang, "admin_only"))
        return
    await message.answer(t(lang, "admin_menu"), reply_markup=admin_kb(lang, theme))


@router.callback_query(AdminCB.filter(F.a == "stats"))
async def stats(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        await call.answer(t(lang, "admin_only"), show_alert=True)
        return
    users, deals, volume = await db.stats()
    await call.message.edit_text(
        t(lang, "admin_stats_text", users=users, deals=deals, volume=f"{volume:.2f}", currency=settings.currency),
        reply_markup=admin_kb(lang, theme),
    )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "ban"))
async def ask_ban(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.ban_id)
    await call.message.answer(t(lang, "admin_ask_id"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "unban"))
async def ask_unban(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.unban_id)
    await call.message.answer(t(lang, "admin_ask_id"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.ban_id)
async def do_ban(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    if not (message.text or "").isdigit():
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_banned(int(message.text), True)
    await state.clear()
    await message.answer(t(lang, "admin_done"))


@router.message(AdminFlow.unban_id)
async def do_unban(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    if not (message.text or "").isdigit():
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_banned(int(message.text), False)
    await state.clear()
    await message.answer(t(lang, "admin_done"))


@router.callback_query(AdminCB.filter(F.a == "bal"))
async def ask_balance_id(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.balance_id)
    await call.message.answer(t(lang, "admin_ask_id"))
    await call.answer()


@router.message(AdminFlow.balance_id)
async def ask_balance_amount(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if is_cancel(message.text or ""):
        return
    if not (message.text or "").isdigit():
        await message.answer(t(lang, "req_bad"))
        return
    user = await db.get_user(int(message.text))
    if user is None:
        await message.answer(t(lang, "admin_user_missing"))
        await state.clear()
        return
    await state.update_data(target_id=user["user_id"])
    await state.set_state(AdminFlow.balance_amount)
    await message.answer(t(lang, "admin_ask_balance", currency=settings.currency))


@router.message(AdminFlow.balance_amount)
async def set_balance(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    amount = parse_amount((message.text or "").lstrip("+"))
    if amount is None:
        await message.answer(t(lang, "req_bad"))
        return
    data = await state.get_data()
    await db.set_balance(data["target_id"], amount)
    await state.clear()
    await message.answer(t(lang, "admin_done"))


@router.callback_query(AdminCB.filter(F.a == "mail"))
async def ask_mail(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.mail)
    await call.message.answer(t(lang, "admin_ask_mail"))
    await call.answer()


@router.message(AdminFlow.mail)
async def send_mail(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    text = message.html_text or message.text or ""
    await state.clear()
    await message.answer(t(lang, "mail_started"))
    ok = fail = 0
    for user_id in await db.user_ids():
        try:
            await message.bot.send_message(user_id, text)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await message.answer(t(lang, "mail_done", ok=ok, fail=fail))


@router.callback_query(AdminCB.filter(F.a == "disp"))
async def disputes(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    rows = await db.open_disputes()
    if not rows:
        await call.answer(t(lang, "admin_no_disputes"), show_alert=True)
        return
    for deal in rows:
        buyer = await db.get_user(deal["buyer_id"])
        seller = await db.get_user(deal["seller_id"])
        await call.message.answer(
            t(
                lang,
                "deal_dispute_admin",
                id=deal["id"],
                buyer=buyer["username"] if buyer else "-",
                buyer_id=deal["buyer_id"],
                seller=seller["username"] if seller else "-",
                seller_id=deal["seller_id"],
                amount=money(deal["amount"]),
                currency=settings.currency,
                nft="—" if not deal["nft_id"] else str(deal["nft_id"]),
            ),
            reply_markup=dispute_admin_kb(lang, theme, deal["id"]),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "win_b"))
async def win_buyer(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    try:
        await svc.verdict_buyer(db, callback_data.i)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    await call.message.edit_text(t(lang, "admin_verdict_buyer"))
    for uid in (deal["seller_id"], deal["buyer_id"]):
        user = await db.get_user(uid)
        try:
            await call.bot.send_message(uid, t(user["lang"] or "ru", "admin_verdict_buyer"))
        except Exception:
            pass
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "win_s"))
async def win_seller(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    try:
        await svc.verdict_seller(db, settings, callback_data.i)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    await call.message.edit_text(t(lang, "admin_verdict_seller"))
    for uid in (deal["seller_id"], deal["buyer_id"]):
        user = await db.get_user(uid)
        try:
            await call.bot.send_message(uid, t(user["lang"] or "ru", "admin_verdict_seller"))
        except Exception:
            pass
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "deps"))
async def deposits(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    rows = await db.pending_deposits()
    if not rows:
        await call.answer(t(lang, "admin_empty_list"), show_alert=True)
        return
    for row in rows:
        await call.message.answer(
            t(
                lang,
                "admin_dep_line",
                id=row["id"],
                amount=f"{row['amount']:.2f}",
                currency=settings.currency,
                comment=row["comment"],
                user=row["user_id"],
            ),
            reply_markup=ticket_kb("dep", row["id"], lang, theme),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "wds"))
async def withdraws(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    rows = await db.pending_withdraws()
    if not rows:
        await call.answer(t(lang, "admin_empty_list"), show_alert=True)
        return
    for row in rows:
        await call.message.answer(
            t(
                lang,
                "admin_wd_line",
                id=row["id"],
                amount=f"{row['amount']:.2f}",
                currency=settings.currency,
                method=row["method"],
                details=row["details"],
                user=row["user_id"],
            ),
            reply_markup=ticket_kb("wd", row["id"], lang, theme),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "dep_ok"))
async def dep_ok(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None or deposit["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_deposit(deposit["id"], WALLET_DONE)
    await db.change_balance(deposit["user_id"], float(deposit["amount"]))
    await call.message.edit_text(t(lang, "admin_dep_ok"))
    try:
        user = await db.get_user(deposit["user_id"])
        await call.bot.send_message(
            deposit["user_id"],
            t(user["lang"] or "ru", "deposit_ok", amount=f"{deposit['amount']:.2f}", currency=settings.currency),
        )
    except Exception:
        pass
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "dep_no"))
async def dep_no(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_deposit(deposit["id"], WALLET_REJECTED)
    await call.message.edit_text(t(lang, "admin_dep_no"))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "wd_ok"))
async def wd_ok(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    item = await db.get_withdraw(callback_data.i)
    if item is None or item["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_withdraw(item["id"], WALLET_DONE)
    await call.message.edit_text(t(lang, "admin_wd_ok"))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "wd_no"))
async def wd_no(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    item = await db.get_withdraw(callback_data.i)
    if item is None or item["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_withdraw(item["id"], WALLET_REJECTED)
    await db.change_balance(item["user_id"], float(item["amount"]))
    await call.message.edit_text(t(lang, "admin_wd_no"))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "home"))
async def admin_home(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await call.message.edit_text(t(lang, "admin_menu"), reply_markup=admin_kb(lang, theme))
    await call.answer()


def _btn_card(lang: str, theme: Theme, key: str) -> str:
    style = theme.style(key) or t(lang, "admin_btn_style_none")
    emoji = theme.emoji(key) or t(lang, "admin_btn_no_emoji")
    return t(
        lang,
        "admin_btn_card",
        title=theme.text(key, lang, id=0),
        key=key,
        ru=theme.text(key, "ru", id=0),
        en=theme.text(key, "en", id=0),
        style=style,
        emoji=emoji,
    )


@router.callback_query(BtnCB.filter(F.a == "list"))
async def btn_list(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await call.message.edit_text(t(lang, "admin_btn_pick"), reply_markup=buttons_list_kb(lang, theme, callback_data.p))
    await call.answer()


@router.callback_query(BtnCB.filter(F.a == "open"))
async def btn_open(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    key = callback_data.k
    if key not in KEYS:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await call.message.edit_text(_btn_card(lang, theme, key), reply_markup=button_edit_kb(lang, theme, key, callback_data.p))
    await call.answer()


@router.callback_query(BtnCB.filter(F.a == "color"))
async def btn_color(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await call.message.edit_text(
        _btn_card(lang, theme, callback_data.k),
        reply_markup=button_style_kb(lang, theme, callback_data.k, callback_data.p),
    )
    await call.answer()


@router.callback_query(BtnCB.filter(F.a == "setst"))
async def btn_set_style(call: CallbackQuery, callback_data: BtnCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    key = callback_data.k
    style = None if callback_data.s in {"-", "none"} else callback_data.s
    await db.patch_button(key, style="" if style is None else style)
    theme = Theme(await db.button_map())
    await call.message.edit_text(
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, key),
        reply_markup=button_edit_kb(lang, theme, key, callback_data.p),
    )
    await call.answer()


@router.callback_query(BtnCB.filter(F.a == "reset"))
async def btn_reset(call: CallbackQuery, callback_data: BtnCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    await db.reset_button(callback_data.k)
    theme = Theme(await db.button_map())
    await call.message.edit_text(
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, callback_data.k),
        reply_markup=button_edit_kb(lang, theme, callback_data.k, callback_data.p),
    )
    await call.answer()


@router.callback_query(BtnCB.filter(F.a == "name"))
async def btn_name(call: CallbackQuery, callback_data: BtnCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.btn_name_ru)
    await state.update_data(btn_key=callback_data.k, btn_page=callback_data.p)
    await call.message.answer(t(lang, "admin_btn_ask_ru"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.btn_name_ru)
async def btn_name_ru(message: Message, state: FSMContext, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    label = (message.text or "").strip()
    if not label or len(label) > 64:
        await message.answer(t(lang, "req_bad"))
        return
    await state.update_data(label_ru=label)
    await state.set_state(AdminFlow.btn_name_en)
    await message.answer(t(lang, "admin_btn_ask_en"), reply_markup=cancel_kb(lang, theme))


@router.message(AdminFlow.btn_name_en)
async def btn_name_en(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    ru = data["label_ru"]
    en = (message.text or "").strip()
    if en in {"-", "—"}:
        en = ru
    if not en or len(en) > 64:
        await message.answer(t(lang, "req_bad"))
        return
    key = data["btn_key"]
    await db.patch_button(key, label_ru=ru, label_en=en)
    theme = Theme(await db.button_map())
    await state.clear()
    await message.answer(
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, key),
        reply_markup=button_edit_kb(lang, theme, key, data.get("btn_page", 0)),
    )


@router.callback_query(BtnCB.filter(F.a == "emoji"))
async def btn_emoji(call: CallbackQuery, callback_data: BtnCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.btn_emoji)
    await state.update_data(btn_key=callback_data.k, btn_page=callback_data.p)
    await call.message.answer(t(lang, "admin_btn_ask_emoji"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.btn_emoji)
async def btn_emoji_save(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    key = data["btn_key"]
    raw = (message.text or "").strip()
    if raw in {"-", "—"}:
        emoji_id = ""
    else:
        emoji_id = extract_emoji_id(message)
        if not emoji_id:
            await message.answer(t(lang, "req_bad"))
            return
    await db.patch_button(key, emoji_id=emoji_id)
    theme = Theme(await db.button_map())
    await state.clear()
    await message.answer(
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, key),
        reply_markup=button_edit_kb(lang, theme, key, data.get("btn_page", 0)),
    )
