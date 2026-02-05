import core.fs.fs as fs
from rich.syntax import Syntax

about = "Показать содержимое файла"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите имя файла[/red]")
        return
        
    content = fs.read_file(args[0])
    if content is None:
        console.print("[red]Файл не найден или это папка[/red]")
    else:
        syntax = Syntax(content, "auto", theme="monokai", line_numbers=True)
        console.print(syntax)