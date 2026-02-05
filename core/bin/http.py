import requests
from rich.panel import Panel

about = "Показать содержимое веб-страницы (GET)"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Использование: http <url>[/red]")
        return
        
    url = args[0]
    try:
        console.print(f"Запрос [yellow]{url}[/yellow]...")
        r = requests.get(url)
        console.print(f"Статус: [bold green]{r.status_code}[/bold green]")
        # Показываем первые 1000 символов ответа
        console.print(Panel(r.text[:1000] + "...", title="Response (first 1000 chars)"))
    except Exception as e:
        console.print(f"[bold red]Ошибка HTTP-запроса: {e}[/bold red]")