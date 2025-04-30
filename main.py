import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from threading import Thread
from datetime import datetime
import logging
from typing import Optional

# Импорт собственных модулей
from config import (
    API_ID, API_HASH, SESSION_STRING,
    FLASK_HOST, FLASK_PORT
)
from utils import (
    validate_group_id, load_groups, save_groups,
    calculate_delay, clean_invalid_groups, logger
)
from bot_handler import TelegramBot

# Flask для поддержания активности
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Mailer Active!"

def run_flask():
    app.run(host=FLASK_HOST, port=FLASK_PORT)

def keep_alive():
    Thread(target=run_flask).start()

class TelegramMailer:
    def __init__(self):
        self.setup_client()
        
    def setup_client(self):
        """Инициализация клиента Telegram"""
        if SESSION_STRING:
            try:
                self.client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
                logger.info("Клиент инициализирован с SESSION_STRING")
            except Exception as e:
                logger.error(f"Ошибка с SESSION_STRING: {e}")
                self.client = TelegramClient("session", API_ID, API_HASH)
        else:
            self.client = TelegramClient("session", API_ID, API_HASH)
            logger.info("Клиент инициализирован с локальной сессией")

    async def view_stats(self):
        """Просмотр статистики групп"""
        try:
            groups = await load_groups()
            stats = f"\nСтатистика:\n"
            stats += f"Всего групп: {len(groups)}\n"
            
            if groups:
                stats += "\nПервые 5 групп:\n"
                for i, group in enumerate(groups[:5], 1):
                    is_valid, message = await validate_group_id(self.client, group)
                    status = "✅" if is_valid else "❌"
                    stats += f"{i}. {group} {status}\n"
            
            print(stats)
            return stats
        except Exception as e:
            logger.error(f"Ошибка при просмотре статистики: {e}")
            return "Ошибка при получении статистики"

    async def manage_groups(self):
        """Управление списком групп"""
        while True:
            print("\nУправление группами:")
            print("1. Добавить группу")
            print("2. Удалить группу")
            print("3. Просмотреть все группы")
            print("4. Очистить невалидные группы")
            print("5. Назад")
            
            choice = input("Выберите действие: ")
            
            if choice == "1":
                group_id = input("Введите ID группы: ")
                is_valid, message = await validate_group_id(self.client, group_id)
                
                if is_valid:
                    groups = await load_groups()
                    if group_id not in groups:
                        groups.append(group_id)
                        await save_groups(groups)
                        print(f"✅ Группа добавлена! {message}")
                    else:
                        print("⚠️ Группа уже существует в списке")
                else:
                    print(f"❌ Ошибка: {message}")
            
            elif choice == "2":
                groups = await load_groups()
                if not groups:
                    print("Список групп пуст!")
                    continue
                    
                print("\nСписок групп:")
                for i, group in enumerate(groups, 1):
                    print(f"{i}. {group}")
                
                try:
                    idx = int(input("Введите номер группы для удаления: ")) - 1
                    if 0 <= idx < len(groups):
                        removed_group = groups.pop(idx)
                        await save_groups(groups)
                        print(f"✅ Группа {removed_group} удалена!")
                    else:
                        print("❌ Неверный номер!")
                except ValueError:
                    print("❌ Введите корректный номер!")
            
            elif choice == "3":
                groups = await load_groups()
                if not groups:
                    print("Список групп пуст!")
                else:
                    print("\nСписок всех групп:")
                    for i, group in enumerate(groups, 1):
                        is_valid, message = await validate_group_id(self.client, group)
                        status = "✅" if is_valid else "❌"
                        print(f"{i}. {group} {status}")
            
            elif choice == "4":
                valid_count, removed_count = await clean_invalid_groups(self.client)
                print(f"\nОчистка завершена:")
                print(f"✅ Валидных групп: {valid_count}")
                print(f"❌ Удалено групп: {removed_count}")
            
            elif choice == "5":
                break

    async def send_messages(self):
        """Отправка сообщений"""
        try:
            groups = await load_groups()
            if not groups:
                print("❌ Список групп пуст!")
                return
                
            print(f"📋 Загружено {len(groups)} групп")
            message = input("Введите сообщение для отправки: ")
            
            print("🚀 Начинаем отправку...")
            async with self.client:
                print("🔄 Подключаемся к Telegram...")
                
                if not await self.client.is_user_authorized():
                    print("❌ Ошибка: Клиент не авторизован! Запустите режим 1 для авторизации.")
                    return
                    
                print("✅ Клиент авторизован успешно")
                print(f"📝 Начинаем отправку сообщения: {message[:30]}...")
                
                success = 0
                failed = 0
                total = len(groups)
                delay = calculate_delay(total)
                
                for idx, group_id in enumerate(groups, 1):
                    try:
                        print(f"📨 Отправка {idx}/{total} в группу {group_id}...")
                        await self.client.send_message(int(group_id), message)
                        success += 1
                        print(f"✅ Успешно отправлено в {group_id}")
                        
                        if idx < total:  # Не ждем после последней отправки
                            print(f"⏳ Ожидание {delay} секунд...")
                            await asyncio.sleep(delay)
                            
                    except ValueError as ve:
                        failed += 1
                        print(f"❌ Ошибка формата ID ({group_id}): {str(ve)}")
                        logger.error(f"Ошибка формата ID для группы {group_id}: {str(ve)}")
                        
                    except Exception as e:
                        failed += 1
                        print(f"❌ Ошибка отправки ({group_id}): {str(e)}")
                        logger.error(f"Ошибка отправки в группу {group_id}: {str(e)}")
                
                print(f"\n📊 Результат:")
                print(f"✅ Успешно: {success}/{total}")
                print(f"❌ Ошибок: {failed}/{total}")
                
        except Exception as e:
            logger.error(f"Общая ошибка при отправке сообщений: {str(e)}")
            print(f"❌ Произошла ошибка: {str(e)}")

    async def auth(self) -> Optional[str]:
        """Авторизация"""
        try:
            async with self.client:
                await self.client.start()
                if await self.client.is_user_authorized():
                    session_string = StringSession.save(self.client.session)
                    print(f"\n🔑 **SESSION_STRING для .env:**\n{session_string}\n")
                    await self.client.send_message("me", "✅ Авторизация успешна!")
                    return session_string
                else:
                    print("❌ Ошибка авторизации!")
                    return None
        except Exception as e:
            logger.error(f"Ошибка при авторизации: {str(e)}")
            print(f"❌ Ошибка: {str(e)}")
            return None

async def main():
    mailer = TelegramMailer()
    keep_alive()
    
    while True:
        print("\nМеню управления:")
        print("1. Авторизация")
        print("2. Отправить рассылку")
        print("3. Просмотр статистики")
        print("4. Управление группами")
        print("5. Запустить бота")
        print("6. Выход")
        
        mode = input("\nВыберите действие: ")
        
        try:
            if mode == "1":
                session = await mailer.auth()
                if session:
                    print(f"✅ Скопируйте это в Secrets → SESSION_STRING:\n{session}")
            elif mode == "2":
                await mailer.send_messages()
            elif mode == "3":
                await mailer.view_stats()
            elif mode == "4":
                await mailer.manage_groups()
            elif mode == "5":
                print("🚀 Запускаем бота...")
                try:
                    bot = TelegramBot(mailer.client)
                    await bot.run()
                except KeyboardInterrupt:
                    print("\n⏹️ Бот остановлен")
            elif mode == "6":
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор!")
        except Exception as e:
            logger.error(f"Ошибка в главном меню: {str(e)}")
            print(f"❌ Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        print(f"❌ Критическая ошибка: {str(e)}")
