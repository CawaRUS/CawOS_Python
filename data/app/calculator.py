import math
import ast
from rich.markup import escape 

# Глобальные объекты (Table, Panel, Prompt, console) проброшены из run.py

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

def is_expression_safe(expr):
    """
    Усиленная проверка через AST (Фикс Бага №14).
    Разрешает математику, но блокирует доступ к атрибутам и методам Python.
    """
    try:
        tree = ast.parse(expr, mode='eval')
        for node in ast.walk(tree):
            allowed_nodes = (
                ast.Expression, ast.BinOp, ast.UnaryOp, 
                ast.Num, ast.Constant, ast.Call, 
                ast.Name, ast.Load,
                ast.Add, ast.Sub, ast.Mult, ast.Div, 
                ast.Pow, ast.Mod, ast.FloorDiv,
                ast.USub, ast.UAdd
            )
            
            if not isinstance(node, allowed_nodes):
                return False, f"Запрещенная структура: {type(node).__name__}"
            
            if isinstance(node, ast.Call):
                # Разрешаем вызов только простых имен: sqrt(), но не ().__class__()
                if not isinstance(node.func, ast.Name):
                    return False, "Вызов методов объектов запрещен"
                    
        return True, None
    except Exception as e:
        return False, f"Ошибка синтаксиса: {e}"

def calc():
    # Набор разрешенных имен (контекст выполнения)
    # Хардкодим PI и E, чтобы они точно были доступны как числа
    safe_dict = {
        "abs": abs, 
        "round": round, 
        "pow": pow,
        "sin": math.sin, 
        "cos": math.cos, 
        "tan": math.tan,
        "sqrt": math.sqrt, 
        "log": math.log,
        "pi": 3.141592653589793, 
        "e": 2.718281828459045
    }

    history = []

    console.print(Panel.fit(
        "[bold green]CawOS Safe Calculator[/]\n"
        "[dim]Защита на уровне AST активна. Константы pi и e захардкожены.[/]",
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
                console.print("[bold red]❌ Ошибка:[/] Слишком длинный ввод.")
                continue

            # 1. AST-фильтрация
            safe, error_reason = is_expression_safe(expr)
            if not safe:
                console.print(f"[bold red]❌ Безопасность:[/] {error_reason}")
                continue

            # 2. Защита от DoS (цепочки степеней)
            if "**" in expr and expr.count("**") > 1:
                console.print("[bold red]❌ Ошибка:[/] Слишком сложная цепочка степеней.")
                continue

            # 3. Выполнение
            # Используем один словарь и для globals, и для locals.
            # Это гарантирует, что eval увидит pi и e в любой среде.
            context = {"__builtins__": {}}
            context.update(safe_dict)
            
            result = eval(expr, context)
            safe_result = escape(str(result))
            
            history.append((escape(expr), safe_result))
            if len(history) > 5: history.pop(0)

            console.print(f"[bold white]Результат:[/] [bold green]{safe_result}[/]")

        except ZeroDivisionError:
            console.print("[bold red]❌ Ошибка:[/] Деление на ноль.")
        except (MemoryError, OverflowError):
            console.print("[bold red]❌ Ошибка:[/] Число слишком велико.")
        except NameError:
            console.print(f"[bold red]❌ Ошибка:[/] Неизвестная функция или переменная.")
        except SyntaxError:
             console.print(f"[bold red]❌ Ошибка:[/] Некорректный синтаксис выражения.")
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