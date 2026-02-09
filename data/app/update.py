deadlock = True
import requests
import os
import json
import hashlib
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
import data.info as info 

console = Console()
VERSION_URL = "http://cawas.duckdns.org/version.json"

def reboot():
    """Завершение процесса для перезагрузки через main.py"""
    os._exit(0)

def calculate_sha256(file_path):
    """Вычисляет SHA-256 хеш файла."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_current_version():
    """Получение текущей версии из файлов системы."""
    try:
        # Пытаемся взять из загруженного модуля
        return info.info.version
    except Exception:
        try:
            with open(os.path.join("data", "json", "info.json"), "r") as f:
                return json.load(f).get("version", "NULL")
        except:
            return "NULL"

# Инициализация
current_version = get_current_version()
console.print(Panel(f"[bold cyan]CawOS Update Center[/bold cyan]\n[dim]Текущая версия: {current_version}[/dim]", expand=False))

try:
    # 1. Запрос данных с сервера
    console.print(f"[bold cyan]Проверка обновлений...[/bold cyan]")
    r = requests.get(VERSION_URL, timeout=5)
    r.raise_for_status()
    data = r.json()
    
    remote_version = data['version_name']
    expected_hash = data.get('sha256')
    update_tag = data.get('tag', 'global').lower() # Теги: global, fix, mandatory
    changelog = data.get('changelog', 'Нет описания')

    # Логика тегов: mandatory игнорирует проверку версии
    is_mandatory = update_tag == "mandatory"
    has_new_version = remote_version != current_version

    if has_new_version or is_mandatory:
        # Настройка стиля в зависимости от тега
        if is_mandatory:
            tag_display = "[bold red]ОБЯЗАТЕЛЬНОЕ ОБНОВЛЕНИЕ[/bold red]"
            border_style = "red"
        elif update_tag == "fix":
            tag_display = "[bold yellow]ИСПРАВЛЕНИЕ (FIX)[/bold yellow]"
            border_style = "yellow"
        else:
            tag_display = "[bold blue]ГЛОБАЛЬНОЕ ОБНОВЛЕНИЕ[/bold blue]"
            border_style = "blue"

        console.print(Panel(
            f"Тип: {tag_display}\n"
            f"Версия: [bold white]{remote_version}[/bold white]\n"
            f"Список изменений: [italic]{changelog}[/italic]",
            title="[bold]Доступен пакет обновления[/bold]",
            border_style=border_style
        ))

        # Текст вопроса (теперь переменная prompt_text всегда доступна здесь)
        prompt_text = "[bold red]Установить критическое обновление? (y/n): [/bold red]" if is_mandatory else "Начать загрузку и подготовку? (y/n): "
        
        # Вся логика загрузки теперь ВНУТРИ условия наличия обновления
        if console.input(prompt_text).lower() == 'y':
            file_name = "update_package.zip"
            with requests.get(data['archive_url'], stream=True) as r:
                r.raise_for_status() 
                total_size = int(r.headers.get('content-length', 0))
                
                with open(file_name, "wb") as f:
                    with Progress() as progress:
                        task = progress.add_task("[yellow]Скачивание...", total=total_size)
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

            # 2. ПРОВЕРКА: Размер файла
            downloaded_size = os.path.getsize(file_name)
            expected_size = data.get('size')
            
            if expected_size and downloaded_size != expected_size:
                console.print(f"[bold red]ОШИБКА: Размер файла не совпадает![/bold red]")
                os.remove(file_name)
                raise Exception("Файл загружен не полностью или поврежден.")

            # 3. Проверка контрольной суммы (SHA-256)
            if expected_hash:
                console.print("[cyan]Проверка целостности файла...[/cyan]")
                actual_hash = calculate_sha256(file_name)
                
                if actual_hash == expected_hash:
                    console.print("[bold green]Контрольная сумма совпала. Файл в порядке.[/bold green]")
                else:
                    console.print("[bold red]ОШИБКА: Контрольная сумма не совпадает![/bold red]")
                    os.remove(file_name)
                    raise Exception("Файл поврежден при загрузке.")
            else:
                console.print("[yellow]Предупреждение: Проверка хеш-суммы пропущена.[/yellow]")

            # 4. Создание флага для main.py
            with open("update_pending.flag", "w", encoding="utf-8") as f:
                f.write(remote_version)

            console.print("\n[bold green]Пакет загружен и проверен.[/bold green] Система будет обновлена при перезагрузке.")
            
            if console.input("Перезагрузить CawOS сейчас? (y/n): ").lower() == 'y':
                if hasattr(info, "set_exit_on"):
                    info.set_exit_on(1)
                reboot()
        else:
            console.print("[yellow]Обновление отменено.[/yellow]")
    else:
        console.print("[green]У вас установлена актуальная версия.[/green]")

except Exception as e:
    console.print(f"[bold red]Ошибка центра обновлений:[/bold red] {e}")

input("\nНажмите Enter для выхода...")