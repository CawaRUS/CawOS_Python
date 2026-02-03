# core/auth.py — хранение и проверка root-настроек/пароля
import os, json, hashlib

INFO_PATH = os.path.join("data", "json", "info.json")

# --- ИЗМЕНЕНИЕ ---
# Переименовано из _load() в load_settings(), чтобы стать
# публичной функцией для secury.py и verify.py
def load_settings():
    try:
        with open(INFO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
# --- КОНЕЦ ИЗМЕНЕНИЯ ---

# --- ИЗМЕНЕНИЕ ---
# Переименовано из _save() для единообразия
def save_settings(data):
    os.makedirs(os.path.dirname(INFO_PATH), exist_ok=True)
    with open(INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
# --- КОНЕЦ ИЗМЕНЕНИЯ ---

def is_root_allowed() -> bool:
    data = load_settings()
    
    # ПРОВЕРКА ИЕРАРХИИ:
    # Если загрузчик заблокирован (oem_unlock: False), 
    # доступ к ROOT запрещен независимо от других настроек.
    if not data.get("oem_unlock", False):
        return False
        
    # Если OEM разблокирован, смотрим на переключатель из настроек
    return bool(data.get("allow_root", False))

def set_root_allowed(allowed: bool):
    data = load_settings()
    data["allow_root"] = bool(allowed)
    save_settings(data) # Используем новую функцию

def has_root_password() -> bool:
    data = load_settings()
    return bool(data.get("root_password_hash"))

def set_root_password(password: str):
    h = hashlib.sha256(password.encode("utf-8")).hexdigest()
    data = load_settings()
    data["root_password_hash"] = h
    save_settings(data)

def verify_root_password(password: str) -> bool:
    data = load_settings()
    stored = data.get("root_password_hash", "")
    if not stored:
        return False
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored