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

# Модуль валют (ЦБ РФ)
def get_forex_rates():
    try:
        url = "https://cbr-xml-daily.ru"
        response = requests.get(url, timeout=5)
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
                "💵 **Официальные курсы валют Центробанка:**\n\n"
                "📊 **К российскому рублю (RUB):**\n"
                f"🇺🇸 1 USD = {usd_rub:.2f} RUB\n"
                f"🇪🇺 1 EUR = {eur_rub:.2f} RUB\n"
                f"🇨🇳 10 CNY = {cny_rub * 10:.2f} RUB\n\n"
                "🇧🇾 **К белорусскому рублю (BYN):**\n"
                f"🇺🇸 1 USD = {usd_byn:.4f} BYN\n"
                f"🇪🇺 1 EUR = {eur_byn:.4f} BYN\n"
                f"🇨🇳 10 CNY = {cny_byn:.4f} BYN\n\n"
                "🏛 _Источник котировок: Банк России_"
            )
    except Exception as e:
        return "❌ Ошибка при запросе курсов валют."

# НОВЫЙ МОДУЛЬ: Получение цен акций с Московской Биржи (MOEX)
def get_moex_stocks():
    try:
        # Запрашиваем данные по рынку акций (акции Т+, режим главного окна)
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Список интересующих нас топ-компаний (тикеры на бирже)
        target_tickers = {
            "SBER": "🍏 Сбербанк",
            "GAZP": "🔥 Газпром",
            "LKOH": "⛽️ Лукойл",
            "YNDX": "📱 Яндекс",
            "NVTK": "❄️ Новатэк"
        }
        
        rows = data["securities"]["data"]
        result_text = "📈 **Котировки акций (Московская Биржа):**\n\n"
        
        found_any = False
        for row in rows:
            secid = row[0]       # Тикер (например, SBER)
            name = row[1]        # Краткое имя
            price = row[2]       # Цена закрытия/последняя цена (в рублях)
            
            if secid in target_tickers:
                found_any = True
                # Берем наше красивое название из словаря
                beautiful_name = target_tickers[secid]
                result_text += f"{beautiful_name} ({secid}) = **{price:.2f} RUB**\n"
                
        if found_any:
            result_text += "\n🔔 _Цены указаны за 1 акцию на момент закрытия или текущих торгов MOEX._"
            return result_text
        else:
            return "⚠️ Данные по акциям получены, но топ-тикеры не найдены."
            
    except Exception as e:
        print(f"Ошибка API MOEX: {e}")
        return "❌ Не удалось подключиться к серверам Московской Биржи. Проверьте сеть."

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
    bot.send_message(message.chat.id, "🤖 Я понимаю только команды из меню. Нажми кнопку <b>«Open»</b> для калькуляторов!", parse_mode="HTML")

if __name__ == '__main__':
    print("Инвестиционная Pro-версия с модулем акций запущена...")
    bot.infinity_polling()

   



