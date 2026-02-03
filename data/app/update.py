import requests
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import data.info as info 

console = Console()
VERSION_URL = "http://cawas.duckdns.org/version.json"

# Пытаемся достать версию из ядра (если shell передает kernel) 
# Или читаем напрямую из info.json, как в settings.py
info_path = os.path.join("data", "json", "info.json")

def get_current_version():
    try:
        import data.info as info_module
        # Обращаемся к классу info внутри модуля info.py
        return info_module.info.version
    except Exception as e:
        # Если не получилось, попробуем прочитать из JSON (на всякий случай)
        try:
            with open(os.path.join("data", "json", "info.json"), "r") as f:
                return json.load(f).get("version", "NULL")
        except:
            return "NULL"

current_version = get_current_version()

console.print(Panel(f"[bold cyan]CawOS Update Center[/bold cyan]\n[dim]Текущая версия: {current_version}[/dim]", expand=False))

try:
    # 1. Проверка версии
    console.print(f"[bold cyan]Проверка обновелний...[/bold cyan]")
    r = requests.get(VERSION_URL, timeout=5)
    r.raise_for_status()
    data = r.json()
    
    remote_version = data['version_name']
    
    if remote_version != current_version:
        console.print(f"[bold green]Доступно обновление![/bold green]")
        console.print(f"Новая версия: [bold white]{remote_version}[/bold white]")
        console.print(f"Что нового: [italic]{data.get('changelog', 'Нет описания')}[/italic]\n")

        if console.input("Начать загрузку и подготовку? (y/n): ").lower() == 'y':
            # 2. Загрузка
            with requests.get(data['archive_url'], stream=True) as r:
                total_size = int(r.headers.get('content-length', 0))
                with open("update_package.zip", "wb") as f:
                    with Progress() as progress:
                        task = progress.add_task("[yellow]Скачивание...", total=total_size)
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

            # 3. Флаг готовности
            with open("update_pending.flag", "w", encoding="utf-8") as f:
                f.write(remote_version)

            console.print("\n[bold green]Пакет загружен.[/bold green] Система будет обновлена при перезагрузке.")
            if console.input("Перезагрузить CawOS сейчас? (y/n): ").lower() == 'y':
                # Вызываем системную команду выхода (зависит от твоего ядра)
                # Если kernel недоступен, можно просто os._exit(0)
                info.set_exit_on(1)
                os._exit(1) 
    else:
        console.print("[green]У вас установлена актуальная версия.[/green]")

except Exception as e:
    console.print(f"[bold red]Ошибка центра обновлений:[/bold red] {e}")

input("\nНажмите Enter для выхода...")