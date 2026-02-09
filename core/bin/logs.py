from core.fs import fs

about = "Просмотр системного журнала (логов)."

def execute(args, kernel, console):
    log_file_path = "data/log/system.log"
    
    if not fs.exists(log_file_path):
        console.print("[bold red]Ошибка:[/bold red] Файл логов еще не создан.")
        return

    # Очистка через fs.write_file
    if args and args[0] == "--clear":
        if fs.write_file(log_file_path, ""):
            console.print("[bold yellow]Журнал очищен.[/bold yellow]")
        else:
            console.print("[red]Ошибка при очистке через FS.[/red]")
        return

    try:
        # Читаем через fs.read_file — это безопасно и доверенно
        content = fs.read_file(log_file_path)
        if content is None:
            console.print("[red]Доступ к логам запрещен или файл занят.[/red]")
            return
            
        lines = content.splitlines()
        last_lines = lines[-15:]
        
        console.print("[bold blue]--- Системный журнал (Последние 15 событий) ---[/bold blue]")
        for line in last_lines:
            line = line.strip()
            # Твоя магия цветов (оставляем как есть, она супер)
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