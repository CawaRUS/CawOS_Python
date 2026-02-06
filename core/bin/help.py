import os
import json
import importlib.util
from rich.table import Table

about = "Показать список доступных команд и пакетов (с пагинацией)"

def execute(args, kernel, console):
    # --- НАСТРОЙКИ СТРАНИЦ ---
    ITEMS_PER_PAGE = 8  # Сколько команд выводить за раз
    
    # Определяем текущую страницу из аргументов (например: help 2)
    try:
        page = int(args[0]) if args else 1
        if page < 1: page = 1
    except ValueError:
        page = 1

    bin_path = os.path.join("core", "bin")
    all_entries = [] # Сюда соберем всё: и Core, и Packages

    # 1. Сбор системных команд
    if os.path.exists(bin_path):
        for file in os.listdir(bin_path):
            if file.endswith(".py"):
                cmd_name = file[:-3]
                cmd_path = os.path.join(bin_path, file)
                try:
                    # Используем кэширование или упрощенный импорт, если можно, 
                    # но пока оставим твою логику импорта для точности
                    spec = importlib.util.spec_from_file_location(cmd_name, cmd_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    desc = getattr(module, "about", "Нет описания")
                except:
                    desc = "[red]Ошибка чтения about[/red]"
                all_entries.append((cmd_name, desc, "Core"))

    # 2. Сбор пакетов
    ignored_dirs = ["__pycache__", ".git", ".pytest_cache"]
    if os.path.exists(bin_path):
        for entry in os.listdir(bin_path):
            sub_path = os.path.join(bin_path, entry)
            if os.path.isdir(sub_path) and entry not in ignored_dirs and not entry.startswith('.'):
                json_path = os.path.join(sub_path, "about.json")
                pack_about = "Краткое описание отсутствует"
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            pack_about = data.get("about", pack_about)
                    except:
                        pack_about = "[red]Ошибка JSON[/red]"
                all_entries.append((entry, pack_about, "Package"))

    # Сортируем общий список по имени
    all_entries.sort(key=lambda x: x[0])

    # --- ЛОГИКА ПАГИНАЦИИ ---
    total_items = len(all_entries)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if page > total_pages:
        page = total_pages

    # Срез списка для текущей страницы
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_items = all_entries[start_idx:end_idx]

    # --- ОТРИСОВКА ---
    table = Table(
        title=f"[bold blue]Справка CawOS[/bold blue] [dim](Страница {page} из {total_pages})[/dim]",
        caption=f"Используйте: [cyan]help [номер_страницы][/cyan] | Всего команд: {total_items}"
    )
    table.add_column("Команда / Пакет", style="cyan", no_wrap=True)
    table.add_column("Описание", style="magenta")
    table.add_column("Тип", style="dim")

    for name, desc, c_type in page_items:
        table.add_row(name, desc, c_type)

    console.print(table)