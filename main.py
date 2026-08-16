import telebot
import time
import requests  

TOKEN = '8806371020:AAEWYJuSncBvdEGksANUfZEyx1sUdp6QR3c'
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

# Функция получения реальных курсов валют через бесплатное API
def get_forex_rates():
    try:
        # Используем открытое API биржевых курсов к доллару США (USD)
        url = "https://er-api.com"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data["result"] == "success":
            rates = data["rates"]
            # Считаем обратные курсы доллара к другим валютам
            usd_rub = rates.get("RUB", 0)
            usd_eur = rates.get("EUR", 0)
            usd_cny = rates.get("CNY", 0)
            
            # Считаем кросс-курсы (например, сколько рублей в одном евро)
            eur_rub = usd_rub / usd_eur if usd_eur else 0
            cny_rub = usd_rub / usd_cny if usd_cny else 0

            text = (
                "💵 **Официальные мировые валюты:**\n\n"
                f"🇺🇸 1 USD = {usd_rub:.2f} RUB\n"
                f"🇪🇺 1 EUR = {eur_rub:.2f} RUB\n"
                f"🇨🇳 1 CNY = {cny_rub:.2f} RUB\n\n"
                "📊 *Данные обновляются автоматически в режиме реального времени.*"
            )
            return text
        else:
            return "⚠️ Не удалось получить свежие данные от биржи. Попробуйте позже."
    except Exception as e:
        print(f"Ошибка API: {e}")
        return "❌ Ошибка при запросе котировок. Проверьте подключение к интернету."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spam(message.chat.id): return
    welcome_text = (
        "👋 <b>Привет! Я твой личный Финансовый Ассистент Pro.</b>\n\n"
        "🚀 <b>Как пользоваться ботом?</b>\n"
        "Нажми кнопку <b>«Open»</b> в углу экрана, чтобы открыть визуальный калькулятор!\n\n"
        "📖 <b>Команды финансовой аналитики:</b>\n"
        "/rates — Актуальные курсы мировых валют\n"
        "/snowball — Стратегия закрытия долгов\n"
        "/compound — Магия сложного процента\n"
        "/safety_net — Расчет финансовой подушки"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")

# Новая профессиональная команда для отслеживания валютных рынков
@bot.message_handler(commands=['rates'])
def show_rates(message):
    if is_spam(message.chat.id): return
    # Отправляем сообщение о загрузке, так как запрос к бирже может занять 1-2 секунды
    waiting_msg = bot.send_message(message.chat.id, "🔄 Запрашиваю свежие котировки с биржи...")
    
    # Получаем текст с курсами
    rates_text = get_forex_rates()
    
    # Удаляем сообщение о загрузке и присылаем финальный результат
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, rates_text, parse_mode="Markdown")

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
    print("Профессиональная версия бота с модулем валют запущена...")
    bot.infinity_polling()

 






