def check_system_status():
    status = app_os["get_status"]()
    
    root_active = status.get("root_active", "NULL")
    root_allowed = status.get("root_allowed", "NULL")
    is_unlocked = status.get("bootloader_unlocked", "NULL")

    # Логика для Доступа к ROOT
    if root_allowed == "NULL":
        access_status = "[dim]НЕИЗВЕСТНО[/]"
    elif root_allowed is True:
        access_status = "[bold green]РАЗРЕШЕН[/]"
    else:
        access_status = "[bold red]ЗАБЛОКИРОВАН[/]"

    # Логика для Текущего состояния
    if root_active == "NULL":
        active_status = "[bold white on red] ERROR [/]"
    elif root_active is True:
        active_status = "[bold yellow]АКТИВЕН[/]"
    else:
        active_status = "[bold blue]ВЫКЛЮЧЕН[/]"

    # Логика загрузчика
    boot_status = "[bold red]РАЗБЛОКИРОВАН[/]" if is_unlocked is True else "[bold green]ЗАБЛОКИРОВАН[/]"
    if is_unlocked == "NULL": boot_status = "[dim]NULL[/]"

    # Формируем расширенный отчет
    status_text = (
        f"🔓 Загрузчик: {boot_status}\n"
        f"🔑 Доступ к ROOT: {access_status}\n"
        f"🛡️ Состояние ROOT: {active_status}"
    )

    app_os["print"](app_os["Panel"](
        status_text, 
        title="📊 Расширенный статус системы", 
        expand=False, 
        border_style="cyan"
    ))

    # Умные советы
    if root_allowed is True and root_active is False:
        app_os["print"]("[dim]ℹ️ Доступ разрешен. Используйте команду [white]'root'[/white] для активации.[/]")
    elif root_allowed is False and is_unlocked is True:
        app_os["print"]("[bold yellow]⚠️ ROOT разрешен в загрузчике, но выключен в системе.[/]")

check_system_status()