import core.fs.fs as fs

about = "Сменить каталог (.. назад, \ в корень)"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите папку[/red]")
        return

    target = args[0]
    
    # Работа с предыдущим путем (сохраняем в kernel, чтобы не терять между вызовами)
    if not hasattr(kernel, 'previous_path'):
        kernel.previous_path = fs.current_path

    if target == "-":
        fs.current_path, kernel.previous_path = kernel.previous_path, fs.current_path
        console.print(f"Перешли в [green]{fs.current_path}[/green]")
        return

    if not kernel.root_mode and target == "\\":
        console.print("[red]Доступ к системной директории запрещен.[/red]")
        return

    kernel.previous_path = fs.current_path
    if fs.change_dir(target):
        console.print(f"Перешли в [green]{fs.current_path}[/green]")
    else:
        console.print("[red]Папка не найдена[/red]")