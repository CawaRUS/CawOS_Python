import os
import json
import shutil
import time
from core import auth

class FastbootInterface:
    def __init__(self):
        self.boot_mode_path = os.path.join("data", "json", "boot_mode.json")
        # Словарь соответствия разделов и реальных папок/файлов
        self.partitions = {
            "kernel": "core/os/CawOS/kernel.py",
            "shell": "core/shell.py",
            "recovery": "core/recovery.py",
            "system": "core/"
        }

    def formating(self):
        json_dir = os.path.join("data", "json")
        if os.path.exists(json_dir):
            shutil.rmtree(json_dir)
        os.makedirs(json_dir)

        # 2. Очистка и восстановление data/0
        user_dir = os.path.join("data", "0")
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        # Список обязательных папок, которые должны быть в системе
        required_dirs = ["app", "download", "documents", "photos", "music"]

        # Удаляем старое содержимое
        for item in os.listdir(user_dir):
            if item == "app": # Твоё условие: приложения плебеев не трогаем
                continue
            
            item_path = os.path.join(user_dir, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                else:
                    shutil.rmtree(item_path)
            except Exception as e:
                pass

        # Создаем чистую структуру
        for folder in required_dirs:
            path = os.path.join(user_dir, folder)
            if not os.path.exists(path):
                os.makedirs(path)

    def set_boot_mode(self, mode):
        os.makedirs(os.path.dirname(self.boot_mode_path), exist_ok=True)
        with open(self.boot_mode_path, "w") as f:
            json.dump({"mode": mode}, f)

    def get_oem_status(self):
        data = auth.load_settings()
        return "UNLOCKED" if data.get("oem_unlock", False) else "LOCKED"

    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        hwid = "CAW-" + str(hash(os.getcwd()))[-4:]
        
        print(f"      CAWOS FASTBOOT INTERFACE      ")
        print(f"====================================")
        print(f"PRODUCT NAME: CawOS")
        print(f"DEVICE ID:    {hwid}")
        print(f"LOCK STATE:   {self.get_oem_status()}")
        print(f"====================================\n")

        while True:
            cmd = input("fastboot> ").strip().split()
            if not cmd: continue
            
            # 1. OEM Unlock (Твоя база)
            if cmd == ["oem", "unlock"]:
                if self.get_oem_status() == "UNLOCKED":
                    print("[!] Device is already unlocked.")
                    continue
                print(f"CAUTION: Unlocking will WIPE /data!")
                confirm = input(f"Enter password ({hwid}): ")
                if confirm == hwid[::-1]:
                    print("[OK] Password verified. Formatting /data...")
                    self.formating()
                    os.makedirs("data/0", exist_ok=True)
                    data = auth.load_settings()
                    data["oem_unlock"] = True
                    auth.save_settings(data)
                    print("[SUCCESS] Device unlocked.")
                else:
                    print("[FAIL] Wrong password.")

            # 2. РЕАЛЬНАЯ ПРОШИВКА (Flash)
            elif cmd[0] == "flash":
                if self.get_oem_status() == "LOCKED":
                    print("[FAIL] Device is locked. Unlock OEM first.")
                    continue
                if len(cmd) < 3:
                    print("Usage: flash <partition> <source_file>")
                    continue
                
                part, source = cmd[1], cmd[2]
                if part in self.partitions:
                    if os.path.exists(source):
                        target = self.partitions[part]
                        print(f"Writing '{source}' to '{part}'...")
                        try:
                            # Если это папка (system), копируем дерево, если файл - файл
                            if os.path.isdir(source):
                                shutil.copytree(source, target, dirs_exist_ok=True)
                            else:
                                shutil.copy2(source, target)
                            print("[OKAY] Flash completed.")
                        except Exception as e:
                            print(f"[ERROR] Flash failed: {e}")
                    else:
                        print(f"[FAIL] Source file '{source}' not found.")
                else:
                    print(f"[FAIL] Partition '{part}' is not flashable.")

            # 3. Стирание данных (Erase)
            elif cmd[0] == "erase":
                if len(cmd) < 2:
                    print("Usage: erase <partition>")
                    continue
                part = cmd[1]
                if part == "data" or part == "userdata":
                    shutil.rmtree("data/0", ignore_errors=True)
                    os.makedirs("data/0", exist_ok=True)
                    print(f"[OKAY] Partition '{part}' erased.")
                else:
                    print(f"[FAIL] Cannot erase '{part}' (read-only in fastboot).")

            # 4. Перезагрузка (с выбором режима)
            elif cmd[0] == "reboot":
                mode = "normal"
                if len(cmd) > 1 and cmd[1] == "recovery":
                    mode = "recovery"
                
                self.set_boot_mode(mode)
                print(f"Rebooting to {mode}...")
                break

            elif cmd[0] == "getvar":
                info = auth.load_settings()
                for k, v in info.items():
                    print(f"{k}: {v}")

            else:
                print(f"Unknown command: {cmd[0]}")