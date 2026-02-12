# Мы импортируем только то, что в белом списке (math, datetime)
import datetime

# Глобальные переменные: console, Panel, Table, Prompt, auth, fs, app_os
# уже доступны в exec_globals, если приложение системное!

def get_status_style(value: bool) -> str:
    return "[bold green]ВКЛ[/]" if value else "[bold red]ВЫКЛ[/]"

def show_menu(info):
    table = Table(title="Системные Настройки", title_style="bold magenta", expand=True)
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Опция", style="white")
    table.add_column("Статус / Значение", justify="right")

    # Используем время из SDK или datetime
    table.add_row("1", "Текущее время", datetime.datetime.now().strftime('%H:%M:%S'))
    table.add_row("2", "Имя пользователя", f"[yellow]{info.get('username', 'user')}[/]")
    
    # Работаем через FS драйвер вместо os.listdir
    apps_count = len(fs.list_dir("/app")) if fs.exists("/app") else 0
    table.add_row("3", "Список приложений", f"{apps_count} шт.")
    
    table.add_row("4", "Проверка целостности", get_status_style(info.get("verify_enabled", True)))
    table.add_row("5", "Модуль безопасности", get_status_style(info.get("secury_enabled", True)))
    table.add_row("6", "Доступ к ROOT", "[bold yellow]ОГРАНИЧЕНО[/]" if not info.get("oem_unlock") else get_status_style(info.get("allow_root")))
    table.add_row("7", "Управление паролем ROOT", "[dim]********[/]")
    table.add_row("8", "Выбор нескольких ОС", get_status_style(info.get("multi_os_boot", False)))
    table.add_row("9", "Цвет промпта", f"[{info.get('color', 'cyan')}]{info.get('color', 'cyan')}[/]")
    table.add_row("10", "Название системы (Hostname)", f"[bold blue]{info.get('name_os', 'CawOS')}[/]")
    table.add_row("0", "[bold red]Выход[/]", "")

    console.print(table)

# Основной цикл
app_os["log"]("Settings menu opened")

while True:
    info = auth.load_settings() 
    show_menu(info)
    
    choice = Prompt.ask("[bold cyan]Введите номер опции[/]").strip()

    if choice == "1":
        console.print(f"[bold green]Дата и время:[/] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    elif choice == "2":
        new_name = Prompt.ask("Введите новое имя пользователя").strip()
        if new_name:
            old_name = info.get('username', 'user')
            info["username"] = new_name
            auth.save_settings(info)
            app_os["log"](f"Username changed: {old_name} -> {new_name}")
            console.print(f"[green]✔ Имя изменено на {new_name}[/]")

    elif choice == "3":
        if fs.exists("/app"):
            apps = [f[:-3] for f in fs.list_dir("/app") if f.endswith(".py")]
            console.print(Panel("\n".join(apps), title="Установленное ПО"))
        else:
            console.print("[red]Ошибка: Папка приложений не найдена[/]")

    elif choice in ["4", "5", "8"]:
        keys = {"4": "verify_enabled", "5": "secury_enabled", "8": "multi_os_boot"}
        key = keys[choice]
        info[key] = not info.get(key, True)
        auth.save_settings(info)
        console.print(f"[yellow]Параметр {key} изменен.[/]")

    elif choice == "6":
        if not info.get("oem_unlock", False):
            console.print("[bold red]КРИТИЧЕСКАЯ ОШИБКА: OEM заблокирован.[/]")
        else:
            new_val = not auth.is_root_allowed()
            auth.set_root_allowed(new_val)
            console.print(f"Статус ROOT: {get_status_style(new_val)}")

    elif choice == "7":
        # Используем Prompt с password=True вместо getpass
        if auth.has_root_password():
            old_p = Prompt.ask("Введите текущий пароль ROOT", password=True)
            if not auth.verify_root_password(old_p):
                console.print("[bold red]ОШИБКА: Неверный пароль![/]")
                continue
        
        p1 = Prompt.ask("Новый пароль", password=True)
        if p1:
            p2 = Prompt.ask("Повторите пароль", password=True)
            if p1 == p2:
                auth.set_root_password(p1)
                console.print("[bold green]Пароль ROOT успешно обновлён.[/]")
            else:
                console.print("[bold red]Ошибка: Пароли не совпадают.[/]")

    elif choice == "9":
        colors = ["cyan", "magenta", "yellow", "green", "red", "white", "blue"]
        console.print(f"[bold]Доступные цвета:[/] {', '.join(colors)}")
        new_color = Prompt.ask("Введите цвет").strip().lower()
        if new_color in colors:
            info["color"] = new_color
            auth.save_settings(info)
            console.print(f"[green]✔ Цвет изменен на {new_color}[/]")

    elif choice == "10":
        new_os_name = Prompt.ask("Введите новое название системы").strip()
        if new_os_name:
            info["name_os"] = new_os_name
            auth.save_settings(info)
            console.print(f"[green]✔ Система переименована в {new_os_name}[/]")

    elif choice == "0":
        break
    
    Prompt.ask("\nНажмите Enter чтобы продолжить")
    console.clear()