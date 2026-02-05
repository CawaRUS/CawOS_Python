import core.fs.fs as fs

about = "Создать пустой файл"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите имя файла[/red]")
        return
        
    if fs.write_file(args[0], ""):
        console.print(f"Файл [cyan]'{args[0]}'[/cyan] создан")
    else:
        console.print("[red]Ошибка создания файла[/red]")