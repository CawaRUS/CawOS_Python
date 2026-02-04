# main.py — основной загрузчик CawOS с поддержкой Recovery и защитой от прерываний
import os
import time
import sys

# --- Импорты Rich ---
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
# --------------------

console = Console()

# Список критически важных файлов для работы системы
REQUIRED_FILES = [
    'core/boot.py',
    'core/verify.py',
    'core/recovery.py',
    'core/fastboot.py'
]

def get_boot_mode():
    mode_file = os.path.join("data", "json", "boot_mode.json")
    if os.path.exists(mode_file):
        try:
            import json
            with open(mode_file, "r") as f:
                data = json.load(f)
                return data.get("mode", "normal")
        except:
            return "normal"
    return "normal"

def set_boot_mode(mode):
    mode_file = os.path.join("data", "json", "boot_mode.json")
    import json
    os.makedirs(os.path.dirname(mode_file), exist_ok=True)
    with open(mode_file, "w") as f:
        json.dump({"mode": mode}, f)

def clear_screen():
    """Очистка консоли."""
    os.system('cls' if os.name == 'nt' else 'clear')

def apply_updates():
    """Проверяет наличие флага обновления и распаковывает его."""
    flag_file = "update_pending.flag"
    package_file = "update_package.zip"

    if os.path.exists(flag_file) and os.path.exists(package_file):
        console.print(Panel("[bold yellow]INSTALLING UPDATE[/bold yellow]\nПожалуйста, не выключайте систему...", border_style="yellow"))
        try:
            import zipfile
            with zipfile.ZipFile(package_file, 'r') as zip_ref:
                # Распаковка всего содержимого архива в корень проекта
                zip_ref.extractall(".")
            
            # Удаление временных файлов
            os.remove(flag_file)
            os.remove(package_file)
            
            console.print("[bold green]Обновление установлено успешно![/bold green]")
            time.sleep(1.5)
            return True # Сообщаем, что нужно перезапустить процесс
        except Exception as e:
            console.print(f"[bold red]Критическая ошибка при установке:[/bold red] {e}")
            time.sleep(5)
    return False


def verify_system():
    """Проверка наличия файлов. Возвращает список отсутствующих."""
    return [f for f in REQUIRED_FILES if not os.path.exists(f)]

def start_recovery(reason="Unknown Error"):
    """Запуск режима восстановления."""
    try:
        from core import recovery
        # Передаем причину падения в меню восстановления
        action = recovery.menu(reason)
        if action == "reboot":
            return True # Флаг для перезапуска цикла загрузки
        os._exit(0) # Если выбрали выход/выключение
    except ImportError:
        console.print("[bold white on red] FATAL ERROR: Recovery module not found! [/bold white on red]")
        os._exit(1)
    except Exception as e:
        console.print(f"[red]Recovery Error: {e}[/red]")
        os._exit(1)

if __name__ == "__main__":
    while True: # Глобальный цикл для поддержки функции Reboot
        try:
            clear_screen()
            
            # 1. Базовая проверка файлов
            missing = verify_system()
            if missing:
                files_str = "\n".join([f"[red]- {f}[/red]" for f in missing])
                start_recovery(f"Missing files:\n{files_str}")
                continue 

            mode = get_boot_mode()
            if mode == "fastboot":
                # Сбрасываем режим на нормальный, чтобы после фастбута зайти в ОС
                set_boot_mode("normal") 
                try:
                    from core.fastboot import FastbootInterface
                    fb = FastbootInterface()
                    fb.run() # Запускаем интерфейс фастбута
                    continue # После выхода из фастбута возвращаемся в начало цикла
                except Exception as e:
                    start_recovery(f"Fastboot Error: {e}")
                    continue
            elif mode == "recovery":
                set_boot_mode("normal") # Сброс для следующего старта
                # Прямой вызов recovery через наш обработчик
                start_recovery("Manual Recovery Entry (User Request)")
                continue

            # 2. Проверка целостности (core/verify.py)
            try:
                from core.verify import verify_system_integrity
                if not verify_system_integrity():
                    start_recovery("System Integrity Check Failed")
                    continue
            except Exception as e:
                start_recovery(f"Integrity Module Error: {e}")
                continue

            # 3. Блокировка безопасности (core/secury.py)
            try:
                from core.secury import sec_block
                sec_block()
            except Exception as e:
                start_recovery(f"Security Module Error: {e}")
                continue

            if apply_updates():
                os.execv(sys.executable, ['python'] + sys.argv)

            # 4. Запуск загрузчика и выбор ОС (core/boot.py)
            try:
                from core.boot import main as boot_main
                os_name = boot_main()
                if os_name == "RECOVERY": 
                    start_recovery("Manual recovery entry")
                    continue
            except Exception as e:
                start_recovery(f"Bootloader Error: {e}")
                continue

            # 5. Динамическая загрузка и запуск ядра
            kernel_path = f"core.os.{os_name}.kernel"
            try:
                module = __import__(kernel_path, fromlist=["Kernel"])
                KernelClass = getattr(module, "Kernel")
                
                kernel_instance = KernelClass(os_name=os_name)
                
                # --- ТОЧКА ЗАПУСКА ЯДРА ---
                # Теперь мы ожидаем результат работы ядра
                exit_code = kernel_instance.start() 
                # -------------------------
                
                if exit_code == "reboot":
                    console.print("\n[blue][BOOT][/blue] [green]Выполняется мягкая перезагрузка...[/green]")
                    time.sleep(1)
                    # Мы не выходим из цикла while True, поэтому он просто начнется сначала
                    continue 

                elif exit_code == "shutdown":
                    console.print("\n[blue][BOOT][/blue] [yellow]Завершение работы системы...[/yellow]")
                    time.sleep(1)
                    os._exit(0)

                else:
                    # Если ядро просто "вылетело" без кода или вернуло None
                    # Это может быть багом, лучше отправить в Recovery
                    start_recovery("Kernel terminated unexpectedly without exit code.")
                    continue

            except Exception as e:
                # Обработка Kernel Panic
                start_recovery(f"Kernel Panic / Crash\nDetails: {e}")
                continue

        except KeyboardInterrupt:
            # Перехват Ctrl+C на любом этапе загрузки или работы
            clear_screen()
            console.print(Panel("[bold yellow]ВНИМАНИЕ: Обнаружено принудительное прерывание (Ctrl+C).[/bold yellow]", border_style="yellow"))
            if start_recovery("User Interruption"):
                continue
            else:
                os._exit(0)