from rich.table import Table

about = "Отображает сетевые интерфейсы и IP-адреса."

def execute(args, kernel, console):
    """Выводит сетевые данные через системный API."""
    
    table = Table(title="[bold cyan]Сетевые данные CawOS[/bold cyan]", border_style="blue")
    table.add_column("Параметр", style="yellow")
    table.add_column("Значение", style="green")

    try:
        # ВНИМАНИЕ: Вызываем твою новую функцию из fs.py
        # Предположим, kernel предоставляет доступ к fs или ты импортируешь его
        from core.fs import fs 
        
        hostname, local_ip = fs.get_network_info()
        
        table.add_row("Имя хоста", hostname)
        table.add_row("Локальный IPv4", local_ip)
        
        # Если хочешь доп. IP, лучше тоже вынеси логику gethostbyname_ex в fs.py
        # Но для теста хватит и этих двух.

        console.print(table)
        
        if "-e" in args:
             console.print(f"[dim]Дополнительная отладка: режим ядра {kernel.os_name}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Ошибка доступа к API сети:[/] {e}")