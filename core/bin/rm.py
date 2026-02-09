import core.fs.fs as fs
import core.secure as secure

about = "Удалить файл или папку"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите файл или папку для удаления[/red]")
        return
        
    target = args[0]
    
    if not secure.confirm_delete(target, kernel.root_mode):
        return
        
    if fs.remove(target):
        console.print(f"'{target}' удалён")
    else:
        console.print("[red]Ошибка удаления или файл/папка не найдены[/red]")