from rich.prompt import Confirm

about = "Выключить ОС"

def execute(args, kernel, console):
    if Confirm.ask("[yellow]Вы уверены, что хотите выключить ОС?[/yellow]"):
        return "shutdown"