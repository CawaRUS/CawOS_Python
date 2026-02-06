import os
import json
import shutil
import logging
from pathlib import Path
from core import auth

# Инициализация логгера
logger = logging.getLogger("fastboot")

class FastbootInterface:
    def __init__(self):
        self.data_dir = Path("data")
        self.json_dir = self.data_dir / "json"
        self.userdata_dir = self.data_dir / "0"
        self.boot_mode_path = self.json_dir / "boot_mode.json"

        self.partitions = {
            "kernel": Path("core/os/CawOS/kernel.py"),
            "shell": Path("core/shell.py"),
            "recovery": Path("core/recovery.py"),
            "system": Path("core"),
        }

        self.required_dirs = ["app", "download", "documents", "photos", "music"]
        logger.info("Fastboot mode started")

    # =========================
    # UTIL
    # =========================

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def get_hwid(self):
        return "CAW-" + hex(abs(hash(Path.cwd())))[-4:].upper()

    def get_oem_status(self):
        data = auth.load_settings()
        return "UNLOCKED" if data.get("oem_unlock", False) else "LOCKED"

    def set_boot_mode(self, mode: str):
        self.json_dir.mkdir(parents=True, exist_ok=True)
        with open(self.boot_mode_path, "w", encoding="utf-8") as f:
            json.dump({"mode": mode}, f)

    # =========================
    # DATA
    # =========================

    def format_data(self):
        logger.warning("Formatting data partition via Fastboot")
        if self.json_dir.exists():
            shutil.rmtree(self.json_dir)

        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.userdata_dir.mkdir(parents=True, exist_ok=True)

        for item in self.userdata_dir.iterdir():
            if item.name == "app":
                continue
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                else:
                    shutil.rmtree(item)
            except Exception as e:
                logger.error(f"Fastboot format error on {item}: {e}")
                print(f"[WARN] Failed to remove {item}: {e}")

        for folder in self.required_dirs:
            (self.userdata_dir / folder).mkdir(exist_ok=True)

    # =========================
    # COMMANDS
    # =========================

    def cmd_oem_unlock(self, hwid):
        logger.warning("OEM Unlock procedure started")
        if self.get_oem_status() == "UNLOCKED":
            print("[!] Device already unlocked.")
            return

        print("CAUTION: Unlocking will WIPE /data!")
        confirm = input(f"Enter password ({hwid}): ")

        if confirm != hwid[::-1]:
            logger.error("OEM Unlock failed: Wrong HWID password")
            print("[FAIL] Wrong password.")
            return

        print("[OK] Password verified. Formatting /data...")
        self.format_data()

        data = auth.load_settings()
        data["oem_unlock"] = True
        auth.save_settings(data)

        logger.info("OEM Unlock successful")
        print("[SUCCESS] Device unlocked.")

    def cmd_flash(self, part, source):
        logger.info(f"Flash command: {part} from {source}")
        if self.get_oem_status() == "LOCKED":
            logger.warning("Flash blocked: Bootloader LOCKED")
            print("[FAIL] Device is locked.")
            return

        if part not in self.partitions:
            print(f"[FAIL] Partition '{part}' is not flashable.")
            return

        src = Path(source)
        dst = self.partitions[part]

        if not src.exists():
            logger.error(f"Flash error: source {source} not found")
            print(f"[FAIL] Source '{source}' not found.")
            return

        print(f"Writing '{src}' to '{part}'...")

        try:
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            logger.info(f"Flash success: {part}")
            print("[OKAY] Flash completed.")
        except Exception as e:
            logger.exception(f"Flash failed for {part}")
            print(f"[ERROR] Flash failed: {e}")

    def cmd_erase(self, part):
        logger.warning(f"Erase command: {part}")
        if part in ("data", "userdata"):
            shutil.rmtree(self.userdata_dir, ignore_errors=True)
            self.userdata_dir.mkdir(exist_ok=True)
            logger.info("Userdata partition erased")
            print(f"[OKAY] Partition '{part}' erased.")
        else:
            print(f"[FAIL] Cannot erase '{part}'.")

    def cmd_reboot(self, mode="normal"):
        logger.info(f"Rebooting to {mode} via Fastboot")
        self.set_boot_mode(mode)
        print(f"Rebooting to {mode}...")

    def cmd_help(self):
        print("""
    Available commands:
    help                        Show this help message
    oem unlock                  Unlock bootloader (WIPES /data)
    flash <partition> <source>  Flash file or directory to partition
    erase <data|userdata>       Erase user data partition
    reboot                      Reboot device normally
    reboot recovery             Reboot device into recovery
    getvar                      Print device variables
    """.strip())

    # =========================
    # MAIN LOOP
    # =========================

    def run(self):
        self.clear_screen()
        hwid = self.get_hwid()

        print("      CAWOS FASTBOOT INTERFACE")
        print("====================================")
        print("PRODUCT NAME: CawOS")
        print(f"DEVICE ID:    {hwid}")
        print(f"LOCK STATE:   {self.get_oem_status()}")
        print("====================================\n")

        while True:
            try:
                raw = input("fastboot> ").strip()
            except KeyboardInterrupt:
                print()
                break

            if not raw:
                continue

            cmd = raw.split()

            match cmd:
                case ["oem", "unlock"]:
                    self.cmd_oem_unlock(hwid)

                case ["flash", part, source]:
                    self.cmd_flash(part, source)

                case ["erase", part]:
                    self.cmd_erase(part)

                case ["reboot"]:
                    self.cmd_reboot()
                    break

                case ["reboot", "recovery"]:
                    self.cmd_reboot("recovery")
                    break

                case ["getvar"]:
                    data = auth.load_settings()
                    print(f"oem_unlock: {data.get('oem_unlock', False)}")
                    print(f"allow_root: {data.get('allow_root', False)}")
                    print(f"has_root_password: {bool(data.get('root_password_hash'))}")

                case ["help"]:
                    self.cmd_help()

                case _:
                    print(f"Unknown command: {cmd[0]}")