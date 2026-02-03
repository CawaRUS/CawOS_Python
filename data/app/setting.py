# settings.py — системное приложение "Настройки"
import json
import os
from datetime import datetime
from core import auth  # новый модуль

info_path = os.path.join("data", "json", "info.json")
apps_path = os.path.join("data", "app")

def read_info():
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def write_info(data):
    os.makedirs(os.path.dirname(info_path), exist_ok=True)
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def show_menu():
    print("\n=== Настройки ===")
    print("1. Показать текущее время")
    print("2. Изменить имя пользователя")
    print("3. Список приложений")
    print("4. Вкл/Выкл проверку целостности (verify.py)")
    print("5. Вкл/Выкл модуль безопасности (secury.py)")
    print("6. Разрешить/запретить получение ROOT")
    print("7. Установить/сменить пароль ROOT")
    print("8. Включить выбор ОС")
    print("0. Выход")

# инициализация info.json (не затираем существующие поля)
info = read_info()
changed = False
if "username" not in info:
    info["username"] = "user"; changed = True
if "verify_enabled" not in info:
    info["verify_enabled"] = True; changed = True
if "secury_enabled" not in info:
    info["secury_enabled"] = True; changed = True
if changed:
    write_info(info)

while True:
    show_menu()
    choice = input("Выберите опцию: ").strip()

    if choice == "1":
        print(f"Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    elif choice == "2":
        new_name = input("Введите новое имя пользователя: ").strip()
        if new_name:
            info["username"] = new_name
            write_info(info)
            print(f"Имя пользователя изменено на: {new_name}")
        else:
            print("Имя не изменено.")

    elif choice == "3":
        print("Установленные приложения:")
        if os.path.exists(apps_path):
            for a in os.listdir(apps_path):
                if a.endswith(".py"):
                    print(" - " + a[:-3])
        else:
            print("Папка с приложениями не найдена.")

    elif choice == "4":
        info["verify_enabled"] = not info.get("verify_enabled", True)
        write_info(info)
        print(f"Проверка целостности: {'Включена' if info['verify_enabled'] else 'Отключена'}")

    elif choice == "5":
        info["secury_enabled"] = not info.get("secury_enabled", True)
        write_info(info)
        print(f"Модуль безопасности: {'Включён' if info['secury_enabled'] else 'Отключён'}")

    elif choice == "6":
        # Проверяем, разрешил ли Fastboot разблокировку
        info = read_info()
        if not info.get("oem_unlock", False):
            print("\n[ОШИБКА] Доступ заблокирован на уровне загрузчика!")
        else:
            # Если в Fastboot всё разрешено, работаем как обычно
            new_val = not auth.is_root_allowed()
            auth.set_root_allowed(new_val)
            print(f"Получение ROOT теперь: {'РАЗРЕШЕНО' if new_val else 'ЗАПРЕЩЕНО'}")

    elif choice == "7":
        p1 = input("Придумайте пароль для ROOT: ")
        p2 = input("Повторите пароль: ")
        if not p1:
            print("Пароль пустой. Отмена.")
        elif p1 != p2:
            print("Пароли не совпадают.")
        else:
            auth.set_root_password(p1)
            print("Пароль ROOT установлен/обновлён.")

    elif choice == "8":
        info["multi_os_boot"] = not info.get("multi_os_boot", False)
        write_info(info)
        print(f"Выбор ОС при старте: {'Включён' if info['multi_os_boot'] else 'Отключён'}")


    elif choice == "0":
        print("Выход из настроек.")
        break

    else:
        print("Неверная опция.")
