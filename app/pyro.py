from __future__ import annotations

import asyncio
import sys
from collections.abc import Coroutine
from typing import Any


def ensure_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        pass
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


ensure_loop()

try:
    from pyrogram import Client
    from pyrogram.handlers import RawUpdateHandler
    from pyrogram.raw import functions, types
except RuntimeError as exc:
    raise SystemExit(
        "Pyrogram не стартует: нет event loop (типично Python 3.12+ и пакет pyrogram).\n"
        "Нужен pyrofork:\n"
        "  pip uninstall -y pyrogram\n"
        "  pip install -U \"pyrofork>=2.3.45\"\n"
        "Дальше: python scripts/login_bank.py --user"
    ) from exc


def ensure_pyrofork() -> None:
    import pyrogram

    name = str(getattr(pyrogram, "__fork_name__", "") or "")
    if name.lower() == "pyrofork":
        return
    ver = getattr(pyrogram, "__version__", "?")
    extra = ""
    if sys.version_info >= (3, 12):
        extra = "\nНа Python 3.12+ обычный pyrogram падает при импорте."
    raise SystemExit(
        f"Установлен pyrogram {ver}, боту нужен pyrofork (NFT и Stars).{extra}\n\n"
        "  pip uninstall -y pyrogram\n"
        "  pip install -U \"pyrofork>=2.3.45\"\n"
        "  python scripts/login_bank.py --user"
    )


ensure_pyrofork()


def run(coro: Coroutine[Any, Any, Any]) -> Any:
    return ensure_loop().run_until_complete(coro)
