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
        raise SystemExit("Set BANK_API_ID and BANK_API_HASH in .env")
    async with Client(
        name="bank_login",
        api_id=settings.bank_api_id,
        api_hash=settings.bank_api_hash,
        workdir="data",
    ) as client:
        me = await client.get_me()
        print(f"logged in as @{me.username} id={me.id}")
        print("BANK_SESSION=")
        print(await client.export_session_string())


if __name__ == "__main__":
    asyncio.run(main())
