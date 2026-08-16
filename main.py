import telebot
import time
import requests

TOKEN = 'ТВОЙ_ТОКЕН_ИЗ_BOTFATHER'
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

# ================= ФИНАНСОВЫЕ МОДУЛИ API =================

# 1. Честные Валюты ЦБ РФ
def get_forex_rates():
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "⚠️ Сервер Банка России временно недоступен. Пожалуйста, попробуйте позже."
            
        data = response.json()
        if "Valute" in data:
            valute = data["Valute"]
            usd_rub = valute["USD"]["Value"]
            eur_rub = valute["EUR"]["Value"]
            cny_rub = valute["CNY"]["Value"] / valute["CNY"]["Nominal"]
            byn_rub = valute["BYN"]["Value"]
            
            usd_byn = usd_rub / byn_rub if byn_rub else 0
            eur_byn = eur_rub / byn_rub if byn_rub else 0
            cny_byn = (cny_rub * 10) / byn_rub if byn_rub else 0
            
            return (
                "💵 **Официальные курсы валют Центробанка РФ:**\n\n"
                "📊 **К российскому рублю (RUB):**\n"
                f"🇺🇸 1 USD = {usd_rub:.2f} RUB\n"
                f"🇪🇺 1 EUR = {eur_rub:.2f} RUB\n"
                f"🇨🇳 10 CNY = {cny_rub * 10:.2f} RUB\n\n"
                "🇧🇾 **К белорусскому рублю (BYN):**\n"
                f"🇺🇸 1 USD = {usd_byn:.4f} BYN\n"
                f"🇪🇺 1 EUR = {eur_byn:.4f} BYN\n"
                f"🇨🇳 10 CNY = {cny_byn:.4f} BYN\n\n"
                "🏛 _Источник данных: Центральный Банк РФ_"
            )
    except Exception as e:
        print(f"Сбой Валют: {e}")
    return "❌ **Ошибка соединения с сервером ЦБ РФ.** Не удалось загрузить свежие курсы."

# 2. Честные Акции MOEX
def get_moex_stocks():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "⚠️ Торговый сервер Московской Биржи временно недоступен."
            
        data = response.json()
        rows = data["securities"]["data"]
        
        target_tickers = {
            "SBER": "🍏 Сбербанк", "GAZP": "🔥 Газпром", "LKOH": "⛽️ Лукойл", "YNDX": "📱 Яндекс", "NVTK": "❄️ Новатэк"
        }
        
        result_text = "📈 **Актуальные котировки акций (MOEX):**\n\n"
        found_any = False
        for row in rows:
            secid, price = row[0], row[1]
            if secid in target_tickers and price is not None:
                found_any = True
                result_text += f"{target_tickers[secid]} ({secid}) = **{price:.2f} RUB**\n"
                
        if found_any:
            result_text += "\n🔔 _Источник данных: Московская Биржа_"
            return result_text
    except Exception as e:
        print(f"Сбой Акций: {e}")
    return "❌ **Ошибка соединения с Московской Биржей.** Запрос цен акций отклонен сетью."

# 3. Честные Облигации MOEX (ОФЗ)
def get_moex_bonds():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "⚠️ Сервер долгового рынка Московской Биржи недоступен."
            
        data = response.json()
        rows = data["securities"]["data"]
        
        target_bonds = {
            "SU26238RMFS4": "🏛 ОФЗ 26238 (Долгосрочная)",
            "SU26244RMFS2": "🏛 ОФЗ 26244 (Среднесрочная)",
            "SU26243RMFS4": "🏛 ОФЗ 26243 (Краткосрочная)"
        }
        
        result_text = "🎫 **Актуальная доходность гособлигаций (ОФЗ):**\n\n"
        found_any = False
        for row in rows:
            secid, name, price, bond_yield = row[0], row[1], row[2], row[3]
            if secid in target_bonds:
                found_any = True
                p_str = f"{price:.2f}%" if price is not None else "нет данных"
                y_str = f"{bond_yield:.2f}%" if bond_yield is not None else "нет данных"
                result_text += f"**{target_bonds[secid]}**\n▪️ Цена: {p_str} от номинала\n▪️ Доходность к погашению: **{y_str}**\n\n"
                
        if found_any:
            result_text += "💡 _Инвестор фиксирует указанную доходность на весь срок, если продержит ОФЗ до даты погашения._"
            return result_text
    except Exception as e:
        print(f"Сбой Облигаций: {e}")
    return "❌ **Ошибка соединения с долговым рынком MOEX.** Доступ к секции облигаций ограничен."


# ================= ОБРАБОТЧИКИ КОМАНД (ХЕНДЛЕРЫ) =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spam(message.chat.id): return
    welcome_text = (
        "👋 <b>Привет! Я твой личный Финансовый Ассистент Pro.</b>\n\n"
        "🚀 Нажми кнопку <b>«Open»</b> в углу экрана, чтобы открыть визуальный калькулятор!\n\n"
        "📖 <b>Команды финансовой аналитики:</b>\n"
        "/rates — Курсы мировых валют ЦБ\n"
        "/stocks — Котировки акций (MOEX)\n"
        "/bonds — Доходность гособлигаций (ОФЗ)\n"
        "/snowball — Стратегия закрытия долгов\n"
        "/compound — Магия сложного процента\n"
        "/safety_net — Финансовая подушка"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")

@bot.message_handler(commands=['rates'])
def show_rates(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Запрашиваю данные у Банка России...")
    text = get_forex_rates()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['stocks'])
def show_stocks(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Подключаюсь к торговой системе MOEX...")
    text = get_moex_stocks()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['bonds'])
def show_bonds(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Запрашиваю данные долгового рынка ММВБ...")
    text = get_moex_bonds()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['snowball'])
def info_snowball(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "📉 **Метод Снежного кома**: гаси мелкие долги первыми для мотивации.", parse_mode="Markdown")

@bot.message_handler(commands=['compound'])
def info_compound(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "📈 **Сложный процент**: проценты на проценты формируют экспоненциальный рост капитала.", parse_mode="Markdown")

@bot.message_handler(commands=['safety_net'])
def info_safety(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "💰 **Подушка безопасности**: резерв на 3-6 месяцев обязательных расходов.", parse_mode="Markdown")

# КРИТИЧЕСКИ ВАЖНО: Универсальная заглушка на текст ВСЕГДА В САМОМ НИЗУ ХЕНДЛЕРОВ!
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "🤖 Я понимаю только команды из меню. Нажми кнопку <b>«Open»</b> для калькуляторов!", parse_mode="HTML")

if __name__ == '__main__':
    print("Инвестиционная Pro-версия со всеми шлюзами успешно запущена...")
    bot.infinity_polling()


   
   

  
