
from telethon import TelegramClient, events
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, client):
        self.client = client
        
    async def setup_handlers(self):
        @self.client.on(events.NewMessage(pattern="(?i)/.*"))
        async def command_handler(event):
            command = event.message.message.lower()
            logger.info(f"Получена команда: {command}")
            
            if command.startswith('/start'):
                await event.reply("👋 Привет! Я бот для рассылки сообщений.\n\nДоступные команды:\n/start - Показать это сообщение\n/stats - Показать статистику\n/help - Помощь")
            elif command.startswith('/stats'):
                try:
                    with open("groups.txt", "r") as f:
                        groups = [line.strip() for line in f if line.strip()]
                    await event.reply(f"📊 Статистика:\nВсего групп: {len(groups)}")
                except FileNotFoundError:
                    await event.reply("❌ Файл groups.txt не найден!")
            elif command.startswith('/help'):
                await event.reply("ℹ️ Справка по командам:\n\n/start - Начать работу с ботом\n/stats - Показать статистику групп\n/help - Показать эту справку")
            
            logger.info("Команда обработана успешно")
            
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            logger.info("Получена команда /start")
            try:
                await event.reply("👋 Привет! Я бот для рассылки сообщений.\n\nДоступные команды:\n/start - Показать это сообщение\n/stats - Показать статистику\n/help - Помощь")
                logger.info("Ответ на /start отправлен успешно")
            except Exception as e:
                logger.error(f"Ошибка при ответе на /start: {e}")
            
        @self.client.on(events.NewMessage(pattern='/stats'))
        async def stats_handler(event):
            logger.info("Получена команда /stats")
            try:
                with open("groups.txt", "r") as f:
                    groups = [line.strip() for line in f if line.strip()]
                await event.reply(f"📊 Статистика:\nВсего групп: {len(groups)}")
                logger.info("Статистика отправлена успешно")
            except FileNotFoundError:
                logger.error("Файл groups.txt не найден")
                await event.reply("❌ Файл groups.txt не найден!")
                
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            logger.info("Получена команда /help")
            try:
                await event.reply("ℹ️ Справка по командам:\n\n/start - Начать работу с ботом\n/stats - Показать статистику групп\n/help - Показать эту справку")
                logger.info("Справка отправлена успешно")
            except Exception as e:
                logger.error(f"Ошибка при отправке справки: {e}")
    
    async def run(self):
        try:
            logger.info("Подключение к Telegram...")
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("Ошибка: Бот не авторизован!")
                return
            
            me = await self.client.get_me()
            logger.info(f"Бот авторизован как: {me.username} (ID: {me.id})")
            
            await self.setup_handlers()
            logger.info("✅ Бот запущен и готов к работе!")
            
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {str(e)}")
        finally:
            await self.client.disconnect()
