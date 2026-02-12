import os
import shutil
import inspect
import logging
import sys
import socket

# Ссылка на ядро
kernel = None 
logger = logging.getLogger("fs")

# Базовые пути
BASE_ROOT = os.path.realpath(os.path.join(os.getcwd(), "data", "0"))
ROOT_LIMIT = os.path.realpath(os.getcwd())
CORE_DIR = os.path.join(ROOT_LIMIT, "core")

# Состояние
current_path = BASE_ROOT

# --- ВНУТРЕННИЕ ХЕЛПЕРЫ ---

def _is_trusted_caller():
    """Проверка: инициирован ли вызов кодом из папки /core/."""
    try:
        stack = inspect.stack()
        for frame in stack:
            # Проверяем реальный путь файла в стеке
            f_path = os.path.realpath(frame.filename)
            if f_path.startswith(CORE_DIR):
                return True
        return False
    except:
        return False

def is_root_active():
    if kernel is None: return False
    return getattr(kernel, "root_mode", False)

def check_access(full_path):
    target = os.path.normpath(os.path.realpath(full_path))
    hard_limit = os.path.normpath(ROOT_LIMIT)
    
    # ПЕРВАЯ ЛИНИЯ ОБОРОНЫ: Физический предел папки проекта
    # Проверяем, не является ли целевой путь частью папки проекта
    if not target.startswith(hard_limit):
        return False

    # ВТОРАЯ ЛИНИЯ: Права внутри проекта
    if is_root_active():
        return True # Root может всё, но только внутри CawOS
    
    user_limit = os.path.normpath(BASE_ROOT)
    if target.startswith(user_limit):
        return True
        
    if _is_trusted_caller():
        sys_app_path = os.path.normpath(os.path.join(hard_limit, "data/app"))
        if target.startswith(sys_app_path):
            return True
            
    return False

# --- ПУТИ ---

def get_full_path(path=None):
    if not path or path == ".":
        return current_path
    
    # Если мы в Root Mode, разрешаем абсолютные пути
    if is_root_active() and os.path.isabs(path):
        return os.path.normpath(os.path.realpath(path))

    # Обработка спец-символов
    if path == "~" or path == "/":
        return BASE_ROOT
    
    # Если путь начинается с /, считаем его от BASE_ROOT
    if path.startswith(("/", "\\")):
        return os.path.normpath(os.path.realpath(os.path.join(BASE_ROOT, path.lstrip("/\\"))))

    # Относительный путь
    return os.path.normpath(os.path.realpath(os.path.join(current_path, path)))

def get_virtual_path(full_path=None):
    """Для отображения в консоли: превращает системный путь в ~/ или [ROOT]."""
    target = os.path.realpath(full_path or current_path)
    if target.startswith(BASE_ROOT):
        rel = os.path.relpath(target, BASE_ROOT).replace("\\", "/")
        return "~/" + (rel if rel != "." else "")
    if target.startswith(ROOT_LIMIT):
        rel = os.path.relpath(target, ROOT_LIMIT).replace("\\", "/")
        return f"/{rel}"
    return target

# --- ОПЕРАЦИИ ---

def list_dir(path=None):
    # Если вызов от системы и путь похож на системный (core/...)
    if _is_trusted_caller() and path and (path.startswith("core") or path.startswith("app")):
        full_path = os.path.normpath(os.path.join(ROOT_LIMIT, path))
    else:
        full_path = get_full_path(path)

    # Проверка доступа для обычных смертных
    if not _is_trusted_caller() and not check_access(full_path):
        logger.warning(f"Access Denied: {full_path}")
        return []
    
    try:
        if os.path.isdir(full_path):
            return os.listdir(full_path)
        return []
    except Exception as e:
        return []

def change_dir(new_dir):
    global current_path
    if new_dir in ("\\", "/"):
        current_path = ROOT_LIMIT if is_root_active() else BASE_ROOT
        return True
    
    # Сначала генерируем потенциальный путь
    full_path = get_full_path(new_dir)
    
    # ТЕПЕРЬ ПРОВЕРЯЕМ: 
    # 1. Это папка?
    # 2. check_access РАЗРЕШАЕТ туда идти? (Теперь проверка обязательна для всех)
    if os.path.isdir(full_path) and check_access(full_path):
        current_path = full_path
        return True
    
    # Если мы здесь, значит доступ запрещен или папки нет
    return False

def read_file(path, bypass_security=False):
    # Если это системная аппа, берем путь от корня проекта
    if path.startswith("data/app"):
        full_path = os.path.normpath(os.path.join(ROOT_LIMIT, path))
    else:
        full_path = get_full_path(path)

    # Страж теперь знает про системные аппы для доверенных лиц
    if not check_access(full_path): 
        logger.warning(f"Read access denied: {full_path}")
        return None

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"IO Error: {e}")
        return None

def write_file(path, content, bypass_security=False):
    full_path = get_full_path(path)
    if not check_access(full_path): return False

    # Проверка прав через модуль secure (если есть)
    if not (bypass_security and _is_trusted_caller()):
        try:
            from core import secure
            if not secure.can_write_file(path, is_root_active()): return False
        except ImportError: pass

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True) 
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except:
        return False

def rename(old_path, new_path):
    f_old = get_full_path(old_path)
    f_new = get_full_path(new_path)
    
    if not check_access(f_old) or not check_access(f_new):
        return False, "Access Denied"

    try:
        os.rename(f_old, f_new)
        return True, None
    except Exception as e:
        return False, str(e)

# --- УТИЛИТЫ ---

def exists(path):
    return os.path.exists(get_full_path(path))

def is_dir(path):
    return os.path.isdir(get_full_path(path))

def get_size(path):
    f = get_full_path(path)
    return os.path.getsize(f) if os.path.isfile(f) else 0

def remove(path):
    f = get_full_path(path)
    if f in (ROOT_LIMIT, BASE_ROOT) or not check_access(f): return False
    try:
        if os.path.isfile(f): os.remove(f)
        else: shutil.rmtree(f)
        return True
    except: return False

def join_paths(*args): return os.path.join(*args)
def get_term_size(): return shutil.get_terminal_size()

def get_command_about(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            import re
            match = re.search(r'about\s*=\s*["\'](.*?)["\']', f.read())
            return match.group(1) if match else "Нет описания"
    except: return "Ошибка чтения"

def get_network_info():
    host = socket.gethostname()
    return host, socket.gethostbyname(host)

def make_dir(path):
    """Создание папки с проверкой доступа."""
    full_path = get_full_path(path)
    if not check_access(full_path):
        return False
    try:
        os.makedirs(full_path, exist_ok=True)
        return True
    except:
        return False

def raw_write(data):
    """Прямая печать в терминал (нужна для управляющих ANSI-последовательностей)."""
    sys.stdout.write(data)
    sys.stdout.flush()