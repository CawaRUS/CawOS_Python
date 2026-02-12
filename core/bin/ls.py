import core.fs.fs as fs
from rich.table import Table
from rich.markup import escape # Импортируем щит от "мясорубки"

about = "Показать содержимое каталога"

def execute(args, kernel, console):
    # 1. Получаем путь. Если args нет, берем текущий рабочий каталог из FS
    # (Предположим, у fs есть метод get_cwd_virtual или аналогичный)
    target_path_raw = args[0] if args else "" 
    
    # Проверяем доступ
    if not fs.exists(target_path_raw):
        console.print(f"[red]Ошибка:[/] Путь [yellow]{escape(target_path_raw)}[/yellow] не найден.")
        return
    
    if not fs.is_dir(target_path_raw):
        console.print(f"[red]Ошибка:[/] [yellow]{escape(target_path_raw)}[/yellow] не является папкой.")
        return

    # 2. ДИНАМИЧЕСКИЙ ЗАГОЛОВОК
    # Вместо гадания, берем реальный виртуальный путь, который видит система
    current_display_path = fs.get_virtual_path(target_path_raw)
    
    table = Table(title=f"Содержимое [green]{escape(current_display_path)}[/green]")
    table.add_column("Имя", style="bright_cyan")
    table.add_column("Тип", style="yellow")
    table.add_column("Размер", style="dim")

    try:
        items = fs.list_dir(target_path_raw)
        
        for item in items:
            item_path = fs.join_paths(target_path_raw, item)
            
            # Важно: сначала проверяем тип, потом экранируем для вывода
            is_dir = fs.is_dir(item_path)
            
            size = ""
            if not is_dir:
                try:
                    size_bytes = fs.get_size(item_path)
                    if size_bytes < 1024:
                        size = f"{size_bytes} B"
                    elif size_bytes < 1024**2:
                        size = f"{round(size_bytes/1024, 1)} KB"
                    else:
                        size = f"{round(size_bytes/(1024**2), 1)} MB"
                except:
                    size = "???"

            # 3. ФИКС HANO-ЭФФЕКТА: Экранируем имя файла перед добавлением в таблицу
            safe_item_name = escape(item) 
            
            table.add_row(
                safe_item_name, 
                "[blue]Папка[/blue]" if is_dir else "Файл",
                size
            )
            
        console.print(table)
    except Exception as e:
        # Экранируем даже текст ошибки на всякий случай
        console.print(f"[red]Ошибка при чтении каталога: {escape(str(e))}[/red]")