import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings
from app.handlers import admin, deals, inventory, profile, start
from app.middlewares import ContextMiddleware
from app.services.bank import BankAccount
from app.storage import Storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("garant")


async def main() -> None:
    settings = get_settings()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)

    db = Storage(settings.db_path)
    await db.connect()

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    bank = BankAccount(settings, db, bot)

    mw = ContextMiddleware(db, settings, bank)
    dp.update.middleware(mw)

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(deals.router)
    dp.include_router(inventory.router)
    dp.include_router(admin.router)

    try:
        await bank.start()
        log.info("polling")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bank.stop()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
