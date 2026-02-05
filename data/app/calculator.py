import os
import math
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()
app_os = globals().get("app_os")

def show_help():
    table = Table(title="Справка калькулятора", title_style="bold magenta")
    table.add_column("Тип", style="cyan")
    table.add_column("Операции / Функции", style="white")
    
    table.add_row("Базовые", "+, -, *, /, ** (степень), % (остаток)")
    table.add_row("Функции", "sqrt(x), abs(x), round(x), log(x)")
    table.add_row("Тригонометрия", "sin(x), cos(x), tan(x)")
    table.add_row("Константы", "pi (3.14...), e (2.71...)")
    table.add_row("Команды", "help (справка), exit (выход)")
    
    console.print(table)

def calc():
    safe_dict = {
        "abs": abs, "round": round, "pow": pow,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "pi": math.pi, "e": math.e,
        "log": math.log
    }

    history = []

    console.print(Panel.fit(
        "[bold green]Калькулятор[/]\n"
        "[dim]Введите [bold white]help[/] для списка функций или [bold red]exit[/] для выхода[/]",
        border_style="magenta"
    ))

    while True:
        expr = Prompt.ask("[bold cyan]>>>[/]").strip()
        
        if not expr:
            continue

        if expr.lower() in ["exit", "выход"]:
            console.print("[yellow]Выход из калькулятора...[/]")
            break
        
        if expr.lower() in ["help", "помощь", "?"]:
            show_help()
            continue

        try:
            # Вычисляем
            result = eval(expr, {"__builtins__": None}, safe_dict)
            
            history.append((expr, result))
            if len(history) > 5: history.pop(0)

            console.print(f"[bold white]Результат:[/] [bold green]{result}[/]")

        except SyntaxError:
            console.print("[bold red]❌ Ошибка синтаксиса:[/] Проверьте правильность написания выражения.")
        except NameError:
            console.print("[bold red]❌ Неизвестная функция:[/] Используйте [white]help[/] для списка команд.")
        except ZeroDivisionError:
            console.print("[bold red]❌ Ошибка:[/] Деление на ноль невозможно.")
        except Exception as e:
            console.print(f"[bold red]❌ Ошибка:[/] [yellow]{e}[/]")

        # Показываем маленькую историю внизу, если она есть
        if history and expr.lower() not in ["help", "?"]:
            table = Table(title="История", title_style="dim", box=None)
            table.add_column("Выражение", style="dim cyan")
            table.add_column("=", style="dim white")
            table.add_column("Результат", style="dim green")
            for e, r in history:
                table.add_row(e, "=", str(r))
            console.print(table)


calc()