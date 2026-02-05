import os
import json
import importlib.util
from rich.table import Table

about = "Показать список доступных команд и пакетов"

def execute(args, kernel, console):
    table = Table(title="[bold blue]Справка по командам CawOS[/bold blue]")
    table.add_column("Команда / Пакет", style="cyan", no_wrap=True)
    table.add_column("Описание", style="magenta")
    table.add_column("Тип", style="dim")

    bin_path = os.path.join("core", "bin")
    
    # 1. Сбор системных команд из корня /bin
    core_commands = []
    for file in os.listdir(bin_path):
        if file.endswith(".py"):
            cmd_name = file[:-3]
            cmd_path = os.path.join(bin_path, file)
            
            try:
                spec = importlib.util.spec_from_file_location(cmd_name, cmd_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                desc = getattr(module, "about", "Нет краткого описания")
            except:
                desc = "[red]Ошибка чтения about[/red]"
            
            core_commands.append((cmd_name, desc, "Core"))

    # Сортируем и добавляем основные команды
    for name, desc, c_type in sorted(core_commands):
        table.add_row(name, desc, c_type)

    # 2. Сбор паков (пакетов) с фильтрацией мусора
    # Список папок, которые мы игнорируем
    ignored_dirs = ["__pycache__", ".git", ".pytest_cache"]
    
    # Сначала проверяем, есть ли вообще валидные пакеты для отображения секции
    valid_packages = []
    for entry in os.listdir(bin_path):
        sub_path = os.path.join(bin_path, entry)
        # Игнорируем если: не папка, в списке игнора, или начинается с точки
        if os.path.isdir(sub_path) and entry not in ignored_dirs and not entry.startswith('.'):
            valid_packages.append(entry)

    if valid_packages:
        table.add_section() # Разделитель между Core и Packages

    for entry in sorted(valid_packages):
        sub_path = os.path.join(bin_path, entry)
        json_path = os.path.join(sub_path, "about.json")
        
        pack_name = entry 
        pack_about = "Краткое описание отсутствует"
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pack_name = data.get("name", entry)
                    pack_about = data.get("about", pack_about)
            except:
                pack_about = "[red]Ошибка чтения about.json[/red]"
        
        table.add_row(pack_name, pack_about, "Package")

    console.print(table)