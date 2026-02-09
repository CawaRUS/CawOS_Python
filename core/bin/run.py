import importlib.util
import logging
from datetime import datetime
import core.fs.fs as fs # Используем твой драйвер

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

# Внутренние модули подтягиваем через fs или стандартный импорт, если они в core
from core import auth
# Предположим, data.info — это обычный модуль
try:
    import data.info as info
    real_time = getattr(info, "real_time", lambda: datetime.now().strftime("%H:%M:%S"))
except:
    info = None
    real_time = lambda: datetime.now().strftime("%H:%M:%S")

from core.etc import api as os_api

about = "Запустить приложение (Системные или Пользовательские)"

def execute(args, kernel, console):
    # Пути теперь относительные для fs
    sys_app_dir = "data/app"
    user_app_dir = "data/0/app"
    
    if not args:
        apps = []
        for path in [sys_app_dir, user_app_dir]:
            if fs.exists(path):
                # Используем твой fs.list_dir вместо os.listdir
                items = fs.list_dir(path)
                apps += [f[:-3] for f in items if f.endswith(".py")]
        console.print("[bold]Доступные приложения:[/bold]")
        for a in sorted(set(apps)): console.print(f" - [cyan]{a}[/cyan]")
        return

    app_name = args[0]
    app_path = None
    is_system = False 

    # Поиск пути через fs
    sys_p = fs.join_paths(sys_app_dir, app_name + ".py")
    user_p = fs.join_paths(user_app_dir, app_name + ".py")

    if fs.exists(sys_p):
        app_path, is_system = sys_p, True
    elif fs.exists(user_p):
        app_path, is_system = user_p, False
            
    if not app_path:
        logger.warning(f"App launch failed: '{app_name}' not found")
        console.print(f"[red]Приложение '{app_name}' не найдено[/red]")
        return

    try:
        logger.info(f"Launching {'SYSTEM' if is_system else 'USER'} app: '{app_name}'")

        if not os_api:
            console.print("[bold red]Критическая ошибка: SDK (os_api) не найден![/bold red]")
            return

        # Получаем защищенный API
        app_os = os_api.get_api(app_name, console, kernel, fs, auth, info, real_time, is_system, Panel, Table)

        # Читаем код ТОЛЬКО через fs
        code = fs.read_file(app_path, bypass_security=True)
        if not code:
            console.print("[red]Ошибка: не удалось прочитать файл приложения[/red]")
            return
            
        # Подготовка безопасных builtins
        if isinstance(__builtins__, dict): safe_builtins = __builtins__.copy()
        else: safe_builtins = vars(__builtins__).copy()

        if not is_system:
            def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
                allowed = ['math', 'json', 'random', 'datetime', 'rich', 're', 'time']
                if name in allowed or name.startswith('rich'):
                    return __import__(name, globals, locals, fromlist, level)
                raise ImportError(f"Доступ к модулю '{name}' запрещен")

            safe_builtins.update({"print": app_os["print"], "__import__": restricted_import})
            for func in ["open", "eval", "exec", "compile", "globals", "locals"]:
                safe_builtins.pop(func, None)

        # Формируем глобальное окружение
        exec_globals = {
            "__builtins__": safe_builtins if not is_system else __builtins__,
            "app_os": app_os,
            "console": console, "Panel": Panel, "Table": Table
        }
        
        # Если системное, даем доступ к fs вместо os
        if is_system:
            exec_globals.update({"fs": fs, "auth": auth, "Prompt": Prompt, "Confirm": Confirm})

        # --- ТОЧКА ЗАПУСКА ---
        compiled_code = compile(code, f"app:{app_name}", "exec")
        exec(compiled_code, exec_globals)
        logger.info(f"App '{app_name}' finished successfully")

    except SystemExit as se:
        logger.warning(f"App '{app_name}' stopped: {se}")
        console.print(f"[bold yellow]ℹ️ Приложение остановлено[/bold yellow]")
    except Exception as e:
        logger.error(f"Execution error in '{app_name}': {str(e)}", exc_info=True)
        console.print(f"[bold red]Ошибка выполнения ('{app_name}'): {e}[/bold red]")
    except BaseException as be:
        logger.critical(f"Critical process break in '{app_name}': {be}")
        console.print(f"[bold white on red] CRITICAL STOP [/] {be}")