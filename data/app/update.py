import requests
import os
import json
import hashlib # Для работы с контрольными суммами
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import data.info as info 

console = Console()
VERSION_URL = "http://cawas.duckdns.org/version.json"

def reboot():
    return "reboot"

def calculate_sha256(file_path):
    """Вычисляет SHA-256 хеш файла."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Читаем по 4КБ, чтобы не забивать ОЗУ
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_current_version():
    try:
        import data.info as info_module
        return info_module.info.version
    except Exception:
        try:
            with open(os.path.join("data", "json", "info.json"), "r") as f:
                return json.load(f).get("version", "NULL")
        except:
            return "NULL"

current_version = get_current_version()
console.print(Panel(f"[bold cyan]CawOS Update Center[/bold cyan]\n[dim]Текущая версия: {current_version}[/dim]", expand=False))

try:
    # 1. Проверка версии
    console.print(f"[bold cyan]Проверка обновлений...[/bold cyan]")
    r = requests.get(VERSION_URL, timeout=5)
    r.raise_for_status()
    data = r.json()
    
    remote_version = data['version_name']
    expected_hash = data.get('sha256') # Получаем хеш из конфига сервера
    
    if remote_version != current_version:
        console.print(f"[bold green]Доступно обновление![/bold green]")
        console.print(f"Новая версия: [bold white]{remote_version}[/bold white]")
        console.print(f"Что нового: [italic]{data.get('changelog', 'Нет описания')}[/italic]\n")

        if console.input("Начать загрузку и подготовку? (y/n): ").lower() == 'y':
            # 2. Загрузка
            file_name = "update_package.zip"
            with requests.get(data['archive_url'], stream=True) as r:
                total_size = int(r.headers.get('content-length', 0))
                with open(file_name, "wb") as f:
                    with Progress() as progress:
                        task = progress.add_task("[yellow]Скачивание...", total=total_size)
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

            # --- НОВЫЙ БЛОК: ПРОВЕРКА КОНТРОЛЬНОЙ СУММЫ ---
            if expected_hash:
                console.print("[cyan]Проверка целостности файла...[/cyan]")
                actual_hash = calculate_sha256(file_name)
                
                if actual_hash == expected_hash:
                    console.print("[bold green]Контрольная сумма совпала. Файл в порядке.[/bold green]")
                else:
                    console.print("[bold red]ОШИБКА: Контрольная сумма не совпадает![/bold red]")
                    console.print(f"[dim]Ожидалось: {expected_hash}[/dim]")
                    console.print(f"[dim]Получено:  {actual_hash}[/dim]")
                    os.remove(file_name) # Удаляем битый файл
                    raise Exception("Файл поврежден при загрузке. Операция отменена.")
            else:
                console.print("[yellow]Предупреждение: Сервер не предоставил хеш-сумму. Проверка пропущена.[/yellow]")
            # ----------------------------------------------

            # 3. Флаг готовности
            with open("update_pending.flag", "w", encoding="utf-8") as f:
                f.write(remote_version)

            console.print("\n[bold green]Пакет загружен и проверен.[/bold green] Система будет обновлена при перезагрузке.")
            if console.input("Перезагрузить CawOS сейчас? (y/n): ").lower() == 'y':
                info.set_exit_on(1)
                reboot()
    else:
        console.print("[green]У вас установлена актуальная версия.[/green]")

except Exception as e:
    console.print(f"[bold red]Ошибка центра обновлений:[/bold red] {e}")

input("\nНажмите Enter для выхода...")