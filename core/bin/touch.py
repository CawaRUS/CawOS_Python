import core.fs.fs as fs
from rich.markup import escape  # <--- Добавляем импорт для защиты

about = "Создать пустой файл"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите имя файла[/red]")
        return
    
    filename = args[0]
    
    if "/" in filename or "\\" in filename:
        console.print("[red]Ошибка: Имя файла не может содержать символы '/' или '\\'[/red]")
        return
    
    if fs.write_file(filename, ""):
        # Используем escape(), чтобы скобки в имени файла не ломали консоль
        console.print(f"Файл [cyan]'{escape(filename)}'[/cyan] создан")
    else:
        # Здесь тоже лучше экранировать на случай, если ошибка выводит путь
        console.print(f"[red]Ошибка создания файла:[/red] {escape(filename)}")