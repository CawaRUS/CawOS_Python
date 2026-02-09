import time
import logging

logger = logging.getLogger("API")

def get_api(app_name, console, kernel, fs, auth, info, real_time, is_system, Panel, Table):
    """Генерирует объект app_os с защитой от флуда, длинных строк и механизмом бана."""
    
    # Состояние для лимитов и безопасности
    state = {
        "last_reset": time.time(),
        "counts": {"log": 0, "print": 0},
        "is_banned": False  # Глобальный флаг бана для текущей сессии приложения
    }

    def safe_wrapper(func, limit, type_name, max_chars=1000):
        def wrapped(*args, **kwargs):
            # 1. Если приложение уже забанено — полный игнор
            if state["is_banned"]:
                return None

            now = time.time()
            # Сброс счетчиков раз в секунду
            if now - state["last_reset"] > 1.0:
                state["counts"] = {"log": 0, "print": 0}
                state["last_reset"] = now
            
            # Проверка входных данных
            msg_str = str(args[0]) if args else ""
            
            # 2. Проверка на длину строки (Защита от переполнения буфера/памяти)
            if len(msg_str) > max_chars:
                state["is_banned"] = True
                logger.warning(f"APP {app_name} BANNED: {type_name} payload too large ({len(msg_str)} chars)")
                console.print(f"\n[bold white on red] SECURITY [/] Приложение {app_name} заблокировано: превышен лимит символов!")
                raise SystemExit(f"Security Violation: {type_name} too long")

            # 3. Проверка на количество вызовов (Flood Protection)
            state["counts"][type_name] += 1
            if state["counts"][type_name] > limit:
                state["is_banned"] = True
                logger.warning(f"APP {app_name} KILLED FOR FLOOD ({type_name})")
                console.print(f"\n[bold white on red] FATAL [/] Приложение {app_name} принудительно остановлено за флуд {type_name}!")
                raise SystemExit(f"Flood limit exceeded: {type_name}")
            
            return func(*args, **kwargs)
        return wrapped

    # Формируем словарь API
    api = {
        # Применяем обертки с твоими лимитами
        "print": safe_wrapper(console.print, 150, "print", max_chars=5000),
        "log": safe_wrapper(logger.info, 10, "log", max_chars=1000),
        "log_err": safe_wrapper(logger.error, 10, "log", max_chars=1000),
        "log_warn": safe_wrapper(logger.warning, 10, "log", max_chars=1000),
        
        # Файловая система (проверяем наличие модуля)
        "read_file": fs.read_file if fs else None,
        "write_file": fs.write_file if fs else None,
        "list_dir": fs.list_dir if fs else None,
        "current_path": fs.current_path if fs else None,
        "change_dir": fs.change_dir if fs else None,
        
        # Инструменты и информация
        "time": real_time,
        "Panel": Panel,
        "Table": Table,
        "is_system": is_system,
        
        "get_status": lambda: {
            "root_active": getattr(kernel, "root_mode", "NULL"),
            "root_allowed": auth.load_settings().get("allow_root", "NULL") if auth else "NULL",
            "bootloader_unlocked": auth.load_settings().get("oem_unlock", "NULL") if auth else "NULL",
            "version": getattr(info, "version", "NULL"),
            "user": auth.load_settings().get("username", "NULL") if auth else "NULL"
        }
    }

    # Если приложение системное, даем расширенные права
    if is_system:
        api["auth"] = auth

    return api