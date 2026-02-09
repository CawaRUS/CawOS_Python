import core.fs.fs as fs

about = "Сменить каталог (.. назад, - прошлый путь, \\ корень)"

def execute(args, kernel, console):
    if not args:
        console.print(f"Текущая директория: [cyan]{fs.current_path}[/cyan]")
        return

    target = args[0]
    if not hasattr(kernel, 'previous_path'):
        kernel.previous_path = fs.current_path

    if target == "\\":
        if not kernel.root_mode:
            console.print("[red]Ошибка доступа: Root Mode необходим.[/red]")
            return
        # Вместо os.path.abspath используем fs
        target_abs = fs.base_root if hasattr(fs, 'base_root') else "."
    
    elif target == "-":
        old_path = fs.current_path
        fs.current_path = kernel.previous_path
        kernel.previous_path = old_path
        console.print(f"Вернулись в [green]{fs.current_path}[/green]")
        return

    potential_path = fs.get_full_path(target)

    if not fs.exists(target): # Используем нашу новую обертку
        console.print(f"[red]Ошибка:[/red] Путь '{target}' не существует.")
        return
    
    if not fs.is_dir(target):
        console.print(f"[red]Ошибка:[/red] '{target}' — это файл.")
        return

    old_path = fs.current_path
    if fs.change_dir(target):
        kernel.previous_path = old_path
        console.print(f"Перешли в [green]{fs.current_path}[/green]")