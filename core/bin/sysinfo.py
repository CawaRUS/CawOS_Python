import json
from rich.panel import Panel

# Безопасные импорты
try:
    from data.info import info
    DEFAULT_OS = info.name_os
    DEFAULT_VER = info.version
except:
    DEFAULT_OS = "NULL"
    DEFAULT_VER = "Unknown"

try:
    from core import auth
except:
    auth = None

about = "Показать информацию о системе"

def execute(args, kernel, console):
    # Безопасное чтение живого конфига
    try:
        with open("data/json/info.json", "r", encoding="utf-8") as f:
            info_data = json.load(f)
    except:
        info_data = {}

    username = info_data.get("username", "user")
    
    # Проверка разрешений через auth (с защитой от отсутствия модуля)
    root_allowed = "Unknown"
    if auth and hasattr(auth, "is_root_allowed"):
        root_allowed = "Yes" if auth.is_root_allowed() else "No"

    panel_content = (
        f"[bold cyan]OS:[/bold cyan] {info_data.get('name_os', DEFAULT_OS)}\n"
        f"[bold cyan]Version:[/bold cyan] {info_data.get('version', DEFAULT_VER)}\n"
        f"[bold cyan]User:[/bold cyan] {username}\n"
        f"[bold cyan]Root Mode:[/bold cyan] {'[red]ACTIVE[/red]' if getattr(kernel, 'root_mode', False) else 'DISABLED'}\n"
        f"[bold cyan]Root Allowed:[/bold cyan] {root_allowed}"
    )
    console.print(Panel(panel_content, title="[bold blue]System Info[/bold blue]", border_style="blue"))