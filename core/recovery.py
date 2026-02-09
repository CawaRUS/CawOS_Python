# core/recovery.py — BOMBPROOF Recovery Mode for CawOS
deadlock = True
import os
import shutil
import time
import zipfile

# --- OPTIONAL DEPENDENCIES ---
try:
    import requests
except Exception:
    requests = None

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn
    from rich.prompt import Prompt, Confirm
except Exception:
    Console = None

# --- CONSTANTS ---
SYSTEM_LOG = os.path.join("data", "log", "system.log")
UPDATE_SERVER = "http://cawas.duckdns.org/system.zip"

# --- SAFE CONSOLE ---
console = Console() if Console else None

def cprint(text):
    if console:
        console.print(text)
    else:
        print(text)

# --- BULLETPROOF LOGGER ---
def recovery_log(msg: str):
    try:
        os.makedirs(os.path.dirname(SYSTEM_LOG), exist_ok=True)
        with open(SYSTEM_LOG, "a", encoding="utf-8") as f:
            f.write(f"[RECOVERY] {msg}\n")
    except Exception:
        pass

# --- CLEAR SCREEN ---
def clear_screen():
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass

# --- SAFE VERSION IMPORT ---
try:
    from data.info import info
    SYSTEM_VERSION = info.version
except Exception:
    SYSTEM_VERSION = "UNKNOWN"

# ===========================
#         MENU
# ===========================
def menu(reason="Manual entry"):
    recovery_log(f"Entered recovery mode: {reason}")

    while True:
        try:
            clear_screen()

            if console:
                console.print(Panel(
                    f"[bold red]CawOS RECOVERY MODE[/bold red]\n"
                    f"[yellow]Status:[/yellow] {reason}",
                    title=f"v {SYSTEM_VERSION}",
                    border_style="red"
                ))
            else:
                print("=== CawOS RECOVERY MODE ===")
                print(f"Status: {reason}\n")

            print("1. Reboot")
            print("2. System Repair (OTA)")
            print("3. Wipe Data")
            print("4. Power Off")

            choice = input("\nSelect action: ").strip()

            if choice == "1":
                recovery_log("User requested reboot")
                return "reboot"

            if choice == "2":
                if run_ota_repair():
                    return "reboot"

            if choice == "3":
                run_wipe_data()

            if choice == "4":
                recovery_log("System powered off")
                os._exit(0)

        except KeyboardInterrupt:
            recovery_log("Ctrl+C ignored in recovery menu")
            reason = "User Interruption (Ctrl+C)"
            time.sleep(0.5)
            continue

# ===========================
#        OTA REPAIR
# ===========================
def run_ota_repair():
    recovery_log("OTA repair started")

    if not requests:
        cprint("[red]Requests module not available[/red]")
        recovery_log("OTA failed: requests not available")
        input("Press Enter...")
        return False

    cprint("[yellow]OTA will reinstall the entire system[/yellow]")
    if input("Continue? (y/N): ").lower() != "y":
        recovery_log("OTA cancelled by user")
        return False

    try:
        r = requests.get(UPDATE_SERVER, stream=True, timeout=15)
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")

        temp_zip = "recovery_image.zip"
        with open(temp_zip, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

        recovery_log("OTA image downloaded")

        temp_dir = "recovery_unpack"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        with zipfile.ZipFile(temp_zip, "r") as z:
            z.extractall(temp_dir)

        shutil.copytree(temp_dir, ".", dirs_exist_ok=True)

        os.remove(temp_zip)
        shutil.rmtree(temp_dir)

        recovery_log("OTA repair completed successfully")
        cprint("[green]System restored successfully[/green]")
        input("Press Enter to reboot...")
        return True

    except Exception as e:
        recovery_log(f"OTA FAILED: {e}")
        cprint(f"[red]OTA failed:[/red] {e}")
        input("Press Enter...")
        return False

# ===========================
#         WIPE DATA
# ===========================
def run_wipe_data():
    recovery_log("Wipe data initiated")

    if input("WIPE ALL USER DATA? (y/N): ").lower() != "y":
        recovery_log("Wipe cancelled")
        return

    try:
        json_dir = os.path.join("data", "json")
        shutil.rmtree(json_dir, ignore_errors=True)
        os.makedirs(json_dir, exist_ok=True)

        user_dir = os.path.join("data", "0")
        os.makedirs(user_dir, exist_ok=True)

        for item in os.listdir(user_dir):
            if item == "app":
                continue
            path = os.path.join(user_dir, item)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)
            except Exception:
                pass

        for d in ["app", "download", "documents", "photos", "music"]:
            os.makedirs(os.path.join(user_dir, d), exist_ok=True)

        recovery_log("Wipe data completed successfully")
        cprint("[green]Factory reset completed[/green]")
        input("Press Enter...")

    except Exception as e:
        recovery_log(f"Wipe FAILED: {e}")
        cprint("[red]Wipe failed[/red]")
        input("Press Enter...")
