import os

about = "Просмотр системного журнала (логов)."

def execute(args, kernel, console):
    log_file_path = "data/log/system.log"
    
    if not os.path.exists(log_file_path):
        console.print("[bold red]Ошибка:[/bold red] Файл логов еще не создан.")
        return

    # Если переданы аргументы, например 'logs --clear'
    if args and args[0] == "--clear":
        with open(log_file_path, "w") as f:
            f.write("")
        console.print("[bold yellow]Журнал очищен.[/bold yellow]")
        return

    # Читаем последние 15 строк, чтобы не засорять консоль
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = lines[-15:] # Берем только хвост
            
            console.print("[bold blue]--- Системный журнал (Последние 15 событий) ---[/bold blue]")
            for line in last_lines:
                # Немного магии: красим уровни логов
                line = line.strip()
                if "[INFO]" in line:
                    console.print(f"[green]{line}[/green]")
                elif "[ERROR]" in line or "[CRITICAL]" in line:
                    console.print(f"[red]{line}[/red]")
                elif "[WARNING]" in line:
                    console.print(f"[yellow]{line}[/yellow]")
                else:
                    console.print(line)
                    
    except Exception as e:
        console.print(f"[bold red]Не удалось прочитать лог:[/bold red] {e}")