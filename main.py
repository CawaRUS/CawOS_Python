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
                mode = data.get("mode", "normal") if isinstance(data, dict) else "normal"
                logging.debug(f"Boot mode read: {mode}")
                return mode
        except Exception as e:
            logging.error(f"Failed to read boot mode: {e}")
            return "normal"
    return "normal"

def set_boot_mode(mode):
    """Безопасная установка режима загрузки."""
    try:
        logging.info(f"Setting system boot mode to: {mode}")
        mode_file = os.path.join("data", "json", "boot_mode.json")
        import json
        os.makedirs(os.path.dirname(mode_file), exist_ok=True)
        with open(mode_file, "w") as f:
            json.dump({"mode": mode}, f)
    except Exception as e:
        logging.error(f"Could not save boot mode: {e}")
        pass # Если не удалось сохранить мод, просто игнорируем

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
            import sys

            # 1. Зачистка кэша импортов
            for module in list(sys.modules.keys()):
                if module.startswith(('core', 'data')):
                    del sys.modules[module]

            with zipfile.ZipFile(package_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                # 2. УМНАЯ ОЧИСТКА: только для системной папки!
                items_to_update = set()
                for f in file_list:
                    for prefix in ["data/app/", "data/0/app/"]:
                        if f.startswith(prefix):
                            parts = f.split("/")
                            idx = 2 if prefix == "data/app/" else 3
                            if len(parts) > idx:
                                items_to_update.add(parts[idx])

                # Очищаем ТОЛЬКО временную системную папку data/app
                # Папку data/0/app НЕ ТРОГАЕМ удалением, чтобы сохранить данные юзера
                for item in items_to_update:
                    target_path = os.path.join("data", "app", item)
                    if os.path.exists(target_path):
                        if os.path.isdir(target_path):
                            shutil.rmtree(target_path)
                        else:
                            os.remove(target_path)

                # 3. Очистка __pycache__ по всему проекту (всегда полезно)
                for root, dirs, files in os.walk("."):
                    if "__pycache__" in dirs:
                        shutil.rmtree(os.path.join(root, "__pycache__"))

                # --- 4. Распаковка архива ---
                # Вместо extractall("."), который падает на существующих папках в Windows
                for member in zip_ref.infolist():
                    # Если это папка, просто создаем её (exist_ok=True)
                    if member.is_dir():
                        os.makedirs(member.filename, exist_ok=True)
                    else:
                        # Если файл — извлекаем с перезаписью
                        zip_ref.extract(member, ".")

                logging.info(f"Extracted {len(file_list)} items")

                # --- 5. Синхронизация (Безопасная для пользователя) ---
                if os.path.exists("data/app"):
                    for item in items_to_update:
                        src = os.path.join("data/app", item)
                        dst = os.path.join("data/0/app", item)
                        
                        if os.path.exists(src):
                            if os.path.isdir(src):
                                # Ключевой момент: используем dirs_exist_ok=True
                                # Это позволит влить файлы обновления в папку приложения, 
                                # не удаляя саму папку и не трогая другие файлы пользователя там.
                                shutil.copytree(src, dst, dirs_exist_ok=True)
                            else:
                                shutil.copy2(src, dst)
                
                console.print("[dim]Синхронизация обновленных приложений завершена.[/dim]")

            # 6. Подчистка
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
    if missing:
        logging.warning(f"System verification failed. Missing: {missing}")
    return missing

def start_recovery(reason="Unknown Error"):
    """Запуск Recovery с защитой от циклической паники."""
    global PANIC_COUNT
    PANIC_COUNT += 1
    logging.error(f"Triggering Recovery. Reason: {reason} | Panic count: {PANIC_COUNT}")
    
    if PANIC_COUNT > MAX_PANIC:
        logging.critical("MAX_PANIC reached. System Halted.")
        clear_screen()
        print("!!! CRITICAL SYSTEM FAILURE !!!")
        print(f"Panic loop detected. Last error: {reason}")
        print("System halted to prevent hardware damage.")
        os._exit(1)

    try:
        # Динамический импорт recovery
        from core import recovery
        logging.info("Entering Recovery Menu...")
        action = recovery.menu(reason)
        logging.info(f"Recovery action: {action}")
        if action == "reboot":
            return True
        os._exit(0)
    except Exception as e:
        logging.critical(f"Fatal: Recovery module failed: {e}")
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
                logging.info(f"System boot mode: {mode}. Resetting panic counter.")
                PANIC_COUNT = 0

            if mode == "fastboot":
                set_boot_mode("normal") 
                try:
                    from core.fastboot import FastbootInterface
                    logging.info("Launching Fastboot interface")
                    fb = FastbootInterface()
                    fb.run()
                    continue 
                except Exception as e:
                    logging.exception("Fastboot crash!")
                    start_recovery(f"Fastboot Error: {e}")
                    continue

            elif mode == "recovery":
                set_boot_mode("normal")
                start_recovery("Manual Recovery Entry")
                continue

            # 2. Проверка целостности
            try:
                from core.verify import verify_system_integrity
                logging.info("Verifying system integrity...")
                if not verify_system_integrity():
                    start_recovery("System Integrity Check Failed")
                    continue
            except Exception as e:
                logging.exception("Integrity module failed!")
                start_recovery(f"Integrity Module Error: {e}")
                continue

            # 3. Безопасность
            try:
                from core.secure import sec_block
                logging.info("Executing security checks")
                sec_block()
            except Exception as e:
                logging.exception("Security module block!")
                start_recovery(f"Security Module Error: {e}")
                continue

            # Обновления
            if apply_updates():
                # Полный перезапуск процесса Python
                logging.info("Update applied. Restarting CawOS via os.execv")
                os.execv(sys.executable, ['python'] + sys.argv)

            # 4. Bootloader
            try:
                from core.boot import main as boot_main
                logging.info("Calling bootloader")
                os_name = boot_main()
                logging.info(f"Selected OS: {os_name}")
                if os_name == "RECOVERY": 
                    start_recovery("Manual recovery entry")
                    continue
            except Exception as e:
                logging.exception("Bootloader failed!")
                start_recovery(f"Bootloader Error: {e}")
                continue

            # 5. Запуск ядра
            kernel_path = f"core.os.{os_name}.kernel"
            try:
                # Очищаем кэш импорта, чтобы загрузить свежее ядро (если оно обновилось)
                if kernel_path in sys.modules:
                    del sys.modules[kernel_path]
                
                logging.info(f"Importing kernel: {kernel_path}")
                module = __import__(kernel_path, fromlist=["Kernel"])
                KernelClass = getattr(module, "Kernel")
                kernel_instance = KernelClass(os_name=os_name)
                
                # При успешном доходе до ядра — сбрасываем счетчик паник
                logging.info("Kernel instance created. Panic count reset.")
                PANIC_COUNT = 0
                
                exit_code = kernel_instance.start() 
                
                logging.info(f"Kernel terminated. Exit code: {exit_code}")
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
                logging.exception("KERNEL PANIC DETECTED!")
                start_recovery(f"Kernel Panic: {e}")
                continue

        except KeyboardInterrupt:
            logging.warning("User sent KeyboardInterrupt")
            clear_screen()
            if start_recovery("User Interruption (Ctrl+C)"):
                continue
            else:
                os._exit(0)