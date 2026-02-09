import json
import core.fs.fs as fs
from rich.table import Table

about = "Показать список доступных команд и пакетов (с пагинацией)"

def execute(args, kernel, console):
    ITEMS_PER_PAGE = 8
    try:
        page = int(args[0]) if args else 1
        page = max(1, page)
    except ValueError:
        page = 1

    bin_path = fs.join_paths(fs.root_limit, "core", "bin")
    all_entries = []
    if fs.exists(bin_path):
        for entry in fs.list_dir(bin_path):
            full_path = fs.join_paths(bin_path, entry)
            
            # 1. Обработка системных команд (.py файлов)
            if entry.endswith(".py") and entry != "__init__.py":
                cmd_name = entry[:-3]
                # Вызываем наш новый безопасный метод
                desc = fs.get_command_about(full_path)
                all_entries.append((cmd_name, desc, "Core"))
            
            # 2. Обработка пакетов (папок)
            elif fs.is_dir(full_path) and not entry.startswith(('.', '__')):
                json_path = fs.join_paths(full_path, "about.json")
                pack_about = "Краткое описание отсутствует"
                
                if fs.exists(json_path):
                    try:
                        # Тут используем обычный open, так как fs разрешает чтение данных
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            pack_about = data.get("about", data.get("description", pack_about))
                    except:
                        pack_about = "[red]Ошибка JSON[/red]"
                all_entries.append((entry, pack_about, "Package"))

    all_entries.sort(key=lambda x: x[0])

    total_items = len(all_entries)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    if page > total_pages: page = total_pages

    start_idx = (page - 1) * ITEMS_PER_PAGE
    page_items = all_entries[start_idx:start_idx + ITEMS_PER_PAGE]

    table = Table(
        title=f"[bold blue]Справка CawOS[/bold blue] [dim](Страница {page} из {total_pages})[/dim]",
        caption=f"Используйте: [cyan]help [номер][/cyan] | Всего: {total_items}",
        border_style="bright_black"
    )
    table.add_column("Команда / Пакет", style="cyan")
    table.add_column("Описание", style="magenta")
    table.add_column("Тип", style="green")

    for name, desc, c_type in page_items:
        table.add_row(name, desc, c_type)

    console.print(table)