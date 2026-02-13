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

base_root = BASE_ROOT
root_limit = ROOT_LIMIT

# Состояние
current_path = BASE_ROOT

# --- ВНУТРЕННИЕ ХЕЛПЕРЫ ---

def _is_trusted_caller():
    """Проверка: инициирован ли вызов системным кодом или системным приложением."""
    try:
        stack = inspect.stack()
        for frame in stack:
            f_path = os.path.normpath(os.path.realpath(frame.filename))
            
            # Доверяем всему, что в /core/
            if f_path.startswith(CORE_DIR):
                return True
            
            # Доверяем системным приложениям из /data/app/
            # (Обычные юзерские аппы лежат в /data/0/ или других папках)
            sys_app_path = os.path.normpath(os.path.join(ROOT_LIMIT, "data", "app"))
            if f_path.startswith(sys_app_path):
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
    
    # 1. Физический предел папки проекта (Path Traversal protection)
    if not target.startswith(hard_limit):
        return False

    # 2. Root Mode
    if is_root_active():
        return True 
    
    # 3. Доступ к пользовательской песочнице
    user_limit = os.path.normpath(BASE_ROOT)
    if target.startswith(user_limit):
        return True
        
    # 4. Доступ для системных компонентов (доверенный код)
    if _is_trusted_caller():
        # Разрешаем системным модулям доступ к приложениям и конфигам
        sys_app_path = os.path.normpath(os.path.join(hard_limit, "data", "app"))
        sys_config_path = os.path.normpath(os.path.join(hard_limit, "data", "json"))
        
        if target.startswith(sys_app_path) or target.startswith(sys_config_path):
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
    if _is_trusted_caller() and path and (path.startswith("core") or path.startswith("app") or path.startswith("data")):
        full_path = os.path.normpath(os.path.join(ROOT_LIMIT, path))
    else:
        full_path = get_full_path(path)

    if not _is_trusted_caller() and not check_access(full_path):
        logger.warning(f"Access Denied: {full_path}")
        return []
    
    try:
        if os.path.isdir(full_path):
            return os.listdir(full_path)
        return []
    except:
        return []

def change_dir(new_dir):
    global current_path
    if new_dir in ("\\", "/"):
        current_path = ROOT_LIMIT if is_root_active() else BASE_ROOT
        return True
    
    full_path = get_full_path(new_dir)
    
    if os.path.isdir(full_path) and check_access(full_path):
        current_path = full_path
        return True
    return False

def read_file(path, bypass_security=False):
    # Логика определения пути: для системных команд проверяем корень проекта
    if (path.startswith("data/") or path.startswith("/data/")) and _is_trusted_caller():
        clean_path = path.lstrip("/")
        full_path = os.path.normpath(os.path.join(ROOT_LIMIT, clean_path))
    else:
        full_path = get_full_path(path)

    if not (bypass_security and _is_trusted_caller()) and not check_access(full_path): 
        logger.warning(f"Read access denied: {full_path}")
        return None

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"IO Error: {e}")
        return None

def write_file(path, content, bypass_security=False):
    # Логика определения пути для системных нужд
    if (path.startswith("data/") or path.startswith("/data/")) and _is_trusted_caller():
        clean_path = path.lstrip("/")
        full_path = os.path.normpath(os.path.join(ROOT_LIMIT, clean_path))
    else:
        full_path = get_full_path(path)

    # Проверка доступа
    if not (bypass_security and _is_trusted_caller()) and not check_access(full_path):
        logger.warning(f"Write Access Denied: {full_path}")
        return False

    # Дополнительная проверка через модуль secure (если есть)
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
    full_path = get_full_path(path)
    if not check_access(full_path):
        return False
    try:
        os.makedirs(full_path, exist_ok=True)
        return True
    except:
        return False

def raw_write(data):
    sys.stdout.write(data)
    sys.stdout.flush()

def walk(top_path):
    """
    Безопасная обертка над os.walk.
    Проверяет доступ к каждой директории перед итерацией.
    """
    full_root = get_full_path(top_path)
    
    for root, dirs, files in os.walk(full_root):
        # Фильтруем папки на лету: оставляем только те, куда есть доступ
        dirs[:] = [d for d in dirs if check_access(os.path.join(root, d))]
        
        # Проверяем доступ к текущему root (на всякий случай)
        if check_access(root):
            yield root, dirs, files

def get_relpath(path, start=None):
    """Обертка над os.path.relpath для find.py"""
    if start is None:
        start = BASE_ROOT
    return os.path.relpath(path, start).replace("\\", "/")