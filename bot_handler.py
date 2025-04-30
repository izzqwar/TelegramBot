from telethon import TelegramClient, events
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Импорт из локальных модулей
from utils import load_groups, logger

class TelegramBot:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.commands: Dict[str, Dict[str, Any]] = {
            '/start': {
                'description': 'Начать работу с ботом',
                'handler': self.start_handler,
                'help': 'Показывает приветственное сообщение и список команд'
            },
            '/stats': {
                'description': 'Показать статистику групп',
                'handler': self.stats_handler,
                'help': 'Отображает количество групп и их статус'
            },
            '/help': {
                'description': 'Показать справку',
                'handler': self.help_handler,
                'help': 'Выводит подробную информацию о командах'
            }
        }

    async def setup_handlers(self):
        """Настройка обработчиков команд"""
        try:
            @self.client.on(events.NewMessage(pattern="(?i)/.*"))
            async def command_handler(event):
                """Общий обработчик команд"""
                command = event.message.message.lower().split()[0]
                logger.info(f"Получена команда: {command}")
                
                if command in self.commands:
                    try:
                        await self.commands[command]['handler'](event)
                        logger.info(f"Команда {command} обработана успешно")
                    except Exception as e:
                        error_msg = f"Ошибка при обработке команды {command}: {str(e)}"
                        logger.error(error_msg)
                        await event.reply(f"❌ {error_msg}")
                else:
                    await event.reply("❌ Неизвестная команда. Используйте /help для списка команд.")

            logger.info("Обработчики команд настроены успешно")
        except Exception as e:
            logger.error(f"Ошибка при настройке обработчиков: {str(e)}")
            raise

    async def start_handler(self, event):
        """Обработчик команды /start"""
        try:
            welcome_message = (
                "👋 Привет! Я бот для рассылки сообщений.\n\n"
                "Доступные команды:\n"
            )
            for cmd, info in self.commands.items():
                welcome_message += f"{cmd} - {info['description']}\n"
                
            await event.reply(welcome_message)
            logger.info("Отправлено приветственное сообщение")
        except Exception as e:
            logger.error(f"Ошибка в start_handler: {str(e)}")
            raise

    async def stats_handler(self, event):
        """Обработчик команды /stats"""
        try:
            groups = await load_groups()
            stats_message = "📊 Статистика:\n"
            
            if not groups:
                stats_message += "Список групп пуст!"
            else:
                valid_count = 0
                total_count = len(groups)
                
                for group in groups:
                    try:
                        await self.client.get_entity(int(group))
                        valid_count += 1
                    except:
                        continue
                
                stats_message += f"Всего групп: {total_count}\n"
                stats_message += f"Активных групп: {valid_count}\n"
                stats_message += f"Неактивных групп: {total_count - valid_count}"
            
            await event.reply(stats_message)
            logger.info("Отправлена статистика групп")
        except Exception as e:
            logger.error(f"Ошибка в stats_handler: {str(e)}")
            raise

    async def help_handler(self, event):
        """Обработчик команды /help"""
        try:
            help_message = "ℹ️ Справка по командам:\n\n"
            for cmd, info in self.commands.items():
                help_message += f"{cmd} - {info['help']}\n"
            
            await event.reply(help_message)
            logger.info("Отправлена справка по командам")
        except Exception as e:
            logger.error(f"Ошибка в help_handler: {str(e)}")
            raise

    async def run(self):
        """Запуск бота"""
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
            
            print("✅ Бот запущен и готов к работе!")
            print("📝 Отправьте команду /start в Telegram чате с ботом")
            
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {str(e)}")
            raise
        finally:
            await self.client.disconnect()
