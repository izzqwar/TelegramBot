import logging
import asyncio
from typing import Optional, List, Tuple
from telethon import TelegramClient
from config import LOG_FORMAT, LOG_LEVEL, GROUPS_FILE

# Настройка логирования
logging.basicConfig(
    format=LOG_FORMAT,
    level=LOG_LEVEL,
    filename="bot.log"
)
logger = logging.getLogger(__name__)

async def validate_group_id(client: TelegramClient, group_id: str) -> Tuple[bool, str]:
    """Проверка валидности ID группы"""
    try:
        group = await client.get_entity(int(group_id))
        return True, f"Группа найдена: {group.title}"
    except ValueError:
        return False, "Неверный формат ID"
    except Exception as e:
        return False, f"Ошибка при проверке группы: {str(e)}"

async def load_groups() -> List[str]:
    """Загрузка списка групп из файла"""
    try:
        with open(GROUPS_FILE, "r", encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"Файл {GROUPS_FILE} не найден")
        return []

async def save_groups(groups: List[str]) -> bool:
    """Сохранение списка групп в файл"""
    try:
        with open(GROUPS_FILE, "w", encoding='utf-8') as f:
            f.write("\n".join(groups))
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении групп: {e}")
        return False

def calculate_delay(total_groups: int) -> int:
    """Расчет оптимальной задержки между отправками"""
    from config import DEFAULT_DELAY, MIN_DELAY, MAX_DELAY
    
    if total_groups <= 10:
        return DEFAULT_DELAY
    elif total_groups <= 50:
        return min(DEFAULT_DELAY * 1.5, MAX_DELAY)
    else:
        return MAX_DELAY

async def clean_invalid_groups(client: TelegramClient) -> Tuple[int, int]:
    """Очистка невалидных групп"""
    groups = await load_groups()
    valid_groups = []
    removed = 0
    
    for group_id in groups:
        is_valid, _ = await validate_group_id(client, group_id)
        if is_valid:
            valid_groups.append(group_id)
        else:
            removed += 1
            
    await save_groups(valid_groups)
    return len(valid_groups), removed
