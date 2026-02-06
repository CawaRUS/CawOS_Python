import os
from rich.table import Table
import core.fs.fs as fs

about = "Поиск файлов по системе."

def execute(args, kernel, console):
    if not args:
        console.print("[yellow]Использование:[/] find <название>")
        return

    query = " ".join(args).lower()
    
    # Определяем точку старта и лимит на основе прав из fs
    # Если root активен, fs.check_access позволит смотреть от root_limit
    search_root = fs.root_limit if fs.is_root_active() else fs.base_root
    
    results = []
    
    # Визуальный индикатор прав
    status_prefix = "[bold red][ROOT][/]" if fs.is_root_active() else "[bold blue][USER][/]"
    console.print(f"{status_prefix} Поиск [italic]{query}[/] в [dim]{search_root}[/]...")

    try:
        # Рекурсивно обходим дерево через os.walk, но фильтруем через fs.check_access
        for root, dirs, files in os.walk(search_root):
            # Проверяем файлы
            for name in files:
                full_path = os.path.join(root, name)
                if query in name.lower() and fs.check_access(full_path):
                    # Делаем путь относительным для красоты вывода
                    display_path = os.path.relpath(full_path, search_root)
                    results.append((display_path, "Файл"))
            
            # Проверяем папки
            for name in dirs:
                full_path = os.path.join(root, name)
                if query in name.lower() and fs.check_access(full_path):
                    display_path = os.path.relpath(full_path, search_root)
                    results.append((display_path, "Папка"))

            # Ограничитель производительности
            if len(results) > 100:
                break

        if not results:
            console.print(f"[red]Ничего не найдено.[/]")
        else:
            table = Table(title=f"find: {query}", border_style="cyan")
            table.add_column("Тип", style="magenta")
            table.add_column("Путь", style="green")

            for path, f_type in results:
                # Добавляем префикс корня для ясности
                prefix = "/" if fs.is_root_active() else "~/"
                table.add_row(f_type, prefix + path)

            console.print(table)
            if len(results) > 100:
                console.print("[dim]Найдено слишком много совпадений, показаны первые 100.[/]")

    except Exception as e:
        console.print(f"[bold red]Ошибка Spotlight:[/] {e}")