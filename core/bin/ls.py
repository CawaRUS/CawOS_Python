import os
import core.fs.fs as fs
from rich.table import Table

about = "Показать содержимое каталога"

def execute(args, kernel, console):
    table = Table(title=f"Содержимое [green]{fs.current_path}[/green]")
    table.add_column("Имя", style="bright_cyan")
    table.add_column("Тип", style="yellow")
    
    try:
        for f in fs.list_dir():
            is_dir = os.path.isdir(os.path.join(fs.current_path, f))
            table.add_row(f, "[blue]Папка[/blue]" if is_dir else "Файл")
        console.print(table)
    except Exception as e:
        console.print(f"[red]Ошибка: {e}[/red]")