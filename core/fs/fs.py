deadlock = True
import os
import shutil
import inspect
import logging
import sys
import socket


# Ссылка на ядро (прописывается ядром при старте)
kernel = None 
logger = logging.getLogger("fs")

# Базовый корень виртуальной ОС (песочница пользователя)
base_root = os.path.realpath(os.path.join(os.getcwd(), "data", "0"))
# Корневая папка всего проекта CawOS
root_limit = os.path.realpath(os.getcwd())

# Текущий рабочий каталог
current_path = base_root

def is_root_active():
    """Безопасная проверка режима суперпользователя."""
    if kernel is None:
        return False
    return getattr(kernel, "root_mode", False)

def check_access(full_path):
    """
    ГЛАВНЫЙ СТРАЖ: Проверяет, имеет ли текущий сеанс право доступа к пути.
    Предотвращает выход за пределы песочницы.
    """
    target = os.path.realpath(full_path)
    limit = root_limit if is_root_active() else base_root
    
    # Путь разрешен только если он начинается с разрешенного лимита
    return os.path.commonpath([target, limit]) == limit

def get_full_path(path=None):
    if path is None:
        return current_path
    
    # 1. Если путь УЖЕ абсолютный (содержит метку диска или корень проекта)
    # Мы проверяем, не является ли он частью нашего root_limit
    if os.path.isabs(path) or path.startswith(root_limit):
        return os.path.realpath(path)

    # 2. Обработка "виртуального" корня ОС (от песочницы)
    if path.startswith("\\") or path.startswith("/"):
        clean_path = path.lstrip("\\/")
        return os.path.realpath(os.path.join(base_root, clean_path))
    
    # 3. Относительный путь от текущего места
    return os.path.realpath(os.path.join(current_path, path))

def list_dir(path=None):
    # Если путь None, get_full_path вернет current_path
    full_path = get_full_path(path)
    trusted = _is_trusted_caller()

    if path and not os.path.isdir(full_path) and trusted:
        system_path = os.path.realpath(os.path.join(root_limit, path))
        if os.path.isdir(system_path):
            full_path = system_path


    if not trusted and not check_access(full_path):
        logger.warning(f"Access denied to dir: {full_path}")
        return []
    
    try:
        if os.path.isdir(full_path):
            return os.listdir(full_path)
        return []
    except Exception as e:
        logger.error(f"Error listing {full_path}: {e}")
        return []

def change_dir(new_dir):
    global current_path
    if new_dir in ("\\", "/"):
        current_path = root_limit if is_root_active() else base_root
        return True
    
    full_path = get_full_path(new_dir)
    if os.path.isdir(full_path) and check_access(full_path):
        current_path = full_path
        return True
    return False

def make_dir(dirname):
    full_path = get_full_path(dirname)
    if not check_access(full_path):
        return False
    try:
        os.makedirs(full_path, exist_ok=True)
        return True
    except:
        return False

def remove(path):
    full_path = get_full_path(path)
    if full_path == root_limit or full_path == base_root:
        return False

    if not check_access(full_path) or not os.path.exists(full_path):
        return False
         
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        else:
            shutil.rmtree(full_path)
        return True
    except:
        return False

def _is_trusted_caller():
    """
    Проверяем весь стек вызовов. Если в цепочке есть системные модули, 
    значит вызов инициирован ядром.
    """
    try:
        stack = inspect.stack()
        for frame in stack:
            caller_name = os.path.basename(frame.filename)
            if caller_name in ["run.py", "shell.py", "kernel.py", "fs.py", "logs.py", "run.py"]:
                return True
        return False
    except:
        return False

def read_file(path, bypass_security=False):
    full_path = get_full_path(path)
    trusted = _is_trusted_caller()

    # 1. Поиск пути (оставляем как есть)
    if not os.path.isfile(full_path) and trusted:
        system_path = os.path.realpath(os.path.join(root_limit, path))
        if os.path.isfile(system_path):
            full_path = system_path

    if not os.path.isfile(full_path):
        return None

    try:
        from core import secure

        if not secure.can_read_file(path, is_root=False): 
            return None
    except Exception as e:
        logger.error(f"Security check failed: {e}")

    if not trusted and not check_access(full_path):
        logger.warning(f"Access denied: {path}")
        return None

    # 4. ЧТЕНИЕ
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"IO Error reading {path}: {e}")
        return None

def write_file(path, content, bypass_security=False):
    """
    Запись файла с защитой от перезаписи DEADLOCK-файлов.
    """
    full_path = get_full_path(path)
    
    if not check_access(full_path):
        return False

    # Проверка доверия для байпаса
    if bypass_security and not _is_trusted_caller():
        bypass_security = False

    # ЗАЩИТА ОТ ИЗМЕНЕНИЯ
    if not bypass_security and os.path.exists(full_path):
        from core import secure
        if not secure.can_read_file(path, is_root_active()):
            return False

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True) 
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except:
        return False
    
def exists(path):
    full_path = get_full_path(path)
    # Если путь не найден в песочнице пользователя, 
    # попробуем проверить от корня проекта, если вызывает система
    if not os.path.exists(full_path) and _is_trusted_caller():
        system_path = os.path.realpath(os.path.join(root_limit, path))
        return os.path.exists(system_path)
    
    return os.path.exists(full_path)

def is_dir(path):
    return os.path.isdir(get_full_path(path))

def get_relpath(path, start):
    return os.path.relpath(path, start)

def walk(root_path):
    return os.walk(root_path)

def makedirs(path, exist_ok=True):
    os.makedirs(path, exist_ok=exist_ok)

def rmtree(path):
    shutil.rmtree(path)

def get_size(path):
    return os.path.getsize(get_full_path(path))

def join_paths(*args):
    return os.path.join(*args)

def walk(path):
    return os.walk(path)

def get_relpath(path, start):
    return os.path.relpath(path, start)

def makedirs(path, exist_ok=True):
    os.makedirs(path, exist_ok=exist_ok)

def rmtree(path):
    shutil.rmtree(path)

def remove_file(path):
    if os.path.exists(path):
        os.remove(path)

def get_term_size():
    return shutil.get_terminal_size()

def raw_write(data):
    sys.stdout.write(data)
    sys.stdout.flush()


def get_command_about(path):
    """Безопасно вытаскивает строку about из .py файла без его импорта"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            import re
            match = re.search(r'about\s*=\s*["\'](.*?)["\']', content)
            return match.group(1) if match else "Нет описания"
    except:
        return "Ошибка чтения"

def get_network_info():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return hostname, local_ip

def rename(old_path, new_path):
    full_old = get_full_path(old_path)
    full_new = get_full_path(new_path)

    # Логика поиска в системе, если вызов доверенный (как в read_file)
    if not os.path.exists(full_old) and _is_trusted_caller():
        full_old = os.path.realpath(os.path.join(root_limit, old_path))
    
    # Проверка доступа (песочница)
    if not _is_trusted_caller() and not check_access(full_old):
        return False, "Access Denied"

    try:
        os.rename(full_old, full_new)
        return True, None
    except Exception as e:
        return False, str(e)