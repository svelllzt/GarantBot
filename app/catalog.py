from __future__ import annotations

from app.storage import KIND_GOODS

CATS = (
    "nft",
    "acc_rbx",
    "acc_stm",
    "acc_epic",
    "acc_dsc",
    "acc_tg",
    "acc_soc",
    "acc_game",
    "goods",
    "other",
)

_LABEL = {
    "nft": {"ru": "🎁 NFT-подарок Telegram", "en": "🎁 Telegram NFT gift"},
    "acc_rbx": {"ru": "🎮 Аккаунт Roblox", "en": "🎮 Roblox account"},
    "acc_stm": {"ru": "🎯 Аккаунт Steam", "en": "🎯 Steam account"},
    "acc_epic": {"ru": "🟣 Аккаунт Epic Games", "en": "🟣 Epic Games account"},
    "acc_dsc": {"ru": "💬 Аккаунт Discord", "en": "💬 Discord account"},
    "acc_tg": {"ru": "✈️ Аккаунт Telegram", "en": "✈️ Telegram account"},
    "acc_soc": {"ru": "📱 Соцсеть / почта", "en": "📱 Social / email account"},
    "acc_game": {"ru": "🕹️ Игровой аккаунт", "en": "🕹️ Game account"},
    "goods": {"ru": "📦 Товар / услуга", "en": "📦 Goods / service"},
    "other": {"ru": "✨ Другое", "en": "✨ Other"},
}

_MANUAL = {
    "nft": {
        "ru": (
            "1. Сумма сделки замораживается на балансе гаранта. Вывод этих монет недоступен.\n"
            "2. После заморозки бот отправляет NFT вам. Дождитесь подарка в Telegram.\n"
            "3. Проверьте уникальный подарок: название, номер, что он у вас.\n"
            "4. Не подтверждайте получение, пока NFT не появился и вы его не проверили.\n"
            "5. Если подарок не пришёл или это не тот — откройте спор. После «Товар получен» откатить нельзя."
        ),
        "en": (
            "1. The deal amount is frozen in escrow. Frozen coins cannot be withdrawn.\n"
            "2. After the freeze the bot sends the NFT to you. Wait until it appears in Telegram.\n"
            "3. Check the unique gift: title, number, that it is yours.\n"
            "4. Do not confirm until the gift is in your account and you have verified it.\n"
            "5. If it never arrives or it is the wrong gift — open a dispute. After confirmation there is no refund."
        ),
    },
    "acc_rbx": {
        "ru": (
            "Чтобы аккаунт не вернули через recovery:\n\n"
            "1. Войдите с нового устройства или инкогнито. Не светите свой основной аккаунт.\n"
            "2. Сразу смените пароль. Старый никому не отправляйте в чат сделки.\n"
            "3. Смените email на свой и подтвердите ящик. Старую почту отвяжите.\n"
            "4. Снимите PIN / Parental PIN, если висит.\n"
            "5. Отключите старый 2FA и включите свой Authenticator.\n"
            "6. Проверьте Billing, подписки, Google / Microsoft — отвяжите.\n"
            "7. Выйдите со всех сессий, затем зайдите только вы.\n"
            "8. Не подтверждайте сделку, пока почта, пароль и 2FA полностью ваши.\n"
            "9. Если продавец тянет с отвязкой — спор, не «Товар получен»."
        ),
        "en": (
            "To stop the seller recovering the account:\n\n"
            "1. Log in from a fresh browser or device.\n"
            "2. Change the password immediately. Never paste the old one in the deal chat.\n"
            "3. Change the email to yours and verify it. Unlink the old mailbox.\n"
            "4. Remove PIN / Parental PIN if it is set.\n"
            "5. Replace 2FA with your own authenticator.\n"
            "6. Unlink Google / Microsoft and check billing.\n"
            "7. Sign out of all sessions, then log in only from your side.\n"
            "8. Do not confirm until email, password and 2FA are yours.\n"
            "9. If the seller stalls on unlinking — open a dispute."
        ),
    },
    "acc_stm": {
        "ru": (
            "1. Смените пароль и почту аккаунта. Подтвердите новую почту.\n"
            "2. Снимите старый Guard, привяжите свой Steam Guard.\n"
            "3. Удалите резервные коды Guard у продавца — сгенерируйте новые себе.\n"
            "4. Проверьте кошелёк, карты, семейный просмотр, limited-статус.\n"
            "5. Выйдите из всех сессий. Не подтверждайте, пока Guard только на вашем телефоне.\n"
            "6. VAC / trade ban смотрите до подтверждения. После него возврата не будет."
        ),
        "en": (
            "1. Change password and account email, then verify the new mailbox.\n"
            "2. Remove the old Steam Guard and attach yours.\n"
            "3. Regenerate Guard backup codes.\n"
            "4. Check wallet, cards, family view, limited status.\n"
            "5. Sign out everywhere. Confirm only when Guard is on your phone only."
        ),
    },
    "acc_epic": {
        "ru": (
            "1. Смените пароль и email, подтвердите ящик.\n"
            "2. Отвяжите PSN / Xbox / Nintendo / Facebook / Google, привяжите свои.\n"
            "3. Включите свой 2FA, старый выключите.\n"
            "4. Проверьте возвраты Fortnite и привязанные карты.\n"
            "5. Не подтверждайте, пока все внешние входы не ваши."
        ),
        "en": (
            "1. Change password and email.\n"
            "2. Unlink PSN / Xbox / Nintendo / social logins, then add yours.\n"
            "3. Replace 2FA.\n"
            "4. Confirm only when every linked login is yours."
        ),
    },
    "acc_dsc": {
        "ru": (
            "1. Смените пароль и email, подтвердите почту.\n"
            "2. Отключите старый 2FA, включите свой. Сохраните свои backup-коды.\n"
            "3. Сбросьте авторизованные приложения и сессии.\n"
            "4. Нитро и платежи: уберите карты продавца.\n"
            "5. Не подтверждайте, пока 2FA и почта только ваши."
        ),
        "en": (
            "1. Change password and email.\n"
            "2. Replace 2FA and keep your own backup codes.\n"
            "3. Revoke sessions and authorized apps.\n"
            "4. Remove the seller's payment methods.\n"
            "5. Confirm only when 2FA and email are yours."
        ),
    },
    "acc_tg": {
        "ru": (
            "1. Номер должен перейти вам: SIM / перенос номера, не общий доступ продавца.\n"
            "2. Сразу поставьте облачный пароль 2FA на свой.\n"
            "3. Отключите старые сессии: Privacy → Active sessions → Terminate others.\n"
            "4. Смените username. Проверьте почту для входа.\n"
            "5. Пока облачный пароль знает продавец — он заберёт аккаунт. Не подтверждайте раньше."
        ),
        "en": (
            "1. You must control the phone number, not a shared login.\n"
            "2. Set your own two-step cloud password immediately.\n"
            "3. Terminate every other session.\n"
            "4. Change the username. Confirm only when the seller cannot sign back in."
        ),
    },
    "acc_soc": {
        "ru": (
            "1. Смените пароль. Отвяжите старый телефон и почту, привяжите свои.\n"
            "2. Выключите старый 2FA, включите свой.\n"
            "3. Сбросьте сессии, приложения, резервные входы (Google / Apple / VK).\n"
            "4. Проверьте восстановление: контрольные вопросы, доверенные контакты.\n"
            "5. Не подтверждайте, пока вход возможен только с ваших данных."
        ),
        "en": (
            "1. Change the password. Replace phone and recovery email.\n"
            "2. Replace 2FA.\n"
            "3. Revoke sessions and third-party logins.\n"
            "4. Confirm only when recovery options are yours."
        ),
    },
    "acc_game": {
        "ru": (
            "1. Смените пароль, почту, телефон, секретный вопрос.\n"
            "2. Отвяжите старый 2FA / Guard / Authenticator, поставьте свой.\n"
            "3. Проверьте привязки магазинов (PlayStation, Xbox, Google Play).\n"
            "4. Выйдите со всех устройств. Не подтверждайте, пока продавец может зайти обратно.\n"
            "5. Баны и регион смотрите до подтверждения."
        ),
        "en": (
            "1. Change password, email, phone and security questions.\n"
            "2. Replace 2FA / authenticator.\n"
            "3. Unlink store accounts. Sign out everywhere.\n"
            "4. Confirm only when the seller cannot log in."
        ),
    },
    "goods": {
        "ru": (
            "1. Сумма заморожена у гаранта до кнопки «Товар получен». Вывести её нельзя.\n"
            "2. Способ передачи и проверку фиксируйте в условиях до старта.\n"
            "3. Не подтверждайте, пока товар у вас и вы его проверили.\n"
            "4. Если продавец пропал или товар не тот — спор.\n"
            "5. После подтверждения монеты уходят продавцу. Комиссию доплачивает покупатель. Откатить нельзя."
        ),
        "en": (
            "1. Funds stay frozen in escrow until you tap «Goods received». They cannot be withdrawn.\n"
            "2. Write delivery terms before the deal starts.\n"
            "3. Do not confirm until you have checked the item.\n"
            "4. If something is wrong, open a dispute.\n"
            "5. After confirmation the seller is paid the full price. The buyer pays the fee on top. This cannot be undone."
        ),
    },
    "other": {
        "ru": (
            "1. Оплата через баланс бота. Гарант держит сумму замороженной до подтверждения.\n"
            "2. Опишите, что передаёте, и как проверите факт передачи.\n"
            "3. Не подтверждайте до проверки. Сомнения — спор.\n"
            "4. Комиссию доплачивает покупатель при закрытии."
        ),
        "en": (
            "1. Pay via the bot balance. Escrow freezes funds until confirmation.\n"
            "2. Write what is transferred and how you will verify it.\n"
            "3. Do not confirm early. Use a dispute if needed.\n"
            "4. The fee is paid by the buyer on close."
        ),
    },
}

_WRAP = {
    "ru": (
        "┏━━━━━━━━━━━━━━━━━━━━┓\n"
        "📌 <b>Памятка покупателя</b>\n"
        "📂 {cat}\n"
        "┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "{body}\n\n"
        "┏━━━━━━━━━━━━━━━━━━━━┓\n"
        "🔒 Сумма сделки заморожена на гаранте.\n"
        "Не подтверждайте, пока всё проверили.\n"
        "Спор — если товар не тот или продавец пропал.\n"
        "┗━━━━━━━━━━━━━━━━━━━━┛"
    ),
    "en": (
        "┏━━━━━━━━━━━━━━━━━━━━┓\n"
        "📌 <b>Buyer memo</b>\n"
        "📂 {cat}\n"
        "┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "{body}\n\n"
        "┏━━━━━━━━━━━━━━━━━━━━┓\n"
        "🔒 The deal amount is frozen in escrow.\n"
        "Do not confirm until you have checked everything.\n"
        "Open a dispute if the item is wrong or the seller vanishes.\n"
        "┗━━━━━━━━━━━━━━━━━━━━┛"
    ),
}


def known(category: str | None) -> bool:
    return (category or "") in _LABEL


def normalize(category: str | None) -> str:
    if category in _LABEL:
        return category
    return "goods"


def label(category: str | None, lang: str) -> str:
    row = _LABEL.get(normalize(category))
    return row.get(lang) or row["ru"]


def manual(category: str | None, lang: str) -> str:
    row = _MANUAL.get(normalize(category)) or _MANUAL["other"]
    body = row.get(lang) or row["ru"]
    wrap = _WRAP.get(lang) or _WRAP["ru"]
    return wrap.format(cat=label(category, lang), body=body)


def payment_kind(category: str | None) -> str:
    return KIND_GOODS


def needs_nft(category: str | None) -> bool:
    return normalize(category) == "nft"


def listing_allowed(category: str | None) -> bool:
    return True


GROUPS = (
    ("acc", ("acc_rbx", "acc_stm", "acc_epic", "acc_dsc", "acc_tg", "acc_soc", "acc_game")),
    ("nft", ("nft",)),
    ("goods", ("goods",)),
    ("other", ("other",)),
)

_GROUP_LABEL = {
    "acc": {"ru": "🎮 Аккаунты", "en": "🎮 Accounts"},
    "nft": {"ru": "🎁 NFT-подарки", "en": "🎁 NFT gifts"},
    "goods": {"ru": "📦 Товар / услуга", "en": "📦 Goods / service"},
    "other": {"ru": "✨ Другое", "en": "✨ Other"},
}


def group_label(key: str, lang: str) -> str:
    row = _GROUP_LABEL.get(key) or _GROUP_LABEL["other"]
    return row.get(lang) or row["ru"]


def group_cats(key: str) -> tuple[str, ...]:
    for name, cats in GROUPS:
        if name == key:
            return cats
    return ()


def is_group(key: str | None) -> bool:
    return any(name == key for name, _ in GROUPS)
