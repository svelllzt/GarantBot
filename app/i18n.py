from typing import Any

RU = {
    "choose_lang": "Выберите язык / Choose language",
    "welcome": "Добро пожаловать, {name}.\nГарант удерживает оплату до подтверждения сделки.",
    "banned": "Аккаунт заблокирован.",
    "need_username": "Укажите username в настройках Telegram, без него сделки недоступны.",
    "menu": "Главное меню",
    "btn_profile": "Профиль",
    "btn_deal": "Начать сделку",
    "btn_faq": "F.A.Q",
    "btn_support": "Поддержка",
    "btn_inventory": "Инвентарь",
    "btn_history": "История",
    "btn_about": "О сервисе",
    "btn_menu": "Меню",
    "lang_ru": "Русский",
    "lang_en": "English",
    "btn_cancel": "Отмена",
    "btn_back": "Назад",
    "btn_yes": "Да",
    "btn_no": "Нет",
    "cancelled": "Отменено.",
    "error": "Не получилось. Попробуйте ещё раз.",
    "profile": (
        "<b>Профиль</b>\n\n"
        "ID: <code>{id}</code>\n"
        "Ник: {nick}\n"
        "Username: @{username}\n"
        "Сделок: {deals}\n"
        "Баланс: <b>{balance} {currency}</b>\n\n"
        "Карта: {card}\n"
        "Телефон: {phone}\n"
        "Банк: {bank}\n"
        "TON: {ton}"
    ),
    "not_set": "не указан",
    "btn_req": "Реквизиты",
    "req_menu": "Реквизиты для вывода. Их видите только вы и администратор.",
    "req_card": "Карта",
    "req_phone": "Телефон и банк",
    "req_ton": "TON-адрес",
    "req_bank_short": "Банк",
    "req_ask_card": "Номер карты, только цифры.",
    "req_ask_phone": "Номер телефона, например +79991234567.",
    "req_ask_bank": "Название банка.",
    "req_ask_ton": "TON-адрес (UQ… / EQ…).",
    "req_saved": "Реквизиты сохранены.",
    "req_bad": "Неверный формат.",
    "lang_changed": "Язык обновлён.",
    "deposit": "Пополнение",
    "withdraw": "Вывод",
    "change_lang": "Язык",
    "deposit_ask": "Сумма пополнения в {currency}. Минимум {min}.",
    "deposit_created": (
        "Заявка #{id}\n"
        "Сумма: <b>{amount} {currency}</b>\n"
        "Комментарий: <code>{comment}</code>\n\n"
        "{extra}\n"
        "После перевода нажмите «Проверить» или дождитесь подтверждения администратора."
    ),
    "deposit_ton": "Переведите на TON-адрес:\n<code>{address}</code>\nВ комментарии укажите код выше.",
    "deposit_manual": "Перевод подтверждает администратор. Напишите @{support}, если платёж уже ушёл.",
    "deposit_check": "Проверить",
    "deposit_wait": "Платёж ещё не найден.",
    "deposit_ok": "Баланс пополнен на {amount} {currency}.",
    "withdraw_ask": "Сумма вывода в {currency}. Минимум {min}. Комиссия сервиса на вывод не берётся.",
    "withdraw_method": "Куда вывести?",
    "withdraw_no_req": "Сначала заполните реквизиты в профиле.",
    "withdraw_ok": "Заявка на вывод #{id}: {amount} {currency} на {details}. Администратор обработает её вручную.",
    "withdraw_low": "Недостаточно средств.",
    "min_amount": "Минимум {min} {currency}.",
    "about": (
        "Гарант для безопасных сделок: аккаунты, NFT-подарки, товар, TON.\n\n"
        "Объявления можно выложить в канал. Покупатель пополняет баланс, "
        "открывает сделку и получает памятку по категории (например, как "
        "перепривязать Roblox, чтобы аккаунт не вернули).\n\n"
        "Обычная сделка: оплата с баланса бота, деньги у гаранта до подтверждения.\n"
        "TON → рубли: TON на кошелёк V4, рубли продавцу, потом автовыплата TON.\n\n"
        "Комиссия: {commission}% с суммы сделки, удерживается с продавца.\n"
        "Поддержка: @{support}\n"
        "{chat}"
    ),
    "deal_role": "Кем вы будете в сделке?",
    "deal_buyer": "Покупатель",
    "deal_seller": "Продавец",
    "deal_kind": "Тип сделки?",
    "deal_kind_goods": "Товар / NFT",
    "deal_kind_ton": "TON → рубли",
    "deal_kind_label_goods": "товар / NFT",
    "deal_kind_label_ton": "TON → рубли",
    "deal_ask_user": "Username второй стороны, без @.",
    "deal_self": "С самим собой сделку открыть нельзя.",
    "deal_missing": "Пользователь не запускал бота.",
    "deal_busy_you": "У вас уже есть активная сделка #{id}.",
    "deal_busy_them": "У этого пользователя уже есть активная сделка.",
    "deal_preview": (
        "Контрагент:\n"
        "ID <code>{id}</code>\n"
        "Ник: {nick}\n"
        "@{username}\n"
        "Сделок: {deals}\n"
        "Роль: {role}\n"
        "Тип: {kind}"
    ),
    "deal_send": "Отправить предложение",
    "deal_reviews": "Отзывы",
    "deal_sent": "Предложение отправлено. Ждём ответа.",
    "deal_offer_in": (
        "Предложение сделки #{id}\n"
        "От @{username} (ID <code>{uid}</code>)\n"
        "Сделок у него: {deals}\n"
        "Вы: {role}\n"
        "Тип: {kind}"
    ),
    "deal_accept": "Принять",
    "deal_decline": "Отклонить",
    "deal_declined": "Предложение отклонено.",
    "deal_declined_peer": "Вторая сторона отклонила предложение.",
    "deal_opened": (
        "Сделка #{id}\n"
        "Категория: {cat}\n"
        "{title}\n"
        "Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "Сумма: {amount}\n"
        "NFT: {nft}\n"
        "Условия: {desc}\n"
        "Статус: {status}"
    ),
    "deal_opened_ton": (
        "Сделка #{id} · TON → рубли\n"
        "Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "TON: <b>{ton}</b>\n"
        "Рубли: <b>{rub} ₽</b>\n"
        "Адрес покупателя: <code>{buyer_ton}</code>\n"
        "Эскроу V4: <code>{escrow}</code>\n"
        "Комментарий: <code>{comment}</code>\n"
        "Получено TON: {received}\n"
        "Реквизиты продавца:\n{req}\n"
        "Условия: {desc}\n"
        "Выплата: <code>{payout}</code>\n"
        "Статус: {status}"
    ),
    "deal_status_pending": "ожидает принятия",
    "deal_status_open": "открыта",
    "deal_status_wait_ton": "ждёт TON на эскроу",
    "deal_status_funded": "TON на гаранте, ждут рубли",
    "deal_status_rub_sent": "рубли отправлены, ждут подтверждения",
    "deal_status_paid": "оплачена",
    "deal_status_dispute": "спор",
    "deal_status_review": "завершена, отзыв",
    "deal_status_closed": "закрыта",
    "deal_status_cancelled": "отменена",
    "deal_status_listed": "в канале, ждёт покупателя",
    "deal_set_price": "Указать сумму",
    "deal_set_nft": "Прикрепить NFT",
    "deal_set_desc": "Условия",
    "deal_set_ton": "Сумма TON",
    "deal_set_rub": "Сумма в рублях",
    "deal_set_buy_ton": "Мой TON-адрес",
    "deal_check_ton": "Проверить TON",
    "deal_rub_paid": "Я отправил рубли",
    "deal_rub_ok": "Рубли получены",
    "deal_pay": "Оплатить",
    "deal_confirm": "Товар получен",
    "deal_dispute": "Спор",
    "deal_cancel": "Отменить",
    "deal_ask_price": "Сумма сделки в {currency}.",
    "deal_price_set": "Сумма установлена: {amount} {currency}.",
    "deal_price_locked": "Сумму уже нельзя менять.",
    "deal_ask_desc": "Кратко опишите товар и условия передачи.",
    "deal_desc_set": "Условия сохранены.",
    "deal_nft_pick": "Выберите NFT из инвентаря. Он будет заморожен до конца сделки.",
    "deal_nft_empty": "В инвентаре нет свободных NFT.",
    "deal_nft_set": "NFT прикреплён: {title}.",
    "deal_nft_none": "не прикреплён",
    "deal_pay_no_amount": "Продавец ещё не указал сумму.",
    "deal_pay_low": "Недостаточно средств. Нужно {need} {currency}, на балансе {have}.",
    "deal_paid": "Оплата прошла. Продавец передаёт товар.",
    "deal_paid_seller": "Покупатель оплатил сделку #{id}. Передайте товар.",
    "deal_nft_sent": "NFT отправлен покупателю через банковский аккаунт.",
    "deal_nft_fail": "Не удалось отправить NFT. Откройте спор, администратор разберёт вручную.",
    "deal_confirm_ask": "Подтверждаете получение и валидность товара?",
    "deal_done_buyer": "Сделка закрыта. Можете оставить отзыв продавцу.",
    "deal_done_seller": "Сделка закрыта. На баланс зачислено {amount} {currency} (комиссия {commission}%).",
    "deal_review_ask": "Напишите отзыв или нажмите «Пропустить».",
    "deal_review_skip": "Пропустить",
    "deal_review_saved": "Отзыв сохранён.",
    "deal_review_empty": "Отзывов нет.",
    "deal_cancel_ask": "Отменить сделку?",
    "deal_cancel_sent": "Запрос на отмену отправлен второй стороне.",
    "deal_cancel_ok": "Сделка отменена.",
    "deal_cancel_denied": "В этой стадии отмена только через спор.",
    "deal_agree": "Согласиться",
    "deal_refuse": "Отказаться",
    "deal_dispute_ok": "Спор открыт. Администратор получил уведомление.",
    "deal_dispute_admin": (
        "Спор по сделке #{id}\n"
        "Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "Сумма: {amount} {currency}\n"
        "NFT: {nft}"
    ),
    "no_reviews": "Отзывов пока нет.",
    "history_empty": "Пусто.",
    "history_role": "Показать сделки, где вы…",
    "history_line": "#{id} · {role} · {amount} · {status}\nКонтрагент: @{peer}",
    "inv_empty": "Инвентарь пуст.",
    "inv_how": (
        "Отправьте NFT-подарок на аккаунт банка: {bank}\n"
        "Подарок появится здесь автоматически и привяжется к вашему Telegram ID."
    ),
    "inv_item": "{title}\nСтатус: {status}\nID: {id}",
    "inv_status_available": "доступен",
    "inv_status_locked": "в сделке",
    "inv_status_transferred": "передан",
    "inv_new": "В инвентарь добавлен подарок: {title}",
    "admin_only": "Нет доступа.",
    "admin_menu": "Админка",
    "admin_stats": "Статистика",
    "admin_ban": "Бан",
    "admin_unban": "Разбан",
    "admin_balance": "Баланс",
    "admin_mail": "Рассылка",
    "admin_buttons": "Кнопки",
    "admin_btn_pick": "Выберите кнопку.",
    "admin_btn_card": (
        "<b>{title}</b>\n<code>{key}</code>\n\n"
        "RU: {ru}\nEN: {en}\n"
        "Цвет: {style}\nЭмодзи: {emoji}\n\n"
        "Цвет и премиум-эмодзи видны, если у владельца бота есть Telegram Premium "
        "или у бота куплен username на Fragment."
    ),
    "admin_btn_name": "Название",
    "admin_btn_color": "Цвет",
    "admin_btn_emoji": "Эмодзи",
    "admin_btn_reset": "Сбросить",
    "admin_btn_ask_ru": "Русское название кнопки.",
    "admin_btn_ask_en": "English label. «-» копирует русское.",
    "admin_btn_ask_emoji": "Пришлите премиум-эмодзи или numeric id. «-» снимает иконку.",
    "admin_btn_style_primary": "Синий",
    "admin_btn_style_success": "Зелёный",
    "admin_btn_style_danger": "Красный",
    "admin_btn_style_none": "Без цвета",
    "admin_btn_saved": "Кнопка обновлена.",
    "admin_btn_no_emoji": "не задан",
    "admin_disputes": "Споры",
    "admin_deposits": "Пополнения",
    "admin_withdraws": "Выводы",
    "admin_stats_text": "Пользователей: {users}\nЗакрытых сделок: {deals}\nОборот: {volume} {currency}",
    "admin_ask_id": "Telegram ID пользователя.",
    "admin_ask_balance": "Новый баланс в {currency}.",
    "admin_ask_mail": "Текст рассылки. HTML можно.",
    "admin_done": "Готово.",
    "admin_user_missing": "Пользователь не найден.",
    "admin_no_disputes": "Открытых споров нет.",
    "admin_buyer": "Покупатель прав",
    "admin_seller": "Продавец прав",
    "admin_verdict_buyer": "Вердикт: деньги возвращены покупателю.",
    "admin_verdict_seller": "Вердикт: деньги переведены продавцу.",
    "admin_empty_list": "Заявок нет.",
    "admin_dep_line": "#{id} · {amount} {currency} · {comment}\nID {user}",
    "admin_wd_line": "#{id} · {amount} {currency} · {method}\n{details}\nID {user}",
    "admin_confirm": "Подтвердить",
    "admin_reject": "Отклонить",
    "admin_dep_ok": "Пополнение подтверждено.",
    "admin_dep_no": "Пополнение отклонено.",
    "admin_wd_ok": "Вывод отмечен как выплаченный.",
    "admin_wd_no": "Вывод отклонён, сумма возвращена на баланс.",
    "mail_started": "Рассылка пошла.",
    "mail_done": "Рассылка закончена: {ok} доставлено, {fail} ошибок.",
    "active_deal_btn": "К сделке #{id}",
    "deal_ton_off": "Эскроу TON не настроен. Задайте address или mnemonic в config.ini [ton].",
    "deal_ton_no_req": "Продавцу TON нужны реквизиты: карта или телефон с банком.",
    "deal_ton_no_refund": "Продавцу TON нужен свой TON-адрес в профиле — на него вернут монеты при отмене.",
    "deal_ask_ton_amt": "Сколько TON продаёте? Минимум {min}.",
    "deal_ask_rub_amt": "Сколько рублей должен заплатить покупатель? Минимум {min} ₽.",
    "deal_ton_set": "Сумма TON: {amount}.",
    "deal_rub_set": "Сумма в рублях: {amount} ₽.",
    "deal_ask_buy_ton": "TON-адрес, куда отправить монеты после оплаты рублей (UQ… / EQ…).",
    "deal_buy_ton_set": "Адрес получателя сохранён.",
    "deal_ton_deposit": (
        "Продавец переводит <b>{amount} TON</b> на кошелёк V4 гаранта.\n"
        "Адрес:\n<code>{address}</code>\n"
        "Комментарий (обязательно):\n<code>{comment}</code>\n\n"
        "После перевода нажмите «Проверить TON»."
    ),
    "deal_ton_wait": "Перевод TON ещё не найден. Проверьте комментарий и сумму.",
    "deal_ton_funded": "TON на гаранте. Покупатель переводит рубли по реквизитам продавца.",
    "deal_ton_funded_buyer": (
        "TON уже на гаранте. Переведите <b>{rub} ₽</b> продавцу:\n{req}\n\n"
        "Когда отправите — нажмите «Я отправил рубли»."
    ),
    "deal_rub_ask": "Подтверждаете, что отправили рубли продавцу?",
    "deal_rub_marked": "Отметили оплату рублей. Ждём подтверждения продавца.",
    "deal_rub_marked_seller": (
        "Покупатель отметил перевод рублей по сделке #{id}.\n"
        "Если деньги пришли — подтвердите. TON уйдут на адрес покупателя автоматически."
    ),
    "deal_rub_confirm_ask": "Рубли пришли? После подтверждения TON уйдут покупателю.",
    "deal_ton_sent": "Сделка закрыта. TON отправлены на {address}.\nХеш: <code>{hash}</code>",
    "deal_ton_sent_buyer": "Продавец подтвердил рубли. TON отправлены на ваш адрес.\nХеш: <code>{hash}</code>",
    "deal_ton_send_fail": "Не удалось отправить TON с кошелька V4. Администратор получил уведомление.",
    "deal_ton_manual": "Автоотправка недоступна. Нужно вручную отправить {amount} TON на {address}.",
    "deal_ton_admin_fail": (
        "Не отправились TON по сделке #{id}\n"
        "Куда: <code>{address}</code>\n"
        "Сумма: {amount} TON\n"
        "{extra}"
    ),
    "btn_feed": "Витрина",
    "deal_mode": "Как открыть сделку?",
    "deal_private": "С человеком (username)",
    "deal_public": "Выложить в канал",
    "deal_channel": "Канал сделок",
    "deal_take": "Открыть сделку",
    "deal_manual_btn": "Памятка",
    "deal_ask_cat": "Категория сделки?",
    "deal_ask_group": "Что продаёте или покупаете?",
    "deal_ask_title": "Короткое название объявления, как в канале. Например: Roblox 1200 Robux, почта отвязана.",
    "deal_list_ok": "Объявление #{id} в канале. Когда покупатель откроет сделку, обоим придёт памятка.",
    "deal_list_no_channel": "Канал не задан в config.ini [bot] deals_channel. Объявление всё равно в витрине бота.",
    "deal_list_ton": "TON → рубли только напрямую с человеком, не в канал.",
    "deal_listed_taken": "Объявление уже сняли или закрыли.",
    "deal_feed_empty": "Открытых объявлений нет.",
    "deal_feed_line": "#{id} · {cat} · {amount}\n{title}\n@{seller}",
    "deal_need_deposit": "Сначала пополните баланс в профиле, затем откройте сделку.",
    "deal_need_price": "У объявления должна быть сумма больше нуля.",
    "nft_need_gift": "Продавец ещё не прикрепил NFT к объявлению.",
    "channel_listing": (
        "<b>Сделка #{id}</b> · {cat}\n"
        "{title}\n\n"
        "Продавец: @{seller}\n"
        "Цена: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Оплата через бота-гаранта. Нажмите «Открыть в боте»."
    ),
    "channel_open": "Открыть в боте",
    "channel_taken": "🔒 Сделку открыли, объявление снято.",
    "channel_closed": "🔒 Объявление снято.",
    "deal_taken_seller": "Покупатель @{username} открыл объявление #{id}. Смотрите памятку и ждите оплату.",
    "faq_title": "F.A.Q",
    "faq_empty": "Пока нет статей. Администратор добавит их в админке.",
    "faq_missing": "Статья удалена.",
    "support_text": "Напишите в поддержку: @{support}\n{chat}",
    "deal_dispute_ask": "Опишите проблему одним сообщением. Можно сразу приложить фото.",
    "deal_dispute_evidence_ask": "Пришлите текст или фото. Когда закончите — нажмите «Готово».",
    "deal_dispute_thread": "Переписка",
    "deal_dispute_evidence": "Доказательства",
    "deal_dispute_done": "Готово",
    "deal_dispute_empty": "Сообщений пока нет.",
    "deal_dispute_msg": "<b>{who}</b>\n{text}",
    "deal_dispute_photo": "📷 фото",
    "deal_dispute_peer": "По сделке #{id} открыт спор.\n{reason}",
    "deal_dispute_new": "Новое сообщение по спору #{id} от {who}:\n{text}",
    "deal_dispute_closed": "Спор по сделке #{id} закрыт.",
    "admin_faq": "F.A.Q",
    "admin_screens": "Картинки меню",
    "admin_bans": "Список банов",
    "admin_faq_add": "Добавить статью",
    "admin_faq_del": "Удалить",
    "admin_faq_photo": "Фото статьи",
    "admin_faq_empty": "Статей нет.",
    "admin_faq_ask_title_ru": "Заголовок статьи на русском.",
    "admin_faq_ask_title_en": "English title. «-» копирует русский.",
    "admin_faq_ask_body_ru": "Текст статьи на русском. HTML можно.",
    "admin_faq_ask_body_en": "English body. «-» копирует русский.",
    "admin_faq_ask_photo": "Пришлите фото для статьи или «-», чтобы без картинки.",
    "admin_faq_saved": "Статья сохранена.",
    "admin_faq_deleted": "Статья удалена.",
    "admin_screens_pick": "Экран, для которого поставить картинку. Дальше пришлите фото. «-» снимет картинку.",
    "admin_screen_ask": "Фото для экрана {key}. «-» удаляет.",
    "admin_screen_saved": "Картинка для {key} сохранена.",
    "admin_screen_cleared": "Картинка {key} снята.",
    "admin_bans_empty": "Заблокированных нет. Нажмите на человека в списке, чтобы разбанить.",
    "admin_bans_line": "{name}\nID <code>{id}</code>\n{reason}",
    "admin_ask_ban": "ID или @username. Потом причина бана.",
    "admin_ask_ban_reason": "Причина бана. «-» без причины.",
    "admin_banned": "Пользователь {id} заблокирован.",
    "admin_unbanned": "Пользователь {id} разблокирован.",
    "admin_ban_notice": "Вас заблокировали в боте.{reason}",
    "admin_reply": "Ответить в спор",
    "admin_ask_reply": "Сообщение в спор #{id}. Текст или фото.",
    "admin_ask_verdict": "Комментарий к вердикту. «-» без комментария.",
    "admin_stats_text": (
        "Пользователей: {users} (бан {banned})\n"
        "Сделок всего: {deals}\n"
        "Закрыто: {closed}\n"
        "Открытых споров: {disputes}\n"
        "Оборот закрытых: {volume} {currency}\n"
        "Сейчас в гаранте: {escrow} {currency}\n\n"
        "По статусам:\n{by_status}\n\n"
        "По категориям:\n{by_cat}\n\n"
        "Последние:\n{recent}"
    ),
    "admin_deal_line": "#{id} · {status} · {cat} · {amount}",
}

EN = {
    "choose_lang": "Choose language / Выберите язык",
    "welcome": "Welcome, {name}.\nThe escrow holds payment until the deal is confirmed.",
    "banned": "This account is banned.",
    "need_username": "Set a Telegram username first. Deals are unavailable without it.",
    "menu": "Main menu",
    "btn_profile": "Profile",
    "btn_deal": "Start a deal",
    "btn_faq": "F.A.Q",
    "btn_support": "Support",
    "btn_inventory": "Inventory",
    "btn_history": "History",
    "btn_about": "About",
    "btn_menu": "Menu",
    "lang_ru": "Русский",
    "lang_en": "English",
    "btn_cancel": "Cancel",
    "btn_back": "Back",
    "btn_yes": "Yes",
    "btn_no": "No",
    "cancelled": "Cancelled.",
    "error": "Something went wrong. Try again.",
    "profile": (
        "<b>Profile</b>\n\n"
        "ID: <code>{id}</code>\n"
        "Nick: {nick}\n"
        "Username: @{username}\n"
        "Deals: {deals}\n"
        "Balance: <b>{balance} {currency}</b>\n\n"
        "Card: {card}\n"
        "Phone: {phone}\n"
        "Bank: {bank}\n"
        "TON: {ton}"
    ),
    "not_set": "not set",
    "btn_req": "Payout details",
    "req_menu": "Payout details. Visible only to you and the admin.",
    "req_card": "Card",
    "req_phone": "Phone and bank",
    "req_ton": "TON address",
    "req_bank_short": "Bank",
    "req_ask_card": "Card number, digits only.",
    "req_ask_phone": "Phone number, e.g. +19995550100.",
    "req_ask_bank": "Bank name.",
    "req_ask_ton": "TON address (UQ… / EQ…).",
    "req_saved": "Details saved.",
    "req_bad": "Invalid format.",
    "lang_changed": "Language updated.",
    "deposit": "Deposit",
    "withdraw": "Withdraw",
    "change_lang": "Language",
    "deposit_ask": "Deposit amount in {currency}. Minimum {min}.",
    "deposit_created": (
        "Request #{id}\n"
        "Amount: <b>{amount} {currency}</b>\n"
        "Memo: <code>{comment}</code>\n\n"
        "{extra}\n"
        "After sending, tap Check or wait for an admin confirmation."
    ),
    "deposit_ton": "Send TON to:\n<code>{address}</code>\nUse the memo above as the comment.",
    "deposit_manual": "An admin confirms the transfer. Message @{support} if it is already sent.",
    "deposit_check": "Check",
    "deposit_wait": "Payment not found yet.",
    "deposit_ok": "Balance credited with {amount} {currency}.",
    "withdraw_ask": "Withdrawal amount in {currency}. Minimum {min}. No extra fee on payout.",
    "withdraw_method": "Where should we send it?",
    "withdraw_no_req": "Fill in payout details in your profile first.",
    "withdraw_ok": "Withdrawal #{id}: {amount} {currency} to {details}. An admin will process it.",
    "withdraw_low": "Insufficient balance.",
    "min_amount": "Minimum {min} {currency}.",
    "about": (
        "Escrow for peer-to-peer deals.\n\n"
        "Regular deal: the buyer funds the bot balance, the seller delivers goods or an NFT. "
        "Funds are released after confirmation.\n\n"
        "TON → RUB: the seller deposits TON into the escrow Wallet V4. The buyer pays rubles "
        "to the seller's payout details. After the seller confirms the rubles, the bot sends "
        "TON to the buyer's address automatically.\n\n"
        "Fee: {commission}% of the deal, taken from the seller.\n"
        "Support: @{support}\n"
        "{chat}"
    ),
    "deal_role": "Your role in this deal?",
    "deal_buyer": "Buyer",
    "deal_seller": "Seller",
    "deal_kind": "Deal type?",
    "deal_kind_goods": "Goods / NFT",
    "deal_kind_ton": "TON → RUB",
    "deal_kind_label_goods": "goods / NFT",
    "deal_kind_label_ton": "TON → RUB",
    "deal_ask_user": "Counterparty username, without @.",
    "deal_self": "You cannot open a deal with yourself.",
    "deal_missing": "This user has never started the bot.",
    "deal_busy_you": "You already have an active deal #{id}.",
    "deal_busy_them": "That user already has an active deal.",
    "deal_preview": (
        "Counterparty:\n"
        "ID <code>{id}</code>\n"
        "Nick: {nick}\n"
        "@{username}\n"
        "Deals: {deals}\n"
        "Your role: {role}\n"
        "Type: {kind}"
    ),
    "deal_send": "Send offer",
    "deal_reviews": "Reviews",
    "deal_sent": "Offer sent. Waiting for a reply.",
    "deal_offer_in": (
        "Deal offer #{id}\n"
        "From @{username} (ID <code>{uid}</code>)\n"
        "Their deals: {deals}\n"
        "You are: {role}\n"
        "Type: {kind}"
    ),
    "deal_accept": "Accept",
    "deal_decline": "Decline",
    "deal_declined": "Offer declined.",
    "deal_declined_peer": "The other party declined the offer.",
    "deal_opened": (
        "Deal #{id}\n"
        "Category: {cat}\n"
        "{title}\n"
        "Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "Seller: @{seller} (<code>{seller_id}</code>)\n"
        "Amount: {amount}\n"
        "NFT: {nft}\n"
        "Terms: {desc}\n"
        "Status: {status}"
    ),
    "deal_opened_ton": (
        "Deal #{id} · TON → RUB\n"
        "Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "Seller: @{seller} (<code>{seller_id}</code>)\n"
        "TON: <b>{ton}</b>\n"
        "Rubles: <b>{rub} ₽</b>\n"
        "Buyer address: <code>{buyer_ton}</code>\n"
        "Escrow V4: <code>{escrow}</code>\n"
        "Memo: <code>{comment}</code>\n"
        "TON received: {received}\n"
        "Seller payout details:\n{req}\n"
        "Terms: {desc}\n"
        "Payout: <code>{payout}</code>\n"
        "Status: {status}"
    ),
    "deal_status_pending": "waiting",
    "deal_status_open": "open",
    "deal_status_wait_ton": "waiting for TON escrow",
    "deal_status_funded": "TON locked, waiting for rubles",
    "deal_status_rub_sent": "rubles sent, waiting confirmation",
    "deal_status_paid": "paid",
    "deal_status_dispute": "dispute",
    "deal_status_review": "completed, review",
    "deal_status_closed": "closed",
    "deal_status_cancelled": "cancelled",
    "deal_status_listed": "listed, waiting for a buyer",
    "deal_set_price": "Set amount",
    "deal_set_nft": "Attach NFT",
    "deal_set_desc": "Terms",
    "deal_set_ton": "TON amount",
    "deal_set_rub": "Ruble amount",
    "deal_set_buy_ton": "My TON address",
    "deal_check_ton": "Check TON",
    "deal_rub_paid": "I sent the rubles",
    "deal_rub_ok": "Rubles received",
    "deal_pay": "Pay",
    "deal_confirm": "Item received",
    "deal_dispute": "Dispute",
    "deal_cancel": "Cancel",
    "deal_ask_price": "Deal amount in {currency}.",
    "deal_price_set": "Amount set: {amount} {currency}.",
    "deal_price_locked": "The amount can no longer be changed.",
    "deal_ask_desc": "Describe the item and how it will be delivered.",
    "deal_desc_set": "Terms saved.",
    "deal_nft_pick": "Pick an NFT from inventory. It will be locked until the deal ends.",
    "deal_nft_empty": "No free NFTs in inventory.",
    "deal_nft_set": "NFT attached: {title}.",
    "deal_nft_none": "not attached",
    "deal_pay_no_amount": "The seller has not set the amount yet.",
    "deal_pay_low": "Not enough funds. Need {need} {currency}, have {have}.",
    "deal_paid": "Payment received. The seller should deliver now.",
    "deal_paid_seller": "The buyer paid deal #{id}. Deliver the item.",
    "deal_nft_sent": "NFT sent to the buyer via the bank account.",
    "deal_nft_fail": "NFT transfer failed. Open a dispute so an admin can handle it.",
    "deal_confirm_ask": "Confirm that you received a valid item?",
    "deal_done_buyer": "Deal closed. You can leave a review for the seller.",
    "deal_done_seller": "Deal closed. Credited {amount} {currency} (fee {commission}%).",
    "deal_review_ask": "Write a review or tap Skip.",
    "deal_review_skip": "Skip",
    "deal_review_saved": "Review saved.",
    "deal_review_empty": "No reviews.",
    "deal_cancel_ask": "Cancel this deal?",
    "deal_cancel_sent": "Cancel request sent to the other party.",
    "deal_cancel_ok": "Deal cancelled.",
    "deal_cancel_denied": "At this stage cancellation goes through a dispute.",
    "deal_agree": "Agree",
    "deal_refuse": "Refuse",
    "deal_dispute_ok": "Dispute opened. An admin has been notified.",
    "deal_dispute_admin": (
        "Dispute on deal #{id}\n"
        "Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "Seller: @{seller} (<code>{seller_id}</code>)\n"
        "Amount: {amount} {currency}\n"
        "NFT: {nft}"
    ),
    "no_reviews": "No reviews yet.",
    "history_empty": "Nothing here.",
    "history_role": "Show deals where you were the…",
    "history_line": "#{id} · {role} · {amount} · {status}\nPeer: @{peer}",
    "inv_empty": "Inventory is empty.",
    "inv_how": (
        "Send an NFT gift to the bank account: {bank}\n"
        "It will show up here and bind to your Telegram ID."
    ),
    "inv_item": "{title}\nStatus: {status}\nID: {id}",
    "inv_status_available": "available",
    "inv_status_locked": "in a deal",
    "inv_status_transferred": "transferred",
    "inv_new": "Gift added to inventory: {title}",
    "admin_only": "No access.",
    "admin_menu": "Admin",
    "admin_stats": "Stats",
    "admin_ban": "Ban",
    "admin_unban": "Unban",
    "admin_balance": "Balance",
    "admin_mail": "Broadcast",
    "admin_buttons": "Buttons",
    "admin_btn_pick": "Pick a button.",
    "admin_btn_card": (
        "<b>{title}</b>\n<code>{key}</code>\n\n"
        "RU: {ru}\nEN: {en}\n"
        "Color: {style}\nEmoji: {emoji}\n\n"
        "Color and premium emoji show up if the bot owner has Telegram Premium "
        "or the bot bought a username on Fragment."
    ),
    "admin_btn_name": "Label",
    "admin_btn_color": "Color",
    "admin_btn_emoji": "Emoji",
    "admin_btn_reset": "Reset",
    "admin_btn_ask_ru": "Russian button label.",
    "admin_btn_ask_en": "English label. Send - to copy the Russian one.",
    "admin_btn_ask_emoji": "Send a premium emoji or its numeric id. - removes the icon.",
    "admin_btn_style_primary": "Blue",
    "admin_btn_style_success": "Green",
    "admin_btn_style_danger": "Red",
    "admin_btn_style_none": "No color",
    "admin_btn_saved": "Button updated.",
    "admin_btn_no_emoji": "not set",
    "admin_disputes": "Disputes",
    "admin_deposits": "Deposits",
    "admin_withdraws": "Withdrawals",
    "admin_stats_text": "Users: {users}\nClosed deals: {deals}\nVolume: {volume} {currency}",
    "admin_ask_id": "User Telegram ID.",
    "admin_ask_balance": "New balance in {currency}.",
    "admin_ask_mail": "Broadcast text. HTML is fine.",
    "admin_done": "Done.",
    "admin_user_missing": "User not found.",
    "admin_no_disputes": "No open disputes.",
    "admin_buyer": "Buyer wins",
    "admin_seller": "Seller wins",
    "admin_verdict_buyer": "Verdict: funds returned to the buyer.",
    "admin_verdict_seller": "Verdict: funds released to the seller.",
    "admin_empty_list": "No requests.",
    "admin_dep_line": "#{id} · {amount} {currency} · {comment}\nID {user}",
    "admin_wd_line": "#{id} · {amount} {currency} · {method}\n{details}\nID {user}",
    "admin_confirm": "Confirm",
    "admin_reject": "Reject",
    "admin_dep_ok": "Deposit confirmed.",
    "admin_dep_no": "Deposit rejected.",
    "admin_wd_ok": "Withdrawal marked as paid.",
    "admin_wd_no": "Withdrawal rejected, funds returned.",
    "mail_started": "Broadcast started.",
    "mail_done": "Broadcast finished: {ok} delivered, {fail} failed.",
    "active_deal_btn": "Open deal #{id}",
    "deal_ton_off": "TON escrow is not configured. Set address or mnemonic in config.ini [ton].",
    "deal_ton_no_req": "The TON seller needs payout details: a card or phone plus bank.",
    "deal_ton_no_refund": "The TON seller needs a TON address in the profile for refunds.",
    "deal_ask_ton_amt": "How much TON are you selling? Minimum {min}.",
    "deal_ask_rub_amt": "How many rubles should the buyer pay? Minimum {min} ₽.",
    "deal_ton_set": "TON amount: {amount}.",
    "deal_rub_set": "Ruble amount: {amount} ₽.",
    "deal_ask_buy_ton": "TON address that should receive coins after the ruble payment (UQ… / EQ…).",
    "deal_buy_ton_set": "Recipient address saved.",
    "deal_ton_deposit": (
        "The seller sends <b>{amount} TON</b> to the escrow Wallet V4.\n"
        "Address:\n<code>{address}</code>\n"
        "Memo (required):\n<code>{comment}</code>\n\n"
        "After sending, tap Check TON."
    ),
    "deal_ton_wait": "TON transfer not found yet. Check the memo and amount.",
    "deal_ton_funded": "TON is in escrow. The buyer should pay rubles using the seller details.",
    "deal_ton_funded_buyer": (
        "TON is already in escrow. Send <b>{rub} ₽</b> to the seller:\n{req}\n\n"
        "When done, tap I sent the rubles."
    ),
    "deal_rub_ask": "Confirm that you sent rubles to the seller?",
    "deal_rub_marked": "Ruble payment marked. Waiting for the seller to confirm.",
    "deal_rub_marked_seller": (
        "The buyer marked a ruble transfer for deal #{id}.\n"
        "If the money arrived, confirm. TON will be sent to the buyer automatically."
    ),
    "deal_rub_confirm_ask": "Did the rubles arrive? Confirming sends TON to the buyer.",
    "deal_ton_sent": "Deal closed. TON sent to {address}.\nHash: <code>{hash}</code>",
    "deal_ton_sent_buyer": "The seller confirmed the rubles. TON were sent to your address.\nHash: <code>{hash}</code>",
    "deal_ton_send_fail": "Could not send TON from the V4 wallet. An admin has been notified.",
    "deal_ton_manual": "Auto-send is unavailable. Send {amount} TON to {address} manually.",
    "deal_ton_admin_fail": (
        "TON payout failed for deal #{id}\n"
        "To: <code>{address}</code>\n"
        "Amount: {amount} TON\n"
        "{extra}"
    ),
    "btn_feed": "Listings",
    "deal_mode": "How do you want to open a deal?",
    "deal_private": "With a user (username)",
    "deal_public": "Post to the channel",
    "deal_channel": "Deals channel",
    "deal_take": "Open this deal",
    "deal_manual_btn": "Memo",
    "deal_ask_cat": "Deal category?",
    "deal_ask_group": "What are you selling or buying?",
    "deal_ask_title": "Short listing title for the channel. Example: Roblox 1200 Robux, email unlinked.",
    "deal_list_ok": "Listing #{id} is in the channel. When a buyer opens it, both of you get the memo.",
    "deal_list_no_channel": "No deals channel in config.ini [bot] deals_channel. The listing is still in the bot feed.",
    "deal_list_ton": "TON → RUB deals are direct only, not posted to the channel.",
    "deal_listed_taken": "This listing is already taken or closed.",
    "deal_feed_empty": "No open listings.",
    "deal_feed_line": "#{id} · {cat} · {amount}\n{title}\n@{seller}",
    "deal_need_deposit": "Top up your balance in the profile first, then open the deal.",
    "deal_need_price": "The listing must have a price greater than zero.",
    "nft_need_gift": "The seller has not attached an NFT to this listing yet.",
    "channel_listing": (
        "<b>Deal #{id}</b> · {cat}\n"
        "{title}\n\n"
        "Seller: @{seller}\n"
        "Price: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Pay through the escrow bot. Tap Open in bot."
    ),
    "channel_open": "Open in bot",
    "channel_taken": "🔒 This deal was taken.",
    "channel_closed": "🔒 Listing removed.",
    "deal_taken_seller": "Buyer @{username} opened listing #{id}. Read the memo and wait for payment.",
    "faq_title": "F.A.Q",
    "faq_empty": "No articles yet. An admin can add them in the admin panel.",
    "faq_missing": "This article was removed.",
    "support_text": "Contact support: @{support}\n{chat}",
    "deal_dispute_ask": "Describe the problem in one message. You can attach a photo.",
    "deal_dispute_evidence_ask": "Send text or a photo. Tap Done when you are finished.",
    "deal_dispute_thread": "Thread",
    "deal_dispute_evidence": "Evidence",
    "deal_dispute_done": "Done",
    "deal_dispute_empty": "No messages yet.",
    "deal_dispute_msg": "<b>{who}</b>\n{text}",
    "deal_dispute_photo": "📷 photo",
    "deal_dispute_peer": "A dispute was opened on deal #{id}.\n{reason}",
    "deal_dispute_new": "New dispute message on #{id} from {who}:\n{text}",
    "deal_dispute_closed": "The dispute on deal #{id} is closed.",
    "admin_faq": "F.A.Q",
    "admin_screens": "Menu photos",
    "admin_bans": "Ban list",
    "admin_faq_add": "Add article",
    "admin_faq_del": "Delete",
    "admin_faq_photo": "Article photo",
    "admin_faq_empty": "No articles.",
    "admin_faq_ask_title_ru": "Russian title.",
    "admin_faq_ask_title_en": "English title. “-” copies the Russian one.",
    "admin_faq_ask_body_ru": "Russian body. HTML is allowed.",
    "admin_faq_ask_body_en": "English body. “-” copies the Russian one.",
    "admin_faq_ask_photo": "Send a photo for the article, or “-” for none.",
    "admin_faq_saved": "Article saved.",
    "admin_faq_deleted": "Article deleted.",
    "admin_screens_pick": "Pick a screen, then send a photo. “-” removes it.",
    "admin_screen_ask": "Photo for screen {key}. “-” removes it.",
    "admin_screen_saved": "Photo for {key} saved.",
    "admin_screen_cleared": "Photo for {key} removed.",
    "admin_bans_empty": "Nobody is banned. Tap a user in the list to unban.",
    "admin_bans_line": "{name}\nID <code>{id}</code>\n{reason}",
    "admin_ask_ban": "ID or @username, then a ban reason.",
    "admin_ask_ban_reason": "Ban reason. “-” for none.",
    "admin_banned": "User {id} is banned.",
    "admin_unbanned": "User {id} is unbanned.",
    "admin_ban_notice": "You were banned from this bot.{reason}",
    "admin_reply": "Reply in dispute",
    "admin_ask_reply": "Message for dispute #{id}. Text or photo.",
    "admin_ask_verdict": "Verdict comment. “-” to skip.",
    "admin_stats_text": (
        "Users: {users} (banned {banned})\n"
        "Deals total: {deals}\n"
        "Closed: {closed}\n"
        "Open disputes: {disputes}\n"
        "Closed volume: {volume} {currency}\n"
        "In escrow now: {escrow} {currency}\n\n"
        "By status:\n{by_status}\n\n"
        "By category:\n{by_cat}\n\n"
        "Recent:\n{recent}"
    ),
    "admin_deal_line": "#{id} · {status} · {cat} · {amount}",
}

LOCALES = {"ru": RU, "en": EN}


def t(lang: str, key: str, **kwargs: Any) -> str:
    table = LOCALES.get(lang) or RU
    text = table.get(key) or RU.get(key) or key
    if kwargs:
        return text.format(**kwargs)
    return text
