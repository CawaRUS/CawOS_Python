import importlib.util
import logging
import ast  # Для безопасного eval
from datetime import datetime
import core.fs.fs as fs 

logger = logging.getLogger("cmd: run")

# --- СИСТЕМНЫЕ БИБЛИОТЕКИ ---
try:
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
except ImportError:
    class Panel: 
        def __init__(self, content, **kwargs): self.content = content
        def __rich__(self): return self.content
    Table = Prompt = Confirm = None

from core import auth
try:
    import data.info as info
    real_time = getattr(info, "real_time", lambda: datetime.now().strftime("%H:%M:%S"))
except:
    info = None
    real_time = lambda: datetime.now().strftime("%H:%M:%S")

from core.etc import api as os_api

about = "Запустить приложение (Системные или Пользовательские)"

def execute(args, kernel, console):
    # ПУТИ: Используем формат "data/...", который твой fs.py считает доверенным
    sys_app_dir = "data/app"
    user_app_dir = "data/0/app"

    if not args:
        apps = []
        # Мы не используем fs.exists для папок здесь, так как list_dir 
        # сам по себе вернет пустой список, если папки нет или нет доступа.
        for path in [sys_app_dir, user_app_dir]:
            items = fs.list_dir(path) # Здесь сработает твой новый if с startswith("data")
            if items:
                apps += [f[:-3] for f in items if f.endswith(".py")]
        
        console.print("[bold]Доступные приложения:[/bold]")
        unique_apps = sorted(set(apps))
        if not unique_apps:
            console.print("[yellow] (пусто)[/yellow]")
        else:
            for a in unique_apps: 
                console.print(f" - [cyan]{a}[/cyan]")
        return

    app_name = args[0]
    app_path = None
    is_system = False 

    # ПРОВЕРКА СУЩЕСТВОВАНИЯ: 
    # Вместо fs.exists (который может косячить с путями), просто пробуем прочитать список файлов
    sys_files = fs.list_dir(sys_app_dir)
    user_files = fs.list_dir(user_app_dir)

    target_file = f"{app_name}.py"

    if sys_files and target_file in sys_files:
        app_path, is_system = f"{sys_app_dir}/{target_file}", True
    elif user_files and target_file in user_files:
        app_path, is_system = f"{user_app_dir}/{target_file}", False
            
    if not app_path:
        logger.warning(f"App launch failed: '{app_name}' not found")
        console.print(f"[red]Приложение '{app_name}' не найдено[/red]")
        return

    try:
        logger.info(f"Launching {'SYSTEM' if is_system else 'USER'} app: '{app_name}'")

        if not os_api:
            console.print("[bold red]Критическая ошибка: SDK (os_api) не найден![/bold red]")
            return

        app_os = os_api.get_api(app_name, console, kernel, fs, auth, info, real_time, is_system, Panel, Table)

        # Читаем код. Благодаря startswith("data"), fs.read_file поймет, что это корень проекта.
        code = fs.read_file(app_path, bypass_security=True)
        if not code:
            console.print("[red]Ошибка: не удалось прочитать файл приложения[/red]")
            return
            
        # --- ПОДГОТОВКА ОКРУЖЕНИЯ (БЕЗОПАСНОСТЬ) ---
        if isinstance(__builtins__, dict): 
            raw_builtins = __builtins__.copy()
        else: 
            raw_builtins = vars(__builtins__).copy()

        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            user_allowed = ['math', 'json', 'random', 'datetime', 'rich', 're', 'time', 'requests', 'hashlib']
            system_allowed = user_allowed + ['base64', 'itertools', 'data.info','ast']
            allowed = system_allowed if is_system else user_allowed
            if name in allowed or name.startswith('rich'):
                return __import__(name, globals, locals, fromlist, level)
            raise ImportError(f"Доступ к модулю '{name}' запрещен в CawOS")

        def safe_eval(expr, globals_dict=None, locals_dict=None):
            # Если контекст не передан, используем текущие глобалы exec_globals
            g = globals_dict if globals_dict is not None else exec_globals
            l = locals_dict if locals_dict is not None else {}
            
            try:
                # Сначала пробуем максимально безопасный literal_eval (для чисел)
                return ast.literal_eval(expr)
            except:
                # Если не вышло (например, там pi + 1), используем обычный eval с переданным контекстом
                return eval(expr, g, l)

        allowed_names = [
            'abs', 'bool', 'dict', 'float', 'int', 'len', 'list', 'max', 'min', 
            'range', 'round', 'str', 'sum', 'tuple', 'type', 'pow', 'divmod',
            'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr',
            'ValueError', 'TypeError', 'IndexError', 'KeyError', 'StopIteration',
            'ZeroDivisionError', 'NameError', 'ArithmeticError', 'LookupError',
            'MemoryError', 'OverflowError', 'AttributeError', 'SyntaxError'
        ]
            
        
        safe_builtins = {n: raw_builtins[n] for n in allowed_names if n in raw_builtins}
        safe_builtins.update({
            "print": app_os["print"], 
            "__import__": restricted_import,
            "eval": safe_eval
        })

        exec_globals = {
            "__builtins__": safe_builtins,
            "app_os": app_os,
            "console": console, 
            "Panel": Panel, 
            "Table": Table
        }
        
        if is_system:
            exec_globals.update({"fs": fs, "auth": auth, "Prompt": Prompt, "Confirm": Confirm})

        # --- ЗАПУСК ---
        compiled_code = compile(code, f"app:{app_name}", "exec")
        exec(compiled_code, exec_globals)
        logger.info(f"App '{app_name}' finished")

    except SystemExit:
        console.print(f"[bold yellow]ℹ️ Приложение остановлено[/bold yellow]")
    except Exception as e:
        logger.error(f"Execution error in '{app_name}': {str(e)}", exc_info=True)
        console.print(f"[bold red]Ошибка выполнения ('{app_name}'): {e}[/bold red]")
    except BaseException as be:
        console.print(f"[bold white on red] CRITICAL STOP [/] {be}")