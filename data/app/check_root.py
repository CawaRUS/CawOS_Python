import core.fs.fs as fs



def check_root():
    current_kernel = getattr(fs, "kernel", None)
    
    if current_kernel is None:
        print("Ошибка: Ядро не обнаружено.")
        return

    if current_kernel.root_mode:
        print("У вас есть root права")
    else:
        print("У вас нет root прав.")


check_root()