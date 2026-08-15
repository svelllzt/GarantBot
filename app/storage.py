from __future__ import annotations

import time
from typing import Any, Iterable, Optional

import aiosqlite

DEAL_PENDING = "pending"
DEAL_OPEN = "open"
DEAL_PAID = "paid"
DEAL_DISPUTE = "dispute"
DEAL_REVIEW = "review"
DEAL_CLOSED = "closed"
DEAL_CANCELLED = "cancelled"

NFT_AVAILABLE = "available"
NFT_LOCKED = "locked"
NFT_TRANSFERRED = "transferred"

ACTIVE_DEALS = (DEAL_PENDING, DEAL_OPEN, DEAL_PAID, DEAL_DISPUTE)
WALLET_PENDING = "pending"
WALLET_DONE = "done"
WALLET_REJECTED = "rejected"


def now() -> int:
    return int(time.time())


class Storage:
    def __init__(self, path: str) -> None:
        self.path = path
        self.db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self.db = await aiosqlite.connect(self.path)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA foreign_keys=ON")
        await self._schema()

    async def close(self) -> None:
        if self.db:
            await self.db.close()
            self.db = None

    async def _schema(self) -> None:
        await self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                lang TEXT,
                balance REAL NOT NULL DEFAULT 0,
                deals_count INTEGER NOT NULL DEFAULT 0,
                card TEXT,
                phone TEXT,
                bank_name TEXT,
                ton_address TEXT,
                banned INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                amount REAL,
                status TEXT NOT NULL,
                nft_id INTEGER,
                description TEXT,
                nft_sent INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_deals_seller ON deals(seller_id, status);
            CREATE INDEX IF NOT EXISTS idx_deals_buyer ON deals(buyer_id, status);

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                gift_id TEXT,
                slug TEXT,
                title TEXT NOT NULL,
                num INTEGER,
                msg_id INTEGER,
                from_user_id INTEGER,
                status TEXT NOT NULL,
                deal_id INTEGER,
                is_unique INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL,
                UNIQUE(msg_id)
            );
            CREATE INDEX IF NOT EXISTS idx_inv_owner ON inventory(owner_id, status);

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                comment TEXT NOT NULL UNIQUE,
                tx_hash TEXT,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            """
        )
        await self.db.commit()

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> aiosqlite.Cursor:
        cur = await self.db.execute(sql, tuple(params))
        await self.db.commit()
        return cur

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[aiosqlite.Row]:
        cur = await self.db.execute(sql, tuple(params))
        return await cur.fetchone()

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[aiosqlite.Row]:
        cur = await self.db.execute(sql, tuple(params))
        return await cur.fetchall()

    async def upsert_user(self, user_id: int, username: Optional[str], first_name: str) -> aiosqlite.Row:
        row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        uname = (username or "").lstrip("@").lower() or None
        if row is None:
            await self.execute(
                "INSERT INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
                (user_id, uname, first_name, now()),
            )
        else:
            await self.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (uname, first_name, user_id),
            )
        return await self.get_user(user_id)

    async def get_user(self, user_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

    async def get_user_by_username(self, username: str) -> Optional[aiosqlite.Row]:
        clean = username.lstrip("@").lower()
        return await self.fetchone("SELECT * FROM users WHERE username = ?", (clean,))

    async def set_lang(self, user_id: int, lang: str) -> None:
        await self.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))

    async def set_banned(self, user_id: int, banned: bool) -> None:
        await self.execute("UPDATE users SET banned = ? WHERE user_id = ?", (int(banned), user_id))

    async def set_requisite(self, user_id: int, field: str, value: Optional[str]) -> None:
        if field not in {"card", "phone", "bank_name", "ton_address"}:
            raise ValueError(field)
        await self.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))

    async def change_balance(self, user_id: int, delta: float) -> float:
        cur = await self.db.execute(
            """
            UPDATE users
            SET balance = ROUND(balance + ?, 2)
            WHERE user_id = ? AND ROUND(balance + ?, 2) >= 0
            """,
            (delta, user_id, delta),
        )
        await self.db.commit()
        if cur.rowcount != 1:
            raise ValueError("insufficient")
        row = await self.get_user(user_id)
        return float(row["balance"])

    async def set_balance(self, user_id: int, amount: float) -> None:
        await self.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (round(amount, 2), user_id),
        )

    async def bump_deals(self, *user_ids: int) -> None:
        for uid in user_ids:
            await self.execute(
                "UPDATE users SET deals_count = deals_count + 1 WHERE user_id = ?",
                (uid,),
            )

    async def user_ids(self) -> list[int]:
        rows = await self.fetchall("SELECT user_id FROM users")
        return [r["user_id"] for r in rows]

    async def stats(self) -> tuple[int, int, float]:
        users = await self.fetchone("SELECT COUNT(*) AS c FROM users")
        deals = await self.fetchone(
            "SELECT COUNT(*) AS c FROM deals WHERE status = ?",
            (DEAL_CLOSED,),
        )
        money = await self.fetchone(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM deals WHERE status = ?",
            (DEAL_CLOSED,),
        )
        return users["c"], deals["c"], float(money["s"])

    async def create_deal(self, seller_id: int, buyer_id: int) -> int:
        cur = await self.execute(
            """
            INSERT INTO deals (seller_id, buyer_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (seller_id, buyer_id, DEAL_PENDING, now(), now()),
        )
        return cur.lastrowid

    async def get_deal(self, deal_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM deals WHERE id = ?", (deal_id,))

    async def active_deal(self, user_id: int) -> Optional[aiosqlite.Row]:
        placeholders = ",".join("?" * len(ACTIVE_DEALS))
        return await self.fetchone(
            f"""
            SELECT * FROM deals
            WHERE (seller_id = ? OR buyer_id = ?) AND status IN ({placeholders})
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, user_id, *ACTIVE_DEALS),
        )

    async def touch_deal(
        self,
        deal_id: int,
        *,
        status: Optional[str] = None,
        amount: Optional[float] = None,
        nft_id: Optional[int] = None,
        description: Optional[str] = None,
        nft_sent: Optional[int] = None,
        clear_nft: bool = False,
    ) -> None:
        deal = await self.get_deal(deal_id)
        if deal is None:
            return
        await self.execute(
            """
            UPDATE deals SET
                status = ?,
                amount = ?,
                nft_id = ?,
                description = ?,
                nft_sent = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status if status is not None else deal["status"],
                amount if amount is not None else deal["amount"],
                None if clear_nft else (nft_id if nft_id is not None else deal["nft_id"]),
                description if description is not None else deal["description"],
                nft_sent if nft_sent is not None else deal["nft_sent"],
                now(),
                deal_id,
            ),
        )

    async def history(self, user_id: int, role: str, limit: int = 15) -> list[aiosqlite.Row]:
        column = "seller_id" if role == "seller" else "buyer_id"
        return await self.fetchall(
            f"""
            SELECT * FROM deals
            WHERE {column} = ? AND status IN (?, ?)
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, DEAL_CLOSED, DEAL_CANCELLED, limit),
        )

    async def open_disputes(self) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM deals WHERE status = ? ORDER BY id DESC",
            (DEAL_DISPUTE,),
        )

    async def add_review(self, seller_id: int, buyer_id: int, deal_id: int, text: str) -> None:
        await self.execute(
            """
            INSERT INTO reviews (seller_id, buyer_id, deal_id, text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (seller_id, buyer_id, deal_id, text, now()),
        )

    async def reviews_for(self, seller_id: int, limit: int = 10) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM reviews WHERE seller_id = ? ORDER BY id DESC LIMIT ?",
            (seller_id, limit),
        )

    async def add_nft(
        self,
        owner_id: int,
        *,
        gift_id: Optional[str],
        slug: Optional[str],
        title: str,
        num: Optional[int],
        msg_id: Optional[int],
        from_user_id: Optional[int],
        is_unique: bool,
    ) -> Optional[int]:
        if msg_id is not None:
            existing = await self.fetchone("SELECT id FROM inventory WHERE msg_id = ?", (msg_id,))
            if existing:
                return None
        cur = await self.execute(
            """
            INSERT INTO inventory
                (owner_id, gift_id, slug, title, num, msg_id, from_user_id, status, is_unique, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_id,
                gift_id,
                slug,
                title,
                num,
                msg_id,
                from_user_id,
                NFT_AVAILABLE,
                int(is_unique),
                now(),
            ),
        )
        return cur.lastrowid

    async def get_nft(self, nft_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM inventory WHERE id = ?", (nft_id,))

    async def nfts_of(self, owner_id: int, status: Optional[str] = None) -> list[aiosqlite.Row]:
        if status:
            return await self.fetchall(
                "SELECT * FROM inventory WHERE owner_id = ? AND status = ? ORDER BY id DESC",
                (owner_id, status),
            )
        return await self.fetchall(
            "SELECT * FROM inventory WHERE owner_id = ? ORDER BY id DESC",
            (owner_id,),
        )

    async def set_nft_status(
        self,
        nft_id: int,
        status: str,
        *,
        deal_id=...,
        owner_id=...,
    ) -> None:
        nft = await self.get_nft(nft_id)
        if nft is None:
            return
        await self.execute(
            """
            UPDATE inventory SET status = ?, deal_id = ?, owner_id = ?
            WHERE id = ?
            """,
            (
                status,
                nft["deal_id"] if deal_id is ... else deal_id,
                nft["owner_id"] if owner_id is ... else owner_id,
                nft_id,
            ),
        )

    async def create_deposit(self, user_id: int, amount: float, comment: str) -> int:
        cur = await self.execute(
            """
            INSERT INTO deposits (user_id, amount, comment, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, round(amount, 2), comment, WALLET_PENDING, now()),
        )
        return cur.lastrowid

    async def deposit_by_comment(self, comment: str) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM deposits WHERE comment = ?", (comment,))

    async def get_deposit(self, deposit_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM deposits WHERE id = ?", (deposit_id,))

    async def pending_deposits(self) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM deposits WHERE status = ? ORDER BY id DESC",
            (WALLET_PENDING,),
        )

    async def finish_deposit(self, deposit_id: int, status: str, tx_hash: Optional[str] = None) -> None:
        await self.execute(
            "UPDATE deposits SET status = ?, tx_hash = COALESCE(?, tx_hash) WHERE id = ?",
            (status, tx_hash, deposit_id),
        )

    async def create_withdraw(self, user_id: int, amount: float, method: str, details: str) -> int:
        cur = await self.execute(
            """
            INSERT INTO withdrawals (user_id, amount, method, details, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, round(amount, 2), method, details, WALLET_PENDING, now()),
        )
        return cur.lastrowid

    async def get_withdraw(self, withdraw_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM withdrawals WHERE id = ?", (withdraw_id,))

    async def pending_withdraws(self) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM withdrawals WHERE status = ? ORDER BY id DESC",
            (WALLET_PENDING,),
        )

    async def finish_withdraw(self, withdraw_id: int, status: str) -> None:
        await self.execute("UPDATE withdrawals SET status = ? WHERE id = ?", (status, withdraw_id))
