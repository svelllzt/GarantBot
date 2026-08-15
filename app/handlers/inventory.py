from aiogram import F, Router
from aiogram.types import Message

from app.i18n import t
from app.storage import Storage
from app.util import nft_title

router = Router()

INV = {t("ru", "btn_inventory"), t("en", "btn_inventory")}


@router.message(F.text.in_(INV))
async def inventory(message: Message, db: Storage, lang: str, bank):
    items = await db.nfts_of(message.from_user.id)
    header = t(lang, "inv_how", bank=bank.mention)
    if not items:
        await message.answer(f"{header}\n\n{t(lang, 'inv_empty')}")
        return
    lines = [header, ""]
    for item in items:
        status = t(lang, f"inv_status_{item['status']}")
        lines.append(t(lang, "inv_item", title=nft_title(item), status=status, id=item["id"]))
        lines.append("")
    await message.answer("\n".join(lines).strip())
