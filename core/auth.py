# core/auth.py — хранение и проверка root-настроек/пароля
import os, json, hashlib, logging, secrets
deadlock = True

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

def set_root_password(password: str):
    logger.info("Setting new root password hash with salt")
    
    # Генерируем случайную соль (16 байт вполне достаточно)
    salt = secrets.token_hex(16)
    
    # Хешируем: соль + пароль
    salted_pass = salt + password
    h = hashlib.sha256(salted_pass.encode("utf-8")).hexdigest()
    
    # Сохраняем в формате salt$hash
    stored_value = f"{salt}${h}"
    
    data = load_settings()
    data["root_password_hash"] = stored_value
    save_settings(data)

def verify_root_password(password: str) -> bool:
    data = load_settings()
    stored_data = data.get("root_password_hash", "")
    
    if not stored_data:
        logger.warning("Root password verification failed: no password set")
        return False
    
    try:
        # Разделяем сохраненную строку на соль и хеш
        salt, stored_hash = stored_data.split("$")
        
        # Хешируем введенный пароль с той же солью
        attempt_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        
        # Сравниваем через hmac.compare_digest для защиты от атак по времени (side-channel attacks)
        import hmac
        success = hmac.compare_digest(attempt_hash, stored_hash)
        
        if success:
            logger.info("Root password verified successfully")
        else:
            logger.warning("Root password ATTEMPT FAILED (Wrong password)")
        return success
        
    except ValueError:
        # Если в конфиге старый пароль без соли (хеш без $)
        logger.error("Stored password format is legacy or corrupted!")
        return False

def has_root_password() -> bool:
    data = load_settings()
    return bool(data.get("root_password_hash"))