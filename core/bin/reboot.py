import json
import core.fs.fs as fs

about = "Перезагрузить устройство"

def execute(args, kernel, console):
    boot_mode_path = "data/json/boot_mode.json"
    
    # Определяем режим
    target_mode = "normal"
    if len(args) > 0:
        mode = args[0].lower()
        if mode in ["bootloader", "fastboot"]:
            target_mode = "fastboot"
        elif mode == "recovery":
            target_mode = "recovery"
        else:
            console.print(f"[bold red][ERROR][/bold red] Неизвестный параметр: {mode}")
            return

    # Подготавливаем данные
    boot_data = json.dumps({"mode": target_mode})

    # Используем системный вызов fs.write_file
    # Он сам создаст директории, если нужно (os.makedirs внутри него уже есть)
    if fs.write_file("data/json/boot_mode.json", boot_data, bypass_security=True):
        return "reboot"
    else:
        console.print("[bold red][ERROR][/bold red] Системная ошибка: доступ к boot_mode.json запрещен.")
        return