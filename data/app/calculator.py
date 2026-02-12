import math
from rich.markup import escape 

# Удалены: os, sys, Console, Panel, Table, Prompt (они уже в глобальном окружении)
# Удален sys.set_int_max_str_digits (это должна контролировать ОС)
# Удален console = Console() (используем готовый объект console)

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

def is_safe(expr):
    """Проверка выражения на запрещенные символы интроспекции."""
    forbidden = ['.', '[', ']', '_', '__']
    for char in forbidden:
        if char in expr:
            return False, char
    return True, None

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
        try:
            expr = Prompt.ask("[bold cyan]>>>[/]").strip()
            
            if not expr:
                continue

            if expr.lower() in ["exit", "выход"]:
                console.print("[yellow]Выход из калькулятора...[/]")
                break
            
            if expr.lower() in ["help", "помощь", "?"]:
                show_help()
                continue

            if len(expr) > 100:
                console.print("[bold red]❌ Ошибка:[/] Выражение слишком длинное.")
                continue

            safe, char = is_safe(expr)
            if not safe:
                console.print(f"[bold red]❌ Уязвимость:[/] Использование '{char}' запрещено в целях безопасности.")
                continue

            if "**" in expr:
                base, exp = expr.split("**", 1)
                try:
                    if float(eval(exp, {"__builtins__": None}, safe_dict)) > 10000:
                        console.print("[bold red]❌ Ошибка:[/] Слишком большая степень.")
                        continue
                except: pass

            result = eval(expr, {"__builtins__": None}, safe_dict)
            safe_result = escape(str(result))
            
            history.append((escape(expr), safe_result))
            if len(history) > 5: history.pop(0)

            console.print(f"[bold white]Результат:[/] [bold green]{safe_result}[/]")

        except (MemoryError, OverflowError):
            console.print("[bold red]❌ Ошибка:[/] Вычисление слишком тяжелое.")
        except SyntaxError:
            console.print("[bold red]❌ Ошибка синтаксиса:[/] Проверьте выражение.")
        except NameError:
            console.print("[bold red]❌ Ошибка:[/] Использованы запрещенные функции.")
        except ZeroDivisionError:
            console.print("[bold red]❌ Ошибка:[/] Деление на ноль.")
        except Exception as e:
            error_msg = str(e) if str(e) else e.__class__.__name__
            console.print(f"[bold red]❌ Ошибка:[/] [yellow]{escape(error_msg)}[/]")

        if history and expr.lower() not in ["help", "?"]:
            table = Table(title="История", title_style="dim", box=None)
            table.add_column("Выражение", style="dim cyan")
            table.add_column("=", style="dim white")
            table.add_column("Результат", style="dim green")
            for e, r in history:
                table.add_row(e, "=", r)
            console.print(table)

calc()