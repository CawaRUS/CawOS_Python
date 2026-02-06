# verify.py — Проверка целостности и статуса загрузчика
import os
import time
import sys
import logging

# Получаем логгер
logger = logging.getLogger("verify")

# --- Ультра-безопасные импорты ---
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
    logger.debug("Rich UI components loaded successfully")
except ImportError:
    logger.warning("Rich library missing in verify module, using fallback")
    class FakeConsole:
        def print(self, text, **kwargs): print(str(text))
    console = FakeConsole()

# Список критических файлов
REQUIRED_FILES = [
    'core/verify.py',
    'core/boot.py',
    'core/secury.py',
    'core/fs/fs.py',
    'core/shell.py',
    'core/auth.py',
    'core/os/CawOS/kernel.py'
]

def safe_clear():
    """Собственная очистка, чтобы не зависеть от main.py"""
    os.system('cls' if os.name == 'nt' else 'clear')

def load_verify_settings():
    """Автономная загрузка настроек без внешних зависимостей."""
    settings_path = os.path.join("data", "json", "settings.json")
    if not os.path.exists(settings_path):
        logger.debug(f"Settings file {settings_path} not found. Using defaults.")
        return {"verify_enabled": True, "oem_unlock": False}
    try:
        import json
        with open(settings_path, "r") as f:
            data = json.load(f)
            logger.debug("Verification settings loaded")
            return data
    except Exception as e:
        logger.error(f"Failed to parse settings.json: {e}")
        return {"verify_enabled": True, "oem_unlock": False}

def verify_system_integrity():
    """Главная проверка целостности."""
    logger.info("Starting system integrity check...")
    from core import auth
    settings = auth.load_settings()
    
    # 1. Если проверка отключена
    if not settings.get("verify_enabled", True): 
        logger.warning("SYSTEM INTEGRITY CHECK IS DISABLED")
        console.print("[yellow][Verify] Модуль проверки отключен в настройках.[/yellow]")
        return True
    
    # 2. Проверка разблокированного загрузчика (OEM Unlock)
    if settings.get("oem_unlock", False):
        logger.warning("BOOTLOADER IS UNLOCKED! Security integrity risk.")
        safe_clear()
        warning_panel = (
            "[bold orange1]ПРЕДУПРЕЖДЕНИЕ: ЗАГРУЗЧИК РАЗБЛОКИРОВАН[/bold orange1]\n\n"
            "Целостность ПО не может быть гарантирована.\n"
            "Риск модификации системных разделов.\n\n"
            "[dim]Загрузка продолжится через 5 секунд...[/dim]"
        )
        console.print(Panel(
            warning_panel,
            title="[bold yellow]! WARNING ![/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
        
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                task = progress.add_task("[yellow]Проверка безопасности...", total=5)
                for _ in range(5):
                    time.sleep(1)
                    progress.update(task, advance=1)
        except Exception as e:
            logger.debug(f"Rich Progress failed: {e}")
            time.sleep(5)
        
        safe_clear()

    # 3. Проверка наличия критических файлов
    logger.debug(f"Checking for {len(REQUIRED_FILES)} required files...")
    missing_files = [f for f in REQUIRED_FILES if not os.path.exists(f)]

    if missing_files:
        logger.critical(f"INTEGRITY FAILURE: Missing files: {missing_files}")
        safe_clear()
        files_str = "\n".join([f"[red]✖ {file}[/red]" for file in missing_files])
        
        console.print(Panel(
            f"[bold red]КРИТИЧЕСКАЯ ОШИБКА ЦЕЛОСТНОСТИ[/bold red]\n\n"
            f"Отсутствуют важные компоненты системы:\n{files_str}\n\n"
            f"[white]Система будет остановлена во избежание Kernel Panic.[/white]",
            title="[bold red]SYSTEM FAILURE[/bold red]",
            border_style="red"
        ))
        
        time.sleep(5)
        return False # Сигнализируем main.py, что нужно уйти в Recovery
        
    logger.info("Integrity check passed.")
    return True