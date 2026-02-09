import os, json, importlib.util, sys
import logging
import ast  # Для анализа структуры кода
import core.fs.fs as fs
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.traceback import install as install_traceback

# Настройка логгера для шелла
logger = logging.getLogger("shell")
console = Console()
install_traceback()

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
    try:
        with open("data/json/info.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.debug(f"User info.json not found or corrupted: {e}")
        return {}

def is_command_safe(command_path):
    """
    Анализирует код команды перед запуском.
    Запрещает прямой импорт опасных системных библиотек.
    """
    try:
        with open(command_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        tree = ast.parse(code)
        # Список модулей, которые запрещено использовать в обход API
        forbidden = ['os', 'shutil', 'subprocess', 'sys', 'pathlib', 'socket']
        
        for node in ast.walk(tree):
            # Проверка 'import os'
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_module = alias.name.split('.')[0]
                    if base_module in forbidden:
                        return False, alias.name
            
            # Проверка 'from os import path'
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    base_module = node.module.split('.')[0]
                    if base_module in forbidden:
                        return False, node.module
                    
        return True, None
    except Exception as e:
        return False, f"Ошибка анализа кода: {e}"

def run(kernel_instance):
    logger.info("Shell session started")
    
    if not hasattr(kernel_instance, 'previous_path'):
        kernel_instance.previous_path = fs.current_path

    bin_path = os.path.join("core", "bin")

    while kernel_instance.running:
        info_data = load_user_info()
        username = info_data.get("username", "user")
        user_color = info_data.get("color", "cyan").lower()
        os_name = info_data.get("name_os", info.name_os)
        
        prompt_style = f"bold {user_color}"
        prompt_text = f"[{prompt_style}]{username}@{os_name}[/{prompt_style}] > "
        
        try:
            cmd_str = Prompt.ask(prompt_text, default="")
        except (EOFError, KeyboardInterrupt):
            logger.info("Keyboard interrupt detected in shell")
            console.print("\n[yellow]Используйте 'exit' для выхода.[/yellow]")
            continue
            
        cmd_parts = cmd_str.strip().split()
        if not cmd_parts:
            continue

        command_name = cmd_parts[0].lower()
        args = cmd_parts[1:]
        
        logger.info(f"Command entered: {command_name} with args: {args}")
        
        command_file = None
        module_key = command_name 

        # --- ПОИСК КОМАНДЫ ---
        potential_pack_path = os.path.join(bin_path, command_name)
        
        if os.path.isdir(potential_pack_path) and len(args) > 0:
            sub_command = args[0].lower()
            target_path = os.path.join(potential_pack_path, f"{sub_command}.py")
            
            if os.path.isfile(target_path):
                command_file = target_path
                module_key = f"{command_name}_{sub_command}" 
                args = args[1:]
        
        if not command_file:
            direct_path = os.path.join(bin_path, f"{command_name}.py")
            if os.path.isfile(direct_path):
                command_file = direct_path

        # --- ЗАПУСК С ПРОВЕРКОЙ БЕЗОПАСНОСТИ ---
        if command_file:
            # 1. СКАНИРОВАНИЕ КОДА (Вариант А)
            safe, violation = is_command_safe(command_file)
            if not safe:
                logger.warning(f"SECURITY ALERT: Command '{command_name}' blocked. Direct use of '{violation}' detected.")
                console.print(Panel(
                    f"[bold red]НАРУШЕНИЕ ПРОТОКОЛА БЕЗОПАСНОСТИ[/bold red]\n\n"
                    f"Команде [cyan]'{command_name}'[/cyan] запрещено напрямую импортировать [yellow]'{violation}'[/yellow].\n"
                    f"Используйте официальные системные вызовы через [green]core.fs[/green].",
                    title="[white on red] SANDBOX VIOLATION [/]",
                    border_style="red"
                ))
                continue

            try:
                # 2. Очистка кэша
                if module_key in sys.modules:
                    del sys.modules[module_key]

                # 3. Загрузка и выполнение
                spec = importlib.util.spec_from_file_location(module_key, command_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_key] = module 
                spec.loader.exec_module(module)
                
                if hasattr(module, 'execute'):
                    result = module.execute(args, kernel_instance, console)
                    
                    if result in ("shutdown", "reboot"):
                        logger.info(f"Command '{command_name}' requested system state: {result}")
                        return result
                else:
                    logger.error(f"Function execute() missing in {command_file}")
                    console.print(f"[bold red][ERROR][/bold red] Функция execute() не найдена.")
                    
            except Exception as e:
                logger.exception(f"Exception during command execution")
                console.print(f"[bold red]Критический сбой команды '{command_name}':[/bold red]")
                console.print_exception() 
        else:
            if os.path.isdir(potential_pack_path):
                console.print(f"[yellow]'{command_name}' - это пакет. Используйте: {command_name} <команда>[/yellow]")
            else:
                logger.warning(f"Unknown command: {command_name}")
                console.print(f"[bold red][ERROR][/bold red] Команда '{command_name}' не найдена.")