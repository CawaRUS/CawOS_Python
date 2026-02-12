import os
import json
import importlib.util
import sys
import logging
import ast
import shlex  # Для корректного парсинга аргументов (кавычки и т.д.)
import core.fs.fs as fs
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markup import escape  # Для защиты от "поедания" скобок в Rich
from rich.traceback import install as install_traceback

# Настройка логгера для шелла
logger = logging.getLogger("shell")
console = Console()
install_traceback()

class KernelProxy:
    """Безопасная прослойка: дает доступ к данным, но запрещает менять состояние ядра."""
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def is_root(self):
        return self._kernel.is_root

    @property
    def running(self):
        return self._kernel.running

    def get_cwd(self):
        # Если у тебя путь хранится в fs, берем оттуда
        return fs.current_path

try:
    from data.info import info
    logger.debug("Core info module linked")
except ImportError:
    logger.warning("Core info module missing! Using fallback class.")
    class info:
        name_os = "CawOS"
        version = "NULL"
    console.print("[yellow][SHELL] Не удалось открыть модуль info.[/yellow]")

def load_user_info():
    """Загрузка данных пользователя из JSON."""
    try:
        # Используем fs для чтения, чтобы соблюдать правила песочницы
        content = fs.read_file("data/json/info.json")
        if content:
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
        return {}
    except Exception as e:
        logger.debug(f"User info.json not found or corrupted: {e}")
        return {}

def is_command_safe(command_path):
    """
    Анализирует код команды перед запуском.
    Разрешает всё для системных команд в core/bin.
    """
    # Если команда лежит в системной папке core/bin, доверяем ей без проверок
    normalized_path = command_path.replace("\\", "/")
    if "core/bin" in normalized_path:
        return True, None

    try:
        with open(command_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        tree = ast.parse(code)
        forbidden = ['os', 'shutil', 'subprocess', 'sys', 'pathlib', 'socket']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in forbidden:
                        return False, alias.name
            
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in forbidden:
                    return False, node.module
                    
        return True, None
    except Exception as e:
        return False, f"Ошибка анализа кода: {e}"

def run(kernel_instance):
    """Основной цикл оболочки."""
    logger.info("Shell session started")
    
    if not hasattr(kernel_instance, 'previous_path'):
        kernel_instance.previous_path = fs.current_path

    bin_path = os.path.join("core", "bin")

    while kernel_instance.running:
        info_data = load_user_info()
        username = info_data.get("username", "user")
        user_color = info_data.get("color", "cyan").lower()
        os_name = info_data.get("name_os", info.name_os)
        
        # Формируем промпт. Используем escape, чтобы имя пользователя не ломало Rich
        prompt_style = f"bold {user_color}"
        prompt_text = f"[{prompt_style}]{escape(username)}@{escape(os_name)}[/{prompt_style}] > "
        
        try:
            # Получаем строку ввода. Default="" предотвращает None
            cmd_str = Prompt.ask(prompt_text, default="")
        except (EOFError, KeyboardInterrupt):
            logger.info("Keyboard interrupt detected in shell")
            console.print("\n[yellow]Используйте 'exit' для выхода.[/yellow]")
            continue
            
        # ПРАВИЛЬНЫЙ ПАРСИНГ через shlex
        if not cmd_str.strip():
            continue
            
        try:
            cmd_parts = shlex.split(cmd_str)
        except ValueError as e:
            console.print(f"[red]Ошибка парсинга аргументов:[/red] {e}")
            continue

        command_name = cmd_parts[0].lower()
        args = cmd_parts[1:]
        
        logger.info(f"Command entered: {command_name} with args: {args}")
        
        command_file = None
        module_key = command_name 

        # --- ПОИСК КОМАНДЫ ---
        potential_pack_path = os.path.join(bin_path, command_name)
        
        # Обработка подкоманд (пакеты в bin/)
        if os.path.isdir(potential_pack_path) and len(args) > 0:
            sub_command = args[0].lower()
            target_path = os.path.join(potential_pack_path, f"{sub_command}.py")
            
            if os.path.isfile(target_path):
                command_file = target_path
                module_key = f"{command_name}_{sub_command}" 
                args = args[1:]
        
        # Поиск одиночного скрипта
        if not command_file:
            direct_path = os.path.join(bin_path, f"{command_name}.py")
            if os.path.isfile(direct_path):
                command_file = direct_path

        # --- ЗАПУСК ---
        if command_file:
            # 1. Проверка безопасности (AST-анализ только для внешних команд)
            safe, violation = is_command_safe(command_file)
            if not safe:
                logger.warning(f"SECURITY ALERT: Command '{command_name}' blocked. Direct use of '{violation}' detected.")
                console.print(Panel(
                    f"[bold red]НАРУШЕНИЕ ПРОТОКОЛА БЕЗОПАСНОСТИ[/bold red]\n\n"
                    f"Команде [cyan]'{escape(command_name)}'[/cyan] запрещено напрямую импортировать [yellow]'{escape(violation)}'[/yellow].\n"
                    f"Используйте официальные системные вызовы через [green]core.fs[/green].",
                    title="[white on red] KERNEL PROTECT [/]",
                    border_style="red"
                ))
                continue

            try:
                # 2. Очистка кэша импорта для горячей перезагрузки команд
                if module_key in sys.modules:
                    del sys.modules[module_key]

                # 3. Загрузка модуля
                spec = importlib.util.spec_from_file_location(module_key, command_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_key] = module 
                spec.loader.exec_module(module)
                
                # 4. Выполнение через ПРОКСИ
                if hasattr(module, 'execute'):
                    # Создаем прокси специально для этой команды
                    safe_kernel = KernelProxy(kernel_instance)
                    
                    # Передаем safe_kernel вместо реального kernel_instance
                    result = module.execute(args, safe_kernel, console)
                    
                    if result in ("shutdown", "reboot"):
                        logger.info(f"Command '{command_name}' requested system state: {result}")
                        return result
                else:
                    logger.error(f"Function execute() missing in {command_file}")
                    console.print(f"[bold red][ERROR][/bold red] Функция execute() не найдена.")
                    
            except Exception as e:
                logger.exception(f"Exception during command execution")
                console.print(f"[bold red]Критический сбой команды '{escape(command_name)}':[/bold red]")
                console.print_exception() 
        else:
            if os.path.isdir(potential_pack_path):
                console.print(f"[yellow]'{escape(command_name)}' - это пакет. Используйте: {escape(command_name)} <команда>[/yellow]")
            else:
                logger.warning(f"Unknown command: {command_name}")
                console.print(f"[bold red][ERROR][/bold red] Команда '{escape(command_name)}' не найдена.")