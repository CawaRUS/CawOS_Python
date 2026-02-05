import os
import shutil

# Ссылка на ядро (прописывается ядром при старте)
kernel = None 

# Базовый корень виртуальной ОС (песочница пользователя)
# Используем реальный путь, чтобы исключить обход через символьные ссылки
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
    
    # Обработка "виртуального" корня ОС
    if path.startswith("\\") or path.startswith("/"):
        # Приводим к корню песочницы
        clean_path = path.lstrip("\\/")
        return os.path.realpath(os.path.join(base_root, clean_path))
    
    return os.path.realpath(os.path.join(current_path, path))

def list_dir(path=None):
    full_path = get_full_path(path)
    if not check_access(full_path):
        return []
    try:
        if os.path.isdir(full_path):
            return os.listdir(full_path)
        return []
    except Exception:
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
    
    # Защита от удаления критических папок (даже для root)
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

def read_file(path):
    full_path = get_full_path(path)
    if not check_access(full_path) or not os.path.isfile(full_path):
        return None
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None

def write_file(path, content):
    full_path = get_full_path(path)
    if not check_access(full_path):
        return False
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True) 
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except:
        return False