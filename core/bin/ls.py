import os
import core.fs.fs as fs
from rich.table import Table

about = "Показать содержимое каталога"

def execute(args, kernel, console):
    # Если аргументы есть — берем первый как путь, иначе — текущий каталог
    target_path_raw = args[0] if args else None
    
    # Получаем полный путь через драйвер ФС (он сам проверит песочницу и root)
    full_path = fs.get_full_path(target_path_raw)
    
    # Проверяем доступ через твой главный страж
    if not fs.check_access(full_path):
        console.print(f"[red]Доступ запрещен:[/] {target_path_raw or 'текущий каталог'}")
        return

    # Проверяем, существует ли это вообще и папка ли это
    if not os.path.exists(full_path):
        console.print(f"[red]Ошибка:[/] Путь [yellow]{target_path_raw}[/yellow] не найден.")
        return
    if not os.path.isdir(full_path):
        console.print(f"[red]Ошибка:[/] [yellow]{target_path_raw}[/yellow] не является папкой.")
        return

    # Создаем таблицу. Для заголовка используем виртуальный путь (красивее для юзера)
    display_path = target_path_raw if target_path_raw else (
        "~/" if not fs.is_root_active() else "/"
    )
    
    table = Table(title=f"Содержимое [green]{display_path}[/green]")
    table.add_column("Имя", style="bright_cyan")
    table.add_column("Тип", style="yellow")
    table.add_column("Размер", style="dim")

    try:
        # Передаем путь в list_dir
        items = fs.list_dir(target_path_raw)
        
        for item in items:
            item_full_path = os.path.join(full_path, item)
            is_dir = os.path.isdir(item_full_path)
            
            # Добавим отображение размера для файлов
            size = ""
            if not is_dir:
                size_bytes = os.path.getsize(item_full_path)
                size = f"{size_bytes} B" if size_bytes < 1024 else f"{round(size_bytes/1024, 1)} KB"

            table.add_row(
                item, 
                "[blue]Папка[/blue]" if is_dir else "Файл",
                size
            )
            
        console.print(table)
    except Exception as e:
        console.print(f"[red]Ошибка при чтении каталога: {e}[/red]")