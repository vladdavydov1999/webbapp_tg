"""
Централизованная конфигурация бота.

Значения задаются как обычный Python-код: ИМЯ = "значение".
Если вы создадите файл .env (см. .env.example), его значения перекроют эти.
Внимание: сюда НЕ нужно вставлять строки из .env вида "KEY=value" —
это не Python, это синтаксис другого файла.
"""

import os

from dotenv import load_dotenv

# Путь к корневой папке проекта (там лежит .env)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _env(name: str, default: str) -> str:
    """Значение из переменной окружения/.env или значение по умолчанию."""
    return os.getenv(name, default).strip()


# --- Значения по умолчанию. Можно перекрыть через файл .env. ---------------
TOKEN = _env(
    "TELEGRAM_BOT_TOKEN",
)

MINI_APP_URL = _env(
    "MINI_APP_URL",
)

# chat_id получателя утренней рассылки; 0 = рассылка отключена
ADMIN_CHAT_ID = int(_env("ADMIN_CHAT_ID", "") or 0)

# Часовой пояс утреннего отчёта. Используем BOT_TIMEZONE, а не TZ,
# чтобы PyCharm/ОС не подменяли значение системным TZ.
TIMEZONE = _env("BOT_TIMEZONE", "Europe/Moscow") or "Europe/Moscow"
