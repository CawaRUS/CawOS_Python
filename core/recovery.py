# core/recovery.py — Модуль восстановления CawOS 1.3
import os
import shutil
import time
import zipfile
import requests
import logging
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn
from rich.prompt import Prompt, Confirm

# Инициализация логгера
logger = logging.getLogger("recovery")

try:
    from main import clear_screen
except ImportError:
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

console = Console()

# --- БЕЗОПАСНЫЙ ИМПОРТ ВЕРСИИ ---
try:
    from data.info import info
    SYSTEM_VERSION = info.version
except Exception:
    SYSTEM_VERSION = "NULL"

# Конфигурация сервера обновлений
UPDATE_SERVER = "http://cawas.duckdns.org/system.zip"

def menu(reason="Manual entry"):
    """Главное меню Recovery Mode."""
    logger.info(f"Entered Recovery Mode. Reason: {reason}")
    while True:
        clear_screen()
        console.print(Panel(
            f"[bold red]CawOS RECOVERY MODE[/bold red]\n"
            f"[yellow]Status:[/yellow] {reason}", 
            border_style="red",
            title=f"v {SYSTEM_VERSION} System Maintenance",
            expand=True
        ))
        
        console.print("1. [bold green]Reboot[/bold green] — Обычная загрузка")
        console.print("2. [bold cyan]System Repair (OTA)[/bold cyan] — ПОЛНАЯ переустановка ОС по сети")
        console.print("3. [bold magenta]Wipe Data[/bold magenta] — Сброс настроек (сохраняя приложения)")
        console.print("4. [bold white]Power Off[/bold white] — Выключить устройство")
        
        choice = Prompt.ask("\nВыберите действие", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            logger.info("Recovery: User requested reboot")
            return "reboot"
        
        elif choice == "2":
            if run_ota_repair():
                return "reboot"
            
        elif choice == "3":
            run_wipe_data()
            
        elif choice == "4":
            logger.info("Recovery: System power off")
            os._exit(0)

def run_ota_repair():
    """Сетевое восстановление ВСЕЙ системы."""
    logger.info("OTA Repair initiated")
    console.print(Panel(
        "[bold yellow]ВНИМАНИЕ:[/bold yellow]\n"
        "Будет произведена полная замена системных файлов (core, main.py, data/info.py).\n"
        "Ваши файлы в [cyan]data/0[/cyan] и настройки [cyan]data/json[/cyan] затронуты не будут.",
        title="OTA Repair Info"
    ))
    
    if not Confirm.ask("Начать процесс восстановления?"):
        logger.info("OTA Repair cancelled by user")
        return False

    console.print(f"\n[cyan]Подключение к {UPDATE_SERVER}...[/cyan]")
    logger.info(f"Connecting to {UPDATE_SERVER}")
    
    try:
        # 1. Загрузка
        response = requests.get(UPDATE_SERVER, stream=True, timeout=15)
        if response.status_code != 200:
            logger.error(f"OTA Server error: HTTP {response.status_code}")
            console.print(f"[bold red]Ошибка:[/bold red] Сервер вернул код {response.status_code}")
            time.sleep(2)
            return False

        total_size = int(response.headers.get('content-length', 0))
        temp_zip = "recovery_cache.zip"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("[yellow]Загрузка полного образа...", total=total_size)
            
            with open(temp_zip, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

        # 2. Распаковка
        logger.info("Download complete. Extracting system image...")
        console.print("[yellow]Распаковка и замена системных компонентов...[/yellow]")
        
        temp_dir = "temp_extraction"
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # 3. Установка
        logger.info("Applying system update (overwriting core files)...")
        shutil.copytree(temp_dir, ".", dirs_exist_ok=True)

        # Очистка
        os.remove(temp_zip)
        shutil.rmtree(temp_dir)

        logger.info("OTA Repair: Success")
        console.print("[bold green]✓ Система CawOS успешно переустановлена![/bold green]")
        input("\nНажмите Enter для перезагрузки...")
        return True

    except Exception as e:
        logger.exception("OTA Repair failed with critical error")
        console.print(f"[bold red]Критическая ошибка восстановления:[/bold red] {e}")
        input("\nНажмите Enter...")
        return False

def run_wipe_data():
    """Сброс пользовательских данных с восстановлением структуры."""
    logger.warning("User initiated WIPE DATA")
    console.print("\n[bold red]ВНИМАНИЕ: Все настройки и личные файлы будут удалены![/bold red]")
    if Confirm.ask("Выполнить Wipe Data (Factory Reset)?", default=False):
        try:
            # 1. Сброс JSON настроек
            json_dir = os.path.join("data", "json")
            if os.path.exists(json_dir):
                shutil.rmtree(json_dir)
            os.makedirs(json_dir)
            logger.info("Wipe Data: JSON settings cleared")
            console.print("[green]✓[/green] Системные конфиги сброшены.")

            # 2. Очистка и восстановление data/0
            user_dir = os.path.join("data", "0")
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)

            required_dirs = ["app", "download", "documents", "photos", "music"]

            for item in os.listdir(user_dir):
                if item == "app": 
                    continue
                
                item_path = os.path.join(user_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    else:
                        shutil.rmtree(item_path)
                except Exception as e:
                    logger.error(f"Failed to clear {item}: {e}")
                    console.print(f"[dim red]Ошибка очистки {item}: {e}[/dim red]")

            for folder in required_dirs:
                path = os.path.join(user_dir, folder)
                if not os.path.exists(path):
                    os.makedirs(path)
            
            logger.info("Wipe Data: Success")
            console.print("[green]✓[/green] Структура папок [cyan]data/0[/cyan] восстановлена.")
            input("\nСброс завершен успешно. Нажмите Enter для перезагрузки...")
            clear_screen()
        except Exception as e:
            logger.exception("Wipe Data failed")