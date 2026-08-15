from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.buttons import Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import (
    DealCB,
    NavCB,
    cancel_kb,
    confirm_kb,
    deal_kb,
    history_kb,
    home_kb,
    kind_kb,
    nft_pick_kb,
    offer_kb,
    peer_cancel_kb,
    preview_kb,
    role_kb,
    skip_review_kb,
    dispute_admin_kb,
)
from app.services import deals as svc
from app.services.deals import DealError
from app.states import DealFlow
from app.storage import DEAL_FUNDED, DEAL_OPEN, DEAL_PAID, DEAL_PENDING, DEAL_RUB_SENT, DEAL_WAIT_TON, KIND_TON_RUB, NFT_AVAILABLE, Storage
from app.util import (
    history_line,
    is_cancel,
    is_ton_deal,
    money,
    money_ton,
    nft_title,
    parse_amount,
    parse_ton,
    render_deal,
    seller_req_text,
    username_of,
    h,
    has_rub_req,
)

router = Router()


async def _show_deal(bot, db: Storage, deal, user_id: int, lang: str, settings: Settings, theme: Theme, message=None, edit=False, ton=None):
    escrow = ton.address if ton is not None else settings.ton_address
    text = await render_deal(db, deal, lang, settings.currency, escrow=escrow or "")
    markup = deal_kb(lang, theme, deal, user_id)
    if message is not None and edit:
        await message.edit_text(text, reply_markup=markup)
        return
    if message is not None:
        await message.answer(text, reply_markup=markup)
        return
    await bot.send_message(user_id, text, reply_markup=markup)


async def _notify_ton_lock(bot, db: Storage, deal, settings: Settings, theme: Theme, ton) -> None:
    deal = await db.get_deal(deal["id"])
    if deal is None or deal["status"] != DEAL_WAIT_TON:
        return
    address = (ton.address if ton is not None else settings.ton_address) or ""
    for uid in (deal["seller_id"], deal["buyer_id"]):
        user = await db.get_user(uid)
        lang = user["lang"] or "ru"
        await bot.send_message(
            uid,
            t(
                lang,
                "deal_ton_deposit",
                amount=money_ton(deal["ton_amount"]),
                address=address,
                comment=deal["ton_comment"],
            ),
        )
        await _show_deal(bot, db, deal, uid, lang, settings, theme, ton=ton)


@router.callback_query(NavCB.filter(F.a == "deal"))
async def new_deal(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    await state.clear()
    if not call.from_user.username:
        await call.answer(t(lang, "need_username"), show_alert=True)
        return
    active = await db.active_deal(call.from_user.id)
    if active:
        await _show_deal(call.bot, db, active, call.from_user.id, lang, settings, theme, message=call.message, edit=True, ton=ton)
        await call.answer()
        return
    await call.message.edit_text(t(lang, "deal_role"), reply_markup=role_kb(lang, theme))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "role"))
async def pick_role(call: CallbackQuery, callback_data: DealCB, state: FSMContext, lang: str, theme: Theme):
    if not call.from_user.username:
        await call.answer(t(lang, "need_username"), show_alert=True)
        return
    await state.update_data(as_buyer=bool(callback_data.x))
    await call.message.edit_text(t(lang, "deal_kind"), reply_markup=kind_kb(lang, theme))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "kind"))
async def pick_kind(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme, ton):
    kind = KIND_TON_RUB if callback_data.x else "goods"
    data = await state.get_data()
    if "as_buyer" not in data:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if kind == KIND_TON_RUB:
        if not ton.address:
            await call.answer(t(lang, "deal_ton_off"), show_alert=True)
            return
        if not data.get("as_buyer"):
            user = await db.get_user(call.from_user.id)
            if not has_rub_req(user):
                await call.answer(t(lang, "deal_ton_no_req"), show_alert=True)
                return
            if not user or not user["ton_address"]:
                await call.answer(t(lang, "deal_ton_no_refund"), show_alert=True)
                return
    await state.update_data(kind=kind)
    await state.set_state(DealFlow.username)
    await call.message.answer(t(lang, "deal_ask_user"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(DealFlow.username)
async def find_peer(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    username = (message.text or "").strip().lstrip("@")
    me = await db.get_user(message.from_user.id)
    if username.lower() == (me["username"] or "").lower():
        await message.answer(t(lang, "deal_self"))
        await state.clear()
        return
    peer = await db.get_user_by_username(username)
    if peer is None:
        await message.answer(t(lang, "deal_missing"))
        await state.clear()
        return
    data = await state.get_data()
    as_buyer = data.get("as_buyer", True)
    kind = data.get("kind", "goods")
    await state.update_data(peer_id=peer["user_id"])
    await state.set_state(None)
    role = t(lang, "deal_buyer" if as_buyer else "deal_seller")
    kind_label = t(lang, "deal_kind_label_ton" if kind == KIND_TON_RUB else "deal_kind_label_goods")
    await message.answer(
        t(
            lang,
            "deal_preview",
            id=peer["user_id"],
            nick=h(peer["nick"] or peer["first_name"] or "-"),
            username=username_of(peer),
            deals=peer["deals_count"],
            role=role,
            kind=kind_label,
        ),
        reply_markup=preview_kb(lang, theme),
    )


@router.callback_query(DealCB.filter(F.a == "abort"))
async def abort_preview(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, theme: Theme):
    await state.clear()
    await call.message.edit_text(t(lang, "cancelled"), reply_markup=await home_kb(db, call.from_user.id, lang, theme))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "rev_peer"))
async def preview_reviews(call: CallbackQuery, state: FSMContext, db: Storage, lang: str):
    data = await state.get_data()
    peer_id = data.get("peer_id")
    if not peer_id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    rows = await db.reviews_for(peer_id)
    if not rows:
        await call.answer(t(lang, "no_reviews"), show_alert=True)
        return
    text = "\n\n".join(f"• {r['text']}" for r in rows)
    await call.message.answer(text)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "send"))
async def send_offer(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    data = await state.get_data()
    peer_id = data.get("peer_id")
    as_buyer = data.get("as_buyer", True)
    kind = data.get("kind", "goods")
    if not peer_id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    try:
        deal_id = await svc.open_offer(db, call.from_user.id, peer_id, as_buyer, kind)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    await state.clear()
    me = await db.get_user(call.from_user.id)
    peer = await db.get_user(peer_id)
    peer_lang = peer["lang"] or "ru"
    peer_role = t(peer_lang, "deal_seller" if as_buyer else "deal_buyer")
    kind_label = t(peer_lang, "deal_kind_label_ton" if kind == KIND_TON_RUB else "deal_kind_label_goods")
    await call.message.edit_text(t(lang, "deal_sent"), reply_markup=await home_kb(db, call.from_user.id, lang, theme))
    await call.bot.send_message(
        peer_id,
        t(
            peer_lang,
            "deal_offer_in",
            id=deal_id,
            username=username_of(me),
            uid=me["user_id"],
            deals=me["deals_count"],
            role=peer_role,
            kind=kind_label,
        ),
        reply_markup=offer_kb(peer_lang, theme, deal_id),
    )
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "acc"))
async def accept_offer(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    try:
        await svc.accept(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    await call.message.edit_reply_markup()
    for uid in (deal["seller_id"], deal["buyer_id"]):
        user = await db.get_user(uid)
        user_lang = user["lang"] or "ru"
        await _show_deal(call.bot, db, deal, uid, user_lang, settings, theme, ton=ton)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "dec"))
async def decline_offer(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    try:
        await svc.decline(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    await call.message.edit_text(t(lang, "deal_declined"))
    other = deal["seller_id"] if deal["buyer_id"] == call.from_user.id else deal["buyer_id"]
    other_user = await db.get_user(other)
    other_lang = other_user["lang"] or "ru"
    await call.bot.send_message(other, t(other_lang, "deal_declined_peer"), reply_markup=await home_kb(db, other, other_lang, theme))
    await call.message.edit_text(t(lang, "deal_declined"), reply_markup=await home_kb(db, call.from_user.id, lang, theme))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "open"))
async def reopen(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, message=call.message, edit=True, ton=ton)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "price"))
async def ask_price(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["seller_id"] != call.from_user.id or deal["status"] != DEAL_OPEN:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.price)
    await state.update_data(deal_id=deal["id"])
    await call.message.answer(t(lang, "deal_ask_price", currency=settings.currency), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(DealFlow.price)
async def save_price(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    amount = parse_amount(message.text or "")
    if amount is None:
        await message.answer(t(lang, "req_bad"))
        return
    data = await state.get_data()
    try:
        await svc.set_price(db, data["deal_id"], message.from_user.id, amount)
    except DealError as exc:
        await message.answer(svc.err_text(lang, exc))
        await state.clear()
        return
    await state.clear()
    deal = await db.get_deal(data["deal_id"])
    await message.answer(t(lang, "deal_price_set", amount=money(amount), currency=settings.currency))
    for uid in (deal["seller_id"], deal["buyer_id"]):
        user = await db.get_user(uid)
        user_lang = user["lang"] or "ru"
        await _show_deal(message.bot, db, deal, uid, user_lang, settings, theme, ton=None)


@router.callback_query(DealCB.filter(F.a == "desc"))
async def ask_desc(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["seller_id"] != call.from_user.id or deal["status"] != DEAL_OPEN:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.description)
    await state.update_data(deal_id=deal["id"])
    await call.message.answer(t(lang, "deal_ask_desc"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(DealFlow.description)
async def save_desc(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer(t(lang, "req_bad"))
        return
    data = await state.get_data()
    try:
        await svc.set_description(db, data["deal_id"], message.from_user.id, text)
    except DealError as exc:
        await message.answer(svc.err_text(lang, exc))
        await state.clear()
        return
    await state.clear()
    await message.answer(t(lang, "deal_desc_set"))
    deal = await db.get_deal(data["deal_id"])
    await _show_deal(message.bot, db, deal, message.from_user.id, lang, settings, theme, message=message)


@router.callback_query(DealCB.filter(F.a == "tonamt"))
async def ask_ton_amt(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["seller_id"] != call.from_user.id or deal["status"] != DEAL_OPEN or not is_ton_deal(deal):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.ton_amount)
    await state.update_data(deal_id=deal["id"])
    await call.message.answer(
        t(lang, "deal_ask_ton_amt", min=money_ton(settings.min_ton_deal)),
        reply_markup=cancel_kb(lang, theme),
    )
    await call.answer()


@router.message(DealFlow.ton_amount)
async def save_ton_amt(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    if is_cancel(message.text or ""):
        return
    amount = parse_ton(message.text or "")
    if amount is None or amount < settings.min_ton_deal:
        await message.answer(t(lang, "min_amount", min=money_ton(settings.min_ton_deal), currency="TON"))
        return
    data = await state.get_data()
    try:
        locked = await svc.set_ton_amount(db, data["deal_id"], message.from_user.id, amount)
    except DealError as exc:
        await message.answer(svc.err_text(lang, exc))
        await state.clear()
        return
    await state.clear()
    await message.answer(t(lang, "deal_ton_set", amount=money_ton(amount)))
    deal = await db.get_deal(data["deal_id"])
    if locked:
        await _notify_ton_lock(message.bot, db, deal, settings, theme, ton)
        return
    await _show_deal(message.bot, db, deal, message.from_user.id, lang, settings, theme, ton=ton)


@router.callback_query(DealCB.filter(F.a == "rubamt"))
async def ask_rub_amt(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["seller_id"] != call.from_user.id or deal["status"] != DEAL_OPEN or not is_ton_deal(deal):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.rub_amount)
    await state.update_data(deal_id=deal["id"])
    await call.message.answer(
        t(lang, "deal_ask_rub_amt", min=money(settings.min_rub_deal)),
        reply_markup=cancel_kb(lang, theme),
    )
    await call.answer()


@router.message(DealFlow.rub_amount)
async def save_rub_amt(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    if is_cancel(message.text or ""):
        return
    amount = parse_amount(message.text or "")
    if amount is None or amount < settings.min_rub_deal:
        await message.answer(t(lang, "min_amount", min=money(settings.min_rub_deal), currency="₽"))
        return
    data = await state.get_data()
    try:
        locked = await svc.set_rub_amount(db, data["deal_id"], message.from_user.id, amount)
    except DealError as exc:
        await message.answer(svc.err_text(lang, exc))
        await state.clear()
        return
    await state.clear()
    await message.answer(t(lang, "deal_rub_set", amount=money(amount)))
    deal = await db.get_deal(data["deal_id"])
    if locked:
        await _notify_ton_lock(message.bot, db, deal, settings, theme, ton)
        return
    await _show_deal(message.bot, db, deal, message.from_user.id, lang, settings, theme, ton=ton)


@router.callback_query(DealCB.filter(F.a == "buyaddr"))
async def ask_buy_ton(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["buyer_id"] != call.from_user.id or deal["status"] != DEAL_OPEN or not is_ton_deal(deal):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.buyer_ton)
    await state.update_data(deal_id=deal["id"])
    await call.message.answer(t(lang, "deal_ask_buy_ton"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(DealFlow.buyer_ton)
async def save_buy_ton(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    if is_cancel(message.text or ""):
        return
    address = (message.text or "").strip()
    data = await state.get_data()
    try:
        locked = await svc.set_buyer_ton(db, data["deal_id"], message.from_user.id, address)
    except DealError as exc:
        await message.answer(svc.err_text(lang, exc))
        await state.clear()
        return
    await state.clear()
    await db.set_requisite(message.from_user.id, "ton_address", address)
    await message.answer(t(lang, "deal_buy_ton_set"))
    deal = await db.get_deal(data["deal_id"])
    if locked:
        await _notify_ton_lock(message.bot, db, deal, settings, theme, ton)
        return
    await _show_deal(message.bot, db, deal, message.from_user.id, lang, settings, theme, ton=ton)


@router.callback_query(DealCB.filter(F.a == "chkton"))
async def check_ton(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    try:
        await svc.check_ton_deposit(db, ton, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    seller = await db.get_user(deal["seller_id"])
    buyer = await db.get_user(deal["buyer_id"])
    req = seller_req_text(seller, buyer["lang"] or "ru")
    await call.message.answer(t(lang, "deal_ton_funded"))
    await call.bot.send_message(
        deal["buyer_id"],
        t(buyer["lang"] or "ru", "deal_ton_funded_buyer", rub=money(deal["rub_amount"]), req=req),
    )
    for uid in (deal["seller_id"], deal["buyer_id"]):
        user = await db.get_user(uid)
        await _show_deal(call.bot, db, deal, uid, user["lang"] or "ru", settings, theme, ton=ton)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "rubpay"))
async def rub_pay_ask(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["buyer_id"] != call.from_user.id or deal["status"] != DEAL_FUNDED:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await call.message.answer(t(lang, "deal_rub_ask"), reply_markup=confirm_kb(lang, theme, "rpaygo", deal["id"]))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "rpaygo"))
async def rub_pay_go(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    if callback_data.x != 1:
        await call.answer()
        return
    try:
        await svc.mark_rub_paid(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    seller = await db.get_user(deal["seller_id"])
    seller_lang = seller["lang"] or "ru"
    await call.message.edit_text(t(lang, "deal_rub_marked"))
    await call.bot.send_message(
        deal["seller_id"],
        t(seller_lang, "deal_rub_marked_seller", id=deal["id"]),
        reply_markup=deal_kb(seller_lang, theme, deal, deal["seller_id"]),
    )
    await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, ton=ton)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "rubok"))
async def rub_ok_ask(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["seller_id"] != call.from_user.id or deal["status"] != DEAL_RUB_SENT:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await call.message.answer(t(lang, "deal_rub_confirm_ask"), reply_markup=confirm_kb(lang, theme, "rokgo", deal["id"]))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "rokgo"))
async def rub_ok_go(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    if callback_data.x != 1:
        await call.answer()
        return
    deal = await db.get_deal(callback_data.i)
    try:
        amount, tx = await svc.confirm_rub(db, settings, ton, callback_data.i, call.from_user.id)
    except DealError as exc:
        text = svc.err_text(lang, exc)
        await call.answer(text, show_alert=True)
        extra = text
        dest = deal["buyer_ton"] if deal else ""
        amt = money_ton(deal["ton_amount"]) if deal else ""
        for admin_id in settings.admins:
            try:
                await call.bot.send_message(
                    admin_id,
                    t("ru", "deal_ton_admin_fail", id=callback_data.i, address=dest, amount=amt, extra=extra),
                )
            except Exception:
                pass
        return
    deal = await db.get_deal(callback_data.i)
    buyer = await db.get_user(deal["buyer_id"])
    await call.message.edit_text(
        t(lang, "deal_ton_sent", address=deal["buyer_ton"], hash=tx),
        reply_markup=await home_kb(db, call.from_user.id, lang, theme),
    )
    await call.bot.send_message(
        deal["buyer_id"],
        t(buyer["lang"] or "ru", "deal_ton_sent_buyer", hash=tx),
        reply_markup=await home_kb(db, deal["buyer_id"], buyer["lang"] or "ru", theme),
    )
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "nft"))
async def pick_nft(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    items = await db.nfts_of(call.from_user.id, NFT_AVAILABLE)
    if not items:
        await call.answer(t(lang, "deal_nft_empty"), show_alert=True)
        return
    await call.message.edit_text(
        t(lang, "deal_nft_pick"),
        reply_markup=nft_pick_kb(lang, theme, callback_data.i, items),
    )
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "nftset"))
async def set_nft(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    try:
        title = await svc.attach_nft(db, callback_data.i, call.from_user.id, callback_data.x)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    await call.answer(t(lang, "deal_nft_set", title=title), show_alert=True)
    deal = await db.get_deal(callback_data.i)
    buyer = await db.get_user(deal["buyer_id"])
    await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, message=call.message, edit=True)
    await call.bot.send_message(
        deal["buyer_id"],
        t(buyer["lang"] or "ru", "deal_nft_set", title=title),
    )


@router.callback_query(DealCB.filter(F.a == "pay"))
async def pay_deal(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, bank, theme: Theme):
    try:
        await svc.pay(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        kwargs = dict(exc.kwargs)
        if "currency" not in kwargs:
            kwargs["currency"] = settings.currency
        await call.answer(t(lang, exc.key, **kwargs), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    nft_note = None
    if deal["nft_id"]:
        nft = await db.get_nft(deal["nft_id"])
        sent = await bank.transfer(nft, deal["buyer_id"]) if nft else False
        if sent:
            await db.touch_deal(deal["id"], nft_sent=1)
            nft_note = "deal_nft_sent"
        else:
            nft_note = "deal_nft_fail"
    seller = await db.get_user(deal["seller_id"])
    seller_lang = seller["lang"] or "ru"
    await call.message.edit_text(t(lang, "deal_paid"))
    if nft_note:
        await call.message.answer(t(lang, nft_note))
    await _show_deal(call.bot, db, await db.get_deal(deal["id"]), call.from_user.id, lang, settings, theme, message=call.message)
    await call.bot.send_message(deal["seller_id"], t(seller_lang, "deal_paid_seller", id=deal["id"]))
    if nft_note:
        await call.bot.send_message(deal["seller_id"], t(seller_lang, nft_note))
    await _show_deal(call.bot, db, await db.get_deal(deal["id"]), deal["seller_id"], seller_lang, settings, theme)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "ok"))
async def confirm_ask(call: CallbackQuery, callback_data: DealCB, lang: str, theme: Theme):
    await call.message.answer(
        t(lang, "deal_confirm_ask"),
        reply_markup=confirm_kb(lang, theme, "okgo", callback_data.i),
    )
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "okgo"))
async def confirm_go(
    call: CallbackQuery,
    callback_data: DealCB,
    state: FSMContext,
    db: Storage,
    lang: str,
    settings: Settings,
    theme: Theme,
):
    if callback_data.x != 1:
        await call.answer()
        return
    try:
        payout = await svc.complete(db, settings, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    seller = await db.get_user(deal["seller_id"])
    seller_lang = seller["lang"] or "ru"
    await state.set_state(DealFlow.review)
    await state.update_data(deal_id=deal["id"])
    await call.message.edit_text(t(lang, "deal_done_buyer"))
    await call.message.answer(t(lang, "deal_review_ask"), reply_markup=skip_review_kb(lang, theme, deal["id"]))
    await call.bot.send_message(
        deal["seller_id"],
        t(
            seller_lang,
            "deal_done_seller",
            amount=f"{payout:.2f}",
            currency=settings.currency,
            commission=settings.commission_percent,
        ),
        reply_markup=await home_kb(db, deal["seller_id"], seller_lang, theme),
    )
    await call.answer()


@router.message(DealFlow.review)
async def save_review(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    deal = await db.get_deal(data.get("deal_id", 0))
    if deal is None:
        await state.clear()
        return
    text = (message.text or "").strip()
    if text:
        await db.add_review(deal["seller_id"], deal["buyer_id"], deal["id"], text[:500])
        seller = await db.get_user(deal["seller_id"])
        await message.bot.send_message(
            deal["seller_id"],
            t(seller["lang"] or "ru", "deal_review_saved") + "\n" + h(text),
        )
        await message.answer(t(lang, "deal_review_saved"))
    await svc.close_after_review(db, deal["id"])
    await state.clear()
    await message.answer(t(lang, "menu"), reply_markup=await home_kb(db, message.from_user.id, lang, theme))


@router.callback_query(DealCB.filter(F.a == "skip"))
async def skip_review(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme):
    await svc.close_after_review(db, callback_data.i)
    await state.clear()
    await call.message.edit_text(t(lang, "deal_done_buyer"))
    await call.message.answer(t(lang, "menu"), reply_markup=await home_kb(db, call.from_user.id, lang, theme))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "can"))
async def cancel_ask(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["status"] in {DEAL_PAID, DEAL_FUNDED, DEAL_RUB_SENT}:
        await call.answer(t(lang, "deal_cancel_denied"), show_alert=True)
        return
    if deal["status"] == DEAL_PENDING:
        await svc.decline(db, deal["id"], call.from_user.id)
        other = deal["seller_id"] if call.from_user.id == deal["buyer_id"] else deal["buyer_id"]
        other_user = await db.get_user(other)
        await call.message.edit_text(t(lang, "deal_cancel_ok"))
        await call.bot.send_message(other, t(other_user["lang"] or "ru", "deal_declined_peer"), reply_markup=await home_kb(db, other, other_user["lang"] or "ru", theme))
        await call.message.answer(t(lang, "menu"), reply_markup=await home_kb(db, call.from_user.id, lang, theme))
        await call.answer()
        return
    await call.message.answer(t(lang, "deal_cancel_ask"), reply_markup=confirm_kb(lang, theme, "cansend", deal["id"]))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "cansend"))
async def cancel_send(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    if callback_data.x != 1:
        await call.answer()
        return
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    other = deal["seller_id"] if call.from_user.id == deal["buyer_id"] else deal["buyer_id"]
    other_user = await db.get_user(other)
    other_lang = other_user["lang"] or "ru"
    await call.message.edit_text(t(lang, "deal_cancel_sent"))
    await call.bot.send_message(
        other,
        t(other_lang, "deal_cancel_ask"),
        reply_markup=peer_cancel_kb(other_lang, theme, deal["id"]),
    )
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "canok"))
async def cancel_ok(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme, ton):
    deal = await db.get_deal(callback_data.i)
    try:
        await svc.cancel_mutual(db, callback_data.i, ton)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    for uid in (deal["seller_id"], deal["buyer_id"]):
        user = await db.get_user(uid)
        await call.bot.send_message(uid, t(user["lang"] or "ru", "deal_cancel_ok"), reply_markup=await home_kb(db, uid, user["lang"] or "ru", theme))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "canno"))
async def cancel_no(call: CallbackQuery, lang: str):
    await call.answer(t(lang, "cancelled"))


@router.callback_query(DealCB.filter(F.a == "dis"))
async def dispute(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    try:
        await svc.open_dispute(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    nft = await db.get_nft(deal["nft_id"]) if deal["nft_id"] else None
    buyer = await db.get_user(deal["buyer_id"])
    seller = await db.get_user(deal["seller_id"])
    await call.answer(t(lang, "deal_dispute_ok"), show_alert=True)
    text = t(
        lang,
        "deal_dispute_ok",
    )
    await call.message.answer(text)
    admin_text = t(
        "ru",
        "deal_dispute_admin",
        id=deal["id"],
        buyer=username_of(buyer),
        buyer_id=deal["buyer_id"],
        seller=username_of(seller),
        seller_id=deal["seller_id"],
        amount=money(deal["amount"]) if not is_ton_deal(deal) else f"{money_ton(deal['ton_amount'])} TON / {money(deal['rub_amount'])} ₽",
        currency="" if is_ton_deal(deal) else settings.currency,
        nft=nft_title(nft) if nft else t("ru", "deal_nft_none"),
    )
    for admin_id in settings.admins:
        try:
            await call.bot.send_message(admin_id, admin_text, reply_markup=dispute_admin_kb("ru", theme, deal["id"]))
        except Exception:
            pass


@router.callback_query(DealCB.filter(F.a == "rev"))
async def offer_reviews(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    seller_id = deal["seller_id"] if call.from_user.id == deal["buyer_id"] else deal["buyer_id"]
    rows = await db.reviews_for(seller_id)
    if not rows:
        await call.answer(t(lang, "no_reviews"), show_alert=True)
        return
    await call.message.answer("\n\n".join(f"• {r['text']}" for r in rows))
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "hist"))
async def history(call: CallbackQuery, lang: str, theme: Theme):
    await call.message.edit_text(t(lang, "history_role"), reply_markup=history_kb(lang, theme))
    await call.answer()


@router.callback_query(NavCB.filter(F.a.in_({"hist_s", "hist_b"})))
async def history_list(call: CallbackQuery, callback_data: NavCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    role = "seller" if callback_data.a == "hist_s" else "buyer"
    rows = await db.history(call.from_user.id, role)
    if not rows:
        await call.answer(t(lang, "history_empty"), show_alert=True)
        return
    lines = []
    for deal in rows:
        peer_id = deal["buyer_id"] if role == "seller" else deal["seller_id"]
        peer = await db.get_user(peer_id)
        lines.append(history_line(deal, call.from_user.id, username_of(peer) if peer else "-", lang, settings.currency))
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_back", lang, callback_data=NavCB(a="hist").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    await call.message.edit_text("\n\n".join(lines), reply_markup=kb.as_markup())
    await call.answer()
