import json
import os
import glob

def del_json():
    try:
        base_dir = os.path.dirname(__file__)
    except NameError:
        base_dir = os.getcwd()
    # Найти путь до CawOS
    parts = os.path.abspath(base_dir).split(os.sep)
    if 'CawOS' in parts:
        cawos_index = parts.index('CawOS')
        cawos_root = os.sep.join(parts[:cawos_index + 1])
        json_dir = os.path.join(cawos_root, 'data', 'json')
    else:
        json_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'data', 'json'))
    print(f"Папка для поиска: {json_dir}")  # отладочный вывод
    json_files = glob.glob(os.path.join(json_dir, '*.json'))
    print(f"Найдено файлов: {json_files}")  # отладочный вывод
    if not json_files:
        print("Нет файлов для удаления.")
        return
    confirm = input(f"Вы действительно хотите удалить {len(json_files)} файлов .json в {json_dir}? (y/n): ")
    if confirm.lower() != 'y':
        print("Удаление отменено.")
        return
    for file_path in json_files:
        try:
            os.remove(file_path)
            print(f"Удалён: {file_path}")
        except Exception as e:
            print(f"Ошибка при удалении {file_path}: {e}")

del_json()