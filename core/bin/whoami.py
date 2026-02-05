about = "Показать текущего пользователя (user/root)"

def execute(args, kernel, console):
    console.print(f"[bold green]root[/bold green]" if kernel.root_mode else "user")