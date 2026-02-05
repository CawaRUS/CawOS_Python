# main.py — основной загрузчик CawOS с поддержкой Recovery и защитой от прерываний
import os
import time
import sys

# --- Ультра-ранняя защита импорта Rich ---
try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    # Если Rich поврежден, создаем заглушку, чтобы система не падала
    class FakeConsole:
        def print(self, text, **kwargs): print(str(text))
    console = FakeConsole()

# Счетчик для предотвращения бесконечного цикла ошибок
PANIC_COUNT = 0
MAX_PANIC = 3

# Список критически важных файлов
REQUIRED_FILES = [
    'core/boot.py',
    'core/verify.py',
    'core/recovery.py',
    'core/fastboot.py'
]

def get_boot_mode():
    """Безопасное получение режима загрузки."""
    mode_file = os.path.join("data", "json", "boot_mode.json")
    if os.path.exists(mode_file):
        try:
            import json
            with open(mode_file, "r") as f:
                data = json.load(f)
                # Проверка, что данные — словарь, и извлечение мода
                return data.get("mode", "normal") if isinstance(data, dict) else "normal"
        except:
            return "normal"
    return "normal"

def set_boot_mode(mode):
    """Безопасная установка режима загрузки."""
    try:
        mode_file = os.path.join("data", "json", "boot_mode.json")
        import json
        os.makedirs(os.path.dirname(mode_file), exist_ok=True)
        with open(mode_file, "w") as f:
            json.dump({"mode": mode}, f)
    except:
        pass # Если не удалось сохранить мод, просто игнорируем

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def apply_updates():
    """Распаковка обновлений с защитой."""
    flag_file = "update_pending.flag"
    package_file = "update_package.zip"

    if os.path.exists(flag_file) and os.path.exists(package_file):
        console.print(Panel("[bold yellow]INSTALLING UPDATE[/bold yellow]\nПожалуйста, не выключайте устройство...", border_style="yellow"))
        try:
            import zipfile
            with zipfile.ZipFile(package_file, 'r') as zip_ref:
                zip_ref.extractall(".")
            
            os.remove(flag_file)
            os.remove(package_file)
            
            console.print("[bold green]Обновление установлено успешно![/bold green]")
            time.sleep(1.5)
            return True 
        except Exception as e:
            console.print(f"[bold red]Ошибка обновления:[/bold red] {e}")
            time.sleep(5)
    return False

def verify_system():
    return [f for f in REQUIRED_FILES if not os.path.exists(f)]

def start_recovery(reason="Unknown Error"):
    """Запуск Recovery с защитой от циклической паники."""
    global PANIC_COUNT
    PANIC_COUNT += 1
    
    if PANIC_COUNT > MAX_PANIC:
        clear_screen()
        print("!!! CRITICAL SYSTEM FAILURE !!!")
        print(f"Panic loop detected. Last error: {reason}")
        print("System halted to prevent hardware damage.")
        os._exit(1)

    try:
        # Динамический импорт recovery
        from core import recovery
        action = recovery.menu(reason)
        if action == "reboot":
            return True
        os._exit(0)
    except Exception as e:
        console.print(f"[bold white on red] FATAL: Recovery failed: {e} [/bold white on red]")
        time.sleep(5)
        os._exit(1)

if __name__ == "__main__":
    while True:
        try:
            clear_screen()
            
            # 1. Базовая проверка файлов
            missing = verify_system()
            if missing:
                files_str = "\n".join([f"- {f}" for f in missing])
                start_recovery(f"Missing files:\n{files_str}")
                continue 

            mode = get_boot_mode()
            
            # Если вошли в спец. режимы, сбрасываем счетчик паник
            if mode != "normal":
                PANIC_COUNT = 0

            if mode == "fastboot":
                set_boot_mode("normal") 
                try:
                    from core.fastboot import FastbootInterface
                    fb = FastbootInterface()
                    fb.run()
                    continue 
                except Exception as e:
                    start_recovery(f"Fastboot Error: {e}")
                    continue

            elif mode == "recovery":
                set_boot_mode("normal")
                start_recovery("Manual Recovery Entry")
                continue

            # 2. Проверка целостности
            try:
                from core.verify import verify_system_integrity
                if not verify_system_integrity():
                    start_recovery("System Integrity Check Failed")
                    continue
            except Exception as e:
                start_recovery(f"Integrity Module Error: {e}")
                continue

            # 3. Безопасность
            try:
                from core.secury import sec_block
                sec_block()
            except Exception as e:
                start_recovery(f"Security Module Error: {e}")
                continue

            # Обновления
            if apply_updates():
                # Полный перезапуск процесса Python
                os.execv(sys.executable, ['python'] + sys.argv)

            # 4. Bootloader
            try:
                from core.boot import main as boot_main
                os_name = boot_main()
                if os_name == "RECOVERY": 
                    start_recovery("Manual recovery entry")
                    continue
            except Exception as e:
                start_recovery(f"Bootloader Error: {e}")
                continue

            # 5. Запуск ядра
            kernel_path = f"core.os.{os_name}.kernel"
            try:
                # Очищаем кэш импорта, чтобы загрузить свежее ядро (если оно обновилось)
                if kernel_path in sys.modules:
                    del sys.modules[kernel_path]
                
                module = __import__(kernel_path, fromlist=["Kernel"])
                KernelClass = getattr(module, "Kernel")
                kernel_instance = KernelClass(os_name=os_name)
                
                # При успешном доходе до ядра — сбрасываем счетчик паник
                PANIC_COUNT = 0
                
                exit_code = kernel_instance.start() 
                
                if exit_code == "reboot":
                    console.print("\n[blue][BOOT][/blue] [green]Rebooting...[/green]")
                    time.sleep(1)
                    continue 
                elif exit_code == "shutdown":
                    os._exit(0)
                else:
                    start_recovery("Kernel exit without code.")
                    continue

            except Exception as e:
                start_recovery(f"Kernel Panic: {e}")
                continue

        except KeyboardInterrupt:
            clear_screen()
            if start_recovery("User Interruption (Ctrl+C)"):
                continue
            else:
                os._exit(0)