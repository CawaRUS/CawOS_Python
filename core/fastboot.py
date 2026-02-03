import os
import json
import shutil
from core import auth # Используем твой новый модуль auth

class FastbootInterface:
    def __init__(self):
        self.boot_mode_path = os.path.join("data", "json", "boot_mode.json")
        self.info_path = os.path.join("data", "json", "info.json")

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
            
            # 1. Хардкорная разблокировка с очисткой данных
            if cmd == ["oem", "unlock"] or cmd == ["root", "unlock"]:
                if self.get_oem_status() == "UNLOCKED":
                    print("[!] Device is already unlocked.")
                    continue

                print(f"CAUTION: Unlocking the bootloader will WIPE all your data!")
                confirm = input(f"Enter password for {hwid}: ")
                
                if confirm == hwid[::-1]:
                    print("[OK] Password verified. Formatting /data...")
                    
                    # Симуляция Wipe Data (удаляем папку пользователя 0)
                    user_data = os.path.join("data", "0")
                    if os.path.exists(user_data):
                        shutil.rmtree(user_data)
                        os.makedirs(user_data)
                    
                    # Сохраняем статус
                    data = auth.load_settings()
                    data["oem_unlock"] = True
                    auth.save_settings(data)
                    
                    print("[SUCCESS] Device unlocked. System reset complete.")
                else:
                    print("[FAIL] Authentication failed.")

            # 2. Обратная блокировка
            elif cmd == ["oem", "lock"]:
                data = auth.load_settings()
                data["oem_unlock"] = False
                auth.save_settings(data)
                print("[SUCCESS] Bootloader locked.")

            # 3. Информационная команда (как в оригинале)
            elif cmd[0] == "getvar":
                if len(cmd) > 1 and cmd[1] == "all":
                    info = auth.load_settings()
                    for k, v in info.items():
                        print(f"{k}: {v}")
                else:
                    print("usage: getvar all")

            # 4. Форматирование (Wipe)
            elif cmd == ["erase", "data"]:
                print("Erasing all user data...")
                shutil.rmtree("data/0", ignore_errors=True)
                os.makedirs("data/0", exist_ok=True)
                print("Done.")

            elif cmd[0] == "reboot":
                self.set_boot_mode("normal")
                print("Rebooting to system...")
                break