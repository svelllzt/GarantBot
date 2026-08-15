from __future__ import annotations

import secrets

from app.config import Settings
from app.i18n import t
from app.services.ton import TonEscrow, enough_ton, payout_ton
from app.storage import (
    DEAL_CANCELLED,
    DEAL_CLOSED,
    DEAL_DISPUTE,
    DEAL_FUNDED,
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
from app.util import has_rub_req, is_ton_deal, nft_title, seller_payout, valid_ton


class DealError(Exception):
    def __init__(self, key: str, **kwargs) -> None:
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)


async def peer_of(deal, user_id: int) -> int:
    return deal["seller_id"] if deal["buyer_id"] == user_id else deal["buyer_id"]


async def open_offer(db: Storage, actor_id: int, peer_id: int, as_buyer: bool, kind: str = KIND_GOODS) -> int:
    if actor_id == peer_id:
        raise DealError("deal_self")
    if await db.active_deal(actor_id):
        active = await db.active_deal(actor_id)
        raise DealError("deal_busy_you", id=active["id"])
    if await db.active_deal(peer_id):
        raise DealError("deal_busy_them")
    seller_id = peer_id if as_buyer else actor_id
    buyer_id = actor_id if as_buyer else peer_id
    if kind == KIND_TON_RUB:
        seller = await db.get_user(seller_id)
        if not has_rub_req(seller):
            raise DealError("deal_ton_no_req")
        if not seller or not seller["ton_address"]:
            raise DealError("deal_ton_no_refund")
    return await db.create_deal(seller_id, buyer_id, kind)


async def accept(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    await db.touch_deal(deal_id, status=DEAL_OPEN)


async def decline(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    await db.touch_deal(deal_id, status=DEAL_CANCELLED)


async def set_price(db: Storage, deal_id: int, user_id: int, amount: float) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id:
        raise DealError("error")
    if is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("deal_price_locked")
    await db.touch_deal(deal_id, amount=amount)


async def set_description(db: Storage, deal_id: int, user_id: int, text: str) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or deal["status"] != DEAL_OPEN:
        raise DealError("error")
    await db.touch_deal(deal_id, description=text[:1000])


async def attach_nft(db: Storage, deal_id: int, user_id: int, nft_id: int) -> str:
    deal = await db.get_deal(deal_id)
    nft = await db.get_nft(nft_id)
    if deal is None or nft is None or deal["seller_id"] != user_id:
        raise DealError("error")
    if is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("error")
    if nft["owner_id"] != user_id or nft["status"] != NFT_AVAILABLE:
        raise DealError("error")
    if deal["nft_id"]:
        old = await db.get_nft(deal["nft_id"])
        if old and old["status"] == NFT_LOCKED:
            await db.set_nft_status(old["id"], NFT_AVAILABLE, deal_id=None)
    await db.set_nft_status(nft_id, NFT_LOCKED, deal_id=deal_id)
    await db.touch_deal(deal_id, nft_id=nft_id)
    return nft_title(nft)


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
    await db.touch_deal(deal_id, status=DEAL_WAIT_TON, ton_comment=comment)
    return True


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
    await db.touch_deal(deal_id, status=DEAL_FUNDED, ton_received=got)
    return got


async def mark_rub_paid(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id or not is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_FUNDED:
        raise DealError("error")
    await db.touch_deal(deal_id, status=DEAL_RUB_SENT, rub_marked=1)


async def confirm_rub(db: Storage, settings: Settings, ton: TonEscrow, deal_id: int, user_id: int) -> tuple[float, str]:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or not is_ton_deal(deal):
        raise DealError("error")
    if deal["status"] != DEAL_RUB_SENT:
        raise DealError("error")
    if deal["payout_hash"]:
        return float(deal["ton_amount"] or 0), deal["payout_hash"]
    received = float(deal["ton_received"] or deal["ton_amount"] or 0)
    amount = payout_ton(float(deal["ton_amount"]), settings.commission_percent, received, settings.ton_gas)
    if amount <= 0:
        raise DealError("deal_ton_send_fail")
    dest = deal["buyer_ton"]
    if not dest:
        raise DealError("error")
    if not ton.can_send:
        raise DealError("deal_ton_manual", amount=f"{amount:.9f}".rstrip("0").rstrip("."), address=dest)
    tx = await ton.send(dest, amount, f"deal {deal_id}")
    if not tx:
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
            have=f"{float(buyer['balance']):.2f}",
        )
    await db.touch_deal(deal_id, status=DEAL_PAID)


async def complete(db: Storage, settings: Settings, deal_id: int, user_id: int) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id or deal["status"] != DEAL_PAID:
        raise DealError("error")
    payout = seller_payout(deal["amount"], settings.commission_percent)
    await db.change_balance(deal["seller_id"], payout)
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    await db.touch_deal(deal_id, status=DEAL_CLOSED)
    return payout


async def close_after_review(db: Storage, deal_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None:
        return
    if deal["status"] == DEAL_REVIEW:
        await db.touch_deal(deal_id, status=DEAL_CLOSED)


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
    if is_ton_deal(deal):
        if deal["status"] in {DEAL_FUNDED, DEAL_RUB_SENT, DEAL_DISPUTE}:
            raise DealError("deal_cancel_denied")
        if deal["status"] == DEAL_WAIT_TON and ton and deal["ton_comment"]:
            found = await ton.incoming(deal["ton_comment"])
            if found and enough_ton(found, float(deal["ton_amount"] or 0)):
                await db.touch_deal(deal_id, status=DEAL_FUNDED, ton_received=found)
                raise DealError("deal_cancel_denied")
        await db.touch_deal(deal_id, status=DEAL_CANCELLED)
        return
    if deal["status"] == DEAL_PAID:
        await db.change_balance(deal["buyer_id"], float(deal["amount"]))
    if deal["nft_id"] and not deal["nft_sent"]:
        await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)
    await db.touch_deal(deal_id, status=DEAL_CANCELLED)


async def open_dispute(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if is_ton_deal(deal):
        if deal["status"] not in {DEAL_FUNDED, DEAL_RUB_SENT}:
            raise DealError("error")
    elif deal["status"] != DEAL_PAID:
        raise DealError("error")
    await db.touch_deal(deal_id, status=DEAL_DISPUTE)


async def verdict_buyer(db: Storage, deal_id: int, ton: TonEscrow | None = None) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    if is_ton_deal(deal):
        await _refund_ton(db, ton, deal)
        await db.touch_deal(deal_id, status=DEAL_CANCELLED)
        return
    if deal["amount"] is not None:
        await db.change_balance(deal["buyer_id"], float(deal["amount"]))
    if deal["nft_id"] and not deal["nft_sent"]:
        await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)
    await db.touch_deal(deal_id, status=DEAL_CANCELLED)


async def verdict_seller(db: Storage, settings: Settings, deal_id: int, ton: TonEscrow | None = None) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    if is_ton_deal(deal):
        if deal["payout_hash"]:
            await db.touch_deal(deal_id, status=DEAL_CLOSED)
            return float(deal["ton_amount"] or 0)
        received = float(deal["ton_received"] or deal["ton_amount"] or 0)
        amount = payout_ton(float(deal["ton_amount"] or 0), settings.commission_percent, received, settings.ton_gas)
        dest = deal["buyer_ton"]
        if not dest or amount <= 0:
            raise DealError("deal_ton_send_fail")
        if ton is None or not ton.can_send:
            raise DealError("deal_ton_manual", amount=f"{amount:.9f}".rstrip("0").rstrip("."), address=dest)
        tx = await ton.send(dest, amount, f"deal {deal_id}")
        if not tx:
            raise DealError("deal_ton_send_fail")
        await db.touch_deal(deal_id, payout_hash=tx, status=DEAL_CLOSED)
        await db.bump_deals(deal["seller_id"], deal["buyer_id"])
        return amount
    payout = seller_payout(deal["amount"] or 0, settings.commission_percent)
    await db.change_balance(deal["seller_id"], payout)
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    if deal["nft_id"] and deal["nft_sent"]:
        await db.set_nft_status(
            deal["nft_id"],
            NFT_TRANSFERRED,
            owner_id=deal["buyer_id"],
            deal_id=deal_id,
        )
    await db.touch_deal(deal_id, status=DEAL_CLOSED)
    return payout


def err_text(lang: str, exc: DealError) -> str:
    return t(lang, exc.key, **exc.kwargs)
