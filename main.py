# main.py — основной загрузчик CawOS с поддержкой Recovery и защитой от прерываний
deadlock = True
import os
import time
import sys
import logging
from core.logger import setup_logger

sys.dont_write_bytecode = True

# Инициализация логгера
setup_logger()
logging.info("--- CawOS Boot Process Started ---")

# --- Ультра-ранняя защита импорта Rich ---
try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
except ImportError:
    logging.warning("Rich library not found, using FakeConsole fallback.")
    class FakeConsole:
        def print(self, text, **kwargs): print(str(text))
    console = FakeConsole()

PANIC_COUNT = 0
MAX_PANIC = 3

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
                mode = data.get("mode", "normal") if isinstance(data, dict) else "normal"
                return mode
        except Exception as e:
            logging.error(f"Failed to read boot mode: {e}")
            return "normal"
    return "normal"

def set_boot_mode(mode):
    try:
        logging.info(f"Setting system boot mode to: {mode}")
        mode_file = os.path.join("data", "json", "boot_mode.json")
        import json
        os.makedirs(os.path.dirname(mode_file), exist_ok=True)
        with open(mode_file, "w") as f:
            json.dump({"mode": mode}, f)
    except Exception as e:
        logging.error(f"Could not save boot mode: {e}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

import shutil

def apply_updates():
    flag_file = "update_pending.flag"
    package_file = "update_package.zip"

    if os.path.exists(flag_file) and os.path.exists(package_file):
        logging.info("Found update package. Starting installation...")
        console.print(Panel("[bold yellow]INSTALLING UPDATE[/bold yellow]"))
        try:
            import zipfile
            import shutil

            for module in list(sys.modules.keys()):
                if module.startswith(('core', 'data')):
                    del sys.modules[module]

            with zipfile.ZipFile(package_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # --- ФИКС БАГА №2: ЗАЩИТА ОТ PATH TRAVERSAL ---
                for f in file_list:
                    # Проверяем, не пытается ли файл вылезти из корня (../../main.py)
                    # Или использовать абсолютный путь
                    normalized_path = os.path.normpath(f)
                    if normalized_path.startswith("..") or os.path.isabs(normalized_path):
                        logging.warning(f"SECURITY ALERT: Blocked malicious path in update: {f}")
                        continue
                
                # Умная очистка системных папок
                sys_items_to_update = set()
                for f in file_list:
                    if f.startswith("data/app/"):
                        parts = f.split("/")
                        if len(parts) > 2:
                            # Дополнительная проверка на безопасность частей пути
                            if ".." not in parts:
                                sys_items_to_update.add(parts[2])

                for item in sys_items_to_update:
                    target_path = os.path.join("data", "app", item)
                    if os.path.exists(target_path):
                        if os.path.isdir(target_path):
                            shutil.rmtree(target_path)
                        else:
                            os.remove(target_path)

                for root, dirs, files in os.walk("."):
                    if "__pycache__" in dirs:
                        shutil.rmtree(os.path.join(root, "__pycache__"))

                # Распаковка только разрешенных путей
                for member in zip_ref.infolist():
                    # Финальный заслон: не распаковываем ничего за пределами текущей директории
                    if ".." in member.filename or member.filename.startswith("/"):
                        continue
                    zip_ref.extract(member, ".")

            os.remove(flag_file)
            os.remove(package_file)
            
            console.print(f"[green]Успешно! Обновлено объектов: {len(file_list)}[/green]")
            time.sleep(2)
            return True 

        except Exception as e:
            logging.critical(f"Critical error during update: {e}", exc_info=True)
            console.print(f"[bold white on red] ОШИБКА ОБНОВЛЕНИЯ: {e} [/bold white on red]")
            time.sleep(5)
    return False

def verify_system():
    missing = [f for f in REQUIRED_FILES if not os.path.exists(f)]
    return missing

def start_recovery(reason="Unknown Error"):
    global PANIC_COUNT
    PANIC_COUNT += 1
    logging.error(f"Triggering Recovery. Reason: {reason} | Panic count: {PANIC_COUNT}")
    
    if PANIC_COUNT > MAX_PANIC:
        logging.critical("MAX_PANIC reached. System Halted.")
        clear_screen()
        print("!!! CRITICAL SYSTEM FAILURE !!!")
        print(f"Panic loop detected. Last error: {reason}")
        os._exit(1)

    try:
        from core import recovery
        action = recovery.menu(reason)
        if action == "reboot":
            return True
        os._exit(0)
    except Exception as e:
        logging.critical(f"Fatal: Recovery module failed: {e}")
        os._exit(1)

if __name__ == "__main__":
    while True:
        try:
            clear_screen()
            
            missing = verify_system()
            if missing:
                files_str = "\n".join([f"- {f}" for f in missing])
                start_recovery(f"Missing files:\n{files_str}")
                continue 

            mode = get_boot_mode()
            
            if mode != "normal":
                PANIC_COUNT = 0

            if mode == "fastboot":
                set_boot_mode("normal") 
                try:
                    from core.fastboot import FastbootInterface
                    fb = FastbootInterface()
                    fb.run()
                    # --- ФИКС БАГА №1: УБИРАЕМ CONTINUE ---
                    # Теперь после выхода из Fastboot система пойдет дальше 
                    # и либо перезагрузится, либо войдет в ядро.
                    # В данном случае лучше сделать перезагрузку процесса:
                    os.execv(sys.executable, ['python'] + sys.argv)
                except Exception as e:
                    logging.exception("Fastboot crash!")
                    start_recovery(f"Fastboot Error: {e}")
                    continue

            elif mode == "recovery":
                set_boot_mode("normal")
                start_recovery("Manual Recovery Entry")
                continue

            # Проверки
            try:
                from core.verify import verify_system_integrity
                if not verify_system_integrity():
                    start_recovery("System Integrity Check Failed")
                    continue
            except Exception as e:
                start_recovery(f"Integrity Module Error: {e}")
                continue

            try:
                from core.secure import sec_block
                sec_block()
            except Exception as e:
                start_recovery(f"Security Module Error: {e}")
                continue

            if apply_updates():
                logging.info("Update applied. Restarting via os.execv")
                os.execv(sys.executable, ['python'] + sys.argv)

            # Bootloader
            try:
                from core.boot import main as boot_main
                os_name = boot_main()
                if os_name == "RECOVERY": 
                    start_recovery("Manual recovery entry")
                    continue
            except Exception as e:
                start_recovery(f"Bootloader Error: {e}")
                continue

            # Запуск ядра
            kernel_path = f"core.os.{os_name}.kernel"
            try:
                if kernel_path in sys.modules:
                    del sys.modules[kernel_path]
                
                module = __import__(kernel_path, fromlist=["Kernel"])
                KernelClass = getattr(module, "Kernel")
                kernel_instance = KernelClass(os_name=os_name)
                
                PANIC_COUNT = 0
                exit_code = kernel_instance.start() 
                
                if exit_code == "reboot":
                    os.execv(sys.executable, ['python'] + sys.argv)
                elif exit_code == "shutdown":
                    os._exit(0)
                else:
                    start_recovery("Kernel exit without code.")
                    continue

            except Exception as e:
                logging.exception("KERNEL PANIC!")
                start_recovery(f"Kernel Panic: {e}")
                continue

        except KeyboardInterrupt:
            clear_screen()
            if not start_recovery("User Interruption (Ctrl+C)"):
                os._exit(0)