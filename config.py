"""
Централизованная конфигурация бота.

Секреты и настройки читаются из переменных окружения / файла .env,
чтобы они не попадали в исходный код и в систему контроля версий.
"""

import os

from dotenv import load_dotenv

# Путь к корневой папке проекта (там лежит .env)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _required(name: str) -> str:
    """Возвращает обязательную переменную окружения или падает с понятной ошибкой."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Не задана обязательная переменная окружения {name}. "
            f"Скопируйте .env.example в .env и заполните её."
        )
    return value


TOKEN = _required("TELEGRAM_BOT_TOKEN")
MINI_APP_URL = _required("MINI_APP_URL")

# chat_id получателя утренней рассылки; 0 означает "рассылка отключена"
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0").strip() or 0)

# Часовой пояс для планировщика утренних новостей
TIMEZONE = os.getenv("TZ", "Europe/Moscow")
