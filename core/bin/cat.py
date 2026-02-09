import core.fs.fs as fs
from rich.syntax import Syntax
from core import secure

about = "Показать содержимое файла"

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите имя файла[/red]")
        return
    
    # Мы не вызываем secure.can_read_file здесь отдельно, 
    # так как fs.read_file() сделает это внутри себя.
    # Это предотвращает двойной вывод панелей и конфликты путей.
    
    filename = args[0]
    content = fs.read_file(filename)
    
    if content is None:
        # Если content None, значит либо файла нет, либо сработал Deadlock.
        # Если сработал Deadlock, панель уже отрисована модулем fs -> secure.
        # Поэтому проверяем существование, чтобы не спамить лишними ошибками.
        full_path = fs.get_full_path(filename)
        if not fs.exists(full_path):
            console.print(f"[bold red][ERROR][/bold red] Файл '{filename}' не найден.")
        return 
    
    # Определяем лексер по расширению
    lexer = "python" if filename.endswith(".py") else "auto"
    
    syntax = Syntax(
        content, 
        lexer, 
        theme="monokai", 
        line_numbers=True, 
        word_wrap=True
    )
    console.print(syntax)