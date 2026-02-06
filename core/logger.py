import logging
import os
import shutil
from logging.handlers import RotatingFileHandler

# Путь к логу
LOG_DIR = "data/log"
LOG_FILE = os.path.join(LOG_DIR, "system.log")
OLD_LOG_FILE = os.path.join(LOG_DIR, "system.old.log")

# Создаем папку, если её нет
os.makedirs(LOG_DIR, exist_ok=True)

_initialized = False # Флаг, чтобы не инициализировать дважды

def setup_logger():
    global _initialized
    if _initialized:
        return
    
    # --- ЛОГИКА ОЧИСТКИ ПРИ СТАРТЕ ---
    # Если текущий лог существует, переносим его в .old.log, затирая предыдущий старый лог
    if os.path.exists(LOG_FILE):
        try:
            # Используем shutil.move или os.replace для надежности
            if os.path.exists(OLD_LOG_FILE):
                os.remove(OLD_LOG_FILE) # Убираем совсем древний лог
            os.rename(LOG_FILE, OLD_LOG_FILE)
        except Exception:
            # Если файл занят другим процессом, просто продолжаем
            pass

    # Настройка ротации для работы ВНУТРИ сессии: 
    # макс 1МБ на файл, если сессия очень длинная, храним 3 части
    handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=1024*1024, 
        backupCount=3, 
        encoding='utf-8'
    )
    
    logging.basicConfig(
        level=logging.INFO,
        # Добавляем ,%(msecs)03d сразу после времени
        format='%(asctime)s,%(msecs)03d [%(levelname)s] [%(module)s] %(message)s',
        # Из datefmt убираем лишнее, так как миллисекунды приклеятся из format
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[handler]
    )
    
    _initialized = True
    logging.info("--- CawOS Logger Initialized (Fresh Session) ---")
    if os.path.exists(OLD_LOG_FILE):
        logging.info("Previous session log saved as system.old.log")

def log_info(message): logging.info(message)
def log_error(message): logging.error(message)
def log_warn(message): logging.warning(message)