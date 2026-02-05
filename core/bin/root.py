from rich.prompt import Prompt
from core import auth

about = "Включить/выключить режим root"

def execute(args, kernel, console):
    sub = args[0].lower() if len(args) > 0 else "on"

    if sub == "off":
        kernel.root_mode = False
        console.print("[yellow]Root режим отключен.[/yellow]")
        return

    if not auth.is_root_allowed():
        console.print("[red]Root запрещён в настройках.[/red]")
        return

    if not auth.has_root_password():
        console.print("[yellow]Создайте пароль root.[/yellow]")
        p1 = Prompt.ask("Пароль", password=True)
        p2 = Prompt.ask("Повторите пароль", password=True)
        if not p1 or p1 != p2:
            console.print("[red]Пароли не совпадают или пустой. Отмена.[/red]")
            return
        auth.set_root_password(p1)
        console.print("[green]Пароль установлен.[/green]")

    pwd = Prompt.ask("Введите пароль root", password=True)
    if auth.verify_root_password(pwd):
        kernel.root_mode = True
        console.print("[bold yellow]Root режим включен.[/bold yellow]")
    else:
        console.print("[bold red]Неверный пароль.[/bold red]")