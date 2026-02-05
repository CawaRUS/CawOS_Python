import os
import json
import getpass
import time
from datetime import datetime

# Библиотеки Rich для красоты
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from core import auth

console = Console()

def get_status_style(value: bool) -> str:
    return "[bold green]ВКЛ[/]" if value else "[bold red]ВЫКЛ[/]"

def show_menu(info):
    table = Table(title="Системные Настройки", title_style="bold magenta", expand=True)
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Опция", style="white")
    table.add_column("Статус / Значение", justify="right")

    table.add_row("1", "Текущее время", datetime.now().strftime('%H:%M:%S'))
    table.add_row("2", "Имя пользователя", f"[yellow]{info.get('username', 'user')}[/]")
    table.add_row("3", "Список приложений", f"{len(os.listdir('data/app')) if os.path.exists('data/app') else 0} шт.")
    table.add_row("4", "Проверка целостности", get_status_style(info.get("verify_enabled", True)))
    table.add_row("5", "Модуль безопасности", get_status_style(info.get("secury_enabled", True)))
    table.add_row("6", "Доступ к ROOT", "[bold yellow]ОГРАНИЧЕНО[/]" if not info.get("oem_unlock") else get_status_style(info.get("allow_root")))
    table.add_row("7", "Управление паролем ROOT", "[dim]********[/]")
    table.add_row("8", "Выбор нескольких ОС", get_status_style(info.get("multi_os_boot", False)))
    table.add_row("0", "[bold red]Выход[/]", "")

    console.print(table)

# Основной цикл
while True:
    # Обновляем данные из файла каждый раз, чтобы видеть изменения других модулей
    info = auth.load_settings() 
    show_menu(info)
    
    choice = console.input("[bold cyan]Введите номер опции > [/]").strip()

    if choice == "1":
        rprint(f"[bold green]Дата и время:[/] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    elif choice == "2":
        new_name = input("Введите новое имя пользователя: ").strip()
        if new_name:
            info["username"] = new_name
            auth.save_settings(info)
            rprint(f"[green]✔ Имя изменено на {new_name}[/]")

    elif choice == "3":
        apps_path = "data/app"
        if os.path.exists(apps_path):
            rprint(Panel("\n".join([f"{a[:-3]}" for a in os.listdir(apps_path) if a.endswith(".py")]), title="Установленное ПО"))
        else:
            rprint("[red]Ошибка: Папка приложений не найдена[/]")

    elif choice in ["4", "5", "8"]:
        # Групповая обработка простых переключателей
        keys = {"4": "verify_enabled", "5": "secury_enabled", "8": "multi_os_boot"}
        key = keys[choice]
        info[key] = not info.get(key, True)
        auth.save_settings(info)
        rprint(f"[yellow]Параметр {key} изменен.[/]")

    elif choice == "6":
        if not info.get("oem_unlock", False):
            rprint("[bold red]КРИТИЧЕСКАЯ ОШИБКА: OEM_UNLOCK заблокирован. ROOT невозможен.[/]")
        else:
            new_val = not auth.is_root_allowed()
            auth.set_root_allowed(new_val)
            rprint(f"Статус ROOT: {get_status_style(new_val)}")

    elif choice == "7":
        # БЕЗОПАСНОСТЬ: Используем getpass, чтобы пароль не отображался при вводе
        if auth.has_root_password():
            old_p = getpass.getpass("Введите текущий пароль ROOT: ")
            if not auth.verify_root_password(old_p):
                rprint("[bold red]ОШИБКА: Доступ запрещен. Неверный пароль![/]")
                time.sleep(1) # Защита от брутфорса
                continue
        
        rprint("[blue]Режим смены пароля активирован.[/]")
        p1 = getpass.getpass("Новый пароль: ")
        if not p1:
            rprint("[red]Отмена: Пароль не может быть пустым.[/]")
            continue
            
        p2 = getpass.getpass("Повторите пароль: ")
        
        if p1 == p2:
            auth.set_root_password(p1)
            rprint("[bold green]Пароль ROOT успешно обновлён и хэширован.[/]")
        else:
            rprint("[bold red]Ошибка: Пароли не совпадают.[/]")

    elif choice == "0":
        rprint("[bold yellow]Завершение сеанса настроек...[/]")
        break
    
    time.sleep(1.5)
    os.system('cls' if os.name == 'nt' else 'clear') # Очистка экрана для красоты