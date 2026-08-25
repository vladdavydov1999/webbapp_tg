# -*- coding: utf-8 -*-
"""
Финансовый Telegram-бот «Фин-Терминал Pro».

Возможности:
  * мгновенная сводка мировых рынков (курсы ЦБ РФ, золото, нефть, BTC);
  * запуск Mini App (сайт-визитка с финансовыми калькуляторами);
  * утренняя автоматическая рассылка по расписанию.

Секреты и настройки берутся из переменных окружения (см. config.py и .env.example).
Данные получаются через модуль market_data.py.
"""

import logging

import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from telebot import types

import config
from market_data import build_market_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(config.TOKEN, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Команды /start и /help
# ---------------------------------------------------------------------------
@bot.message_handler(commands=["start", "help"])
def send_welcome(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_app = types.KeyboardButton("📱 Открыть Фин-Терминал")
    btn_rates = types.KeyboardButton("📊 Мировые рынки")
    markup.add(btn_app, btn_rates)

    welcome_text = (
        "👋 <b>Приветствую в Фин-Терминале Pro!</b>\n\n"
        "Это международная финансовая экосистема прямо в Telegram.\n\n"
        "ℹ️ Кнопка «📊 Мировые рынки» — мгновенный срез курсов ЦБ РФ, "
        "золота, нефти и Bitcoin.\n"
        "Кнопка «📱 Открыть Фин-Терминал» — запуск Mini App с финансовыми калькуляторами."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


# ---------------------------------------------------------------------------
# Обработка кнопок меню
# ---------------------------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_menu_buttons(message: telebot.types.Message):
    text = message.text or ""

    if text == "📊 Мировые рынки":
        report = build_market_report()
        bot.send_message(message.chat.id, report, parse_mode="HTML")
        return

    if text == "📱 Открыть Фин-Терминал":
        inline_markup = types.InlineKeyboardMarkup()
        btn_launch = types.InlineKeyboardButton(
            text="🚀 Запустить Приложение",
            web_app=types.WebAppInfo(url=config.MINI_APP_URL),
        )
        inline_markup.add(btn_launch)
        bot.send_message(
            message.chat.id,
            "⬇️ Нажми на кнопку ниже, чтобы развернуть инвест-терминал на весь экран:",
            reply_markup=inline_markup,
        )
        return

    bot.reply_to(
        message,
        "Используйте кнопки меню ниже или команду /start.",
    )


# ---------------------------------------------------------------------------
# Утренняя рассылка
# ---------------------------------------------------------------------------
def send_morning_investment_news():
    if not config.ADMIN_CHAT_ID:
        logger.info("Утренняя рассылка отключена: ADMIN_CHAT_ID не задан.")
        return

    report_data = build_market_report()
    morning_report = (
        "☀️ <b>УТРЕННИЙ ФИНАНСОВЫЙ ОТЧЁТ</b>\n"
        f"📅 <i>Доставлено автоматически</i>\n\n"
        f"{report_data}\n\n"
        "🎯 <b>План на день:</b> Не совершайте эмоциональных сделок. "
        "Рынок вознаграждает терпеливых!"
    )

    try:
        bot.send_message(config.ADMIN_CHAT_ID, morning_report, parse_mode="HTML")
        logger.info("Утренний отчёт отправлен.")
    except Exception as exc:  # noqa: BLE001
        logger.error("Ошибка утренней рассылки: %s", exc)


# ---------------------------------------------------------------------------
# Планировщик и запуск
# ---------------------------------------------------------------------------
scheduler = BackgroundScheduler(timezone=config.TIMEZONE)
scheduler.add_job(send_morning_investment_news, "cron", hour=9, minute=0)
scheduler.start()


def main() -> None:
    logger.info("🚀 Бот «Фин-Терминал Pro» запущен.")
    logger.info("Mini App URL: %s", config.MINI_APP_URL)
    bot.infinity_polling()


if __name__ == "__main__":
    main()
