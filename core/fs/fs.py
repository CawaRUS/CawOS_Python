import os
import shutil

# --- Исправленный блок инициализации переменной kernel ---
# Мы не импортируем Kernel напрямую, чтобы избежать цикличной ошибки.
# Объект ядра сам запишет себя сюда при запуске.
kernel = None 

# Базовый корень виртуальной ОС (песочница пользователя)
base_root = os.path.abspath(os.path.join(os.getcwd(), "data", "0"))
# Корневая папка проекта (предел для root-пользователя)
root = os.path.abspath(os.path.join(os.getcwd()))

# Текущий рабочий каталог
current_path = base_root

def get_full_path(path=None):
    if path is None:
        return current_path
    # Обработка случая, если передали абсолютный путь внутри виртуальной ОС
    if path.startswith("\\"):
        return os.path.abspath(os.path.join(base_root, path.lstrip("\\")))
    return os.path.abspath(os.path.join(current_path, path))

def get_base_root():
    return base_root

def list_dir(path=None):
    full_path = get_full_path(path)
    try:
        # Проверка прав доступа
        is_root = getattr(kernel, "root_mode", False)
        if not is_root and os.path.commonpath([full_path, base_root]) != base_root:
             return []
        return os.listdir(full_path)
    except Exception:
        return []

def change_dir(new_dir):
    global current_path
    is_root = getattr(kernel, "root_mode", False)
    
    # 1. Переход в корень системы (Только для ROOT)
    if new_dir == "\\":
        if is_root:
            current_path = root
            return True
        else:
            current_path = base_root # Обычного пользователя кидаем в его корень
            return True
    
    # 2. Переход на уровень выше
    elif new_dir == "..":
        parent = os.path.abspath(os.path.join(current_path, ".."))
        limit = root if is_root else base_root

        # Если пытаемся выйти за пределы разрешенного лимита
        if os.path.commonpath([parent, limit]) != limit:
            current_path = limit # Просто остаемся на границе
            return True
        
        current_path = parent
        return True
        
    else:
        full_path = get_full_path(new_dir)
        limit = root if is_root else base_root
        
        if os.path.isdir(full_path):
            # Проверка, что папка находится внутри разрешенной зоны
            if os.path.commonpath([full_path, limit]) == limit:
                current_path = full_path
                return True
    return False

def make_dir(dirname):
    """Создание папки"""
    full_path = get_full_path(dirname)
    try:
        # Проверка, что не выходим за пределы base_root, если не root
        if not kernel.root_mode and os.path.commonpath([full_path, base_root]) != base_root:
             return False
        os.makedirs(full_path, exist_ok=True)
        return True
    except Exception:
        return False

def remove(path):
    """Удаление файла/папки"""
    full_path = get_full_path(path)
    if not os.path.exists(full_path):
        return False
        
    # Проверка: запрет удаления файлов вне песочницы для обычного пользователя
    if not kernel.root_mode and os.path.commonpath([full_path, base_root]) != base_root:
         return False
         
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        else:
            shutil.rmtree(full_path)
        return True
    except Exception:
        return False

def read_file(path):
    """Чтение файла"""
    full_path = get_full_path(path)
    # Проверка: запрет чтения файлов вне песочницы для обычного пользователя
    if not kernel.root_mode and os.path.commonpath([full_path, base_root]) != base_root:
         return None
         
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

def write_file(path, content):
    """Запись в файл"""
    full_path = get_full_path(path)
    # Проверка: запрет записи файлов вне песочницы для обычного пользователя
    if not kernel.root_mode and os.path.commonpath([full_path, base_root]) != base_root:
         return False
         
    try:
        # Создаем родительские директории, если их нет
        os.makedirs(os.path.dirname(full_path), exist_ok=True) 
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False