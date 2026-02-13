import json
import core.fs.fs as fs # Используем наш системный модуль
from rich.panel import Panel

# Пробуем достать статику, но не падаем
try:
    from data.info import info
    DEFAULT_OS = info.name_os
    DEFAULT_VER = info.version
except:
    DEFAULT_OS = "CawOS"
    DEFAULT_VER = "Unknown"

about = "Показать информацию о системе"

def execute(args, kernel, console):
    # ПРАВИЛЬНО: Читаем через fs.read_file
    # Это гарантирует проверку прав и корректность путей
    content = fs.read_file("data/json/info.json")
    
    try:
        info_data = json.loads(content) if content else {}
    except:
        info_data = {}

    username = info_data.get("username", "user")
    
    # Режим root берем из проксированного ядра
    is_root = getattr(kernel, 'root_mode', False)
    
    # Собираем панель
    panel_content = (
        f"[bold cyan]OS:[/bold cyan] {info_data.get('name_os', DEFAULT_OS)}\n"
        f"[bold cyan]Version:[/bold cyan] {info_data.get('version', DEFAULT_VER)}\n"
        f"[bold cyan]User:[/bold cyan] {username}\n"
        f"[bold cyan]Root Mode:[/bold cyan] {'[red]ACTIVE[/red]' if is_root else 'DISABLED'}\n"
    )
    
    # Добавим немного стиля от Rich
    console.print(Panel(
        panel_content, 
        title="[bold blue]System Information[/]", 
        border_style="cyan",
        expand=False
    ))