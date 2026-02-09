def check_system_status():
    # Пишем в системный лог о начале проверки (User App Log)
    app_os["log"](f"Status check started by user app")

    status = app_os["get_status"]()
    
    root_active = status.get("root_active", "NULL")
    root_allowed = status.get("root_allowed", "NULL")
    is_unlocked = status.get("bootloader_unlocked", "NULL")

    # Логика для Доступа к ROOT
    if root_allowed == "NULL":
        access_status = "[dim]НЕИЗВЕСТНО[/]"
    elif root_allowed is True:
        access_status = "[bold red]РАЗРЕШЕН[/]"
    else:
        access_status = "[bold green]ЗАБЛОКИРОВАН[/]"

    # Логика для Текущего состояния
    if root_active == "NULL":
        active_status = "[bold white on red] ERROR [/]"
        app_os["log_err"]("Root state is NULL - potential system info failure")
    elif root_active is True:
        active_status = "[bold red]АКТИВЕН[/]"
    else:
        active_status = "[bold green]ВЫКЛЮЧЕН[/]"

    # Логика загрузчика
    boot_status = "[bold red]РАЗБЛОКИРОВАН[/]" if is_unlocked is True else "[bold green]ЗАБЛОКИРОВАН[/]"
    if is_unlocked == "NULL": 
        boot_status = "[dim]NULL[/]"

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

    # Умные советы + логирование аномалий
    if root_allowed is True and root_active is False:
        app_os["print"]("[dim]ℹ️ Доступ разрешен. Используйте команду [white]'root'[/white] для активации.[/]")
    
    elif root_allowed is False and is_unlocked is True:
        # Логируем подозрительное состояние
        app_os["log_warn"]("Inconsistency detected: Bootloader unlocked but ROOT disabled in settings")
        app_os["print"]("[bold yellow]⚠️ ROOT разрешен в загрузчике, но выключен в системе.[/]")

# Запуск
try:
    check_system_status()
    app_os["log"]("Status check finished successfully")
except Exception as e:
    # Если в приложении произойдет ошибка, оно само может залогировать её (если успеет)
    app_os["log_err"](f"App error: {str(e)}")