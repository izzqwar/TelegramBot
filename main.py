import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread
from config import (
    API_ID, API_HASH, SESSION_STRING,
    FLASK_HOST, FLASK_PORT
)
from utils import (
    validate_group_id, load_groups, save_groups,
    calculate_delay, clean_invalid_groups, logger
)
from bot_handler import TelegramBot

# Инициализация клиента
if SESSION_STRING:
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        logger.info("Используется STRING_SESSION")
    except Exception as e:
        logger.error(f"Ошибка с SESSION_STRING: {e}")
        client = TelegramClient("session", API_ID, API_HASH)
        logger.info("Используется локальная сессия")
else:
    client = TelegramClient("session", API_ID, API_HASH)
    logger.info("Используется локальная сессия")

# Flask для поддержания активности
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Mailer Active!"

def run_flask():
    app.run(host=FLASK_HOST, port=FLASK_PORT)

def keep_alive():
    Thread(target=run_flask, daemon=True).start()
    logger.info(f"Flask сервер запущен на порту {FLASK_PORT}")

async def view_stats():
    """Просмотр статистики групп"""
    try:
        groups = await load_groups()
        print(f"\nСтатистика:")
        print(f"Всего групп: {len(groups)}")
        if groups:
            print("\nПервые 5 групп:")
            for i, group in enumerate(groups[:5], 1):
                is_valid, message = await validate_group_id(client, group)
                status = "✅" if is_valid else "❌"
                print(f"{i}. {group} {status}")
    except Exception as e:
        logger.error(f"Ошибка при просмотре статистики: {e}")
        print(f"Ошибка при просмотре статистики: {e}")

async def manage_groups():
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
            is_valid, message = await validate_group_id(client, group_id)
            if is_valid:
                groups = await load_groups()
                if group_id not in groups:
                    groups.append(group_id)
                    await save_groups(groups)
                    print(f"✅ Группа добавлена: {message}")
                else:
                    print("❗ Эта группа уже есть в списке")
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
                continue
                
            print("\nСписок всех групп:")
            for i, group in enumerate(groups, 1):
                is_valid, message = await validate_group_id(client, group)
                status = "✅" if is_valid else "❌"
                print(f"{i}. {group} {status}")
        
        elif choice == "4":
            print("Проверка и очистка невалидных групп...")
            valid_count, removed_count = await clean_invalid_groups(client)
            print(f"✅ Готово! Валидных групп: {valid_count}, Удалено: {removed_count}")
        
        elif choice == "5":
            break

async def send_messages():
    """Отправка сообщений"""
    try:
        groups = await load_groups()
        if not groups:
            print("❌ Список групп пуст!")
            return
        
        print(f"📊 Загружено {len(groups)} групп")
    except Exception as e:
        logger.error(f"Ошибка при загрузке групп: {e}")
        print("❌ Ошибка при загрузке списка групп!")
        return

    message = input("Введите сообщение для отправки: ")
    if not message.strip():
        print("❌ Сообщение не может быть пустым!")
        return

    print("🚀 Начинаем отправку...")

    async with client:
        print("🔄 Подключаемся к Telegram...")
        await client.start()
        if not await client.is_user_authorized():
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
                print(f"[{idx}/{total}] Отправка в группу {group_id}...")
                await client.send_message(int(group_id), message)
                success += 1
                print(f"✅ Успешно отправлено в {group_id}")
                await asyncio.sleep(delay)
            except ValueError as ve:
                failed += 1
                logger.error(f"Ошибка формата ID ({group_id}): {ve}")
                print(f"❌ Ошибка формата ID ({group_id}): {ve}")
            except Exception as e:
                failed += 1
                logger.error(f"Ошибка отправки ({group_id}): {e}")
                print(f"❌ Ошибка отправки ({group_id}): {e}")
                
        print(f"\n📊 Результат: Успешно {success}/{total} | Ошибок: {failed}")

async def auth():
    """Авторизация"""
    async with client:
        await client.start()
        if await client.is_user_authorized():
            session_string = StringSession.save(client.session)
            print(f"\n🔑 **SESSION_STRING для .env:**\n{session_string}\n")
            await client.send_message("me", "✅ Авторизация успешна!")
            return session_string
        else:
            print("❌ Ошибка авторизации!")
            return None

if __name__ == "__main__":
    keep_alive()
    while True:
        print("\n📱 Меню управления:")
        print("1. Авторизация")
        print("2. Отправить рассылку")
        print("3. Просмотр статистики")
        print("4. Управление группами")
        print("5. Запустить бота")
        print("6. Выход")
        
        mode = input("\nВыберите действие: ")
        
        try:
            if mode == "1":
                session = asyncio.run(auth())
                if session:
                    print(f"✅ Скопируйте это в Secrets → SESSION_STRING:\n{session}")
            elif mode == "2":
                asyncio.run(send_messages())
            elif mode == "3":
                asyncio.run(view_stats())
            elif mode == "4":
                asyncio.run(manage_groups())
            elif mode == "5":
                print("🚀 Запускаем бота...")
                try:
                    asyncio.run(TelegramBot(client).run())
                except KeyboardInterrupt:
                    print("\n⛔ Бот остановлен")
            elif mode == "6":
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор!")
        except Exception as e:
            logger.error(f"Ошибка в главном меню: {e}")
            print(f"❌ Произошла ошибка: {e}")