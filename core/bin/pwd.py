import core.fs.fs as fs

about = "Показать текущий рабочий каталог"

def execute(args, kernel, console):
    console.print(f"[green]{fs.current_path}[/green]")