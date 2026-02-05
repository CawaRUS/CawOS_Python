import os, json, importlib.util, sys
import core.fs.fs as fs
from rich.console import Console
from rich.prompt import Prompt
from rich.traceback import install as install_traceback

# Инициализируем консоль rich и красивый вывод ошибок
console = Console()
install_traceback()

def run(kernel_instance):
    # --- ПОДГОТОВКА ПЕРЕМЕННЫХ ---
    if not hasattr(kernel_instance, 'previous_path'):
        kernel_instance.previous_path = fs.current_path

    # Загружаем конфиг (Безопасно)
    def load_user_info():
        try:
            with open("data/json/info.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except:
            return {}

    info_data = load_user_info()
    bin_path = os.path.join("core", "bin")

    while kernel_instance.running:
        # Перечитываем инфо каждый цикл (опционально, чтобы цвета менялись сразу)
        # Для скорости можно оставить снаружи, но для гибкости — лучше внутри
        username = info_data.get("username", "user")
        user_color = info_data.get("color", "cyan").lower()
        
        prompt_style = f"bold {user_color}"
        prompt_text = f"[{prompt_style}]{username}@CawOS[/{prompt_style}] > "
        
        try:
            cmd_str = Prompt.ask(prompt_text, default="")
        except (EOFError, KeyboardInterrupt):
            # Перехват Ctrl+C и Ctrl+D, чтобы не падал шелл
            console.print("\n[yellow]Используйте 'exit' для выхода.[/yellow]")
            continue
            
        cmd_parts = cmd_str.strip().split()
        if not cmd_parts:
            continue

        command_name = cmd_parts[0].lower()
        args = cmd_parts[1:]
        command_file = None
        module_key = command_name # Ключ для кэша sys.modules

        # --- ЛОГИКА ПОИСКА (ПРОСТАЯ ИЛИ ПАКЕТНАЯ) ---
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

        # --- ЗАПУСК КОМАНДЫ ---
        if command_file:
            try:
                # 1. Очистка кэша модуля (ГЛАВНАЯ ФИШКА)
                # Позволяет менять код .py файла и сразу видеть результат без ребута
                if module_key in sys.modules:
                    del sys.modules[module_key]

                # 2. Динамический импорт
                spec = importlib.util.spec_from_file_location(module_key, command_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_key] = module # Регистрируем
                spec.loader.exec_module(module)
                
                # 3. Безопасное выполнение
                if hasattr(module, 'execute'):
                    result = module.execute(args, kernel_instance, console)
                    
                    if result in ("shutdown", "reboot"):
                        return result
                else:
                    console.print(f"[bold red][ERROR][/bold red] В файле '{command_name}' не найдена функция execute().")
                    
            except Exception as e:
                console.print(f"[bold red]Критический сбой команды '{command_name}':[/bold red]")
                console.print_exception() 
        else:
            if os.path.isdir(potential_pack_path):
                console.print(f"[yellow]'{command_name}' - это пакет. Используйте: {command_name} <команда>[/yellow]")
            else:
                console.print(f"[bold red][ERROR][/bold red] Команда '{command_name}' не найдена.")