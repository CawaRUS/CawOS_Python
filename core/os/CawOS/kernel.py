import time
import os
import logging
from colorama import Fore, Style

# Получаем логгер для ядра
logger = logging.getLogger("kernel")

# --- Безопасные импорты ---
try:
    import core.shell as shell
    logger.debug("Shell module imported successfully")
except ImportError:
    logger.critical("Shell module NOT FOUND!")
    shell = None # Заглушка, если оболочка повреждена

try:
    import data.info as info 
    logger.debug("Info module imported")
except ImportError:
    logger.warning("Info module not found, some features may be disabled")
    info = None

import core.fs.fs as fs 

class Kernel:
    """Класс ядра ОС, который управляет состоянием системы."""
    
    def __init__(self, os_name):
        self.os_name = os_name
        self.running = True
        self.root_mode = False
        self.processes = []
        # Передаем ссылку на ядро в FS
        fs.kernel = self 
        logger.info(f"Kernel initialized for {self.os_name}")

    def start(self):
        """Точка входа. Обернута в глобальную защиту."""
        logger.info("Kernel execution started")
        print(Fore.GREEN + f"[KERNEL] Запуск ядра для {self.os_name}..." + Style.RESET_ALL)
        
        try:
            self.init_system()
            self.log_shell_start() 
            
            if shell is None:
                logger.error("System stop: Shell is missing")
                print(Fore.RED + "[CRITICAL] Ошибка: Модуль Shell не найден!" + Style.RESET_ALL)
                return "recovery" # Отправляем main.py команду на вход в рекавери

            # --- ИЗОЛЯЦИЯ ОБОЛОЧКИ ---
            try:
                logger.info("Transferring control to Shell...")
                # Запускаем оболочку и ждем код выхода
                result = shell.run(self)
                logger.info(f"Shell exited with code: {result}")
            except Exception as e:
                logger.exception(f"Shell encountered a fatal error: {e}")
                print(Fore.RED + f"[PANIC] Shell Crash: {e}" + Style.RESET_ALL)
                # Если оболочка упала, пробуем перезагрузиться или в рекавери
                return "reboot" 

            self.shutdown()
            return result # Передаем 'reboot' или 'shutdown' обратно в main.py

        except Exception as e:
            # Если упало само ядро на этапе инициализации
            logger.critical(f"KERNEL PANIC during initialization: {e}", exc_info=True)
            print(Fore.RED + f"[CRITICAL KERNEL PANIC] {e}" + Style.RESET_ALL)
            return "recovery"

    def enter_root_mode(self):
        self.root_mode = True
        logger.warning("ROOT MODE ACTIVATED by user/process")
        print(Fore.RED + "[KERNEL] Режим ROOT активирован." + Style.RESET_ALL)
        
    def exit_root_mode(self):
        self.root_mode = False
        logger.info("Root mode deactivated")
        print(Fore.YELLOW + "[KERNEL] Режим ROOT деактивирован." + Style.RESET_ALL)

    def init_system(self):
        # Здесь можно добавить проверку здоровья FS перед стартом
        logger.info("System subsystems check: OK")
        print(Fore.GREEN + "[KERNEL] Модули инициализированы успешно." + Style.RESET_ALL)
        
    def log_shell_start(self):
        logger.debug("Kernel is now in idle state, waiting for shell input")
        print(Fore.CYAN + "[KERNEL] Ожидание ввода пользователя..." + Style.RESET_ALL)
        
    def shutdown(self):
        self.running = False
        logger.info("Shutdown sequence initiated")
        if info:
            try:
                info.set_exit_on(1) # Пытаемся сохранить статус выхода
                logger.debug("Exit status saved to info module")
            except Exception as e:
                logger.error(f"Failed to save exit status: {e}")
        
        print(Fore.YELLOW + "[KERNEL] Завершение процессов и выключение..." + Style.RESET_ALL)
        time.sleep(0.5)
        logger.info("Kernel halted.")