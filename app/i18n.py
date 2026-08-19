from typing import Any

RU = {
    "choose_lang": "🌐 <b>Язык / Language</b>\n\nВыберите язык интерфейса.",
    "welcome": (
        "🛡️ <b>Phantom OTC</b>\n"
        "Привет, {name}!\n\n"
        "Оплата на гаранте до подтверждения сделки.\n"
        "Аккаунты · NFT · товар · TON"
    ),
    "banned": (
        "🚫 <b>Доступ закрыт</b>\n\n"
        "Ваш аккаунт заблокирован администратором.\n"
        "Вы не можете пользоваться этим ботом.\n\n"
        "{reason}"
        "💬 Если это ошибка, напишите в поддержку: @{support}"
    ),
    "banned_reason": "📝 Причина: <b>{reason}</b>\n\n",
    "need_username": "⚠️ Укажите username в настройках Telegram — без него сделки недоступны.",
    "menu": "🏠 <b>Главное меню</b>\n\nВыберите действие ниже.",
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
    "cancelled": "❌ Отменено.",
    "error": "⚠️ Не получилось. Попробуйте ещё раз.",
    "profile": (
        "👤 <b>Профиль</b>\n\n"
        "🆔 ID: <code>{id}</code>\n"
        "✨ Ник: <b>{nick}</b>\n"
        "🔗 Username: @{username}\n"
        "🤝 Сделок: <b>{deals}</b>\n"
        "💵 USDT: <b>{usdt}</b> (заморожено {frozen_usdt})\n"
        "💎 TON: <b>{ton_bal}</b> (заморожено {frozen_ton})\n"
        "💎 Адрес вывода: {ton}"
    ),
    "not_set": "не указан",
    "btn_req": "Реквизиты",
    "req_menu": "💎 <b>Адрес вывода</b>\n\nТолько TON-сеть. Сюда уходят TON и USDT.",
    "req_card": "Карта",
    "req_phone": "Телефон и банк",
    "req_ton": "TON-адрес",
    "req_bank_short": "Банк",
    "req_ask_card": "💳 Номер карты, только цифры.",
    "req_ask_phone": "📱 Номер телефона, например +79991234567.",
    "req_ask_bank": "🏦 Название банка.",
    "req_ask_ton": "💎 TON-адрес (UQ… / EQ…).",
    "req_saved": "✅ Реквизиты сохранены.",
    "req_bad": "⚠️ Неверный формат.",
    "lang_changed": "✅ Язык обновлён.",
    "deposit": "Пополнение",
    "withdraw": "Вывод",
    "change_lang": "Язык",
    "deposit_ask": "⬇️ Сумма пополнения в <b>{currency}</b>. Минимум <b>{min}</b>.",
    "deposit_created": (
        "⬇️ <b>Заявка #{id}</b>\n\n"
        "💰 Сумма: <b>{amount} {currency}</b>\n"
        "🔖 Комментарий: <code>{comment}</code>\n\n"
        "{extra}\n\n"
        "После перевода нажмите «Проверить» или дождитесь администратора."
    ),
    "deposit_ton": "Переведите на TON-адрес:\n<code>{address}</code>\nВ комментарии укажите код выше.",
    "deposit_manual": "Перевод подтверждает администратор. Напишите @{support}, если платёж уже ушёл.",
    "deposit_check": "Проверить",
    "deposit_wait": "⏳ Платёж ещё не найден.",
    "deposit_ok": "✅ Баланс пополнен на <b>{amount} {currency}</b>.",
    "withdraw_ask": "⬆️ Сумма вывода в <b>{currency}</b>. Минимум <b>{min}</b>. Комиссия на вывод не берётся.",
    "withdraw_method": "⬆️ <b>Куда вывести?</b>",
    "withdraw_no_req": "⚠️ Сначала заполните реквизиты в профиле.",
    "withdraw_ok": "✅ Заявка на вывод #{id}: <b>{amount} {currency}</b> на {details}. Администратор обработает её вручную.",
    "withdraw_low": "⚠️ Недостаточно средств.",
    "min_amount": "⚠️ Минимум {min} {currency}.",
    "about": (
        "ℹ️ <b>Phantom OTC</b>\n\n"
        "Безопасные сделки в TON и USDT: аккаунты, NFT-подарки, товар.\n\n"
        "• Пополнение TON или USDT через сеть TON. Монеты хранятся в боте\n"
        "• Когда сделка стартует, сумма замораживается и вывести её нельзя\n"
        "• Покупатель подтверждает получение — продавец получает монеты минус комиссия\n"
        "• Любая сторона может открыть спор, решение принимает администратор\n\n"
        "💸 Комиссия: <b>{commission}%</b> с продавца\n"
        "💬 Поддержка: @{support}\n"
        "{chat}"
    ),
    "deal_role": "🛡️ <b>Кем вы будете в сделке?</b>",
    "deal_buyer": "Покупатель",
    "deal_seller": "Продавец",
    "deal_kind": "Тип сделки?",
    "deal_kind_goods": "Товар / NFT",
    "deal_kind_ton": "TON → рубли",
    "deal_kind_label_goods": "товар / NFT",
    "deal_kind_label_ton": "TON → рубли",
    "deal_ask_user": "👤 Username второй стороны, без @.",
    "deal_self": "⚠️ С самим собой сделку открыть нельзя.",
    "deal_missing": "⚠️ Пользователь не запускал бота.",
    "deal_busy_you": "⚠️ У вас уже есть активная сделка #{id}.",
    "deal_busy_them": "⚠️ У этого пользователя уже есть активная сделка.",
    "deal_preview": (
        "👤 <b>Контрагент</b>\n\n"
        "🆔 ID <code>{id}</code>\n"
        "✨ Ник: {nick}\n"
        "🔗 @{username}\n"
        "🤝 Сделок: <b>{deals}</b>\n"
        "🎭 Роль: {role}\n"
        "📦 Тип: {kind}"
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
        "🛡️ <b>Сделка #{id}</b>\n"
        "📂 {cat}\n"
        "🏷 {title}\n\n"
        "🛒 Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "💰 Сумма: <b>{amount}</b>\n"
        "🔑 Данные: {secret}\n"
        "📝 Условия: {desc}\n"
        "📌 Статус: <b>{status}</b>"
    ),
    "deal_opened_nft": (
        "🎁 <b>Сделка #{id}</b> · NFT\n"
        "📂 {cat}\n"
        "🏷 {title}\n\n"
        "🛒 Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "💰 Цена: <b>{amount}</b>\n"
        "🎁 NFT: {nft}\n"
        "🔑 Данные: {secret}\n"
        "📝 Условия: {desc}\n"
        "📌 Статус: <b>{status}</b>"
    ),
    "deal_opened_req": (
        "🛡️ <b>Сделка #{id}</b>\n"
        "📂 {cat}\n"
        "🏷 {title}\n\n"
        "🛒 Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "💰 Цена: <b>{amount}</b>\n"
        "💳 Реквизиты продавца:\n{req}\n"
        "📄 Чек: {receipt}\n"
        "📝 Условия: {desc}\n"
        "📌 Статус: <b>{status}</b>"
    ),
    "deal_opened_ton": (
        "💎 <b>Сделка #{id}</b> · TON → рубли\n\n"
        "🛒 Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "🔹 TON: <b>{ton}</b>\n"
        "🔹 Рубли: <b>{rub} ₽</b>\n"
        "📥 Адрес покупателя: <code>{buyer_ton}</code>\n"
        "🏦 Эскроу V4: <code>{escrow}</code>\n"
        "🔖 Комментарий: <code>{comment}</code>\n"
        "📥 Получено TON: {received}\n"
        "💳 Реквизиты продавца:\n{req}\n"
        "📝 Условия: {desc}\n"
        "🔗 Выплата: <code>{payout}</code>\n"
        "📌 Статус: <b>{status}</b>"
    ),
    "deal_status_pending": "⏳ ожидает принятия",
    "deal_status_open": "🔒 сумма заморожена",
    "deal_status_wait_ton": "⏳ ждёт TON на эскроу",
    "deal_status_funded": "🔒 TON на гаранте, ждут рубли",
    "deal_status_rub_sent": "💸 рубли отправлены, ждут подтверждения",
    "deal_status_paid": "💳 оплачена",
    "deal_status_dispute": "⚠️ спор",
    "deal_status_review": "⭐ завершена, отзыв",
    "deal_status_closed": "✅ закрыта",
    "deal_status_cancelled": "❌ отменена",
    "deal_status_listed": "📣 в канале, ждёт покупателя",
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
    "deal_pdf": "Чек PDF",
    "deal_confirm": "Товар получен",
    "deal_dispute": "Спор",
    "deal_cancel": "Отменить",
    "deal_ask_price": "Сумма сделки в {currency}.",
    "deal_price_set": "Сумма установлена: {amount} {currency}.",
    "deal_price_locked": "Сумму уже нельзя менять.",
    "deal_ask_desc": "Кратко опишите товар и условия передачи.",
    "deal_desc_set": "Условия сохранены.",
    "deal_nft_pick": "Выберите NFT из инвентаря. Сначала подарок должен лежать на банке — без этого сделку создать нельзя. После выбора он заморозится.",
    "deal_nft_empty": "В инвентаре нет свободных NFT. Сначала отправьте подарок на банк.",
    "deal_nft_set": "NFT прикреплён: {title}.",
    "deal_nft_none": "не прикреплён",
    "deal_nft_need_item": "Сначала отправьте NFT на банк. Без подарка в инвентаре сделку на него создать нельзя.",
    "deal_nft_need_req": "Чтобы продать NFT, укажите реквизиты в профиле: карта или телефон и банк.",
    "deal_nft_pdf_only": "Нужен только чек в формате PDF. Фото и другие файлы не принимаются.",
    "deal_nft_pdf_ask": "Оплатите по реквизитам продавца и пришлите чек одним файлом PDF.",
    "deal_nft_pdf_sent": "Чек PDF отправлен продавцу. Ждём подтверждения, что деньги пришли.",
    "deal_nft_pdf_got": (
        "Покупатель прислал чек PDF по сделке #{id}.\n"
        "Проверьте перевод. Если деньги пришли — подтвердите, NFT уйдёт покупателю автоматически."
    ),
    "deal_nft_confirm_ask": "Рубли пришли по реквизитам? После подтверждения NFT автоматически уйдёт покупателю.",
    "deal_nft_done": "Деньги подтверждены. NFT отправлен покупателю.",
    "deal_nft_done_buyer": "Продавец подтвердил оплату. NFT отправлен вам.",
    "deal_nft_no_pay": "NFT оплачивается по реквизитам продавца, не с баланса бота. Прикрепите чек PDF.",
    "deal_req_no_pay": "Эта сделка оплачивается по реквизитам продавца, не с баланса бота. Прикрепите чек PDF.",
    "deal_req_confirm_ask": "Рубли пришли по реквизитам? После подтверждения передайте товар покупателю.",
    "deal_req_done": "Оплата подтверждена. Передайте товар покупателю.",
    "deal_req_done_buyer": "Продавец подтвердил оплату. Проверьте товар и нажмите «Товар получен».",
    "deal_req_pdf_got": (
        "Покупатель прислал чек PDF по сделке #{id}.\n"
        "Проверьте перевод. Если деньги пришли — подтвердите."
    ),
    "deal_nft_pay_hint": "Оплатите <b>{amount} ₽</b> по реквизитам продавца и прикрепите чек PDF.",
    "deal_receipt_none": "не прикреплён",
    "deal_receipt_yes": "PDF получен",
    "deal_pay_no_amount": "Продавец ещё не указал сумму.",
    "deal_pay_low": "Недостаточно средств. Нужно {need} {currency}, на балансе {have}.",
    "deal_paid": "Оплата прошла. Продавец передаёт товар.",
    "deal_paid_seller": "Покупатель оплатил сделку #{id}. Передайте товар.",
    "deal_nft_sent": "NFT отправлен покупателю через банковский аккаунт.",
    "deal_nft_wait_send": "Сначала дождитесь передачи NFT. Подтвердить можно после отправки подарка.",
    "deal_nft_fail": "Не удалось отправить NFT. Откройте спор, администратор разберёт вручную.",
    "deal_nft_no_stars": "NFT пока не отправлен: на банковском аккаунте не хватает Stars. Как пополнят — уйдёт автоматически.",
    "deal_nft_retry_ok": "NFT по сделке #{id} отправлен: {title}.",
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
    "admin_ask_id": "Telegram ID пользователя.",
    "admin_ask_balance": "Новый баланс в {currency}.",
    "admin_ask_balance_asset": "Какой баланс изменить?",
    "admin_balance_frozen": "Нельзя поставить баланс ниже заморозки ({frozen} {currency}).",
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
    "deal_mode": "🛡️ <b>Как открыть сделку?</b>",
    "deal_private": "С человеком (username)",
    "deal_public": "Выложить в канал",
    "deal_channel": "📣 Канал сделок",
    "deal_take": "Открыть сделку",
    "deal_manual_btn": "Памятка",
    "deal_ask_cat": "📂 <b>Категория сделки</b>",
    "deal_ask_group": "🛡️ <b>Что продаёте?</b>",
    "deal_ask_title": "🏷 Короткое название объявления, как в канале. Например: Roblox 1200 Robux, почта отвязана.",
    "deal_list_ok": "✅ Объявление #{id} в канале. Памятка придёт покупателю, когда он откроет сделку.",
    "deal_list_ok_buy": "✅ Объявление #{id} в канале. Когда продавец откроет сделку, обоим придёт памятка.",
    "deal_list_no_channel": "📣 Канал не задан в config.ini. Объявление всё равно в витрине бота.",
    "deal_list_ton": "⚠️ TON → рубли только напрямую с человеком, не в канал.",
    "deal_listed_taken": "⚠️ Объявление уже сняли или закрыли.",
    "deal_feed_empty": "🛒 Открытых объявлений нет.",
    "deal_feed_line": "#{id} · {cat} · {amount}\n{title}\n@{seller}",
    "deal_need_deposit": "⬇️ Сначала пополните баланс в профиле, затем откройте сделку.",
    "deal_need_price": "⚠️ У объявления должна быть сумма больше нуля.",
    "nft_need_gift": "🎁 Сначала закиньте NFT на банк и выберите его. Без подарка в инвентаре сделку открыть нельзя.",
    "channel_listing": (
        "🛡️ <b>Сделка #{id}</b> · {cat}\n"
        "{title}\n\n"
        "💼 Продавец: @{seller}\n"
        "💰 Цена: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Оплата через бота-гаранта. Нажмите «Открыть в боте»."
    ),
    "channel_listing_req": (
        "🛡️ <b>Сделка #{id}</b> · {cat}\n"
        "{title}\n\n"
        "💼 Продавец: @{seller}\n"
        "💰 Цена: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Оплата по реквизитам продавца, чек PDF. Нажмите «Открыть в боте»."
    ),
    "channel_listing_buy": (
        "🛡️ <b>Ищу #{id}</b> · {cat}\n"
        "{title}\n\n"
        "🛒 Покупатель: @{buyer}\n"
        "💰 Готов заплатить: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Оплата через бота-гаранта. Нажмите «Открыть в боте»."
    ),
    "channel_listing_nft": (
        "🎁 <b>NFT #{id}</b> · {cat}\n"
        "{title}\n\n"
        "💼 Продавец: @{seller}\n"
        "💰 Цена: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Оплата TON или USDT через бота-гаранта. Нажмите «Открыть в боте»."
    ),
    "channel_listing_nft_buy": (
        "🎁 <b>Куплю NFT #{id}</b> · {cat}\n"
        "{title}\n\n"
        "🛒 Покупатель: @{buyer}\n"
        "💰 Готов заплатить: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Продавец сначала кладёт NFT на банк. Оплата по его реквизитам, чек PDF. Нажмите «Открыть в боте»."
    ),
    "channel_open": "🛡️ Открыть в боте",
    "channel_taken": "🔒 Сделку открыли, объявление снято.",
    "channel_closed": "🔒 Объявление снято.",
    "deal_taken_seller": "🛒 Покупатель @{username} открыл объявление #{id}. Сумма заморожена на гаранте.",
    "deal_taken_buyer": "💼 Продавец @{username} откликнулся на объявление #{id}. Смотрите памятку.",
    "faq_title": "❓ <b>F.A.Q</b>\n\nОтветы на частые вопросы.",
    "faq_empty": "❓ Пока нет статей. Администратор добавит их в админке.",
    "faq_missing": "⚠️ Статья удалена.",
    "support_text": "💬 <b>Поддержка</b>\n\nНапишите нам: @{support}\n{chat}",
    "history_empty": "📜 История пуста.",
    "history_role": "📜 <b>История сделок</b>\n\nПоказать сделки, где вы…",
    "history_line": "#{id} · {role} · {amount} · {status}\nКонтрагент: @{peer}",
    "inv_empty": "🎁 Инвентарь пуст.",
    "inv_how": (
        "🎁 <b>Инвентарь NFT</b>\n\n"
        "Отправьте уникальный подарок на банк: <b>{bank}</b>\n"
        "Он появится здесь и привяжется к вашему Telegram ID."
    ),
    "inv_item": "🎁 <b>{title}</b>\nСтатус: {status}\nID: {id}",
    "inv_status_available": "✅ доступен",
    "inv_status_locked": "🔒 в сделке",
    "inv_status_transferred": "📤 передан",
    "inv_new": "🎁 В инвентарь добавлен подарок: <b>{title}</b>",
    "admin_menu": "🎛 <b>Админка</b>",
    "btn_feed": "Витрина",
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
        "Банк: {bank}\n"
        "Stars: {stars}\n"
        "Fragment: {fragment}\n"
        "Передача NFT: {fee}★, хватит на {nft_left}\n"
        "Ожидают отправки NFT: {pending_nft}\n\n"
        "По статусам:\n{by_status}\n\n"
        "По категориям:\n{by_cat}\n\n"
        "Последние:\n{recent}"
    ),
    "admin_deal_line": "#{id} · {status} · {cat} · {amount}",
    "admin_stars_offline": "офлайн (нет session)",
    "admin_stars_unknown": "не удалось прочитать",
    "admin_stars_low": (
        "На банковском аккаунте {stars}★, порог {min}★.\n"
        "Передача NFT стоит ≈{fee}★. Автопокупка {pack}★ за TON через Fragment не закрыла нехватку — проверьте [fragment] в config.ini.\n"
        "Ожидают отправки: {pending}."
    ),
    "admin_stars_bought": "✅ Fragment купил {amount}★ на банк @{user} за TON.\nTX: <code>{tx}</code>",
    "admin_stars_buy_fail": "❌ Fragment не купил Stars на банк @{user}: {error}",
    "admin_fragment_on": "автопокупка ★",
    "admin_fragment_off": "выкл.",
    "admin_fragment_wait": "не готово (cookies / ключ / библиотека)",
    "admin_nft_no_stars": "Сделка #{id}: не хватило Stars на передачу NFT. Баланс {stars}★, нужно {fee}★.",
    "btn_admin": "Админка",
    "deal_ask_currency": "💎 <b>Валюта сделки</b>\n\nTON или USDT. Покупатель должен пополнить этот актив.",
    "deal_cur_ton": "TON",
    "deal_cur_usdt": "USDT",
    "deal_ask_secret": "🔑 Данные от товара (логин, пароль, почта). Покупатель увидит их после заморозки суммы.",
    "deal_secret_hidden": "скрыто до старта сделки",
    "deal_seller_only": "⚠️ Сделку создаёт только продавец.",
    "deposit_pick": "⬇️ <b>Какой актив пополнить?</b>\n\nОба идут через сеть TON на кошелёк гаранта.",
    "deposit_asset_ton": "TON",
    "deposit_asset_usdt": "USDT",
    "deposit_usdt_net": "Отправьте USDT (jetton) в сети TON на адрес:\n<code>{address}</code>\nВ комментарии / memo укажите код выше.",
    "withdraw_pick": "⬆️ <b>Какой актив вывести?</b>\n\nВывод только на TON-адрес. Замороженные в сделке монеты недоступны.",
    "withdraw_frozen": "⚠️ Доступно {have} {currency}, ещё {frozen} заморожено в сделке. Замороженное вывести нельзя.",
    "admin_wallets": "Кошельки",
    "admin_sessions": "Сессии",
    "admin_admins": "Админы",
    "admin_adm_add": "Добавить админа",
    "admin_cfg_ton_address": "TON-адрес эскроу",
    "admin_cfg_ton_mnemonic": "Мнемоника TON",
    "admin_cfg_ton_api_key": "TON API-ключ",
    "admin_cfg_usdt_master": "USDT jetton master",
    "admin_cfg_fragment_mnemonic": "Мнемоника Fragment",
    "admin_cfg_fragment_wallet": "Кошелёк Fragment",
    "admin_cfg_fragment_api_key": "API-ключ Fragment",
    "admin_cfg_bank_api_id": "Bank api_id",
    "admin_cfg_bank_api_hash": "Bank api_hash",
    "admin_cfg_bank_session": "Bank session",
    "admin_cfg_bank_username": "Bank username",
    "admin_cfg_fragment_cookies": "Fragment cookies",
    "admin_cfg_ask": "Новое значение для <b>{key}</b>. Отправьте «-», чтобы очистить поле.",
    "admin_cfg_saved": "✅ Сохранено: {key}",
    "admin_cfg_reconnect": "Переподключил сервис: {svc}",
    "admin_cfg_reconnect_fail": "⚠️ Сохранено, но {svc} не переподключился. Проверьте значение.",
    "admin_cfg_wallets_text": "💎 <b>Кошельки</b>\n\n{lines}\n\nНажмите поле, чтобы заменить значение.",
    "admin_cfg_sessions_text": "🔐 <b>Сессии</b>\n\n{lines}\n\nНажмите поле, чтобы заменить значение.",
    "admin_cfg_admins_text": "👑 <b>Админы</b>\n\n{lines}\n\nДобавьте ID или @username. Нельзя удалить последнего админа.",
    "admin_adm_ask": "Пришлите Telegram ID или @username нового админа.",
    "admin_adm_added": "✅ Админ {id} добавлен.",
    "admin_adm_removed": "✅ Админ {id} удалён.",
    "admin_adm_last": "⚠️ Нельзя удалить последнего админа.",
    "admin_adm_self": "⚠️ Нельзя удалить себя.",
    "admin_adm_exists": "⚠️ Этот пользователь уже админ.",
    "admin_cfg_value": "{title}\n<code>{value}</code>",
}

EN = {
    "choose_lang": "🌐 <b>Language / Язык</b>\n\nChoose the interface language.",
    "welcome": (
        "🛡️ <b>Phantom OTC</b>\n"
        "Hey, {name}!\n\n"
        "Funds stay in escrow until the deal is confirmed.\n"
        "Accounts · NFT · goods · TON and USDT"
    ),
    "banned": (
        "🚫 <b>Access denied</b>\n\n"
        "Your account was banned by an administrator.\n"
        "You cannot use this bot.\n\n"
        "{reason}"
        "💬 If this is a mistake, contact support: @{support}"
    ),
    "banned_reason": "📝 Reason: <b>{reason}</b>\n\n",
    "need_username": "⚠️ Set a Telegram username first. Deals are unavailable without it.",
    "menu": "🏠 <b>Main menu</b>\n\nPick an action below.",
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
    "cancelled": "❌ Cancelled.",
    "error": "⚠️ Something went wrong. Try again.",
    "profile": (
        "👤 <b>Profile</b>\n\n"
        "🆔 ID: <code>{id}</code>\n"
        "✨ Nick: <b>{nick}</b>\n"
        "🔗 Username: @{username}\n"
        "🤝 Deals: <b>{deals}</b>\n"
        "💵 USDT: <b>{usdt}</b> (frozen {frozen_usdt})\n"
        "💎 TON: <b>{ton_bal}</b> (frozen {frozen_ton})\n"
        "💎 Withdrawal address: {ton}"
    ),
    "not_set": "not set",
    "btn_req": "Payout details",
    "req_menu": "💎 <b>Withdrawal address</b>\n\nTON network only. TON and USDT are sent here.",
    "req_card": "Card",
    "req_phone": "Phone and bank",
    "req_ton": "TON address",
    "req_bank_short": "Bank",
    "req_ask_card": "💳 Card number, digits only.",
    "req_ask_phone": "📱 Phone number, e.g. +19995550100.",
    "req_ask_bank": "🏦 Bank name.",
    "req_ask_ton": "💎 TON address (UQ… / EQ…).",
    "req_saved": "✅ Details saved.",
    "req_bad": "⚠️ Invalid format.",
    "lang_changed": "✅ Language updated.",
    "deposit": "Deposit",
    "withdraw": "Withdraw",
    "change_lang": "Language",
    "deposit_ask": "⬇️ Deposit amount in <b>{currency}</b>. Minimum <b>{min}</b>.",
    "deposit_created": (
        "⬇️ <b>Request #{id}</b>\n\n"
        "💰 Amount: <b>{amount} {currency}</b>\n"
        "🔖 Memo: <code>{comment}</code>\n\n"
        "{extra}\n\n"
        "After sending, tap Check or wait for an admin."
    ),
    "deposit_ton": "Send TON to:\n<code>{address}</code>\nUse the memo above as the comment.",
    "deposit_manual": "An admin confirms the transfer. Message @{support} if it is already sent.",
    "deposit_check": "Check",
    "deposit_wait": "⏳ Payment not found yet.",
    "deposit_ok": "✅ Balance credited with <b>{amount} {currency}</b>.",
    "withdraw_ask": "⬆️ Withdrawal amount in <b>{currency}</b>. Minimum <b>{min}</b>. No extra fee on payout.",
    "withdraw_method": "⬆️ <b>Where should we send it?</b>",
    "withdraw_no_req": "⚠️ Fill in payout details in your profile first.",
    "withdraw_ok": "✅ Withdrawal #{id}: <b>{amount} {currency}</b> to {details}. An admin will process it.",
    "withdraw_low": "⚠️ Insufficient balance.",
    "min_amount": "⚠️ Minimum {min} {currency}.",
    "about": (
        "ℹ️ <b>Phantom OTC</b>\n\n"
        "Safe P2P deals in TON and USDT: accounts, NFT gifts, goods.\n\n"
        "• Deposit TON or USDT via the TON network. Funds live in the bot\n"
        "• When a deal starts the amount is frozen and cannot be withdrawn\n"
        "• The buyer confirms receipt — the seller is paid minus the fee\n"
        "• Either side can open a dispute; an admin decides\n\n"
        "💸 Fee: <b>{commission}%</b> from the seller\n"
        "💬 Support: @{support}\n"
        "{chat}"
    ),
    "deal_role": "🛡️ <b>Your role in this deal?</b>",
    "deal_buyer": "Buyer",
    "deal_seller": "Seller",
    "deal_kind": "Deal type?",
    "deal_kind_goods": "Goods / NFT",
    "deal_kind_ton": "TON → RUB",
    "deal_kind_label_goods": "goods / NFT",
    "deal_kind_label_ton": "TON → RUB",
    "deal_ask_user": "👤 Counterparty username, without @.",
    "deal_self": "⚠️ You cannot open a deal with yourself.",
    "deal_missing": "⚠️ This user has never started the bot.",
    "deal_busy_you": "⚠️ You already have an active deal #{id}.",
    "deal_busy_them": "⚠️ That user already has an active deal.",
    "deal_preview": (
        "👤 <b>Counterparty</b>\n\n"
        "🆔 ID <code>{id}</code>\n"
        "✨ Nick: {nick}\n"
        "🔗 @{username}\n"
        "🤝 Deals: <b>{deals}</b>\n"
        "🎭 Your role: {role}\n"
        "📦 Type: {kind}"
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
        "🛡️ <b>Deal #{id}</b>\n"
        "📂 {cat}\n"
        "🏷 {title}\n\n"
        "🛒 Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Seller: @{seller} (<code>{seller_id}</code>)\n"
        "💰 Amount: <b>{amount}</b>\n"
        "🔑 Credentials: {secret}\n"
        "📝 Terms: {desc}\n"
        "📌 Status: <b>{status}</b>"
    ),
    "deal_opened_nft": (
        "🎁 <b>Deal #{id}</b> · NFT\n"
        "📂 {cat}\n"
        "🏷 {title}\n\n"
        "🛒 Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Seller: @{seller} (<code>{seller_id}</code>)\n"
        "💰 Price: <b>{amount}</b>\n"
        "🎁 NFT: {nft}\n"
        "🔑 Credentials: {secret}\n"
        "📝 Terms: {desc}\n"
        "📌 Status: <b>{status}</b>"
    ),
    "deal_opened_req": (
        "🛡️ <b>Deal #{id}</b>\n"
        "📂 {cat}\n"
        "🏷 {title}\n\n"
        "🛒 Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Seller: @{seller} (<code>{seller_id}</code>)\n"
        "💰 Price: <b>{amount}</b>\n"
        "💳 Seller details:\n{req}\n"
        "📄 Receipt: {receipt}\n"
        "📝 Terms: {desc}\n"
        "📌 Status: <b>{status}</b>"
    ),
    "deal_opened_ton": (
        "💎 <b>Deal #{id}</b> · TON → RUB\n\n"
        "🛒 Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "💼 Seller: @{seller} (<code>{seller_id}</code>)\n"
        "🔹 TON: <b>{ton}</b>\n"
        "🔹 Rubles: <b>{rub} ₽</b>\n"
        "📥 Buyer address: <code>{buyer_ton}</code>\n"
        "🏦 Escrow V4: <code>{escrow}</code>\n"
        "🔖 Memo: <code>{comment}</code>\n"
        "📥 TON received: {received}\n"
        "💳 Seller payout details:\n{req}\n"
        "📝 Terms: {desc}\n"
        "🔗 Payout: <code>{payout}</code>\n"
        "📌 Status: <b>{status}</b>"
    ),
    "deal_status_pending": "⏳ waiting",
    "deal_status_open": "🔒 amount frozen",
    "deal_status_wait_ton": "⏳ waiting for TON escrow",
    "deal_status_funded": "🔒 TON locked, waiting for rubles",
    "deal_status_rub_sent": "💸 rubles sent, waiting confirmation",
    "deal_status_paid": "💳 paid",
    "deal_status_dispute": "⚠️ dispute",
    "deal_status_review": "⭐ completed, review",
    "deal_status_closed": "✅ closed",
    "deal_status_cancelled": "❌ cancelled",
    "deal_status_listed": "📣 listed, waiting for a buyer",
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
    "deal_pdf": "PDF receipt",
    "deal_confirm": "Item received",
    "deal_dispute": "Dispute",
    "deal_cancel": "Cancel",
    "deal_ask_price": "Deal amount in {currency}.",
    "deal_price_set": "Amount set: {amount} {currency}.",
    "deal_price_locked": "The amount can no longer be changed.",
    "deal_ask_desc": "Describe the item and how it will be delivered.",
    "deal_desc_set": "Terms saved.",
    "deal_nft_pick": "Pick an NFT from inventory. The gift must already be on the bank account — you cannot create a deal without it. It will be locked after you pick it.",
    "deal_nft_empty": "No free NFTs in inventory. Send the gift to the bank account first.",
    "deal_nft_set": "NFT attached: {title}.",
    "deal_nft_none": "not attached",
    "deal_nft_need_item": "Send the NFT to the bank first. You cannot create a deal for a gift that is not in inventory.",
    "deal_nft_need_req": "To sell an NFT, add payout details in your profile: a card or phone plus bank.",
    "deal_nft_pdf_only": "Only a PDF receipt is accepted. Photos and other files are rejected.",
    "deal_nft_pdf_ask": "Pay the seller’s details, then send the receipt as a single PDF file.",
    "deal_nft_pdf_sent": "PDF receipt sent to the seller. Waiting for them to confirm the money arrived.",
    "deal_nft_pdf_got": (
        "The buyer sent a PDF receipt for deal #{id}.\n"
        "Check the transfer. If the money arrived, confirm — the NFT will go to the buyer automatically."
    ),
    "deal_nft_confirm_ask": "Did the rubles arrive? After you confirm, the NFT is sent to the buyer automatically.",
    "deal_nft_done": "Payment confirmed. The NFT was sent to the buyer.",
    "deal_nft_done_buyer": "The seller confirmed payment. The NFT was sent to you.",
    "deal_nft_no_pay": "NFT deals are paid to the seller’s details, not from the bot balance. Attach a PDF receipt.",
    "deal_req_no_pay": "This deal is paid to the seller’s details, not from the bot balance. Attach a PDF receipt.",
    "deal_req_confirm_ask": "Did the rubles arrive? After you confirm, deliver the item to the buyer.",
    "deal_req_done": "Payment confirmed. Deliver the item to the buyer.",
    "deal_req_done_buyer": "The seller confirmed payment. Check the item and tap Item received.",
    "deal_req_pdf_got": (
        "The buyer sent a PDF receipt for deal #{id}.\n"
        "Check the transfer. If the money arrived, confirm."
    ),
    "deal_nft_pay_hint": "Pay <b>{amount} ₽</b> to the seller’s details and attach a PDF receipt.",
    "deal_receipt_none": "not attached",
    "deal_receipt_yes": "PDF received",
    "deal_pay_no_amount": "The seller has not set the amount yet.",
    "deal_pay_low": "Not enough funds. Need {need} {currency}, have {have}.",
    "deal_paid": "Payment received. The seller should deliver now.",
    "deal_paid_seller": "The buyer paid deal #{id}. Deliver the item.",
    "deal_nft_sent": "NFT sent to the buyer via the bank account.",
    "deal_nft_wait_send": "Wait until the NFT is transferred. You can confirm after the gift is sent.",
    "deal_nft_fail": "NFT transfer failed. Open a dispute so an admin can handle it.",
    "deal_nft_no_stars": "NFT not sent yet: the bank account is out of Stars. It will go automatically after a top-up.",
    "deal_nft_retry_ok": "NFT for deal #{id} was sent: {title}.",
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
    "admin_ask_id": "User Telegram ID.",
    "admin_ask_balance": "New balance in {currency}.",
    "admin_ask_balance_asset": "Which balance should be changed?",
    "admin_balance_frozen": "Balance cannot go below the frozen amount ({frozen} {currency}).",
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
    "deal_mode": "🛡️ <b>How do you want to open a deal?</b>",
    "deal_private": "With a user (username)",
    "deal_public": "Post to the channel",
    "deal_channel": "📣 Deals channel",
    "deal_take": "Open this deal",
    "deal_manual_btn": "Memo",
    "deal_ask_cat": "📂 <b>Deal category</b>",
    "deal_ask_group": "🛡️ <b>What are you selling?</b>",
    "deal_ask_title": "Short listing title for the channel. Example: Roblox 1200 Robux, email unlinked.",
    "deal_list_ok": "Listing #{id} is in the channel. The buyer gets the memo when they open the deal.",
    "deal_list_ok_buy": "Listing #{id} is in the channel. When a seller opens it, both of you get the memo.",
    "deal_list_no_channel": "No deals channel in config.ini [bot] deals_channel. The listing is still in the bot feed.",
    "deal_list_ton": "TON → RUB deals are direct only, not posted to the channel.",
    "deal_listed_taken": "This listing is already taken or closed.",
    "deal_feed_empty": "🛒 No open listings.",
    "deal_feed_line": "#{id} · {cat} · {amount}\n{title}\n@{seller}",
    "deal_need_deposit": "Top up your balance in the profile first, then open the deal.",
    "deal_need_price": "The listing must have a price greater than zero.",
    "nft_need_gift": "Send the NFT to the bank and attach it first. You cannot open a deal without that gift in inventory.",
    "channel_listing": (
        "🛡️ <b>Deal #{id}</b> · {cat}\n"
        "{title}\n\n"
        "💼 Seller: @{seller}\n"
        "💰 Price: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Pay through the escrow bot. Tap Open in bot."
    ),
    "channel_listing_req": (
        "🛡️ <b>Deal #{id}</b> · {cat}\n"
        "{title}\n\n"
        "💼 Seller: @{seller}\n"
        "💰 Price: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Pay the seller’s details. The buyer sends a PDF receipt. Tap Open in bot."
    ),
    "channel_listing_buy": (
        "🛡️ <b>Wanted #{id}</b> · {cat}\n"
        "{title}\n\n"
        "🛒 Buyer: @{buyer}\n"
        "💰 Will pay: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Pay through the escrow bot. Tap Open in bot."
    ),
    "channel_listing_nft": (
        "🎁 <b>NFT #{id}</b> · {cat}\n"
        "{title}\n\n"
        "💼 Seller: @{seller}\n"
        "💰 Price: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "Pay the seller’s details. The buyer sends a PDF receipt. Tap Open in bot."
    ),
    "channel_listing_nft_buy": (
        "🎁 <b>Buying NFT #{id}</b> · {cat}\n"
        "{title}\n\n"
        "🛒 Buyer: @{buyer}\n"
        "💰 Will pay: <b>{amount}</b>\n\n"
        "{desc}\n\n"
        "The seller must put the NFT on the bank first. Pay their details, PDF receipt. Tap Open in bot."
    ),
    "channel_open": "🛡️ Open in bot",
    "channel_taken": "🔒 This deal was taken.",
    "channel_closed": "🔒 Listing removed.",
    "deal_taken_seller": "Buyer @{username} opened listing #{id}. The amount is frozen in escrow.",
    "deal_taken_buyer": "Seller @{username} took listing #{id}. Read the memo.",
    "faq_title": "❓ <b>F.A.Q</b>\n\nAnswers to common questions.",
    "faq_empty": "❓ No articles yet. An admin can add them in the admin panel.",
    "faq_missing": "⚠️ This article was removed.",
    "support_text": "💬 <b>Support</b>\n\nMessage us: @{support}\n{chat}",
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
        "Bank: {bank}\n"
        "Stars: {stars}\n"
        "Fragment: {fragment}\n"
        "NFT transfer: {fee}★, enough for {nft_left}\n"
        "Pending NFT sends: {pending_nft}\n\n"
        "By status:\n{by_status}\n\n"
        "By category:\n{by_cat}\n\n"
        "Recent:\n{recent}"
    ),
    "admin_deal_line": "#{id} · {status} · {cat} · {amount}",
    "admin_stars_offline": "offline (no session)",
    "admin_stars_unknown": "unavailable",
    "admin_stars_low": (
        "Bank account has {stars}★, threshold {min}★.\n"
        "An NFT transfer costs ≈{fee}★. Auto-buy of {pack}★ for TON via Fragment did not cover it — check [fragment] in config.ini.\n"
        "Waiting to send: {pending}."
    ),
    "admin_stars_bought": "✅ Fragment bought {amount}★ for bank @{user} with TON.\nTX: <code>{tx}</code>",
    "admin_stars_buy_fail": "❌ Fragment failed to buy Stars for bank @{user}: {error}",
    "admin_fragment_on": "★ auto-buy",
    "admin_fragment_off": "off",
    "admin_fragment_wait": "not ready (cookies / key / library)",
    "admin_nft_no_stars": "Deal #{id}: not enough Stars to transfer the NFT. Balance {stars}★, need {fee}★.",
    "btn_admin": "Admin",
    "deal_ask_currency": "💎 <b>Deal currency</b>\n\nTON or USDT. The buyer must top up this asset.",
    "deal_cur_ton": "TON",
    "deal_cur_usdt": "USDT",
    "deal_ask_secret": "🔑 Account/item credentials (login, password, email). The buyer sees them after the amount is frozen.",
    "deal_secret_hidden": "hidden until the deal starts",
    "deal_seller_only": "⚠️ Only the seller can create a deal.",
    "deposit_pick": "⬇️ <b>Which asset to deposit?</b>\n\nBoth go through the TON network to the escrow wallet.",
    "deposit_asset_ton": "TON",
    "deposit_asset_usdt": "USDT",
    "deposit_usdt_net": "Send USDT (jetton) on TON to:\n<code>{address}</code>\nUse the memo above as the comment.",
    "withdraw_pick": "⬆️ <b>Which asset to withdraw?</b>\n\nPayout is to a TON address only. Frozen deal funds cannot be withdrawn.",
    "withdraw_frozen": "⚠️ Available {have} {currency}, another {frozen} is frozen in a deal. Frozen coins cannot be withdrawn.",
    "admin_wallets": "Wallets",
    "admin_sessions": "Sessions",
    "admin_admins": "Admins",
    "admin_adm_add": "Add admin",
    "admin_cfg_ton_address": "TON escrow address",
    "admin_cfg_ton_mnemonic": "TON mnemonic",
    "admin_cfg_ton_api_key": "TON API key",
    "admin_cfg_usdt_master": "USDT jetton master",
    "admin_cfg_fragment_mnemonic": "Fragment mnemonic",
    "admin_cfg_fragment_wallet": "Fragment wallet",
    "admin_cfg_fragment_api_key": "Fragment API key",
    "admin_cfg_bank_api_id": "Bank api_id",
    "admin_cfg_bank_api_hash": "Bank api_hash",
    "admin_cfg_bank_session": "Bank session",
    "admin_cfg_bank_username": "Bank username",
    "admin_cfg_fragment_cookies": "Fragment cookies",
    "admin_cfg_ask": "New value for <b>{key}</b>. Send “-” to clear the field.",
    "admin_cfg_saved": "✅ Saved: {key}",
    "admin_cfg_reconnect": "Reconnected: {svc}",
    "admin_cfg_reconnect_fail": "⚠️ Saved, but {svc} did not reconnect. Check the value.",
    "admin_cfg_wallets_text": "💎 <b>Wallets</b>\n\n{lines}\n\nTap a field to replace its value.",
    "admin_cfg_sessions_text": "🔐 <b>Sessions</b>\n\n{lines}\n\nTap a field to replace its value.",
    "admin_cfg_admins_text": "👑 <b>Admins</b>\n\n{lines}\n\nAdd an ID or @username. You cannot remove the last admin.",
    "admin_adm_ask": "Send the Telegram ID or @username of the new admin.",
    "admin_adm_added": "✅ Admin {id} added.",
    "admin_adm_removed": "✅ Admin {id} removed.",
    "admin_adm_last": "⚠️ You cannot remove the last admin.",
    "admin_adm_self": "⚠️ You cannot remove yourself.",
    "admin_adm_exists": "⚠️ This user is already an admin.",
    "admin_cfg_value": "{title}\n<code>{value}</code>",
}

LOCALES = {"ru": RU, "en": EN}


def t(lang: str, msgid: str, /, **kwargs: Any) -> str:
    table = LOCALES.get(lang) or RU
    text = table.get(msgid) or RU.get(msgid) or msgid
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text
