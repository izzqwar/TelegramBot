import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Telegram API конфигурация
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

# Настройки бота
DEFAULT_DELAY = 5  # Базовая задержка между отправками сообщений
MIN_DELAY = 3      # Минимальная задержка
MAX_DELAY = 30     # Максимальная задержка

# Пути к файлам
GROUPS_FILE = "groups.txt"
SESSION_FILE = "session.session"
LOG_FILE = "bot.log"

# Настройки логирования
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Flask конфигурация
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 8080
