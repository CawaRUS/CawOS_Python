import os
import sys
import importlib.util

# --- СИСТЕМНЫЕ БИБЛИОТЕКИ (Обычно всегда есть) ---
try:
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
except ImportError:
    # Если rich пропал, создаем заглушки, чтобы ядро не упало
    class Panel: 
        def __init__(self, content, **kwargs): self.content = content
        def __rich__(self): return self.content
    Table = None
    Prompt = None

# --- ВНУТРЕННИЕ МОДУЛИ (Самая опасная зона) ---
def safe_import(module_name, attribute=None):
    """Пытается импортировать модуль или атрибут, возвращает None при провале."""
    try:
        module = importlib.import_module(module_name)
        if attribute:
            return getattr(module, attribute, None)
        return module
    except Exception:
        return None

# Динамически подгружаем зависимости
fs = safe_import("core.fs.fs")
auth = safe_import("core.auth")
info = safe_import("data.info")
real_time = safe_import("data.info", "real_time")

# Если real_time не найден, делаем локальный fallback
if not real_time:
    import datetime
    real_time = lambda: datetime.datetime.now().strftime("%H:%M:%S")

about = "Запустить приложение (Системные или Пользовательские)"

def execute(args, kernel, console):
    root_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "0"))
    sys_app_dir = os.path.join(os.getcwd(), "data", "app")
    user_app_dir = os.path.join(root_dir, "app")
    
    app_dirs = [user_app_dir, sys_app_dir]
    
    # Сбор списка для справки
    apps = []
    for path in app_dirs:
        if os.path.exists(path):
            apps += [f[:-3] for f in os.listdir(path) if f.endswith(".py")]

    if not args:
        console.print("[bold]Доступные приложения:[/bold]")
        for a in sorted(set(apps)):
            console.print(f" - [cyan]{a}[/cyan]")
        return

    app_name = args[0]
    app_path = None
    is_system = False # Флаг доверия
    
    # Поиск файла и определение уровня доверия
    if os.path.isfile(os.path.join(sys_app_dir, app_name + ".py")):
        app_path = os.path.join(sys_app_dir, app_name + ".py")
        is_system = True
    elif os.path.isfile(os.path.join(user_app_dir, app_name + ".py")):
        app_path = os.path.join(user_app_dir, app_name + ".py")
        is_system = False
            
    if app_path is None:
        console.print(f"[red]Приложение '{app_name}' не найдено[/red]")
        return

    try:
        with open(app_path, "r", encoding="utf-8") as f:
            code = f.read()
            
            # API для всех приложений
            app_os = {
                "print": console.print, 
                "read_file": fs.read_file,
                "write_file": fs.write_file,
                "list_dir": fs.list_dir,
                "current_path": fs.current_path,
                "change_dir": fs.change_dir,
                "time": real_time,
                "Panel": Panel,
                "Table": Table,
                "is_system": is_system,
                "get_status": lambda: {
                    "root_active": getattr(kernel, "root_mode", "NULL"),
                    # Проверяем, разрешен ли ROOT в настройках системы
                    "root_allowed": auth.load_settings().get("allow_root", "NULL") if hasattr(auth, "load_settings") else "NULL",
                    "bootloader_unlocked": auth.load_settings().get("oem_unlock", "NULL") if hasattr(auth, "load_settings") else "NULL",
                    "version": getattr(info, "version", "NULL"),
                    "user": auth.load_settings().get("username", "NULL")
                }
            }
            
            # --- НАСТРОЙКА ОКРУЖЕНИЯ ---
            if isinstance(__builtins__, dict):
                safe_builtins = __builtins__.copy()
            else:
                safe_builtins = vars(__builtins__).copy()

            if is_system:
                # СИСТЕМНЫЕ приложения получают полный доступ
                exec_globals = {
                    "__builtins__": __builtins__, # Оригинальные встроенные функции
                    "app_os": app_os,
                    "fs": fs,
                    "os": os,
                    "console": console,
                    "Panel": Panel,
                    "Table": Table,
                    "Prompt": Prompt,
                    "Confirm": Confirm
                }
            else:
                # ПОЛЬЗОВАТЕЛЬСКИЕ приложения (песочница)
                ALLOWED_MODULES = ['math', 'json', 'random', 'datetime', 'rich', 're']

                def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
                    if name in ALLOWED_MODULES or name.startswith('rich'):
                        return __import__(name, globals, locals, fromlist, level)
                    raise ImportError(f"Доступ к модулю '{name}' запрещен (User App Restriction)")

                safe_builtins.update({
                    "print": console.print,
                    "__import__": restricted_import,
                    "Confirm": Confirm, "Prompt": Prompt,
                })
                
                # Чистим опасное
                for func in ["open", "eval", "exec", "compile", "globals", "locals"]:
                    safe_builtins.pop(func, None)
                
                exec_globals = {
                    "__builtins__": safe_builtins,
                    "app_os": app_os,
                    "console": console,
                    "Panel": Panel,
                    "Table": Table
                }
            
            # Запуск
            exec(code, exec_globals)
            
    except Exception as e:
        console.print(f"[bold red]Ошибка выполнения ('{app_name}'): {e}[/bold red]")