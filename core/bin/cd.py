import core.fs.fs as fs
from rich.markup import escape

about = "Сменить каталог (.. назад, - прошлый путь, / корень)"

def execute(args, kernel, console):
    if not args:
        # Показываем красивый виртуальный путь вместо системного
        vpath = fs.get_virtual_path()
        console.print(f"Текущая директория: [cyan]{escape(vpath)}[/cyan]")
        return

    target = args[0]
    
    if not hasattr(kernel, 'previous_path'):
        kernel.previous_path = fs.current_path

    # Обработка возврата назад
    if target == "-":
        old_path = fs.current_path
        fs.current_path = kernel.previous_path
        kernel.previous_path = old_path
        console.print(f"Вернулись в [green]{escape(fs.get_virtual_path())}[/green]")
        return

    # Попытка смены директории
    old_path = fs.current_path
    
    # change_dir теперь сам внутри вызывает get_full_path и check_access
    if fs.change_dir(target):
        kernel.previous_path = old_path
        # Показываем виртуальный путь после перехода
        console.print(f"Перешли в [green]{escape(fs.get_virtual_path())}[/green]")
    else:
        # Если не перешли, значит либо нет папки, либо СТРАЖ заблокировал выход
        if not fs.exists(target):
            console.print(f"[red]Ошибка:[/red] Путь '{escape(target)}' не существует.")
        elif not fs.is_dir(target):
            console.print(f"[red]Ошибка:[/red] '{escape(target)}' — это файл.")
        else:
            console.print("[red]Доступ запрещен.[/]")