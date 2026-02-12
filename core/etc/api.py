import time
import logging

logger = logging.getLogger("API")

# --- ЗАЩИТА ЯДРА API ---
_safe_str = str
_safe_len = len
_safe_time = time.time

def get_api(app_name, console, kernel, fs, auth, info, real_time, is_system, Panel, Table):
    """Генерирует объект app_os с защитой от флуда и проверкой системных параметров."""
    
    state = {
        "last_reset": _safe_time(),
        "counts": {"log": 0, "print": 0},
        "is_banned": False 
    }

    def safe_wrapper(func, limit, type_name, max_chars=1000):
        def wrapped(*args, **kwargs):
            if state["is_banned"]:
                return None

            now = _safe_time()
            if now - state["last_reset"] > 1.0:
                state["counts"] = {"log": 0, "print": 0}
                state["last_reset"] = now
            
            msg_str = _safe_str(args[0]) if args else ""
            msg_len = _safe_len(msg_str)
            
            if msg_len > max_chars:
                state["is_banned"] = True
                logger.warning(f"APP {app_name} BANNED: {type_name} payload too large")
                console.print(f"\n[bold white on red] SECURITY [/] {app_name} заблокирован: лимит символов!")
                raise SystemExit(f"Security Violation: {type_name} too long")

            state["counts"][type_name] += 1
            if state["counts"][type_name] > limit:
                state["is_banned"] = True
                logger.warning(f"APP {app_name} KILLED FOR FLOOD")
                console.print(f"\n[bold white on red] FATAL [/] {app_name} остановлен за флуд!")
                raise SystemExit(f"Flood limit exceeded: {type_name}")
            
            return func(*args, **kwargs)
        return wrapped

    # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ВЕРСИИ ---
    def fetch_version():
        # 1. Пробуем вытащить из объекта info (data.info)
        v = getattr(info, "version", None)
        if v and v != "NULL": return v
        
        # 2. Пробуем вытащить напрямую из модуля, если info — это обертка
        if hasattr(info, "info"):
            v = getattr(info.info, "version", None)
            if v: return v

        # 3. Читаем из конфига через auth
        if auth:
            try:
                settings = auth.load_settings()
                return settings.get("version", "1.4 alpha")
            except:
                pass
        
        return "1.4 alpha" # Hardcode fallback

    # Формируем словарь API
    api = {
        "print": safe_wrapper(console.print, 150, "print", max_chars=5000),
        "log": safe_wrapper(logger.info, 10, "log", max_chars=1000),
        "log_err": safe_wrapper(logger.error, 10, "log", max_chars=1000),
        "log_warn": safe_wrapper(logger.warning, 10, "log", max_chars=1000),
        
        "read_file": fs.read_file if fs else None,
        "write_file": fs.write_file if fs else None,
        "list_dir": fs.list_dir if fs else None,
        "current_path": fs.current_path if fs else None,
        "change_dir": fs.change_dir if fs else None,
        
        "time": real_time,
        "Panel": Panel,
        "Table": Table,
        "is_system": is_system,
        
        "get_status": lambda: {
            "root_active": getattr(kernel, "root_mode", False),
            "root_allowed": auth.load_settings().get("allow_root", False) if auth else False,
            "bootloader_unlocked": auth.load_settings().get("oem_unlock", False) if auth else False,
            "version": fetch_version(),
            "user": auth.load_settings().get("username", "user") if auth else "user"
        }
    }

    if is_system:
        api["auth"] = auth

    return api