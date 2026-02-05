import core.fs.fs as fs

about = "Создать папку"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите имя папки[/red]")
        return
        
    if fs.make_dir(args[0]):
        console.print(f"Папка [cyan]'{args[0]}'[/cyan] создана")
    else:
        console.print("[red]Ошибка создания папки или она уже существует[/red]")