deadlock = True
# Импортируем только то, что разрешено в run.py
import requests
import hashlib
import json

# Глобальные объекты console, Panel, Table, Prompt, Progress, fs, app_os 
# уже проброшены через exec_globals в run.py

VERSION_URL = "http://cawas.duckdns.org/version.json"

def calculate_sha256(file_path):
    """Вычисляет SHA-256 хеш файла через драйвер fs."""
    sha256_hash = hashlib.sha256()
    # Читаем бинарные данные через твой драйвер
    content = fs.read_file(file_path, bypass_security=True)
    if isinstance(content, str):
        content = content.encode()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()

def get_current_version():
    """Получение текущей версии через системный API."""
    try:
        status = app_os["get_status"]()
        return status.get("version", "NULL")
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
    update_tag = data.get('tag', 'global').lower()
    changelog = data.get('changelog', 'Нет описания')

    is_mandatory = update_tag == "mandatory"
    has_new_version = remote_version != current_version

    if has_new_version or is_mandatory:
        if is_mandatory:
            tag_display, border_style = "[bold red]ОБЯЗАТЕЛЬНОЕ ОБНОВЛЕНИЕ[/bold red]", "red"
        elif update_tag == "fix":
            tag_display, border_style = "[bold yellow]ИСПРАВЛЕНИЕ (FIX)[/bold yellow]", "yellow"
        else:
            tag_display, border_style = "[bold blue]ГЛОБАЛЬНОЕ ОБНОВЛЕНИЕ[/bold blue]", "blue"

        console.print(Panel(
            f"Тип: {tag_display}\n"
            f"Версия: [bold white]{remote_version}[/bold white]\n"
            f"Список изменений: [italic]{changelog}[/italic]",
            title="[bold]Доступен пакет обновления[/bold]",
            border_style=border_style
        ))

        prompt_text = "Установить критическое обновление?" if is_mandatory else "Начать загрузку и подготовку?"
        
        if Confirm.ask(prompt_text):
            file_name = "update_package.zip"
            
            # Загрузка файла
            with requests.get(data['archive_url'], stream=True) as r_file:
                r_file.raise_for_status()
                total_size = int(r_file.headers.get('content-length', 0))
                
                chunks = []
                with Progress() as progress:
                    task = progress.add_task("[yellow]Скачивание...", total=total_size)
                    for chunk in r_file.iter_content(chunk_size=8192):
                        chunks.append(chunk)
                        progress.update(task, advance=len(chunk))
                
                # Собираем файл и пишем через fs драйвер
                full_data = b"".join(chunks)
                fs.write_file(file_name, full_data)

            # 2. ПРОВЕРКА: Размер
            downloaded_size = len(full_data)
            expected_size = data.get('size')
            
            if expected_size and downloaded_size != expected_size:
                console.print(f"[bold red]ОШИБКА: Размер файла не совпадает![/bold red]")
                # В твоем fs нет прямого remove, но можно записать пустоту или игнорировать
                raise Exception("Файл поврежден.")

            # 3. Проверка контрольной суммы
            if expected_hash:
                console.print("[cyan]Проверка целостности файла...[/cyan]")
                actual_hash = calculate_sha256(file_name)
                
                if actual_hash == expected_hash:
                    console.print("[bold green]Контрольная сумма совпала.[/bold green]")
                else:
                    console.print("[bold red]ОШИБКА: SHA-256 mismatch![/bold red]")
                    raise Exception("Checksum failed.")

            # 4. Создание флага для main.py (через fs)
            fs.write_file("update_pending.flag", remote_version)

            console.print("\n[bold green]Пакет готов.[/bold green] Система будет обновлена при перезагрузке.")
            
            if Confirm.ask("Перезагрузить CawOS сейчас?"):
                # Сообщаем ядру о необходимости выхода с кодом 1
                raise SystemExit("Reboot")
        else:
            console.print("[yellow]Обновление отменено.[/yellow]")
    else:
        console.print("[green]У вас установлена актуальная версия.[/green]")

except Exception as e:
    console.print(f"[bold red]Ошибка центра обновлений:[/bold red] {e}")

Prompt.ask("\nНажмите Enter для выхода")