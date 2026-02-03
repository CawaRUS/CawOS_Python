# boot.py — загрузчик ОС с выбором

import os
import json

# Для rich
try:
    from rich.console import Console
    console = Console()
except ImportError:
    # Заглушка, если rich не установлен
    class MockConsole:
        def print(self, *args, **kwargs):
            print(*args)
    console = MockConsole()

info_path = os.path.join("data", "json", "info.json")

def read_info():
    """Читает общий конфигурационный файл info.json."""
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
def choose_os():
    """Предлагает пользователю выбрать ОС, если включена опция multi_os_boot."""
    os_path = os.path.join("core", "os")
    if not os.path.exists(os_path):
        console.print("[blue][BOOT][/blue] Папка с ОС не найдена.")
        return "CawOS"

    systems = [d for d in os.listdir(os_path) if os.path.isdir(os.path.join(os_path, d))]
    if not systems:
        console.print("[blue][BOOT][/blue] Не найдено ни одной ОС.")
        return "CawOS"

    console.print("\n[bold]=== Меню загрузки ОС ===[/bold]")
    for i, s in enumerate(systems, 1):
        console.print(f"{i}. {s}")

    while True:
        choice = input("Выберите ОС (по номеру): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(systems):
            return systems[int(choice) - 1]
        console.print("[red]Неверный ввод.[/red]")

def main():
    """Основная функция загрузки."""
    console.print("[blue][BOOT][/blue] Загрузка...")
    # ИСПРАВЛЕНИЕ NameError: read_info() теперь доступна
    info = read_info()
    allow_choice = info.get("multi_os_boot", False)
    
    if allow_choice:
        os_name = choose_os()
    else:
        os_name = "CawOS" # ОС по умолчанию
        console.print(f"[blue][BOOT][/blue] Загружаем [bold green]{os_name}[/bold green]...")

    # Формируем путь к модулю ядра динамически
    kernel_path = f"core.os.{os_name}.kernel"

    try:
        # Динамический импорт модуля ядра
        kernel_module = __import__(kernel_path, fromlist=["*"])
        
        # Вызываем функцию start в модуле ядра, передавая ей имя ОС
        # Эта функция должна создать и запустить экземпляр класса Kernel
        try:
            kernel_module.start(os_name)
        except Exception:
            pass
        
        return os_name
        
    except ModuleNotFoundError:
        console.print(f"[blue][BOOT][/blue] [bold red]Ошибка: kernel для {os_name} не найден. Проверьте путь: {kernel_path}[/bold red]")
        exit(1)
    except AttributeError:
        # Теперь это отлавливает ошибку, если в kernel.py нет функции start(os_name)
        console.print(f"[blue][BOOT][/blue] [bold red]Ошибка: в модуле kernel.py для {os_name} отсутствует функция start(os_name) или она не определена корректно.[/bold red]")
        exit(1)