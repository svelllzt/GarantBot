import asyncio
import os
import tempfile

from app.i18n import EN, RU
from app.services.ton import ton_to_currency
from app.storage import DEAL_OPEN, DEAL_PAID, KIND_TON_RUB, NFT_AVAILABLE, NFT_LOCKED, Storage


async def main() -> None:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        db = Storage(path)
        await db.connect()
        user = await db.upsert_user(1, "seller", "Иван")
        assert user["user_id"] == 1
        assert user["nick"] == "Иван"
        assert user["username"] == "seller"
        assert user["deals_count"] == 0
        await db.set_requisite(1, "card", "4111111111111111")
        await db.set_requisite(1, "ton_address", "UQD" + "A" * 45)
        await db.upsert_user(2, "buyer", "Пётр")
        deal_id = await db.create_deal(1, 2, KIND_TON_RUB)
        await db.touch_deal(deal_id, ton_amount=1.5, rub_amount=10000, buyer_ton="UQ" + "B" * 46)
        deal = await db.get_deal(deal_id)
        assert deal["kind"] == KIND_TON_RUB
        assert float(deal["ton_amount"]) == 1.5
        assert float(deal["rub_amount"]) == 10000
        row = await db.get_user(1)
        assert row["card"] == "4111111111111111"
        assert row["ton_address"].startswith("UQD")
        cols = await db._columns("users")
        for name in ("user_id", "nick", "username", "deals_count", "card", "phone", "bank_name", "ton_address", "lang"):
            assert name in cols, name
        await db.set_lang(1, "en")
        again = await db.upsert_user(1, "seller", "Иван")
        assert again["lang"] == "en"
        lid = await db.create_deal(
            1,
            0,
            category="acc_rbx",
            title="Roblox",
            status="listed",
            amount=12.5,
            description="mail unbound",
        )
        listed = await db.get_deal(lid)
        assert listed["status"] == "listed"
        assert listed["category"] == "acc_rbx"
        assert listed["title"] == "Roblox"
        assert listed["buyer_id"] == 0
        feed = await db.listed_deals()
        assert feed and feed[0]["id"] == lid
        nft_id = await db.add_nft(
            1,
            gift_id="g1",
            slug="slug",
            title="Gift",
            num=7,
            msg_id=42,
            from_user_id=1,
            is_unique=True,
        )
        paid_id = await db.create_deal(1, 2, category="nft", title="gift nft")
        await db.touch_deal(paid_id, nft_id=nft_id, status="paid", amount=10)
        pending = await db.pending_nft_sends()
        assert any(r["id"] == paid_id for r in pending)
        await db.touch_deal(paid_id, nft_sent=1)
        assert not any(r["id"] == paid_id for r in await db.pending_nft_sends())
        await db.set_banned(1, True, "test")
        banned = await db.banned_users()
        assert banned and banned[0]["user_id"] == 1
        assert banned[0]["ban_reason"] == "test"
        await db.set_banned(1, False)
        assert not await db.banned_users()
        faq_id = await db.add_faq("Как оплатить", "How to pay", "С баланса", "From balance")
        await db.set_faq_photo(faq_id, "file123")
        item = await db.get_faq(faq_id)
        assert item["title_ru"] == "Как оплатить"
        assert item["photo_id"] == "file123"
        await db.set_screen("menu", "AgPHOTO")
        assert (await db.screen_map())["menu"] == "AgPHOTO"
        await db.add_dispute_msg(lid, 2, "не отвязал почту", is_admin=False)
        msgs = await db.dispute_messages(lid)
        assert msgs and msgs[0]["text"] == "не отвязал почту"
        info = await db.stats()
        assert info["users"] >= 2
        assert "deals" in info
        deal_cols = await db._columns("deals")
        for name in ("category", "title", "channel_msg_id", "kind", "dispute_reason", "dispute_by", "nft_sent"):
            assert name in deal_cols, name

        missing = set(RU) - set(EN)
        extra = set(EN) - set(RU)
        assert not missing, missing
        assert not extra, extra

        class _Rate:
            ton_rate = 0.0

        assert ton_to_currency(10.0, _Rate(), 100.0) is None
        _Rate.ton_rate = 10.0
        assert ton_to_currency(10.0, _Rate(), 100.0) == 100.0
        assert ton_to_currency(5.0, _Rate(), 100.0) is None

        await db.change_balance(2, 50)
        paid = await db.create_deal(1, 2, status=DEAL_OPEN, amount=10)
        assert await db.claim_deal(paid, DEAL_OPEN, status=DEAL_PAID)
        assert not await db.claim_deal(paid, DEAL_OPEN, status=DEAL_PAID)
        dep = await db.create_deposit(2, 5, "G2test1")
        assert await db.claim_deposit(dep, "done")
        assert not await db.claim_deposit(dep, "done")
        other = await db.add_nft(1, gift_id="g2", slug="slug", title="Dup", num=1, msg_id=99, from_user_id=1, is_unique=True)
        assert other is None
        nft_b = await db.add_nft(1, gift_id="g3", slug="other", title="B", num=2, msg_id=100, from_user_id=1, is_unique=True)
        assert nft_b
        assert await db.claim_nft(nft_b, NFT_AVAILABLE, NFT_LOCKED, deal_id=paid)
        assert not await db.claim_nft(nft_b, NFT_AVAILABLE, NFT_LOCKED, deal_id=paid)
        exclusive = await db.create_deal(1, 2, exclusive=True)
        assert exclusive is None
        await db.close()
        print("ok")
    finally:
        os.unlink(path)


if __name__ == "__main__":
    asyncio.run(main())
