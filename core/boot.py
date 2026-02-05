# boot.py — загрузчик ОС с соблюдением пользовательских настроек
import os
import json

try:
    from rich.console import Console
    console = Console()
except ImportError:
    class MockConsole:
        def print(self, *args, **kwargs): print(*args)
    console = MockConsole()

info_path = os.path.join("data", "json", "info.json")

def read_info():
    """Чтение конфига. Если файла нет или он битый — multi_os_boot будет False."""
    if not os.path.exists(info_path):
        return {}
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def choose_os():
    """Меню выбора ОС."""
    os_path = os.path.join("core", "os")
    if not os.path.exists(os_path):
        return "CawOS"

    systems = [d for d in os.listdir(os_path) if os.path.isdir(os.path.join(os_path, d))]
    if not systems:
        return "CawOS"
    
    display_systems = systems + ["RECOVERY"]

    console.print("\n[bold cyan]─── CawOS Boot Manager ───[/bold cyan]")
    for i, s in enumerate(display_systems, 1):
        color = "green" if s == "CawOS" else "white"
        if s == "RECOVERY": color = "red"
        console.print(f" {i} > [{color}]{s}[/{color}]")

    while True:
        try:
            choice = input("\nbooting > ").strip()
            if not choice: continue
            idx = int(choice) - 1
            if 0 <= idx < len(display_systems):
                return display_systems[idx]
        except ValueError:
            pass
        console.print("[red]Используйте номер из списка.[/red]")

def main():
    """Определяет ОС строго по инструкции из info.json."""
    console.print("[blue][BOOT][/blue] Инициализация...")
    
    info = read_info()
    os_path = os.path.join("core", "os")
    
    # СТРОГОЕ СОБЛЮДЕНИЕ ПУНКТА 8:
    # Берем значение из конфига. Если его нет — по умолчанию False (ВЫКЛ).
    allow_choice = info.get("multi_os_boot", False)

    if allow_choice:
        os_name = choose_os()
    else:
        # Прямая загрузка без лишних вопросов
        # Если CawOS нет (стерли?), берем первую попавшуюся папку из os/
        if os.path.exists(os_path):
            installed = [d for d in os.listdir(os_path) if os.path.isdir(os.path.join(os_path, d))]
            os_name = "CawOS" if "CawOS" in installed else (installed[0] if installed else "CawOS")
        else:
            os_name = "CawOS"
            
        console.print(f"[blue][BOOT][/blue] Авто-запуск: [bold green]{os_name}[/bold green]...")

    return os_name