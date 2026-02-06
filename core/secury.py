import os
import json
import logging
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

# Инициализация логгера
logger = logging.getLogger("secury")

try:
    import data.info as info
except ImportError:
    logger.warning("data.info module not found")
    info = None

import core.fs.fs as fs 
from core import auth 

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def sec_block():
    """Проверка чистого завершения предыдущей сессии."""
    logger.info("Running security boot check (sec_block)")
    try:
        settings = auth.load_settings()
    except Exception as e:
        logger.error(f"Could not load settings in sec_block: {e}")
        settings = {"secury_enabled": True}
        
    if not settings.get("secury_enabled", True):
        logger.warning("Security module is DISABLED in settings")
        console.print("[yellow][Secury] Модуль защиты отключен в настройках.[/yellow]")
        return True

    exit_status = 1 
    if info and hasattr(info, "get_exit_on"):
        exit_status = info.get_exit_on()

    if exit_status == 0:  # Аварийный флаг
        logger.warning("Unclean shutdown detected! Triggering Emergency Mode.")
        clear_screen()
        console.print(Panel(
            "[bold white]CawOS обнаружила некорректное завершение работы.[/bold white]\n"
            "Возможно, произошел программный сбой или принудительная остановка.",
            title="[bold red]⚠️ SYSTEM RESCUE[/bold red]",
            border_style="red",
            subtitle="[yellow]Emergency Mode[/yellow]"
        ))
        
        if Confirm.ask("[bold cyan]Запустить систему в обычном режиме?[/bold cyan]", default=True):
            logger.info("User chose to continue boot after unclean shutdown")
            if info and hasattr(info, "set_exit_on"):
                info.set_exit_on(0) 
            clear_screen()
            return True
        else:
            logger.critical("Boot aborted by user in Emergency Mode")
            console.print("[bold red]Загрузка отменена.[/bold red]")
            os._exit(1)
            
    else:
        logger.debug("Clean shutdown verified. Setting session flag to 0 (Active)")
        if info and hasattr(info, "set_exit_on"):
            info.set_exit_on(0)
        return True

def confirm_delete(path, is_root):
    """Интеллектуальное подтверждение удаления."""
    try:
        settings = auth.load_settings()
    except Exception:
        settings = {"secury_enabled": True}

    if not settings.get("secury_enabled", True):
        logger.debug(f"Bypassing delete confirmation for: {path} (Secury disabled)")
        return True

    secury_file_path = os.path.abspath(__file__)
    target_full_path = fs.get_full_path(path)

    # 1. Защита КОРНЯ
    if path in ["/", "\\", "root"]:
        logger.critical(f"ACCESS DENIED: Attempt to delete ROOT directory by {'Root' if is_root else 'User'}")
        console.print(Panel(
            "[bold red]ДОСТУП ЗАПРЕЩЕН[/bold red]\nУдаление корневого каталога приведет к гибели ОС.",
            title="[white on red] CRITICAL PROTECT [/]",
            border_style="red"
        ))
        return False

    # 2. Самозащита модуля Secury
    if target_full_path == secury_file_path:
        logger.warning("SELF-PROTECT: Blocked attempt to delete secury.py")
        console.print("[bold red]🛡️ [Secury]: Я не могу позволить вам удалить протоколы защиты.[/bold red]")
        return False

    # 3. Подтверждение для обычных файлов
    logger.info(f"Deletion pending for: {path} (Full: {target_full_path})")
    console.print(Panel(
        f"Вы собираетесь безвозвратно удалить:\n[bold cyan]{path}[/bold cyan]\n"
        f"[dim]Полный путь: {target_full_path}[/dim]",
        title="[bold yellow]ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ[/bold yellow]",
        border_style="yellow"
    ))

    if Confirm.ask("[bold red]Вы уверены?[/bold red]", default=False):
        logger.warning(f"User CONFIRMED deletion of: {path}")
        return True
    else:
        logger.info(f"User CANCELLED deletion of: {path}")
        console.print("[green]Действие отменено.[/green]")
        return False