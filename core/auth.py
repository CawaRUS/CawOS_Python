# core/auth.py — хранение и проверка root-настроек/пароля
import os, json, hashlib, logging

logger = logging.getLogger("auth")
INFO_PATH = os.path.join("data", "json", "info.json")

def load_settings():
    try:
        with open(INFO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.debug("info.json not found, returning empty settings")
        return {}
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return {}

def save_settings(data):
    try:
        os.makedirs(os.path.dirname(INFO_PATH), exist_ok=True)
        with open(INFO_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.debug("Settings saved to info.json")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")

def is_root_allowed() -> bool:
    data = load_settings()
    
    # ПРОВЕРКА ИЕРАРХИИ:
    if not data.get("oem_unlock", False):
        logger.debug("Root disallowed: OEM is locked")
        return False
        
    allowed = bool(data.get("allow_root", False))
    logger.debug(f"Root allowed status: {allowed}")
    return allowed

def set_root_allowed(allowed: bool):
    logger.info(f"Changing allow_root to: {allowed}")
    data = load_settings()
    data["allow_root"] = bool(allowed)
    save_settings(data)

def has_root_password() -> bool:
    data = load_settings()
    return bool(data.get("root_password_hash"))

def set_root_password(password: str):
    logger.info("Setting new root password hash")
    h = hashlib.sha256(password.encode("utf-8")).hexdigest()
    data = load_settings()
    data["root_password_hash"] = h
    save_settings(data)

def verify_root_password(password: str) -> bool:
    data = load_settings()
    stored = data.get("root_password_hash", "")
    if not stored:
        logger.warning("Root password verification failed: no password set")
        return False
    
    success = hashlib.sha256(password.encode("utf-8")).hexdigest() == stored
    if success:
        logger.info("Root password verified successfully")
    else:
        logger.warning("Root password ATTEMPT FAILED (Wrong password)")
    return success