# shell.py — красивая командная строка на 'rich'
import core.fs.fs as fs
from data.info import real_time
import os, json, time
import core.secury as secury
from core import auth
import requests # <--- Для новой команды http

# --- Новые импорты Rich ---
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as install_traceback
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.progress import Progress
# -------------------------

# Инициализируем консоль rich и красивый вывод ошибок
console = Console()
install_traceback()

root_dir = os.path.abspath(os.path.join(os.getcwd(), "data", "0"))

def clear():
    os.system("cls" if os.name == 'nt' else 'clear')

def run(kernel_instance):
    previous_path = fs.current_path

    # --- УЛУЧШЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ ---
    # Загружаем конфиг ОДИН РАЗ перед циклом, а не на каждой итерации
    try:
        with open("data/json/info.json", "r", encoding="utf-8") as f:
            info_data = json.load(f)
    except:
        info_data = {}

    username = info_data.get("username", "user")
    # 'rich' использует имена цветов, а не объекты Fore
    user_color = info_data.get("color", "cyan").lower()
    # ------------------------------------

    while kernel_instance.running:
        
        # --- УЛУЧШЕНИЕ UI ---
        # Используем 'rich.prompt' для красивого ввода
        prompt_style = f"bold {user_color}"
        prompt_text = f"[{prompt_style}]{username}@CawOS[/{prompt_style}] > "
        cmd_str = Prompt.ask(prompt_text, default="")
        cmd = cmd_str.strip().split()
        # --------------------

        if not cmd:
            continue

        command = cmd[0].lower()

        if command == "exit":
            if Confirm.ask("[yellow]Вы уверены, что хотите выключить ОС?[/yellow]"):
                kernel_instance.shutdown()

        elif command == "clear":
            clear()

        elif command == "help":
            table = Table(title="[bold blue]Справка по командам CawOS[/bold blue]")
            table.add_column("Команда", style="cyan", no_wrap=True)
            table.add_column("Описание", style="magenta")
            
            # --- РЕФАКТОРИНГ UI ---
            commands_list = [
                ("help", "Показать это сообщение"),
                ("exit", "Выключить ОС"),
                ("clear", "Очистить экран"),
                ("ls", "Показать содержимое каталога"),
                ("cd <папка>", "Сменить каталог (.. назад, \\ в корень)"),
                ("cat <файл>", "Показать содержимое файла"),
                ("mkdir <имя>", "Создать папку"),
                ("touch <имя>", "Создать пустой файл"),
                ("rm <имя>", "Удалить файл или папку"),
                ("echo <текст>", "Вывести текст"),
                ("echo > <файл>", "Записать текст в файл"),
                ("run <прил>", "Запустить приложение из /app"),
                ("root", "Включить/выключить режим root"),
                ("whoami", "Показать текущего пользователя (user/root)"),
                ("pwd", "Показать текущий рабочий каталог"),
                ("sysinfo", "Показать информацию о системе"),
                ("date", "Показать текущее время"),
                ("edit <файл>", "Простой текстовый редактор"),
                ("sleep <сек>", "Пауза (ожидание)"),
                ("http <url>", "Показать содержимое веб-страницы (GET)"),
                ("reboot <mode>", "Перезагрузить устройство"),
            ]
            for c, d in commands_list:
                table.add_row(c, d)
            console.print(table)
            # --------------------
            
        # Внутри обработчика команд в ядре
        elif cmd[0] == "reboot":
            args = cmd # Мы уже разделили строку, так что args это и есть cmd
            boot_mode_path = os.path.join("data", "json", "boot_mode.json")
            
            os.makedirs(os.path.dirname(boot_mode_path), exist_ok=True)

            if len(args) == 1:
                print("[SYSTEM] Перезагрузка системы...")
                with open(boot_mode_path, "w") as f:
                    json.dump({"mode": "normal"}, f)
                os._exit(0)

            # Используем args[1], так как args[0] это само слово 'reboot'
            elif args[1] in ["bootloader", "fastboot"]:
                print("[SYSTEM] Перезагрузка в режим загрузчика (FASTBOOT)...")
                with open(boot_mode_path, "w") as f:
                    json.dump({"mode": "fastboot"}, f)
                os._exit(0)

            elif args[1] == "recovery":
                print("[SYSTEM] Перезагрузка в режим восстановления (RECOVERY)...")
                with open(boot_mode_path, "w") as f:
                    json.dump({"mode": "recovery"}, f)
                os._exit(0)

            else:
                print(f"[ERROR] Неизвестный параметр перезагрузки: {args[1]}")
        elif command == "whoami":
            console.print(f"[bold green]root[/bold green]" if kernel_instance.root_mode else "user")

        elif command == "root":
            # (Код этой команды почти не изменился, только 'print' заменен на 'console.print'
            # и 'input' на 'Prompt.ask' для безопасного ввода пароля)
            sub = cmd[1].lower() if len(cmd) > 1 else "on"

            if sub == "off":
                kernel_instance.root_mode = False
                console.print("[yellow]Root режим отключен.[/yellow]")
                continue

            if not auth.is_root_allowed():
                console.print("[red]Root запрещён в настройках.[/red]")
                continue

            if not auth.has_root_password():
                console.print("[yellow]Создайте пароль root.[/yellow]")
                p1 = Prompt.ask("Пароль", password=True)
                p2 = Prompt.ask("Повторите пароль", password=True)
                if not p1 or p1 != p2:
                    console.print("[red]Пароли не совпадают или пустой. Отмена.[/red]")
                    continue
                auth.set_root_password(p1)
                console.print("[green]Пароль установлен.[/green]")

            pwd = Prompt.ask("Введите пароль root", password=True)
            if auth.verify_root_password(pwd):
                kernel_instance.root_mode = True
                console.print("[bold yellow]Root режим включен.[/bold yellow]")
            else:
                console.print("[bold red]Неверный пароль.[/bold red]")

        elif command == "ls":
            # --- РЕФАКТОРИНГ UI ---
            table = Table(title=f"Содержимое [green]{fs.current_path}[/green]")
            table.add_column("Имя", style="bright_cyan")
            table.add_column("Тип", style="yellow")
            
            try:
                for f in fs.list_dir():
                    # Проверяем, папка это или файл
                    is_dir = os.path.isdir(os.path.join(fs.current_path, f))
                    table.add_row(f, "[blue]Папка[/blue]" if is_dir else "Файл")
                console.print(table)
            except Exception as e:
                console.print(f"[red]Ошибка чтения каталога: {e}[/red]")
            # --------------------

        elif command == "cd":
            if len(cmd) < 2:
                console.print("[red]Укажите папку[/red]")
                continue
            target = cmd[1]
            if target == "-":
                fs.current_path, previous_path = previous_path, fs.current_path
                console.print(f"Перешли в [green]{fs.current_path}[/green]")
                continue
            if not kernel_instance.root_mode and target == "\\":
                console.print("[red]Доступ к системной директории запрещен.[/red]")
                continue
            previous_path = fs.current_path
            if fs.change_dir(target):
                console.print(f"Перешли в [green]{fs.current_path}[/green]")
            else:
                console.print("[red]Папка не найдена[/red]")

        elif command == "mkdir":
            if len(cmd) < 2:
                console.print("[red]Укажите имя папки[/red]")
            elif fs.make_dir(cmd[1]):
                console.print(f"Папка [cyan]'{cmd[1]}'[/cyan] создана")
            else:
                console.print("[red]Ошибка создания папки или она уже существует[/red]")

        elif command == "touch":
            if len(cmd) < 2:
                console.print("[red]Укажите имя файла[/red]")
            elif fs.write_file(cmd[1], ""):
                console.print(f"Файл [cyan]'{cmd[1]}'[/cyan] создан")
            else:
                console.print("[red]Ошибка создания файла[/red]")

        elif command == "cat":
            if len(cmd) < 2:
                console.print("[red]Укажите имя файла[/red]")
            else:
                content = fs.read_file(cmd[1])
                if content is None:
                    console.print("[red]Файл не найден или это папка[/red]")
                else:
                    # --- РЕФАКТОРИНГ UI ---
                    # Используем 'rich.Syntax' для красивой подсветки синтаксиса
                    # Он сам определит язык, если у файла есть расширение.
                    syntax = Syntax(content, "auto", theme="monokai", line_numbers=True)
                    console.print(syntax)
                    # --------------------

        elif command == "rm":
            if len(cmd) < 2:
                console.print("[red]Укажите файл или папку для удаления[/red]")
                continue
            target = cmd[1]
            
            # --- УЛУЧШЕНИЕ ЛОГИКИ ---
            # Передаем 'root_mode' в secury, как и обсуждали.
            # (Это потребует от вас изменить secury.confirm_delete,
            # чтобы он принимал 2 аргумента: 'path' и 'is_root')
            if not secury.confirm_delete(target, kernel_instance.root_mode):
                continue
            # ------------------------
            
            if fs.remove(target):
                console.print(f"'{target}' удалён")
            else:
                console.print("[red]Ошибка удаления или файл/папка не найдены[/red]")

        elif command == "echo":
            if ">" in cmd:
                pos = cmd.index(">")
                if pos < 2 or pos == len(cmd) - 1:
                    console.print("[red]Неверный синтаксис: echo <текст> > <файл>[/red]")
                else:
                    text = " ".join(cmd[1:pos])
                    filename = cmd[pos + 1]
                    if fs.write_file(filename, text):
                        console.print(f"Записано в файл [cyan]'{filename}'[/cyan]")
                    else:
                        console.print("[red]Ошибка записи в файл[/red]")
            else:
                console.print(" ".join(cmd[1:]))

        elif command == "ping":
            console.print("[bold green]Pong![/bold green]")

        # --- НОВАЯ КОМАНДА ---
        elif command == "pwd":
            console.print(f"[green]{fs.current_path}[/green]")

        # --- НОВАЯ КОМАНДА ---
        elif command == "date":
            console.print(f"Текущее системное время: [bold]{real_time()}[/bold]")

        # --- НОВАЯ КОМАНДА ---
        elif command == "sysinfo":
            from data.info import info
            panel_content = (
                f"[bold]OS:[/bold] {info_data.get('name_os', info.name_os)}\n"
                f"[bold]Version:[/bold] {info_data.get('version', info.version)}\n"
                f"[bold]User:[/bold] {username}\n"
                f"[bold]Root Status:[/bold] {'[red]ENABLED[/red]' if kernel_instance.root_mode else 'DISABLED'}\n"
                f"[bold]Root Allowed:[/bold] {'Yes' if auth.is_root_allowed() else 'No'}"
            )
            console.print(Panel(panel_content, title="[cyan]System Information[/cyan]", border_style="blue"))

        # --- НОВАЯ КОМАНДА ---
        elif command == "edit":
            if len(cmd) < 2:
                console.print("[red]Укажите имя файла[/red]")
                continue
            
            filename = cmd[1]
            content = fs.read_file(filename) or ""
            console.print(f"--- Редактирование [yellow]{filename}[/yellow] ---")
            console.print(f"--- Введите [cyan]EOF!/cyan] на новой строке для сохранения и выхода ---")
            
            lines = []
            if content:
                console.print(f"[dim]Текущий файл:[/dim]\n{content}")
                lines = content.split('\n')
            
            while True:
                line = input()
                if line == "EOF!":
                    break
                lines.append(line)
            
            fs.write_file(filename, "\n".join(lines))
            console.print(f"[green]Файл '{filename}' сохранен.[/green]")

        # --- НОВАЯ КОМАНДА ---
        elif command == "sleep":
            if len(cmd) < 2 or not cmd[1].isdigit():
                console.print("[red]Использование: sleep <секунды>[/red]")
                continue
            duration = int(cmd[1])
            # Используем 'rich.progress' для красивого sleep
            with Progress() as progress:
                task = progress.add_task("[green]Sleeping...", total=duration)
                for _ in range(duration):
                    time.sleep(1)
                    progress.update(task, advance=1)
            console.print(f"Проснулся после [yellow]{duration} сек.[/yellow]")

        # --- НОВАЯ КОМАНДА ---
        elif command == "http":
            if len(cmd) < 2:
                console.print("[red]Использование: http <url>[/red]")
                continue
            url = cmd[1]
            try:
                console.print(f"Запрос [yellow]{url}[/yellow]...")
                r = requests.get(url)
                console.print(f"Статус: [bold green]{r.status_code}[/bold green]")
                console.print(Panel(r.text[:1000] + "...", title="Response (first 1000 chars)"))
            except Exception as e:
                console.print(f"[bold red]Ошибка HTTP-запроса: {e}[/bold red]")
                
        elif command == "run":
            app_dirs = [
                os.path.join(root_dir, "app"),
                os.path.join(os.getcwd(), "data", "app")
            ]
            apps = []
            for path in app_dirs:
                try:
                    apps += [f[:-3] for f in os.listdir(path) if f.endswith(".py")]
                except:
                    pass

            if len(cmd) < 2:
                console.print("[bold]Доступные приложения:[/bold]")
                for a in apps:
                    console.print(f" - [cyan]{a}[/cyan]")
                continue

            app_name = cmd[1]
            # ... (логика поиска app_path остается той же) ...
            
            # --- (Начало блока поиска app_path) ---
            app_path = None
            for path in app_dirs:
                candidate = os.path.join(path, app_name + ".py")
                if os.path.isfile(candidate):
                    app_path = candidate
                    break
            if app_path is None:
                console.print(f"[red]Приложение '{app_name}' не найдено[/red]")
                continue
            # --- (Конец блока поиска app_path) ---

            try:
                with open(app_path, "r", encoding="utf-8") as f:
                    code = f.read()
                    app_os = {
                        # Передаем 'rich.console.print' вместо 'print'
                        "print": console.print, 
                        "read_file": fs.read_file,
                        "write_file": fs.write_file,
                        "list_dir": fs.list_dir,
                        "current_path": fs.current_path,
                        "change_dir": fs.change_dir,
                        "time": real_time,
                        # Даем доступ к некоторым UI-элементам
                        "Panel": Panel,
                        "Table": Table,
                    }
                    
                    # --- КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ БЕЗОПАСНОСТИ ---
                    # Создаем "белый список" безопасных встроенных функций
                    safe_builtins = __builtins__.copy()
                    
                    safe_builtins.update({
                        "print": console.print,
                        "len": len, "str": str, "int": int, "float": float,
                        "list": list, "dict": dict, "tuple": tuple,
                        "True": True, "False": False, "None": None,
                        "Confirm": Confirm, "Prompt": Prompt,
                        })
                    
                    # 'exec' теперь НЕ ИМЕЕТ доступа к '__import__', 'os', 'open' и т.д.
                    exec_globals = {
                        "__builtins__": safe_builtins,
                        "app_os": app_os
                    }
                    exec(code, exec_globals)
                    # --------------------------------------------------
                    
            except Exception as e:
                # 'rich.traceback' (вызванный 'install_traceback()')
                # автоматически красиво обработает эту ошибку.
                console.print(f"[bold red]Ошибка выполнения приложения '{app_name}': {e}[/bold red]")

        else:
            console.print(f"[bold red][ERROR][/bold red] Неизвестная команда '{command}'")