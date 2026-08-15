from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.buttons import Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import NavCB
from app.storage import Storage
from app.util import nft_title, paint

router = Router()


@router.callback_query(NavCB.filter(F.a == "inv"))
async def inventory(call: CallbackQuery, db: Storage, lang: str, bank, theme: Theme, settings: Settings):
    items = await db.nfts_of(call.from_user.id)
    header = t(lang, "inv_how", bank=bank.mention)
    if not items:
        text = f"{header}\n\n{t(lang, 'inv_empty')}"
    else:
        lines = [header, ""]
        for item in items:
            status = t(lang, f"inv_status_{item['status']}")
            lines.append(t(lang, "inv_item", title=nft_title(item), status=status, id=item["id"]))
            lines.append("")
        text = "\n".join(lines).strip()
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    await paint(call, text, kb.as_markup(), screen="inventory", settings=settings)
