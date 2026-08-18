from __future__ import annotations

import secrets

from app.config import Settings
from app.i18n import t
from app.services.ton import TonEscrow, enough_ton, payout_ton
from app.catalog import listing_allowed, needs_nft, normalize, payment_kind
from app.storage import (
    DEAL_CANCELLED,
    DEAL_CLOSED,
    DEAL_DISPUTE,
    DEAL_FUNDED,
    DEAL_LISTED,
    DEAL_OPEN,
    DEAL_PAID,
    DEAL_PENDING,
    DEAL_REVIEW,
    DEAL_RUB_SENT,
    DEAL_WAIT_TON,
    KIND_GOODS,
    KIND_TON_RUB,
    NFT_AVAILABLE,
    NFT_LOCKED,
    NFT_TRANSFERRED,
    Storage,
)
from app.util import has_rub_req, is_nft_deal, is_ton_deal, listing_is_buy, listing_owner, nft_title, pays_requisites, seller_payout, valid_ton


class DealError(Exception):
    def __init__(self, key: str, **kwargs) -> None:
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)


async def peer_of(deal, user_id: int) -> int:
    return deal["seller_id"] if deal["buyer_id"] == user_id else deal["buyer_id"]


async def open_offer(
    db: Storage,
    actor_id: int,
    peer_id: int,
    as_buyer: bool,
    kind: str = KIND_GOODS,
    category: str = "goods",
    title: str = "",
    nft_id: int = 0,
) -> int:
    if actor_id == peer_id:
        raise DealError("deal_self")
    if await db.active_deal(actor_id):
        active = await db.active_deal(actor_id)
        raise DealError("deal_busy_you", id=active["id"])
    if await db.active_deal(peer_id):
        active = await db.active_deal(peer_id)
        raise DealError("deal_busy_them")
    category = normalize(category)
    kind = payment_kind(category) if category else kind
    seller_id = peer_id if as_buyer else actor_id
    buyer_id = actor_id if as_buyer else peer_id
    if kind == KIND_TON_RUB:
        seller = await db.get_user(seller_id)
        if not has_rub_req(seller):
            raise DealError("deal_ton_no_req")
        if not seller or not seller["ton_address"]:
            raise DealError("deal_ton_no_refund")
    nft = needs_nft(category)
    if nft and not as_buyer:
        seller = await db.get_user(seller_id)
        if not has_rub_req(seller):
            raise DealError("deal_nft_need_req")
        if not nft_id:
            raise DealError("deal_nft_need_item")
    deal_id = await db.create_deal(seller_id, buyer_id, kind, category=category, title=title, exclusive=True)
    if not deal_id:
        if await db.active_deal(actor_id):
            active = await db.active_deal(actor_id)
            raise DealError("deal_busy_you", id=active["id"])
        raise DealError("deal_busy_them")
    if nft and not as_buyer:
        try:
            await attach_nft(db, deal_id, seller_id, nft_id)
        except DealError:
            await db.claim_deal(deal_id, DEAL_PENDING, status=DEAL_CANCELLED)
            raise
    return deal_id


async def create_listing(
    db: Storage,
    actor_id: int,
    category: str,
    title: str,
    amount: float,
    description: str,
    as_buyer: bool = False,
    nft_id: int = 0,
) -> int:
    if await db.active_deal(actor_id):
        active = await db.active_deal(actor_id)
        raise DealError("deal_busy_you", id=active["id"])
    category = normalize(category)
    if not listing_allowed(category):
        raise DealError("deal_list_ton")
    kind = payment_kind(category)
    title = (title or "").strip()[:120]
    if len(title) < 2:
        raise DealError("req_bad")
    if float(amount or 0) <= 0:
        raise DealError("deal_need_price")
    nft = needs_nft(category)
    seller_id = 0 if as_buyer else actor_id
    buyer_id = actor_id if as_buyer else 0
    if nft and not as_buyer:
        seller = await db.get_user(actor_id)
        if not has_rub_req(seller):
            raise DealError("deal_nft_need_req")
        if not nft_id:
            raise DealError("deal_nft_need_item")
    deal_id = await db.create_deal(
        seller_id,
        buyer_id,
        kind,
        category=category,
        title=title,
        status=DEAL_LISTED,
        amount=amount,
        description=(description or "")[:1000],
        exclusive=True,
    )
    if not deal_id:
        if await db.active_deal(actor_id):
            active = await db.active_deal(actor_id)
            raise DealError("deal_busy_you", id=active["id"])
        raise DealError("error")
    if nft and not as_buyer:
        try:
            await attach_nft(db, deal_id, actor_id, nft_id)
        except DealError:
            await db.claim_deal(deal_id, DEAL_LISTED, status=DEAL_CANCELLED)
            raise
    return deal_id


async def take_listing(db: Storage, deal_id: int, taker_id: int, nft_id: int = 0) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_LISTED:
        raise DealError("deal_listed_taken")
    if taker_id in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("deal_self")
    if await db.active_deal(taker_id):
        active = await db.active_deal(taker_id)
        raise DealError("deal_busy_you", id=active["id"])
    nft = needs_nft(deal["category"] if "category" in deal.keys() else "")
    buy_ad = listing_is_buy(deal)
    need = float(deal["amount"] or 0)
    if need <= 0:
        raise DealError("deal_need_price")
    if nft and not buy_ad and not deal["nft_id"]:
        raise DealError("deal_nft_need_item")
    if nft and buy_ad:
        seller = await db.get_user(taker_id)
        if not has_rub_req(seller):
            raise DealError("deal_nft_need_req")
        if not nft_id:
            raise DealError("deal_nft_need_item")
    seller_id = taker_id if buy_ad else deal["seller_id"]
    seller = await db.get_user(seller_id) if seller_id else None
    if not nft and not has_rub_req(seller):
        payer_id = deal["buyer_id"] if buy_ad else taker_id
        payer = await db.get_user(payer_id)
        if payer is None or float(payer["balance"] or 0) < need:
            raise DealError("deal_need_deposit")
    fields = {"status": DEAL_OPEN}
    if buy_ad:
        fields["seller_id"] = taker_id
    else:
        fields["buyer_id"] = taker_id
    if not await db.claim_deal(deal_id, DEAL_LISTED, **fields):
        raise DealError("deal_listed_taken")
    if nft and buy_ad:
        try:
            await attach_nft(db, deal_id, taker_id, nft_id)
        except DealError:
            await db.claim_deal(deal_id, DEAL_OPEN, status=DEAL_CANCELLED)
            nft_row = await db.get_nft(nft_id)
            if nft_row and nft_row["status"] == NFT_LOCKED and nft_row["deal_id"] == deal_id:
                await db.claim_nft(nft_id, NFT_LOCKED, NFT_AVAILABLE, deal_id=None)
            raise DealError("deal_nft_need_item")


async def accept(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if is_nft_deal(deal) and user_id == deal["seller_id"] and not deal["nft_id"]:
        raise DealError("deal_nft_need_item")
    if not await db.claim_deal(deal_id, DEAL_PENDING, status=DEAL_OPEN):
        raise DealError("error")


async def decline(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if not await db.claim_deal(deal_id, DEAL_PENDING, status=DEAL_CANCELLED):
        raise DealError("error")


async def set_price(db: Storage, deal_id: int, user_id: int, amount: float) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None:
        raise DealError("error")
    if is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] == DEAL_LISTED:
        if listing_owner(deal) != user_id:
            raise DealError("error")
    elif deal["seller_id"] != user_id:
        raise DealError("error")
    if deal["status"] not in {DEAL_OPEN, DEAL_LISTED}:
        raise DealError("deal_price_locked")
    await db.touch_deal(deal_id, amount=amount)


async def set_description(db: Storage, deal_id: int, user_id: int, text: str) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] not in {DEAL_OPEN, DEAL_LISTED}:
        raise DealError("error")
    if deal["status"] == DEAL_LISTED:
        if listing_owner(deal) != user_id:
            raise DealError("error")
    elif deal["seller_id"] != user_id:
        raise DealError("error")
    await db.touch_deal(deal_id, description=text[:1000])


async def attach_nft(db: Storage, deal_id: int, user_id: int, nft_id: int) -> str:
    deal = await db.get_deal(deal_id)
    nft = await db.get_nft(nft_id)
    if deal is None or nft is None or deal["seller_id"] != user_id:
        raise DealError("error")
    if is_ton_deal(deal):
        raise DealError("error")
    if not is_nft_deal(deal):
        raise DealError("error")
    if deal["status"] not in {DEAL_OPEN, DEAL_LISTED, DEAL_PENDING}:
        raise DealError("error")
    if nft["owner_id"] != user_id:
        raise DealError("error")
    if nft["status"] == NFT_LOCKED and nft["deal_id"] == deal_id:
        await db.touch_deal(deal_id, nft_id=nft_id)
        return nft_title(nft)
    if nft["status"] != NFT_AVAILABLE:
        raise DealError("error")
    old_id = deal["nft_id"]
    if not await db.claim_nft(nft_id, NFT_AVAILABLE, NFT_LOCKED, deal_id=deal_id):
        raise DealError("error")
    if old_id and old_id != nft_id:
        await db.claim_nft(old_id, NFT_LOCKED, NFT_AVAILABLE, deal_id=None)
    await db.touch_deal(deal_id, nft_id=nft_id)
    return nft_title(nft)


async def submit_receipt(db: Storage, deal_id: int, user_id: int, file_id: str) -> None:
    deal = await db.get_deal(deal_id)
    seller = await db.get_user(deal["seller_id"]) if deal and deal["seller_id"] else None
    if deal is None or deal["buyer_id"] != user_id or not pays_requisites(deal, seller):
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("error")
    if not deal["amount"]:
        raise DealError("deal_pay_no_amount")
    if is_nft_deal(deal) and not deal["nft_id"]:
        raise DealError("deal_nft_need_item")
    if not (file_id or "").strip():
        raise DealError("deal_nft_pdf_only")
    if not await db.claim_deal(deal_id, DEAL_OPEN, status=DEAL_RUB_SENT, receipt_id=file_id.strip(), rub_marked=1):
        raise DealError("error")


async def confirm_nft_rub(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or not is_nft_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_RUB_SENT:
        raise DealError("error")
    if not deal["receipt_id"]:
        raise DealError("deal_nft_pdf_only")
    if not await db.claim_deal(deal_id, DEAL_RUB_SENT, status=DEAL_REVIEW):
        raise DealError("error")
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])


async def confirm_req_pay(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or is_nft_deal(deal) or is_ton_deal(deal):
        raise DealError("error")
    seller = await db.get_user(user_id)
    if not pays_requisites(deal, seller):
        raise DealError("error")
    if deal["status"] != DEAL_RUB_SENT:
        raise DealError("error")
    if not deal["receipt_id"]:
        raise DealError("deal_nft_pdf_only")
    if not await db.claim_deal(deal_id, DEAL_RUB_SENT, status=DEAL_PAID):
        raise DealError("error")


async def set_ton_amount(db: Storage, deal_id: int, user_id: int, amount: float) -> bool:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or not is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("deal_price_locked")
    await db.touch_deal(deal_id, ton_amount=amount)
    return await _lock_ton_terms(db, deal_id)


async def set_rub_amount(db: Storage, deal_id: int, user_id: int, amount: float) -> bool:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or not is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("deal_price_locked")
    await db.touch_deal(deal_id, rub_amount=amount)
    return await _lock_ton_terms(db, deal_id)


async def set_buyer_ton(db: Storage, deal_id: int, user_id: int, address: str) -> bool:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id or not is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("deal_price_locked")
    if not valid_ton(address):
        raise DealError("req_bad")
    await db.touch_deal(deal_id, buyer_ton=address.strip())
    return await _lock_ton_terms(db, deal_id)


async def _lock_ton_terms(db: Storage, deal_id: int) -> bool:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_OPEN:
        return False
    if not deal["ton_amount"] or not deal["rub_amount"] or not deal["buyer_ton"]:
        return False
    comment = deal["ton_comment"] or f"T{deal_id}{secrets.randbelow(9000) + 1000}"
    return await db.claim_deal(deal_id, DEAL_OPEN, status=DEAL_WAIT_TON, ton_comment=comment)


async def check_ton_deposit(db: Storage, ton: TonEscrow, deal_id: int, user_id: int) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or not is_ton_deal(deal):
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if deal["status"] != DEAL_WAIT_TON:
        raise DealError("error")
    if not deal["ton_comment"]:
        raise DealError("error")
    got = await ton.incoming(deal["ton_comment"])
    if got is None or not enough_ton(got, float(deal["ton_amount"])):
        raise DealError("deal_ton_wait")
    if not await db.claim_deal(deal_id, DEAL_WAIT_TON, status=DEAL_FUNDED, ton_received=got):
        raise DealError("error")
    return got


async def mark_rub_paid(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id or not is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_FUNDED:
        raise DealError("error")
    if not await db.claim_deal(deal_id, DEAL_FUNDED, status=DEAL_RUB_SENT, rub_marked=1):
        raise DealError("error")


async def confirm_rub(db: Storage, settings: Settings, ton: TonEscrow, deal_id: int, user_id: int) -> tuple[float, str]:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or not is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_RUB_SENT:
        raise DealError("error")
    if deal["payout_hash"] and deal["payout_hash"] != "pending":
        return float(deal["ton_amount"] or 0), deal["payout_hash"]
    received = float(deal["ton_received"] or 0)
    amount = payout_ton(float(deal["ton_amount"] or 0), settings.commission_percent, received, settings.ton_gas)
    if amount <= 0:
        raise DealError("deal_ton_send_fail")
    dest = deal["buyer_ton"]
    if not dest:
        raise DealError("error")
    if not ton.can_send:
        raise DealError("deal_ton_manual", amount=f"{amount:.9f}".rstrip("0").rstrip("."), address=dest)
    if not await db.claim_deal(deal_id, DEAL_RUB_SENT, payout_hash="pending", where={"payout_hash": None}):
        again = await db.get_deal(deal_id)
        if again and again["payout_hash"] and again["payout_hash"] != "pending":
            return float(again["ton_amount"] or 0), again["payout_hash"]
        raise DealError("error")
    tx = await ton.send(dest, amount, f"deal {deal_id}")
    if not tx:
        await db.touch_deal(deal_id, payout_hash=None)
        raise DealError("deal_ton_send_fail")
    await db.touch_deal(deal_id, payout_hash=tx, status=DEAL_CLOSED)
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    return amount, tx


async def pay(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id:
        raise DealError("error")
    if is_ton_deal(deal):
        raise DealError("error")
    if is_nft_deal(deal):
        raise DealError("deal_nft_no_pay")
    seller = await db.get_user(deal["seller_id"]) if deal["seller_id"] else None
    if pays_requisites(deal, seller):
        raise DealError("deal_req_no_pay")
    if deal["status"] != DEAL_OPEN:
        raise DealError("error")
    if deal["amount"] is None:
        raise DealError("deal_pay_no_amount")
    try:
        await db.change_balance(user_id, -float(deal["amount"]))
    except ValueError:
        buyer = await db.get_user(user_id)
        raise DealError(
            "deal_pay_low",
            need=f"{float(deal['amount']):.2f}",
            have=f"{float(buyer['balance']):.2f}" if buyer else "0.00",
        )
    if not await db.claim_deal(deal_id, DEAL_OPEN, status=DEAL_PAID):
        await db.change_balance(user_id, float(deal["amount"]))
        raise DealError("error")


async def complete(db: Storage, settings: Settings, deal_id: int, user_id: int) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id or deal["status"] != DEAL_PAID:
        raise DealError("error")
    if is_nft_deal(deal):
        raise DealError("error")
    seller = await db.get_user(deal["seller_id"]) if deal["seller_id"] else None
    if pays_requisites(deal, seller):
        if not await db.claim_deal(deal_id, DEAL_PAID, status=DEAL_REVIEW):
            raise DealError("error")
        await db.bump_deals(deal["seller_id"], deal["buyer_id"])
        return 0.0
    payout = seller_payout(deal["amount"], settings.commission_percent)
    if not await db.claim_deal(deal_id, DEAL_PAID, status=DEAL_REVIEW):
        raise DealError("error")
    try:
        await db.change_balance(deal["seller_id"], payout)
    except Exception:
        await db.claim_deal(deal_id, DEAL_REVIEW, status=DEAL_PAID)
        raise
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    if deal["nft_id"] and deal["nft_sent"]:
        await db.set_nft_status(
            deal["nft_id"],
            NFT_TRANSFERRED,
            owner_id=deal["buyer_id"],
            deal_id=deal_id,
        )
    return payout


async def close_after_review(db: Storage, deal_id: int) -> None:
    await db.claim_deal(deal_id, DEAL_REVIEW, status=DEAL_CLOSED)


async def _refund_ton(db: Storage, ton: TonEscrow | None, deal) -> None:
    if not is_ton_deal(deal):
        return
    if deal["payout_hash"] or not deal["ton_received"]:
        return
    if ton is None or not ton.can_send:
        raise DealError("deal_ton_send_fail")
    seller = await db.get_user(deal["seller_id"])
    dest = seller["ton_address"] if seller else None
    if not dest:
        raise DealError("deal_ton_no_refund")
    received = float(deal["ton_received"])
    amount = round(received - max(ton.settings.ton_gas, 0), 9)
    if amount <= 0:
        raise DealError("deal_ton_send_fail")
    tx = await ton.send(dest, amount, f"refund {deal['id']}")
    if not tx:
        raise DealError("deal_ton_send_fail")
    await db.touch_deal(deal["id"], payout_hash=tx)


async def cancel_mutual(db: Storage, deal_id: int, ton: TonEscrow | None = None) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None:
        raise DealError("error")
    if deal["status"] in {DEAL_PAID, DEAL_FUNDED, DEAL_RUB_SENT, DEAL_DISPUTE, DEAL_REVIEW, DEAL_CLOSED}:
        raise DealError("deal_cancel_denied")
    if deal["status"] == DEAL_LISTED:
        if not await db.claim_deal(deal_id, DEAL_LISTED, status=DEAL_CANCELLED):
            raise DealError("error")
        if deal["nft_id"] and not deal["nft_sent"]:
            await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)
        return
    if is_ton_deal(deal):
        if deal["status"] == DEAL_WAIT_TON and ton and deal["ton_comment"]:
            found = await ton.incoming(deal["ton_comment"])
            if found:
                if enough_ton(found, float(deal["ton_amount"] or 0)):
                    await db.claim_deal(deal_id, DEAL_WAIT_TON, status=DEAL_FUNDED, ton_received=found)
                else:
                    await db.touch_deal(deal_id, ton_received=found)
                raise DealError("deal_cancel_denied")
        if not await db.claim_deal(deal_id, deal["status"], status=DEAL_CANCELLED):
            raise DealError("error")
        return
    if not await db.claim_deal(deal_id, deal["status"], status=DEAL_CANCELLED):
        raise DealError("error")
    if deal["nft_id"] and not deal["nft_sent"]:
        await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)


async def open_dispute(db: Storage, deal_id: int, user_id: int, reason: str = "") -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if deal["status"] == DEAL_DISPUTE:
        return
    if is_ton_deal(deal):
        if deal["status"] not in {DEAL_FUNDED, DEAL_RUB_SENT, DEAL_WAIT_TON}:
            raise DealError("error")
    elif is_nft_deal(deal):
        if deal["status"] not in {DEAL_RUB_SENT, DEAL_REVIEW}:
            raise DealError("error")
    elif pays_requisites(deal, await db.get_user(deal["seller_id"]) if deal["seller_id"] else None):
        if deal["status"] not in {DEAL_RUB_SENT, DEAL_PAID}:
            raise DealError("error")
    elif deal["status"] != DEAL_PAID:
        raise DealError("error")
    if not await db.claim_deal(
        deal_id,
        deal["status"],
        status=DEAL_DISPUTE,
        dispute_reason=(reason or "")[:1000],
        dispute_by=user_id,
    ):
        again = await db.get_deal(deal_id)
        if again is not None and again["status"] == DEAL_DISPUTE:
            return
        raise DealError("error")


async def _settle_nft(db: Storage, deal, to_buyer: bool) -> None:
    if not deal["nft_id"]:
        return
    if deal["nft_sent"] and to_buyer:
        await db.set_nft_status(
            deal["nft_id"],
            NFT_TRANSFERRED,
            owner_id=deal["buyer_id"],
            deal_id=deal["id"],
        )
        return
    if not deal["nft_sent"]:
        await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)


async def verdict_buyer(db: Storage, deal_id: int, ton: TonEscrow | None = None) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    if not await db.claim_deal(deal_id, DEAL_DISPUTE, status=DEAL_CANCELLED):
        raise DealError("error")
    try:
        if is_ton_deal(deal):
            await _refund_ton(db, ton, deal)
        elif is_nft_deal(deal):
            pass
        elif pays_requisites(deal, await db.get_user(deal["seller_id"]) if deal["seller_id"] else None):
            pass
        elif deal["amount"] is not None:
            await db.change_balance(deal["buyer_id"], float(deal["amount"]))
    except Exception:
        await db.claim_deal(deal_id, DEAL_CANCELLED, status=DEAL_DISPUTE)
        raise
    await _settle_nft(db, deal, to_buyer=False)


async def verdict_seller(db: Storage, settings: Settings, deal_id: int, ton: TonEscrow | None = None) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    if is_ton_deal(deal):
        if deal["payout_hash"] and deal["payout_hash"] != "pending":
            if not await db.claim_deal(deal_id, DEAL_DISPUTE, status=DEAL_CLOSED):
                raise DealError("error")
            return float(deal["ton_amount"] or 0)
        received = float(deal["ton_received"] or 0)
        amount = payout_ton(float(deal["ton_amount"] or 0), settings.commission_percent, received, settings.ton_gas)
        dest = deal["buyer_ton"]
        if not dest or amount <= 0:
            raise DealError("deal_ton_send_fail")
        if ton is None or not ton.can_send:
            raise DealError("deal_ton_manual", amount=f"{amount:.9f}".rstrip("0").rstrip("."), address=dest)
        if not await db.claim_deal(deal_id, DEAL_DISPUTE, payout_hash="pending", where={"payout_hash": None}):
            raise DealError("error")
        tx = await ton.send(dest, amount, f"deal {deal_id}")
        if not tx:
            await db.touch_deal(deal_id, payout_hash=None)
            raise DealError("deal_ton_send_fail")
        await db.touch_deal(deal_id, payout_hash=tx, status=DEAL_CLOSED)
        await db.bump_deals(deal["seller_id"], deal["buyer_id"])
        return amount
    if is_nft_deal(deal):
        if not await db.claim_deal(deal_id, DEAL_DISPUTE, status=DEAL_CLOSED):
            raise DealError("error")
        await db.bump_deals(deal["seller_id"], deal["buyer_id"])
        if deal["nft_sent"]:
            await _settle_nft(db, deal, to_buyer=True)
        return 0.0
    if pays_requisites(deal, await db.get_user(deal["seller_id"]) if deal["seller_id"] else None):
        if not await db.claim_deal(deal_id, DEAL_DISPUTE, status=DEAL_CLOSED):
            raise DealError("error")
        await db.bump_deals(deal["seller_id"], deal["buyer_id"])
        return 0.0
    if not await db.claim_deal(deal_id, DEAL_DISPUTE, status=DEAL_CLOSED):
        raise DealError("error")
    payout = seller_payout(deal["amount"] or 0, settings.commission_percent)
    try:
        await db.change_balance(deal["seller_id"], payout)
    except Exception:
        await db.claim_deal(deal_id, DEAL_CLOSED, status=DEAL_DISPUTE)
        raise
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    await _settle_nft(db, deal, to_buyer=True)
    return payout


def err_text(lang: str, exc: DealError) -> str:
    return t(lang, exc.key, **exc.kwargs)
