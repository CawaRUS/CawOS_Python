# verify.py — Проверка целостности и статуса загрузчика
import os
import time
import sys

# --- Ультра-безопасные импорты ---
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
except ImportError:
    # Если Rich нет, мы в беде, но должны работать
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
    settings_path = os.path.join("data", "json", "settings.json") # Или где у тебя лежат настройки auth
    if not os.path.exists(settings_path):
        return {"verify_enabled": True, "oem_unlock": False}
    try:
        import json
        with open(settings_path, "r") as f:
            return json.load(f)
    except:
        return {"verify_enabled": True, "oem_unlock": False}

def verify_system_integrity():
    """Главная проверка целостности."""
    settings = load_verify_settings()
    
    # 1. Если проверка отключена — выходим мгновенно
    if not settings.get("verify_enabled", True):
        return True
    
    # 2. Проверка разблокированного загрузчика (OEM Unlock)
    if settings.get("oem_unlock", False):
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
        
        # Используем простую задержку, если Progress упадет
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                task = progress.add_task("[yellow]Проверка безопасности...", total=5)
                for _ in range(5):
                    time.sleep(1)
                    progress.update(task, advance=1)
        except:
            time.sleep(5)
        
        safe_clear()

    # 3. Проверка наличия критических файлов
    missing_files = [f for f in REQUIRED_FILES if not os.path.exists(f)]

    if missing_files:
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
        
    return True