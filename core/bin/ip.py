import socket
from rich.table import Table

about = "Отображает сетевые интерфейсы и IP-адреса."

def execute(args, kernel, console):
    """Выводит информацию о локальном IP-адресе и имени хоста."""
    
    table = Table(title="[bold cyan]Сетевые данные CawOS[/bold cyan]", border_style="blue")
    table.add_column("Параметр", style="yellow")
    table.add_column("Значение", style="green")

    try:
        # Получаем имя устройства
        hostname = socket.gethostname()
        # Получаем локальный IP
        # (Этот метод работает почти везде: и на твоем OnePlus, и на Windows)
        local_ip = socket.gethostbyname(hostname)
        
        table.add_row("Имя хоста", hostname)
        table.add_row("Локальный IPv4", local_ip)
        
        # Попробуем получить список всех IP (если их несколько)
        all_ips = socket.gethostbyname_ex(hostname)[2]
        if len(all_ips) > 1:
            table.add_row("Доп. адреса", ", ".join(all_ips[1:]))

        console.print(table)
        
        # Если передан аргумент -e или --extra, можно добавить что-то еще
        if "-e" in args:
             console.print(f"[dim]Дополнительная отладка: режим ядра {kernel.os_name}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Ошибка сети:[/] {e}")