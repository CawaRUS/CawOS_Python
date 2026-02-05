import os

about = "Очистить экран"

def execute(args, kernel, console):
    os.system("cls" if os.name == 'nt' else 'clear')