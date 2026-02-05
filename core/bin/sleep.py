import time
from rich.progress import Progress

about = "Пауза (ожидание)"

def execute(args, kernel, console):
    if not args or not args[0].isdigit():
        console.print("[red]Использование: sleep <секунды>[/red]")
        return
        
    duration = int(args[0])
    with Progress() as progress:
        task = progress.add_task("[green]Sleeping...", total=duration)
        for _ in range(duration):
            time.sleep(1)
            progress.update(task, advance=1)
    console.print(f"Проснулся после [yellow]{duration} сек.[/yellow]")