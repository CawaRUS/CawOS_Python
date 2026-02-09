from rich.table import Table
import core.fs.fs as fs

about = "Поиск файлов по системе."

def execute(args, kernel, console):
    if not args:
        console.print("[yellow]Использование:[/] find <название>")
        return

    query = " ".join(args).lower()
    search_root = fs.root_limit if fs.is_root_active() else fs.base_root
    results = []

    try:
        # Используем fs.walk
        for root, dirs, files in fs.walk(search_root):
            for name in files + dirs:
                # Используем fs.join_paths вместо os.path.join
                full_path = fs.join_paths(root, name) 
                
                if query in name.lower() and fs.check_access(full_path):
                    display_path = fs.get_relpath(full_path, search_root)
                    f_type = "Файл" if name in files else "Папка"
                    results.append((display_path, f_type))

            if len(results) > 100: break

        if not results:
            console.print(f"[red]Ничего не найдено.[/]")
        else:
            table = Table(title=f"find: {query}", border_style="cyan")
            table.add_column("Тип", style="magenta")
            table.add_column("Путь", style="green")
            for path, f_type in results:
                prefix = "/" if fs.is_root_active() else "~/"
                table.add_row(f_type, prefix + path)
            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Ошибка find:[/] {e}")