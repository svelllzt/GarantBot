import asyncio
import os
import tempfile

from app.storage import KIND_TON_RUB, Storage


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
        for name in ("category", "title", "channel_msg_id", "kind", "dispute_reason", "dispute_by"):
            assert name in deal_cols, name
        await db.close()
        print("ok")
    finally:
        os.unlink(path)


if __name__ == "__main__":
    asyncio.run(main())
