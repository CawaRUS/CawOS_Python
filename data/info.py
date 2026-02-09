deadlock = True
try:
    import json
except ImportError:
    print("[ERROR] Не удалось импортировать модуль 'json'. Работа невозможна.")
    import sys
    sys.exit(1)

try:
    import os
except ImportError:
    print("[ERROR] Не удалось импортировать модуль 'os'. Работа невозможна.")
    import sys
    sys.exit(1)
class info:
    name_os = "CawOS"
    version = "1.4 alpha"

def real_time():
    import time
    return time.strftime("%#H:%M")

JSON_FILE = os.path.join("data", "json")
os.makedirs(JSON_FILE, exist_ok=True)
_exit_file = os.path.join(JSON_FILE, "exit_status.json")


def get_exit_on():
    if not os.path.exists(_exit_file):
        return 0
    try:
        with open(_exit_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("exit_on", 0)
    except Exception:
        return 0

def set_exit_on(value):
    try:
        with open(_exit_file, "w", encoding="utf-8") as f:
            json.dump({"exit_on": value}, f)
    except Exception as e:
        print(f"Ошибка записи exit_on: {e}")


errors = {
    "p_kernel": "Kernel Panic",
    "e_disk": "Disk Error"
}