import asyncio
import sys
from pathlib import Path

from pyrogram import Client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    if not settings.bank_api_id or not settings.bank_api_hash:
        raise SystemExit("Укажите api_id и api_hash в config.ini секция [bank] (my.telegram.org)")
    workdir = ROOT / "data"
    workdir.mkdir(parents=True, exist_ok=True)
    async with Client(
        name="bank_login",
        api_id=settings.bank_api_id,
        api_hash=settings.bank_api_hash,
        workdir=str(workdir),
    ) as client:
        me = await client.get_me()
        session = await client.export_session_string()
    leftover = workdir / "bank_login.session"
    if leftover.exists():
        leftover.unlink()
    journal = workdir / "bank_login.session-journal"
    if journal.exists():
        journal.unlink()
    settings.patch("bank_session", session)
    if me.username:
        settings.patch("bank_username", me.username)
    print(f"logged in as @{me.username or '-'} id={me.id}")
    print(f"patched {settings.path} [bank] session / username")


if __name__ == "__main__":
    asyncio.run(main())
