import os, json

about = "Перезагрузить устройство"

def execute(args, kernel, console):
    boot_mode_path = os.path.join("data", "json", "boot_mode.json")
    os.makedirs(os.path.dirname(boot_mode_path), exist_ok=True)

    if len(args) == 0:
        with open(boot_mode_path, "w") as f:
            json.dump({"mode": "normal"}, f)
        return "reboot"

    mode = args[0].lower()
    if mode in ["bootloader", "fastboot"]:
        target_mode = "fastboot"
    elif mode == "recovery":
        target_mode = "recovery"
    else:
        console.print(f"[bold red][ERROR][/bold red] Неизвестный параметр перезагрузки: {mode}")
        return

    with open(boot_mode_path, "w") as f:
        json.dump({"mode": target_mode}, f)
    return "reboot"