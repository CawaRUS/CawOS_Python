import os
import json
import zipfile
import shutil
import requests
import hashlib
import core.fs.fs as fs  # Импортируем твою файловую систему
from rich.prompt import Confirm, Prompt
from rich.progress import Progress

about = "Менеджер пакетов CawOS (SDK + Remote)"

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def execute(args, kernel, console):
    REPO_URL = "https://cawas.duckdns.org/package"

    if not args or args[0] not in ["install", "remote", "list", "build", "push"]:
        console.print("[yellow]Использование:[/yellow]")
        console.print("  cop build <папка>    - собрать пакет")
        console.print("  cop push <файл.cop>  - отправить на сервер")
        console.print("  cop install <путь>   - локальная установка")
        console.print("  cop remote <имя>     - установка из репозитория")
        return

    # --- СБОРКА ПАКЕТА (BUILD) ---
    if args[0] == "build":
        if len(args) < 2:
            console.print("[red]Ошибка: Укажите папку для сборки[/red]")
            return
        
        # 1. Определяем, ЧТО собираем
        raw_path = args[1]
        src_dir = fs.get_full_path(raw_path) 
        
        # 2. Проверки папки и конфига (оставляем как было)
        if not os.path.exists(src_dir):
            console.print(f"[bold red]❌ ОШИБКА:[/bold red] Директория '[white]{raw_path}[/white]' не найдена.")
            return
        
        about_path = os.path.join(src_dir, "about.json")
        if not os.path.exists(about_path):
            console.print(f"[bold red]❌ ОШИБКА:[/bold red] В папке отсутствует [yellow]about.json[/yellow]")
            return

        try:
            with open(about_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            pkg_name = data.get("name", "unknown")
            
            # --- МАГИЯ ПУТИ СОХРАНЕНИЯ ---
            # Берем текущий путь пользователя из fs.current_path
            # и создаем полный путь для сохранения .cop файла именно туда
            file_name = f"{pkg_name}.cop"
            output_full_path = os.path.join(fs.current_path, file_name)

            # 4. Сборка архива
            # Теперь используем полный путь для сохранения
            with zipfile.ZipFile(output_full_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(src_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, src_dir)
                        zipf.write(file_path, arcname)
            
            console.print(f"[bold green]✓ Пакет {file_name} успешно собран![/bold green]")
            console.print(f"[dim]Сохранено в: {output_full_path}[/dim]")
            console.print(f"[dim]SHA256: {calculate_sha256(output_full_path)}[/dim]")
            
        except Exception as e:
            console.print(f"[red]Критическая ошибка сборки: {e}[/red]")

    # --- ПУБЛИКАЦИЯ (PUSH) ---
    elif args[0] == "push":
        if len(args) < 2:
            console.print("[red]Ошибка: Укажите файл .cop[/red]")
            return
        
        # Также используем fs для поддержки локальных путей
        file_path = fs.get_full_path(args[1])
        
        if not os.path.exists(file_path):
            console.print(f"[red]Файл '{args[1]}' не найден![/red]")
            return

        token = Prompt.ask("Введите Token доступа", password=True)
        
        try:
            with open(file_path, "rb") as f:
                files = {'file': f}
                payload = {'token': token, 'hash': calculate_sha256(file_path)}
                
                console.print(f"[cyan]Отправка на сервер...[/cyan]")
                r = requests.post(f"{REPO_URL}", files=files, data=payload, timeout=30)
                r.raise_for_status()
                
            console.print(f"[bold green]✓ Пакет опубликован![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Ошибка публикации:[/bold red] {e}")

    # --- УСТАНОВКА ---
    elif args[0] == "install":
        if len(args) < 2:
            console.print("[red]Укажите путь к .cop[/red]")
            return
        install_local(fs.get_full_path(args[1]), kernel, console)
    
# --- УДАЛЕННАЯ УСТАНОВКА ---
    elif args[0] == "remote":
        if len(args) < 2:
            console.print("[red]Ошибка: Укажите имя пакета[/red]")
            return
        
        pkg_name = args[1].replace(".cop", "")
        # Теперь стучимся сразу к .cop файлу
        FILE_URL = f"https://cawas.duckdns.org/package/{pkg_name}.cop"

        try:
            console.print(f"[cyan]Поиск '{pkg_name}' на сервере...[/cyan]")
            
            # 1. Скачиваем во временный файл
            temp_path = os.path.join(fs.current_path, f"downloading_{pkg_name}.cop")
            
            with requests.get(FILE_URL, stream=True) as r:
                if r.status_code == 404:
                    console.print(f"[red]Пакет '{pkg_name}' не найден.[/red]")
                    return
                r.raise_for_status()
                
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # 2. Открываем архив, чтобы прочитать о чем он
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                if 'about.json' not in zip_ref.namelist():
                    console.print("[bold red]Ошибка: Пакет поврежден (нет about.json)[/bold red]")
                    os.remove(temp_path)
                    return
                
                with zip_ref.open('about.json') as f:
                    pkg_data = json.load(f)
                
                # Показываем инфу пользователю
                console.print(f"\n[bold blue]ИНФОРМАЦИЯ О ПАКЕТЕ:[/bold blue]")
                console.print(f"📦 Имя: [green]{pkg_data.get('name', '???')}[/green]")
                console.print(f"📝 Описание: {pkg_data.get('description', 'Нет описания')}")
                console.print(f"👤 Автор: {pkg_data.get('author', 'Неизвестен')}")
                console.print(f"🏗 Тип: {pkg_data.get('type', 'app')}")
                console.print(f"📏 Размер: {os.path.getsize(temp_path) // 1024} KB")

                if not Confirm.ask("\n[bold yellow]Установить этот пакет?[/bold yellow]"):
                    os.remove(temp_path)
                    console.print("[gray]Установка отменена.[/gray]")
                    return

            # 3. Если согласились — вызываем локальную установку
            # Переименовываем в нормальное имя, чтобы install_local не путался
            final_temp = os.path.join(fs.current_path, f"{pkg_name}.cop")
            os.rename(temp_path, final_temp)
            
            install_local(final_temp, kernel, console)
            
            # Чистим за собой
            if os.path.exists(final_temp):
                os.remove(final_temp)

        except Exception as e:
            console.print(f"[bold red]Ошибка:[/bold red] {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

def install_local(package_path, kernel, console):
    # Логика установки остается прежней, но теперь всегда получает полный путь
    try:
        if not os.path.exists(package_path):
            console.print(f"[red]Файл '{package_path}' не найден.[/red]")
            return

        with zipfile.ZipFile(package_path, 'r') as zip_ref:
            if 'about.json' not in zip_ref.namelist():
                console.print("[bold red]Ошибка: В пакете нет about.json![/bold red]")
                return
            
            with zip_ref.open('about.json') as f:
                pkg_about = json.load(f)

            pkg_name = pkg_about.get("name", "unknown")
            pkg_type = pkg_about.get("type", "app")
            
            if pkg_type == "pack":
                if not kernel.root_mode:
                    console.print("[bold white on red] ACCESS DENIED [/]\n[red]ROOT необходим для 'pack'.[/red]")
                    return
                install_dir = os.path.join("core", "bin", pkg_name)
            else:
                install_dir = os.path.join("data", "0", "app", pkg_name)

            if os.path.exists(install_dir):
                shutil.rmtree(install_dir)

            os.makedirs(install_dir, exist_ok=True)
            zip_ref.extractall(install_dir)
            console.print(f"[bold green]✓ '{pkg_name}' установлен в {install_dir}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Ошибка установки:[/bold red] {e}")