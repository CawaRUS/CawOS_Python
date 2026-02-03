# secury.py — Модуль безопасности (обновлен с 'rich')
import os
import json
import data.info as info
import core.fs.fs as fs # <--- Нам нужен fs для проверки пути
from core import auth # <--- Импортируем auth для настроек

# --- Новые импорты Rich ---
from rich.console import Console
from rich.prompt import Confirm
# -------------------------

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- УЛУЧШЕНИЕ: Убрали дублирование ---
# 'load_settings' теперь импортируется из 'auth'
# (Предполагая, что в auth.py функция _load() переименована в load_settings())
# -----------------------------------

def sec_block():
    try:
        settings = auth.load_settings() # Используем auth
    except Exception:
        settings = {"secury_enabled": True}
        
    if not settings.get("secury_enabled", True):
        console.print("[yellow][Secury] Модуль защиты отключен в настройках.[/yellow]")
        return True

    clear_screen()
    if info.get_exit_on() == 0:  # если аварийное завершение
        console.print("[bold red][Secury] Система была завершена нестабильно![/bold red]")
        
        # --- УЛУЧШЕНИЕ UI ---
        if Confirm.ask("[yellow]Вы хотите запустить ОС?[/yellow]", default=True):
            console.print("Запуск..")
            info.set_exit_on(0) 
            clear_screen()
            return True
        else:
            os._exit(1)
        # --------------------
            
    else:
        info.set_exit_on(0)
        return True

# --- АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ ---
# 'confirm_delete' теперь принимает 'is_root' как аргумент,
# вместо того чтобы импортировать 'kernel'
def confirm_delete(path, is_root):
    try:
        settings = auth.load_settings()
    except Exception:
        settings = {"secury_enabled": True}

    if not settings.get("secury_enabled", True):
        return True

    # --- УЛУЧШЕНИЕ ЛОГИКИ ---
    # Получаем полный, "реальный" путь к файлу secury.py
    secury_file_path = os.path.abspath(__file__)
    # Получаем полный путь к файлу, который хотят удалить
    target_full_path = fs.get_full_path(path)

    if path == "\\":
        if is_root == False:
            console.print("[bold red][Secury] У вас недостаточно прав, чтобы удалить этот файл.[/bold red]")
        else:
            console.print("[bold red][Secury] Вы пытаетесь удалить всю систему, защита не даст это сделать.[/bold red]")
        return False
    # Сравниваем реальные пути, а не просто имена
    elif target_full_path == secury_file_path:
        console.print("[bold red][Secury] Вы пытаетесь удалить защитника, защитник не даст удалить себя.[/bold red]")
        return False
    # ------------------------

    console.print(f"[bold red][Secury] ВНИМАНИЕ! Вы пытаетесь удалить '{path}'[/bold red]")
    console.print("[yellow]Это может привести к потере данных![/yellow]")

    # --- УЛУЧШЕНИЕ UI ---
    if Confirm.ask("Вы уверены?", default=False):
        return True
    else:
        console.print("Удаление отменено.")
        return False
    # --------------------