import core.fs.fs as fs
from core import secure

about = "Переименовать файл или папку"

def execute(args, kernel, console):
    if len(args) < 2:
        console.print("[red]Использование: rename <старое_имя> <новое_имя>[/red]")
        return

    old_name, new_name = args[0], args[1]

    # 1. Проверка Deadlock (уже используем существующий secure)
    if not secure.can_read_file(old_name, kernel.root_mode):
        return

    # 2. Выполняем операцию через системный драйвер
    # Передаем управление fs.rename, который знает про root_limit и песочницы
    success, error = fs.rename(old_name, new_name)

    if success:
        console.print(f"[green]Успешно переименовано:[/green] {old_name} -> {new_name}")
    else:
        if "Access Denied" in str(error):
            console.print("[red]Доступ запрещен: нельзя изменять системные объекты.[/red]")
        else:
            console.print(f"[red]Ошибка при переименовании: {error}[/red]")