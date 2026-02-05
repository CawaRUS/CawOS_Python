try:
    from data.info import real_time
except:
    import datetime
    # Fallback на системное время Python, если CawOS API недоступно
    real_time = lambda: datetime.datetime.now().strftime("%H:%M:%S")

about = "Показать текущее системное время"

def execute(args, kernel, console):
    try:
        t = real_time()
        console.print(f"🕒 Текущее время CawOS: [bold green]{t}[/bold green]")
    except Exception as e:
        console.print(f"[red]Не удалось получить время: {e}[/red]")