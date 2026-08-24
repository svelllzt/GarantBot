import asyncio
import os
import tempfile
from pathlib import Path

from app.i18n import EN, RU
from app.services.ton import ton_to_currency
from app.storage import DEAL_CANCELLED, DEAL_CLOSED, DEAL_LISTED, DEAL_OPEN, DEAL_PENDING, NFT_AVAILABLE, NFT_LOCKED, NFT_TRANSFERRED, WALLET_DONE, WALLET_SENDING, Storage
from app.util import seller_payout, service_fee, listing_is_buy


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
        await db.set_requisite(1, "ton_address", "UQD" + "A" * 45)
        await db.upsert_user(2, "buyer", "Пётр")
        deal_id = await db.create_deal(1, 2, currency="TON", secret="login:pass")
        await db.touch_deal(deal_id, amount=1.5)
        deal = await db.get_deal(deal_id)
        assert deal["currency"] == "TON"
        assert deal["secret"] == "login:pass"
        assert float(deal["amount"]) == 1.5
        row = await db.get_user(1)
        assert row["ton_address"].startswith("UQD")
        cols = await db._columns("users")
        for name in ("user_id", "nick", "username", "deals_count", "ton_address", "lang", "balance", "balance_ton", "frozen_usdt", "frozen_ton"):
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
            currency="USDT",
            secret="mail:pass",
        )
        listed = await db.get_deal(lid)
        assert listed["status"] == "listed"
        assert listed["category"] == "acc_rbx"
        assert listed["title"] == "Roblox"
        assert listed["buyer_id"] == 0
        assert listed["currency"] == "USDT"
        assert listed["secret"] == "mail:pass"
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
        open_nft = await db.create_deal(1, 2, category="nft", title="gift nft")
        await db.touch_deal(open_nft, nft_id=nft_id, status=DEAL_OPEN, amount=10)
        pending = await db.pending_nft_sends()
        assert any(r["id"] == open_nft for r in pending)
        await db.touch_deal(open_nft, nft_sent=1)
        assert not any(r["id"] == open_nft for r in await db.pending_nft_sends())
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
        for name in ("category", "title", "channel_msg_id", "kind", "dispute_reason", "dispute_by", "nft_sent", "currency", "secret", "cancel_by", "created_by"):
            assert name in deal_cols, name
        msg_cols = await db._columns("dispute_messages")
        assert "target_id" in msg_cols

        missing = set(RU) - set(EN)
        extra = set(EN) - set(RU)
        assert not missing, missing
        assert not extra, extra
        from app.i18n import t
        from app.util import ban_notice
        from app.buttons import EMOJI, Theme
        from app.config import DEFAULTS, Settings, load_values
        from app.services.fragment import StarsBuyer, cookies_line, parse_cookies
        assert "menu" in t("ru", "admin_screen_ask", key="menu")
        assert "Иван" in t("ru", "welcome", name="Иван")
        assert "Phantom OTC" in t("ru", "welcome", name="Иван")
        assert "Phantom OTC" in t("en", "welcome", name="Ivan")
        assert parse_cookies("stel_ssid=a; stel_dt=b; stel_token=c") == {
            "stel_ssid": "a",
            "stel_dt": "b",
            "stel_token": "c",
        }
        assert parse_cookies('{"stel_ssid": "a", "stel_token": "b"}') == {"stel_ssid": "a", "stel_token": "b"}
        assert cookies_line({"a": "1", "b": "2"}) == "a=1; b=2"
        buyer = StarsBuyer(Settings(dict(DEFAULTS), Path("config.ini")))
        assert buyer.pack() == 100
        assert not buyer.enabled()
        assert buyer.status_key() == "admin_fragment_off"
        assert "btn_deal" in t("ru", "admin_btn_card", title="x", key="btn_deal", ru="a", en="b", style="s", emoji="e")
        notice = ban_notice("ru", "спам", "support")
        assert "спам" in notice and "support" in notice and "Доступ закрыт" in notice
        themed = Theme({"btn_deal": {"emoji_id": "123456789012345", "label_ru": "Сделка", "label_en": "Deal"}})
        labeled = themed.text("btn_deal", "ru")
        assert labeled == "Сделка"
        assert EMOJI["btn_deal"] not in labeled
        assert EMOJI["btn_deal"] in Theme({}).text("btn_deal", "ru")

        class _Rate:
            ton_rate = 0.0

        assert ton_to_currency(10.0, _Rate(), 100.0) is None
        _Rate.ton_rate = 10.0
        assert ton_to_currency(10.0, _Rate(), 100.0) == 100.0
        assert ton_to_currency(5.0, _Rate(), 100.0) is None

        from app.services.ton import ton_comment_total, usdt_comment_total

        split_ton = {
            "ok": True,
            "result": [
                {"transaction_id": {"hash": "a", "lt": "1"}, "in_msg": {"message": "Gsplit", "value": "40000000"}},
                {"transaction_id": {"hash": "b", "lt": "2"}, "in_msg": {"message": "Gsplit", "value": "70000000"}},
                {"transaction_id": {"hash": "c", "lt": "3"}, "in_msg": {"message": "other", "value": "9000000000"}},
            ],
        }
        assert abs(ton_comment_total(split_ton, "Gsplit") - 0.11) < 1e-9
        assert ton_comment_total(split_ton, "missing") is None
        split_usdt = {
            "jetton_transfers": [
                {"transaction_hash": "h1", "comment": "Usplit", "amount": "1000000"},
                {"transaction_hash": "h2", "comment": "Usplit", "amount": "2500000"},
                {"transaction_hash": "h3", "comment": "other", "amount": "9000000"},
            ]
        }
        assert abs(usdt_comment_total(split_usdt, "Usplit") - 3.5) < 1e-9
        assert usdt_comment_total(split_usdt, "missing") is None

        await db.credit_asset(2, "USDT", 50)
        paid = await db.create_deal(1, 2, status=DEAL_OPEN, amount=10)
        assert await db.claim_deal(paid, DEAL_OPEN, status=DEAL_CLOSED)
        assert not await db.claim_deal(paid, DEAL_OPEN, status=DEAL_CLOSED)
        dep = await db.create_deposit(2, 5, "G2test1", asset="USDT")
        assert await db.claim_deposit(dep, "done")
        assert not await db.claim_deposit(dep, "done")
        extra_dep = await db.create_deposit(2, 1, "G2test1", asset="USDT")
        assert extra_dep
        rec = await db.record_deposit(2, 3, "G2", "USDT", "tx-auto-1")
        assert rec
        assert await db.record_deposit(2, 1, "G2", "USDT", "tx-auto-1") is None
        rec2 = await db.record_deposit(2, 1, "G2", "USDT", "tx-auto-2")
        assert rec2
        from app.services.deposits import memo_user_id, user_memo
        assert user_memo(2) == "G2"
        assert memo_user_id("G2") == 2
        assert memo_user_id("pay G8296379573 now") == 8296379573
        assert memo_user_id("hello") is None
        other = await db.add_nft(1, gift_id="g2", slug="slug", title="Dup", num=1, msg_id=99, from_user_id=1, is_unique=True)
        assert other is None
        nft_b = await db.add_nft(1, gift_id="g3", slug="other", title="B", num=2, msg_id=100, from_user_id=1, is_unique=True)
        assert nft_b
        assert await db.claim_nft(nft_b, NFT_AVAILABLE, NFT_LOCKED, deal_id=paid)
        assert not await db.claim_nft(nft_b, NFT_AVAILABLE, NFT_LOCKED, deal_id=paid)
        exclusive = await db.create_deal(1, 2, exclusive=True)
        assert exclusive is None
        from app.keyboards import CatCB, NavCB, main_menu, screens_admin_kb
        packed = CatCB(k="acc", g=1).pack()
        assert ":" not in CatCB(k="acc", g=1).k
        assert packed.startswith("cat:")
        parsed = CatCB.unpack(packed)
        assert parsed.k == "acc" and parsed.g == 1
        theme = Theme({})
        admin_cbs = [btn.callback_data or "" for row in main_menu("ru", theme, admin=True).inline_keyboard for btn in row]
        user_cbs = [btn.callback_data or "" for row in main_menu("ru", theme, admin=False).inline_keyboard for btn in row]
        assert NavCB(a="admin").pack() in admin_cbs
        assert NavCB(a="admin").pack() not in user_cbs
        assert NavCB(a="feed").pack() in user_cbs
        scr_txt = [btn.text for row in screens_admin_kb("ru", theme).inline_keyboard for btn in row]
        assert "Меню" in scr_txt and "Профиль" in scr_txt and "Пополнение" in scr_txt
        assert "menu" not in scr_txt

        from app.services import deals as dsvc
        from app.services.deals import DealError as DealErr

        for row in await db.fetchall("SELECT id FROM deals"):
            await db.touch_deal(row["id"], status=DEAL_CLOSED)
        await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)
        await db.credit_asset(2, "USDT", -float((await db.get_user(2))["balance"]))
        assert float((await db.get_user(2))["balance"]) == 0
        listed_nft = await dsvc.create_listing(
            db, 1, "nft", "Gift", 15, "unique gift", nft_id=nft_id, currency="USDT", secret="gift"
        )
        listed_row = await db.get_deal(listed_nft)
        assert listed_row["status"] == DEAL_LISTED
        assert listed_row["nft_id"] == nft_id
        assert listed_row["currency"] == "USDT"
        locked = await db.get_nft(nft_id)
        assert locked["status"] == NFT_LOCKED
        try:
            await dsvc.take_listing(db, listed_nft, 2)
            raise AssertionError("buyer without funds must fail")
        except DealErr as exc:
            assert exc.key == "deal_need_deposit"
        await db.credit_asset(2, "USDT", 20)
        await dsvc.take_listing(db, listed_nft, 2)
        taken = await db.get_deal(listed_nft)
        assert taken["status"] == DEAL_OPEN
        assert taken["buyer_id"] == 2
        buyer_row = await db.get_user(2)
        assert abs(db.available(buyer_row, "USDT") - 5) < 1e-9
        assert abs(db.frozen_of(buyer_row, "USDT") - 15) < 1e-9
        try:
            await db.spend_available(2, "USDT", 6)
            raise AssertionError("frozen funds must not be spendable")
        except ValueError:
            pass
        await db.spend_available(2, "USDT", 5)
        buyer_row = await db.get_user(2)
        assert abs(db.available(buyer_row, "USDT")) < 1e-9
        assert abs(db.frozen_of(buyer_row, "USDT") - 15) < 1e-9
        settings = Settings(dict(DEFAULTS), Path("config.ini"))
        try:
            await dsvc.complete(db, settings, listed_nft, 2)
            raise AssertionError("nft complete before send must fail")
        except DealErr as exc:
            assert exc.key == "deal_nft_wait_send"
        await db.touch_deal(listed_nft, nft_sent=1)
        try:
            await dsvc.cancel_mutual(db, listed_nft)
            raise AssertionError("cancel after nft send must fail")
        except DealErr as exc:
            assert exc.key == "deal_cancel_denied"
        payout = await dsvc.complete(db, settings, listed_nft, 2)
        assert abs(payout - seller_payout(15, settings.commission_percent, "USDT")) < 1e-9
        seller_row = await db.get_user(1)
        buyer_row = await db.get_user(2)
        assert abs(db.frozen_of(buyer_row, "USDT")) < 1e-9
        assert abs(db.available(seller_row, "USDT") - payout) < 1e-9
        assert (await db.get_nft(nft_id))["status"] == NFT_TRANSFERRED
        await db.touch_deal(listed_nft, status=DEAL_CLOSED)
        await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)

        await db.upsert_user(11, "sel11", "Продавец11")
        await db.upsert_user(12, "buy12", "Покуп12")
        await db.credit_asset(12, "USDT", 40)
        buy_lid = await dsvc.create_listing(db, 12, "nft", "Want gift", 20, "buy", as_buyer=True)
        buy_row = await db.get_deal(buy_lid)
        assert buy_row["seller_id"] == 0
        assert buy_row["buyer_id"] == 12
        assert listing_is_buy(buy_row)
        assert buy_row["created_by"] == 12
        feed_rows = await db.listed_deals()
        assert any(r["id"] == buy_lid for r in feed_rows)
        nft_buy = await db.add_nft(11, gift_id="gbuy", slug="giftbuy", title="BuyNFT", num=9, msg_id=201, from_user_id=11, is_unique=True)
        try:
            await dsvc.take_listing(db, buy_lid, 11)
            raise AssertionError("nft buy listing must need nft")
        except DealErr as exc:
            assert exc.key == "deal_nft_need_item"
        await dsvc.take_listing(db, buy_lid, 11, nft_id=nft_buy)
        taken_buy = await db.get_deal(buy_lid)
        assert taken_buy["status"] == DEAL_OPEN
        assert taken_buy["seller_id"] == 11
        assert taken_buy["buyer_id"] == 12
        assert taken_buy["nft_id"] == nft_buy
        buyer12 = await db.get_user(12)
        assert abs(db.frozen_of(buyer12, "USDT") - 20) < 1e-9
        await db.touch_deal(buy_lid, status=DEAL_CLOSED)
        await db.unfreeze_asset(12, "USDT", 20)
        await db.set_nft_status(nft_buy, NFT_AVAILABLE, deal_id=None)

        goods_buy = await dsvc.create_listing(db, 12, "goods", "Want item", 8, "need it", as_buyer=True)
        await dsvc.take_listing(db, goods_buy, 11)
        opened_buy = await db.get_deal(goods_buy)
        assert opened_buy["seller_id"] == 11 and opened_buy["buyer_id"] == 12
        assert abs(db.frozen_of(await db.get_user(12), "USDT") - 8) < 1e-9
        from app.keyboards import DealCB as DealCBChat, deal_kb as deal_kb_early
        buy_kb = deal_kb_early("ru", theme, opened_buy, 12, await db.get_user(11))
        buy_cbs = [btn.callback_data or "" for row in buy_kb.inline_keyboard for btn in row]
        assert DealCBChat(a="chat", i=goods_buy).pack() in buy_cbs
        await dsvc.request_cancel(db, goods_buy, 12)
        await dsvc.confirm_cancel(db, goods_buy, 11)
        assert (await db.get_deal(goods_buy))["status"] == DEAL_CANCELLED

        offer_buy = await dsvc.open_offer(db, 12, 11, as_buyer=True, category="goods", title="Buy direct", amount=4, currency="USDT")
        pending_buy = await db.get_deal(offer_buy)
        assert pending_buy["buyer_id"] == 12 and pending_buy["seller_id"] == 11
        assert pending_buy["created_by"] == 12
        try:
            await dsvc.accept(db, offer_buy, 12)
            raise AssertionError("buyer must not accept own offer")
        except DealErr as exc:
            assert exc.key == "error"
        await dsvc.accept(db, offer_buy, 11)
        opened_off = await db.get_deal(offer_buy)
        assert opened_off["status"] == DEAL_OPEN
        assert abs(db.frozen_of(await db.get_user(12), "USDT") - 4) < 1e-9
        await db.add_dispute_msg(offer_buy, 12, "hello seller", is_admin=False)
        await db.add_dispute_msg(offer_buy, 1, "admin to seller", is_admin=True, target_id=11)
        await db.add_dispute_msg(offer_buy, 1, "admin to buyer", is_admin=True, target_id=12)
        thread_msgs = await db.dispute_messages(offer_buy)
        assert len(thread_msgs) >= 3
        await dsvc.request_cancel(db, offer_buy, 11)
        await dsvc.confirm_cancel(db, offer_buy, 12)

        await db.upsert_user(4, "accseller", "Акк")
        acc_id = await dsvc.create_listing(db, 4, "acc_rbx", "Roblox", 8, "mail unbound", currency="TON", secret="rbx:mail")
        acc = await db.get_deal(acc_id)
        assert not acc["nft_id"]
        assert acc["currency"] == "TON"
        try:
            await dsvc.take_listing(db, acc_id, 2)
            raise AssertionError("account listing without TON must fail")
        except DealErr as exc:
            assert exc.key == "deal_need_deposit"
        await db.credit_asset(2, "TON", 10)
        await dsvc.take_listing(db, acc_id, 2)
        opened_acc = await db.get_deal(acc_id)
        assert opened_acc["status"] == DEAL_OPEN
        assert opened_acc["buyer_id"] == 2
        buyer_row = await db.get_user(2)
        assert abs(db.available(buyer_row, "TON") - 2) < 1e-9
        assert abs(db.frozen_of(buyer_row, "TON") - 8) < 1e-9
        from app.keyboards import deal_kb
        from app.catalog import needs_nft
        assert not needs_nft("acc_rbx")
        seller4 = await db.get_user(4)
        seller_kb = deal_kb("ru", theme, opened_acc, 4, seller4)
        seller_cb = [btn.callback_data or "" for row in seller_kb.inline_keyboard for btn in row]
        assert not any(cb.startswith("deal:nft") for cb in seller_cb)
        assert any(cb.startswith("deal:dis") for cb in seller_cb)
        buyer_kb = deal_kb("ru", theme, opened_acc, 2, seller4)
        buyer_cb = [btn.callback_data or "" for row in buyer_kb.inline_keyboard for btn in row]
        assert any(cb.startswith("deal:ok") for cb in buyer_cb)
        assert any(cb.startswith("deal:dis") for cb in buyer_cb)
        assert any(cb.startswith("deal:chat") for cb in buyer_cb)
        assert any(cb.startswith("deal:chat") for cb in seller_cb)
        assert any(cb.startswith("deal:disth") for cb in buyer_cb)
        assert any(cb.startswith("deal:disth") for cb in seller_cb)
        assert not any(cb.startswith("deal:pdf") for cb in buyer_cb)
        assert not any(cb.startswith("deal:pay") for cb in buyer_cb)
        try:
            await dsvc.attach_nft(db, acc_id, 4, nft_id)
            raise AssertionError("account deal must not attach nft")
        except DealErr:
            pass
        payout_ton = await dsvc.complete(db, settings, acc_id, 2)
        assert abs(payout_ton - seller_payout(8, settings.commission_percent, "TON")) < 1e-9
        seller4 = await db.get_user(4)
        buyer_row = await db.get_user(2)
        assert abs(db.frozen_of(buyer_row, "TON")) < 1e-9
        assert abs(db.available(seller4, "TON") - payout_ton) < 1e-9
        await db.touch_deal(acc_id, status=DEAL_CLOSED)

        await db.upsert_user(21, "sel21", "Прод21")
        await db.upsert_user(22, "buy22", "Пок22")
        await db.upsert_user(90, "cashier", "Касса")
        await db.credit_asset(22, "USDT", 10)
        fee_lid = await dsvc.create_listing(db, 21, "goods", "Fee item", 10, "x", currency="USDT")
        await dsvc.take_listing(db, fee_lid, 22)
        fee_vals = dict(DEFAULTS)
        fee_vals["service_id"] = 90
        fee_vals["commission_percent"] = 2.0
        fee_settings = Settings(fee_vals, Path("config.ini"))
        fee_payout = await dsvc.complete(db, fee_settings, fee_lid, 22)
        assert abs(fee_payout - seller_payout(10, 2, "USDT")) < 1e-9
        seller21 = await db.get_user(21)
        buyer22 = await db.get_user(22)
        svc90 = await db.get_user(90)
        assert abs(db.available(seller21, "USDT") - seller_payout(10, 2, "USDT")) < 1e-9
        assert abs(db.available(buyer22, "USDT")) < 1e-9
        assert abs(db.frozen_of(buyer22, "USDT")) < 1e-9
        assert svc90 is not None
        assert svc90["nick"] == "Касса"
        assert svc90["username"] == "cashier"
        assert abs(db.available(svc90, "USDT") - service_fee(10, 2, "USDT")) < 1e-9
        await db.touch_deal(fee_lid, status=DEAL_CLOSED)

        nft_d = await db.add_nft(1, gift_id="g5", slug="giftd", title="D", num=5, msg_id=102, from_user_id=1, is_unique=True)
        offer = await dsvc.open_offer(db, 1, 2, category="nft", title="GiftD", nft_id=nft_d, amount=3, currency="USDT")
        assert (await db.get_nft(nft_d))["status"] == NFT_LOCKED
        await dsvc.decline(db, offer, 2)
        assert (await db.get_nft(nft_d))["status"] == NFT_AVAILABLE
        await db.credit_asset(2, "USDT", 10)
        listed2 = await dsvc.create_listing(db, 1, "nft", "Gift2", 4, "x", nft_id=nft_d, currency="USDT")
        await dsvc.take_listing(db, listed2, 2)
        await db.touch_deal(listed2, nft_sent=1)
        await dsvc.open_dispute(db, listed2, 2, "bad")
        await dsvc.verdict_buyer(db, listed2)
        nft_after = await db.get_nft(nft_d)
        assert nft_after["status"] == NFT_TRANSFERRED
        assert nft_after["owner_id"] == 2

        nft_e = await db.add_nft(1, gift_id="g6", slug="gifte", title="E", num=6, msg_id=103, from_user_id=1, is_unique=True)
        offer_e = await dsvc.open_offer(db, 1, 2, category="nft", title="GiftE", nft_id=nft_e, amount=2, currency="USDT", secret="login:pass")
        try:
            await dsvc.accept(db, offer_e, 1)
            raise AssertionError("seller must not accept")
        except DealErr as exc:
            assert exc.key == "error"
        assert (await db.get_deal(offer_e))["status"] == DEAL_PENDING
        from app.keyboards import DealCB, deal_kb as deal_kb_fn
        pending_offer = await db.get_deal(offer_e)
        buyer_pending_kb = deal_kb_fn("ru", theme, pending_offer, 2, await db.get_user(1))
        buyer_pending_cb = [btn.callback_data or "" for row in buyer_pending_kb.inline_keyboard for btn in row]
        assert DealCB(a="acc", i=offer_e).pack() in buyer_pending_cb
        seller_pending_kb = deal_kb_fn("ru", theme, pending_offer, 1, await db.get_user(1))
        seller_pending_cb = [btn.callback_data or "" for row in seller_pending_kb.inline_keyboard for btn in row]
        assert DealCB(a="acc", i=offer_e).pack() not in seller_pending_cb
        await db.credit_asset(2, "USDT", 10)
        await dsvc.accept(db, offer_e, 2)
        await db.touch_deal(offer_e, nft_sent=1)
        nft_f = await db.add_nft(1, gift_id="g7", slug="giftf", title="F", num=7, msg_id=104, from_user_id=1, is_unique=True)
        try:
            await dsvc.attach_nft(db, offer_e, 1, nft_f)
            raise AssertionError("nft swap after send must fail")
        except DealErr:
            pass
        assert (await db.get_nft(nft_e))["status"] == NFT_LOCKED
        assert (await db.get_nft(nft_f))["status"] == NFT_AVAILABLE
        from app.util import render_deal
        opened_e = await db.get_deal(offer_e)
        stranger = await render_deal(db, opened_e, "ru", "USDT", viewer_id=99)
        assert "login:pass" not in stranger
        assert t("ru", "deal_secret_hidden") in stranger
        party_text = await render_deal(db, opened_e, "ru", "USDT", viewer_id=2)
        assert "login:pass" in party_text
        assert "Комиссия" in party_text
        assert "продавцу" in party_text
        await db.touch_deal(offer_e, status=DEAL_CANCELLED)
        await db.unfreeze_asset(2, "USDT", 2)
        await db.set_nft_status(nft_e, NFT_AVAILABLE, deal_id=None)

        await db.upsert_user(7, "s7", "S7")
        await db.upsert_user(8, "b8", "B8")
        await db.credit_asset(8, "USDT", 20)
        mut_id = await dsvc.create_listing(db, 7, "goods", "Item", 10, "desc", currency="USDT", secret="hidden")
        await dsvc.take_listing(db, mut_id, 8)
        assert abs(db.frozen_of(await db.get_user(8), "USDT") - 10) < 1e-9
        try:
            await dsvc.confirm_cancel(db, mut_id, 8)
            raise AssertionError("buyer must not cancel alone")
        except DealErr:
            pass
        assert (await db.get_deal(mut_id))["status"] == DEAL_OPEN
        assert await dsvc.request_cancel(db, mut_id, 7) == "wait"
        assert int((await db.get_deal(mut_id))["cancel_by"] or 0) == 7
        try:
            await dsvc.confirm_cancel(db, mut_id, 7)
            raise AssertionError("initiator must not confirm own cancel")
        except DealErr:
            pass
        await dsvc.confirm_cancel(db, mut_id, 8)
        cancelled = await db.get_deal(mut_id)
        assert cancelled["status"] == DEAL_CANCELLED
        assert abs(db.frozen_of(await db.get_user(8), "USDT")) < 1e-9

        await db.credit_asset(8, "USDT", 10)
        mut2 = await dsvc.create_listing(db, 7, "goods", "Item2", 6, "desc", currency="USDT")
        await dsvc.take_listing(db, mut2, 8)
        assert await dsvc.request_cancel(db, mut2, 7) == "wait"
        assert await dsvc.request_cancel(db, mut2, 8) == "done"
        assert (await db.get_deal(mut2))["status"] == DEAL_CANCELLED
        assert abs(db.frozen_of(await db.get_user(8), "USDT")) < 1e-9

        sent_id = await db.create_deal(7, 8, status=DEAL_OPEN, amount=1)
        assert await db.claim_nft_sent(sent_id)
        assert not await db.claim_nft_sent(sent_id)
        await db.revert_nft_sent(sent_id)
        assert await db.claim_nft_sent(sent_id)

        wd_cols = await db._columns("withdrawals")
        assert "tx_hash" in wd_cols
        from app.handlers import profile as ph
        from app.keyboards import asset_pick_kb
        from app.util import clean_ton, valid_ton
        assert ph.asset_pick_kb is asset_pick_kb
        wd_kb = asset_pick_kb("ru", theme, "wasset")
        wd_cbs = [btn.callback_data or "" for row in wd_kb.inline_keyboard for btn in row]
        assert any("wasset" in cb and "USDT" in cb for cb in wd_cbs)
        assert any("wasset" in cb and "TON" in cb for cb in wd_cbs)
        sample = "UQ" + ("A" * 46)
        assert valid_ton(sample)
        assert clean_ton("https://tonviewer.com/" + sample + "?utm=1") == sample
        assert abs(seller_payout(100, 2, "USDT") - 98) < 1e-9
        assert abs(seller_payout(10, 2, "TON") - 9.8) < 1e-9
        assert abs(service_fee(100, 2, "USDT") - 2) < 1e-9
        assert abs(service_fee(10, 2, "TON") - 0.2) < 1e-9
        uid_vals = dict(DEFAULTS)
        uid_vals["admin_ids"] = "5,3"
        uid_vals["service_id"] = 0
        assert Settings(uid_vals, Path("config.ini")).service_uid() == 3
        uid_vals["service_id"] = 9
        assert Settings(uid_vals, Path("config.ini")).service_uid() == 9
        from app.services.ton import TonEscrow
        addr = "UQ" + ("A" * 46)
        first_wd = await db.create_withdraw(2, 3, "ton", addr, "USDT")
        try:
            await db.create_withdraw(2, 1, "ton", addr, "USDT")
            raise AssertionError("second pending withdraw must fail")
        except ValueError:
            pass
        assert await db.claim_withdraw(first_wd, WALLET_SENDING)
        try:
            await db.create_withdraw(2, 1, "ton", addr, "USDT")
            raise AssertionError("sending withdraw must block a new one")
        except ValueError:
            pass
        await db.finish_withdraw(first_wd, WALLET_DONE, "txhash")
        done_wd = await db.get_withdraw(first_wd)
        assert done_wd["tx_hash"] == "txhash"
        assert done_wd["status"] == "done"
        second_wd = await db.create_withdraw(2, 1, "ton", addr, "TON")
        assert second_wd
        await db.finish_withdraw(second_wd, WALLET_DONE)
        escrow = TonEscrow(Settings(dict(DEFAULTS), Path("config.ini")))
        assert await escrow.payout(addr, 1, "TON") is None
        assert await escrow.payout(addr, 1, "USDT") is None
        assert "txhash" in t("ru", "admin_wd_ok", id=1, amount="1", currency="USDT", address=addr, hash="txhash")
        assert "txhash" in t("en", "withdraw_sent", id=1, amount="1", currency="TON", address=addr, hash="txhash")

        cfg_fd, cfg_path = tempfile.mkstemp(suffix=".ini")
        os.close(cfg_fd)
        try:
            Path(cfg_path).write_text("[bot]\nadmin_ids = 1\n", encoding="utf-8")
            cfg = Settings(dict(DEFAULTS), Path(cfg_path))
            cfg.patch("admin_ids", "1")
            assert cfg.admins == frozenset({1})
            cfg.patch("admin_ids", "1,42")
            assert 42 in cfg.admins
            cfg.patch("ton_address", "EQDtestaddress")
            assert cfg.ton_address == "EQDtestaddress"
            cfg.patch("bank_session", "sess-value")
            assert cfg.bank_session == "sess-value"
            from app.config import clean_session_string, session_string_ok
            assert clean_session_string("session = AgH2abcDEF") == "AgH2abcDEF"
            assert clean_session_string('session = session = "AgH2abcDEF"') == "AgH2abcDEF"
            assert clean_session_string("  AgH2abcDEF \n") == "AgH2abcDEF"
            import base64 as _b64
            fake_sess = _b64.urlsafe_b64encode(b"x" * 80).decode().rstrip("=")
            assert session_string_ok(fake_sess)
            assert session_string_ok("session = " + fake_sess)
            assert not session_string_ok("session = short")
            Path(cfg_path).write_text("[bank]\nsession = session = " + fake_sess + "\n", encoding="utf-8")
            loaded = Settings(load_values(Path(cfg_path)), Path(cfg_path))
            assert loaded.bank_session == fake_sess
        finally:
            os.unlink(cfg_path)

        await db.close()
        print("ok")
    finally:
        os.unlink(path)


if __name__ == "__main__":
    asyncio.run(main())
