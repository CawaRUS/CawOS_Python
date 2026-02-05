import time
import os
from colorama import Fore, Style

# --- Безопасные импорты ---
try:
    import core.shell as shell
except ImportError:
    shell = None # Заглушка, если оболочка повреждена

try:
    import data.info as info 
except ImportError:
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

    def start(self):
        """Точка входа. Обернута в глобальную защиту."""
        print(Fore.GREEN + f"[KERNEL] Запуск ядра для {self.os_name}..." + Style.RESET_ALL)
        
        try:
            self.init_system()
            self.log_shell_start() 
            
            if shell is None:
                print(Fore.RED + "[CRITICAL] Ошибка: Модуль Shell не найден!" + Style.RESET_ALL)
                return "recovery" # Отправляем main.py команду на вход в рекавери

            # --- ИЗОЛЯЦИЯ ОБОЛОЧКИ ---
            try:
                # Запускаем оболочку и ждем код выхода
                result = shell.run(self)
            except Exception as e:
                print(Fore.RED + f"[PANIC] Shell Crash: {e}" + Style.RESET_ALL)
                # Если оболочка упала, пробуем перезагрузиться или в рекавери
                return "reboot" 

            self.shutdown()
            return result # Передаем 'reboot' или 'shutdown' обратно в main.py

        except Exception as e:
            # Если упало само ядро на этапе инициализации
            print(Fore.RED + f"[CRITICAL KERNEL PANIC] {e}" + Style.RESET_ALL)
            return "recovery"

    def enter_root_mode(self):
        self.root_mode = True
        print(Fore.RED + "[KERNEL] Режим ROOT активирован." + Style.RESET_ALL)
        
    def exit_root_mode(self):
        self.root_mode = False
        print(Fore.YELLOW + "[KERNEL] Режим ROOT деактивирован." + Style.RESET_ALL)

    def init_system(self):
        # Здесь можно добавить проверку здоровья FS перед стартом
        print(Fore.GREEN + "[KERNEL] Модули инициализированы успешно." + Style.RESET_ALL)
        
    def log_shell_start(self):
        print(Fore.CYAN + "[KERNEL] Ожидание ввода пользователя..." + Style.RESET_ALL)
        
    def shutdown(self):
        self.running = False
        if info:
            try:
                info.set_exit_on(1) # Пытаемся сохранить статус выхода
            except:
                pass
        print(Fore.YELLOW + "[KERNEL] Завершение процессов и выключение..." + Style.RESET_ALL)
        time.sleep(0.5)