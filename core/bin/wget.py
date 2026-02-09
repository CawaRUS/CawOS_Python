import requests
import core.fs.fs as fs
from rich.progress import Progress

about = "Скачивание файлов по прямым ссылкам из сети."

def execute(args, kernel, console):
    if not args:
        console.print("[yellow]Использование:[/] wget <url> [название_файла]")
        return

    url = args[0]
    # Если имя файла не указано, берем его из URL
    filename = args[1] if len(args) > 1 else url.split("/")[-1]
    if not filename:
        filename = "downloaded_file"

    # Получаем полный путь через твой FS (он проверит права и песочницу)
    full_path = fs.get_full_path(filename)

    if not fs.check_access(full_path):
        console.print("[bold red]Ошибка доступа:[/] Нельзя сохранить файл вне системы.")
        return

    try:
        console.print(f"[cyan]Подключение к[/] [bold]{url}[/]...")
        
        # Делаем запрос с потоковой передачей (stream=True) для больших файлов
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status() # Проверка на 404, 500 и т.д.
        
        total_size = int(response.headers.get('content-length', 0))

        # Красивый индикатор загрузки Rich
        with Progress(console=console) as progress:
            task = progress.add_task(f"[green]Загрузка {filename}...", total=total_size)
            
            with open(full_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

        console.print(f"[bold green]Успешно![/] Файл сохранен: [yellow]{filename}[/yellow]")

    except requests.exceptions.MissingSchema:
        console.print("[bold red]Ошибка:[/] Некорректный URL. Забыли http:// или https://?")
    except requests.exceptions.ConnectionError:
        console.print("[bold red]Ошибка:[/] Не удалось подключиться к серверу.")
    except Exception as e:
        console.print(f"[bold red]Сбой загрузки:[/] {e}")