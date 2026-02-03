# verify.py — Проверка целостности (обновлен с 'rich')
import os
import time
import json
from core import auth  # <--- ИЗМЕНЕНИЕ: Импортируем auth
from main import clear_screen # (main.py тоже нужно будет обновить)

# --- ИЗМЕНЕНИЯ ---
# Убираем colorama, импортируем rich
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
# --------------------

console = Console()

REQUIRED_FILES = [
    'core/verify.py',
    'core/boot.py',
    'core/secury.py',
    'data/info.py',
    'core/fs/fs.py',
    'core/shell.py',
    'core/auth.py',
    'core/os/CawOS/kernel.py'
]
# --- УДАЛЕНО ---
# Локальная функция load_settings() удалена.
# Мы будем использовать auth.load_settings()
# -----------------

def verify_system_integrity():
    # --- ИЗМЕНЕНИЕ ---
    # Используем единую функцию из auth.py
    try:
        settings = auth.load_settings()
    except Exception:
        settings = {"verify_enabled": True}
    # -----------------
    
    if not settings.get("verify_enabled", True):
        console.print("[yellow][Verify] Проверка целостности отключена в настройках.[/yellow]")
        return True

    missing_files = []
    for file in REQUIRED_FILES:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        clear_screen()
        
        # --- УЛУЧШЕНИЕ UI ---
        # Формируем список файлов для 'Panel'
        files_str = "\n".join([f"- {file}" for file in missing_files])
        
        panel_content = (
            f"[bold]Missing critical files:[/bold]\n\n{files_str}\n\n"
            f"[bold red]KERNEL PANIC: CRITICAL FILES MISSING[/bold red]"
        )
        
        console.print(
            Panel(
                panel_content,
                title="[bold red]SYSTEM INTEGRITY CHECK FAILED[/bold red]",
                border_style="red"
            )
        )
        
        console.print("[yellow]\nSystem will terminate in 5 seconds...[/yellow]")
        
        # Красивый 5-секундный таймер
        with Progress(transient=True) as progress:
            task = progress.add_task("[red]Shutting down...", total=5)
            for i in range(5):
                time.sleep(1)
                progress.update(task, advance=1)
        # --------------------
        
        os._exit(1)
    return True