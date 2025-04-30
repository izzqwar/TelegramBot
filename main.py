
import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# Конфигурация
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# Инициализация клиента
if SESSION_STRING:
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    except:
        print("Ошибка с SESSION_STRING, использую локальную сессию")
        client = TelegramClient("session", API_ID, API_HASH)
else:
    client = TelegramClient("session", API_ID, API_HASH)

# Flask для поддержания активности
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Mailer Active!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

async def view_stats():
    """Просмотр статистики групп"""
    try:
        with open("groups.txt", "r") as f:
            groups = [line.strip() for line in f if line.strip()]
        print(f"\nСтатистика:")
        print(f"Всего групп: {len(groups)}")
        print("\nПервые 5 групп:")
        for i, group in enumerate(groups[:5], 1):
            print(f"{i}. {group}")
    except FileNotFoundError:
        print("Файл groups.txt не найден!")

async def manage_groups():
    """Управление списком групп"""
    while True:
        print("\nУправление группами:")
        print("1. Добавить группу")
        print("2. Удалить группу")
        print("3. Просмотреть все группы")
        print("4. Назад")
        
        choice = input("Выберите действие: ")
        
        if choice == "1":
            group_id = input("Введите ID группы: ")
            with open("groups.txt", "a") as f:
                f.write(f"{group_id}\n")
            print("Группа добавлена!")
        
        elif choice == "2":
            with open("groups.txt", "r") as f:
                groups = f.readlines()
            print("\nСписок групп:")
            for i, group in enumerate(groups, 1):
                print(f"{i}. {group.strip()}")
            idx = input("Введите номер группы для удаления: ")
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(groups):
                    del groups[idx]
                    with open("groups.txt", "w") as f:
                        f.writelines(groups)
                    print("Группа удалена!")
                else:
                    print("Неверный номер!")
            except ValueError:
                print("Введите корректный номер!")
        
        elif choice == "3":
            with open("groups.txt", "r") as f:
                print("\nСписок всех групп:")
                for i, line in enumerate(f, 1):
                    print(f"{i}. {line.strip()}")
        
        elif choice == "4":
            break

async def send_messages():
    """Отправка сообщений"""
    try:
        with open("groups.txt", "r") as f:
            chat_ids = [line.strip() for line in f if line.strip()]
        print(f"Загружено {len(chat_ids)} групп")
    except FileNotFoundError:
        print("ERROR: groups.txt not found!")
        return

    message = input("Введите сообщение для отправки: ")
    print("Начинаем отправку...")

    async with client:
        print("Подключаемся к Telegram...")
        await client.start()
        if not await client.is_user_authorized():
            print("Ошибка: Клиент не авторизован! Запустите режим 1 для авторизации.")
            return
        print("Клиент авторизован успешно")
        print(f"Начинаем отправку сообщения: {message[:30]}...")
        success = 0
        total = len(chat_ids)
        
        for idx, chat_id in enumerate(chat_ids, 1):
            try:
                print(f"Отправка {idx}/{total} в группу {chat_id}...")
                await client.send_message(int(chat_id), message)
                success += 1
                print(f"✓ Успешно отправлено в {chat_id}")
                await asyncio.sleep(5)
            except ValueError as ve:
                print(f"❌ Ошибка формата ID ({chat_id}): {str(ve)}")
            except Exception as e:
                print(f"❌ Ошибка отправки ({chat_id}): {str(e)}")
        print(f"Результат: {success}/{total}")

from bot_handler import TelegramBot

async def run_bot():
    """Запуск бота"""
    try:
        print("Инициализация бота...")
        await client.start()
        
        if not await client.is_user_authorized():
            print("Ошибка: Клиент не авторизован! Выполните пункт 1 для авторизации.")
            return
            
        me = await client.get_me()
        print(f"Бот авторизован как: @{me.username} (ID: {me.id})")
        
        bot = TelegramBot(client)
        print("Настройка обработчиков команд...")
        await bot.setup_handlers()
        print("✅ Бот запущен и готов к работе!")
        print("Отправьте команду /start в Telegram чате с ботом")
        
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {str(e)}")
    finally:
        await client.disconnect()

async def auth():
    """Авторизация"""
    async with client:
        await client.start()
        if await client.is_user_authorized():
            session_string = StringSession.save(client.session)
            print(f"\n🔑 **SESSION_STRING для .env:**\n{session_string}\n")
            await client.send_message("me", "Auth successful!")
            return session_string
        else:
            print("Ошибка авторизации!")
            return None

if __name__ == "__main__":
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
        
        if mode == "1":
            session = asyncio.run(auth())
            print(f"Скопируйте это в Secrets → SESSION_STRING:\n{session}")
        elif mode == "2":
            asyncio.run(send_messages())
        elif mode == "3":
            asyncio.run(view_stats())
        elif mode == "4":
            asyncio.run(manage_groups())
        elif mode == "5":
            print("Запускаем бота...")
            try:
                asyncio.run(run_bot())
            except KeyboardInterrupt:
                print("\nБот остановлен")
        elif mode == "6":
            print("До свидания!")
            break
        else:
            print("Неверный выбор!")
