import json
import core.fs.fs as fs
from rich.table import Table
from rich.markup import escape # Защита от [red] в описаниях

about = "Показать список доступных команд и пакетов"

def execute(args, kernel, console):
    ITEMS_PER_PAGE = 8
    try:
        page = int(args[0]) if args else 1
        page = max(1, page)
    except (ValueError, IndexError):
        page = 1

    bin_rel_path = "core/bin"
    all_raw_entries = fs.list_dir(bin_rel_path)
    all_entries = []

    if all_raw_entries:
        for entry in all_raw_entries:
            item_path = fs.join_paths(bin_rel_path, entry)
            
            # 1. Системные команды
            if entry.endswith(".py") and entry != "__init__.py":
                cmd_name = entry[:-3]
                
                # Попробуем прочитать напрямую через fs.read_file, 
                # если get_command_about капризничает
                desc = fs.get_command_about(item_path) 
                
                # Если desc всё еще "Ошибка чтения", значит fs.py блокирует доступ
                all_entries.append((cmd_name, desc, "Core"))
            
            # 2. Пакеты
            elif fs.is_dir(item_path) and not entry.startswith(('.', '__')):
                json_path = fs.join_paths(item_path, "about.json")
                pack_about = "Краткое описание отсутствует"
                
                if fs.exists(json_path):
                    content = fs.read_file(json_path)
                    if content:
                        try:
                            data = json.loads(content)
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
        table.add_row(escape(name), escape(desc), c_type)

    console.print(table)