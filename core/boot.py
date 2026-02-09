# boot.py — загрузчик ОС с соблюдением пользовательских настроек
deadlock = True
import os
import json
import logging

# Мы не вызываем setup_logger здесь, так как он уже поднят в main.py
logger = logging.getLogger("boot")

try:
    from rich.console import Console
    console = Console()
except ImportError:
    logger.warning("Rich library not found, using MockConsole")
    class MockConsole:
        def print(self, *args, **kwargs): print(*args)
    console = MockConsole()

info_path = os.path.join("data", "json", "info.json")

def read_info():
    """Чтение конфига. Если файла нет или он битый — multi_os_boot будет False."""
    if not os.path.exists(info_path):
        logger.debug(f"Config file not found: {info_path}")
        return {}
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                logger.debug("Configuration loaded successfully")
                return data
            else:
                logger.warning("info.json is not a dictionary, ignoring content")
                return {}
    except Exception as e:
        logger.error(f"Error parsing info.json: {e}")
        return {}

def choose_os():
    """Меню выбора ОС."""
    os_path = os.path.join("core", "os")
    if not os.path.exists(os_path):
        logger.warning(f"OS directory {os_path} missing during selection")
        return "CawOS"

    systems = [d for d in os.listdir(os_path) if os.path.isdir(os.path.join(os_path, d))]
    if not systems:
        logger.warning("No operating systems found in core/os/")
        return "CawOS"
    
    display_systems = systems + ["RECOVERY"]
    logger.info(f"Available systems for boot: {display_systems}")

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
                selected = display_systems[idx]
                logger.info(f"User manually selected: {selected}")
                return selected
        except ValueError:
            pass
        logger.debug(f"Invalid boot input: '{choice}'")
        console.print("[red]Используйте номер из списка.[/red]")

def main():
    """Определяет ОС строго по инструкции из info.json."""
    logger.info("Initializing Bootloader...")
    console.print("[blue][BOOT][/blue] Инициализация...")
    
    info = read_info()
    os_path = os.path.join("core", "os")
    
    # СТРОГОЕ СОБЛЮДЕНИЕ ПУНКТА 8:
    allow_choice = info.get("multi_os_boot", False)
    logger.info(f"Multi-OS boot capability: {allow_choice}")

    if allow_choice:
        os_name = choose_os()
    else:
        # Прямая загрузка без лишних вопросов
        if os.path.exists(os_path):
            installed = [d for d in os.listdir(os_path) if os.path.isdir(os.path.join(os_path, d))]
            if "CawOS" in installed:
                os_name = "CawOS"
                logger.debug("Auto-boot: CawOS found and prioritized")
            elif installed:
                os_name = installed[0]
                logger.info(f"Auto-boot: CawOS missing, fallback to {os_name}")
            else:
                os_name = "CawOS"
                logger.warning("Auto-boot: No OS folders found, attempting default CawOS")
        else:
            os_name = "CawOS"
            logger.error(f"Auto-boot: {os_path} missing! Fallback to default name")
            
        console.print(f"[blue][BOOT][/blue] Авто-запуск: [bold green]{os_name}[/bold green]...")

    logger.info(f"Bootloader passing control to: {os_name}")
    return os_name