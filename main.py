import telebot
import time
import requests

TOKEN = 'TOKEN'
bot = telebot.TeleBot(TOKEN)

last_message_time = {}


def is_spam(chat_id):
    current_time = time.time()
    if chat_id not in last_message_time:
        last_message_time[chat_id] = current_time
        return False
    time_passed = current_time - last_message_time[chat_id]
    last_message_time[chat_id] = current_time
    if time_passed < 1.5:
        return True
    return False


# Модуль валют (ЦБ РФ)
# Модернизированный модуль валют с защитой от региональных сбоев API
def get_forex_rates():
    try:
        # Используем быстрое зеркало официального API Центробанка РФ (ЦБ РФ)
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)

        # Если шлюз вернул ошибку, не выводим недостоверные цифры
        if response.status_code != 200:
            return "⚠️ Сервер Банка России временно недоступен. Пожалуйста, попробуйте позже."

        data = response.json()

        if "Valute" in data:
            valute = data["Valute"]

            # Строго первоисточник: извлекаем курсы к российскому рублю (RUB)
            usd_rub = valute["USD"]["Value"]
            eur_rub = valute["EUR"]["Value"]
            cny_rub = valute["CNY"]["Value"] / valute["CNY"]["Nominal"]  # с учетом номинала
            byn_rub = valute["BYN"]["Value"]  # курс 1 белорусского рубля к российскому

            # Рассчитываем кросс-курсы к белорусскому рублю (BYN) на основе точных пропорций ЦБ РФ
            usd_byn = usd_rub / byn_rub if byn_rub else 0
            eur_byn = eur_rub / byn_rub if byn_rub else 0
            cny_byn = (cny_rub * 10) / byn_rub if byn_rub else 0

            # Формируем отчет, где на первом месте СТРОГО данные к RUB
            text = (
                "💵 **Официальные курсы валют Центробанка РФ:**\n\n"
                "📊 **К российскому рублю (RUB):**\n"
                f"🇺🇸 1 USD = {usd_rub:.2f} RUB\n"
                f"🇪🇺 1 EUR = {eur_rub:.2f} RUB\n"
                f"🇨🇳 10 CNY = {cny_rub * 10:.2f} RUB\n\n"
                "🇧🇾 **К белорусскому рублю (BYN):**\n"
                f"🇺🇸 1 USD = {usd_byn:.4f} BYN\n"
                f"🇪🇺 1 EUR = {eur_byn:.4f} BYN\n"
                f"🇨🇳 10 CNY = {cny_byn:.4f} BYN\n\n"
                "🏛 _Источник данных: Центральный Банк Российской Федерации_"
            )
            return text
        else:
            return "⚠️ Ошибка парсинга: структура ответа ЦБ РФ изменилась."

    except requests.exceptions.RequestException as e:
        # Никакого обмана: в случае блокировки IP честно сообщаем о сетевой проблеме
        print(f"Сетевой сбой ЦБ РФ: {e}")
        return (
            "❌ **Ошибка соединения с сервером ЦБ РФ**\n\n"
            "Запрос заблокирован защитными системами или сетевым брандмауэром. "
            "Попробуйте запустить скрипт через VPN с российским IP-адресом для прямого доступа к серверам Банка России."
        )


# НОВЫЙ МОДУЛЬ: Получение цен акций с Московской Биржи (MOEX)
# Модернизированный модуль акций с защитой от региональных блокировок
def get_moex_stocks():
    try:
        # Официальный шлюз ISS Московской Биржи (Рынок акций, режим Т+)
        url = "https://moex.com"

        # Устанавливаем жесткий тайм-аут 5 секунд, чтобы бот не зависал при плохом соединении
        response = requests.get(url, timeout=5)

        # Если биржа вернула ошибку сервера или Cloudflare заблокировал запрос
        if response.status_code != 200:
            return "⚠️ Торговый сервер Московской Биржи временно недоступен. Пожалуйста, попробуйте позже."

        data = response.json()
        rows = data["securities"]["data"]

        # Словарь топ-компаний, котировки которых мы ищем
        target_tickers = {
            "SBER": "🍏 Сбербанк",
            "GAZP": "🔥 Газпром",
            "LKOH": "⛽️ Лукойл",
            "YNDX": "📱 Яндекс",
            "NVTK": "❄️ Новатэк"
        }

        result_text = "📈 **Актуальные котировки акций (MOEX):**\n\n"
        found_any = False

        for row in rows:
            secid = row[0]  # Код бумаги (Тикер)
            price = row[1]  # Цена последней сделки / закрытия

            if secid in target_tickers and price is not None:
                found_any = True
                beautiful_name = target_tickers[secid]
                result_text += f"{beautiful_name} ({secid}) = **{price:.2f} RUB**\n"

        if found_any:
            result_text += "\n🔔 _Источник данных: Информационно-статистический сервер ММВБ_"
            return result_text
        else:
            return "⚠️ Ошибка парсинга: структура данных торговой сессии MOEX изменилась."

    except requests.exceptions.RequestException as e:
        # Честный отказ: сообщаем инвестору о сетевой блокировке без выдуманных цен
        print(f"Сетевая блокировка MOEX ISS: {e}")
        return (
            "❌ **Ошибка соединения с Московской Биржей**\n\n"
            "Торговая система MOEX отклонила автоматический запрос от вашего сервера. "
            "Для получения точных биржевых котировок в реальном времени запустите скрипт "
            "с использованием прокси или VPN с российским IP-адресом."
        )


# Честный модуль государственных облигаций (ОФЗ) на базе API Мосбиржи
def get_moex_bonds():
    try:
        # Официальный шлюз ISS Московской Биржи (Рынок гособлигаций, режим Т+, плата в рублях)
        url = "https://moex.com"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return "⚠️ Сервер долгового рынка Московской Биржи временно недоступен. Попробуйте позже."

        data = response.json()
        rows = data["securities"]["data"]

        # Список популярных ОФЗ, которые мы отслеживаем
        target_bonds = {
            "SU26238RMFS4": "🏛 ОФЗ 26238 (Долгосрочная)",
            "SU26244RMFS2": "🏛 ОФЗ 26244 (Среднесрочная)",
            "SU26243RMFS4": "🏛 ОФЗ 26243 (Краткосрочная)"
        }

        result_text = "🎫 **Актуальная доходность гособлигаций (ОФЗ):**\n\n"
        found_any = False

        for row in rows:
            secid = row  # ISIN / Код облигации (например, SU26238RMFS4)
            name = row  # Краткое имя на бирже
            price = row  # Цена в % от номинала (номинал обычно 1000 RUB)
            bond_yield = row  # Эффективная доходность к погашению в %

            if secid in target_bonds:
                found_any = True
                beautiful_name = target_bonds[secid]

                # Защита на случай, если в текущую секунду торгов цена или доходность временно пустые
                p_str = f"{price:.2f}%" if price is not None else "нет данных"
                y_str = f"{bond_yield:.2f}%" if bond_yield is not None else "нет данных"

                result_text += f"**{beautiful_name}**\n"
                result_text += f"▪️ Текущая цена: {p_str} от номинала\n"
                result_text += f"▪️ Доходность к погашению: **{y_str}**\n\n"

        if found_any:
            result_text += "💡 _Инвестор фиксирует указанную доходность на весь срок, если купит облигацию сейчас и продержит её до даты погашения._"
            return result_text
        else:
            return "⚠️ Ошибка парсинга: целевые выпуски ОФЗ не найдены в текущей сессии."

    except requests.exceptions.RequestException as e:
        print(f"Сетевая блокировка MOEX Bonds: {e}")
        return (
            "❌ **Ошибка соединения с долговым рынком MOEX**\n\n"
            "Запрос к секции облигаций отклонен сетевым брандмауэром. "
            "Используйте прокси или VPN с российским IP-адресом для получения точных расчетов доходности."
        )


# Честный модуль государственных облигаций (ОФЗ) на базе API Мосбиржи
def get_moex_bonds():
    try:
        # Официальный шлюз ISS Московской Биржи (Рынок гособлигаций, режим Т+, плата в рублях)
        url = "https://moex.com"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return "⚠️ Сервер долгового рынка Московской Биржи временно недоступен. Попробуйте позже."

        data = response.json()
        rows = data["securities"]["data"]

        # Список популярных ОФЗ, которые мы отслеживаем
        target_bonds = {
            "SU26238RMFS4": "🏛 ОФЗ 26238 (Долгосрочная)",
            "SU26244RMFS2": "🏛 ОФЗ 26244 (Среднесрочная)",
            "SU26243RMFS4": "🏛 ОФЗ 26243 (Краткосрочная)"
        }

        result_text = "🎫 **Актуальная доходность гособлигаций (ОФЗ):**\n\n"
        found_any = False

        for row in rows:
            secid = row  # ISIN / Код облигации (например, SU26238RMFS4)
            name = row  # Краткое имя на бирже
            price = row  # Цена в % от номинала (номинал обычно 1000 RUB)
            bond_yield = row  # Эффективная доходность к погашению в %

            if secid in target_bonds:
                found_any = True
                beautiful_name = target_bonds[secid]

                # Защита на случай, если в текущую секунду торгов цена или доходность временно пустые
                p_str = f"{price:.2f}%" if price is not None else "нет данных"
                y_str = f"{bond_yield:.2f}%" if bond_yield is not None else "нет данных"

                result_text += f"**{beautiful_name}**\n"
                result_text += f"▪️ Текущая цена: {p_str} от номинала\n"
                result_text += f"▪️ Доходность к погашению: **{y_str}**\n\n"

        if found_any:
            result_text += "💡 _Инвестор фиксирует указанную доходность на весь срок, если купит облигацию сейчас и продержит её до даты погашения._"
            return result_text
        else:
            return "⚠️ Ошибка парсинга: целевые выпуски ОФЗ не найдены в текущей сессии."

    except requests.exceptions.RequestException as e:
        print(f"Сетевая блокировка MOEX Bonds: {e}")
        return (
            "❌ **Ошибка соединения с долговым рынком MOEX**\n\n"
            "Запрос к секции облигаций отклонен сетевым брандмауэром. "
            "Используйте прокси или VPN с российским IP-адресом для получения точных расчетов доходности."
        )


# Обработчик команды /bonds
@bot.message_handler(commands=['bonds'])
def show_bonds(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Запрашиваю данные долгового рынка ММВБ...")
    bonds_text = get_moex_bonds()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, bonds_text, parse_mode="Markdown")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spam(message.chat.id): return
    welcome_text = (
        "👋 <b>Привет! Я твой личный Финансовый Ассистент Pro.</b>\n\n"
        "🚀 <b>Как пользоваться ботом?</b>\n"
        "Нажми кнопку <b>«Open»</b> в углу экрана, чтобы открыть визуальный калькулятор!\n\n"
        "📖 <b>Команды финансовой аналитики:</b>\n"
        "/rates — Актуальные курсы мировых валют\n"
        "/stocks — Котировки акций (Топ компаний)\n"
        "/snowball — Стратегия закрытия долгов\n"
        "/compound — Магия сложного процента\n"
        "/safety_net — Расчет финансовой подушки"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")


@bot.message_handler(commands=['rates'])
def show_rates(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Запрашиваю официальные данные у Банка России...")
    rates_text = get_forex_rates()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, rates_text, parse_mode="Markdown")


# НОВАЯ КОМАНДА: Вывод акций
@bot.message_handler(commands=['stocks'])
def show_stocks(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Подключаюсь к торговой системе MOEX...")
    stocks_text = get_moex_stocks()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, stocks_text, parse_mode="Markdown")


@bot.message_handler(commands=['snowball'])
def info_snowball(message):
    if is_spam(message.chat.id): return
    text = "📉 **Метод 'Снежного кома'**: отсортируй долги от меньшего к большему и направляй ускоритель на первый."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['compound'])
def info_compound(message):
    if is_spam(message.chat.id): return
    text = "📈 **Сложный процент**: начисление процентов на проценты. Время — твой главный союзник."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['safety_net'])
def info_safety(message):
    if is_spam(message.chat.id): return
    text = "💰 **Подушка безопасности**: сумма обязательных расходов за 3-6 месяцев, хранящаяся на накопительном счете."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id,
                     "🤖 Я понимаю только команды из меню. Нажми кнопку <b>«Open»</b> для калькуляторов!",
                     parse_mode="HTML")


if __name__ == '__main__':
    print("Инвестиционная Pro-версия с модулем акций запущена...")
    bot.infinity_polling()



   
   

  
