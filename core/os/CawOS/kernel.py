# core/os/CawOS/kernel.py — Ядро ОС (Объектно-ориентированный стиль)

import core.shell as shell
import data.info as info 
import time
from colorama import Fore, Style
import os
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

    # --- МЕТОД ЗАПУСКА (теперь внутри класса) ---
    def start(self):
        """Основная точка входа для запуска ядра."""
        print(Fore.GREEN + "[KERNEL] Ядро запущено" + Style.RESET_ALL)
        self.init_system()
        self.run_shell()

    def enter_root_mode(self):
        self.root_mode = True
        print(Fore.RED + "[KERNEL] Переход в режим ROOT." + Style.RESET_ALL)
        
    def exit_root_mode(self):
        self.root_mode = False
        print(Fore.YELLOW + "[KERNEL] Выход из режима root." + Style.RESET_ALL)

    def init_system(self):
        print(Fore.GREEN + "[KERNEL] Инициализация системных модулей..." + Style.RESET_ALL)
        
    def run_shell(self):
        print(Fore.GREEN + "[KERNEL] Запуск оболочки CawOS." + Style.RESET_ALL)
        shell.run(self) 
        
    def shutdown(self):
        info.set_exit_on(1)
        self.running = False
        print(Fore.GREEN + "[KERNEL] Выключение ОС..." + Style.RESET_ALL)

