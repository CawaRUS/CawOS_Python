import core.fs.fs as fs

about = "Вывести текст / Записать текст в файл ( > )"

def execute(args, kernel, console):
    if not args:
        return

    if ">" in args:
        pos = args.index(">")
        # Синтаксис: echo текст > файл
        if pos == 0 or pos == len(args) - 1:
            console.print("[red]Неверный синтаксис: echo <текст> > <файл>[/red]")
        else:
            text = " ".join(args[:pos])
            filename = args[pos + 1]
            if fs.write_file(filename, text):
                console.print(f"Записано в файл [cyan]'{filename}'[/cyan]")
            else:
                console.print("[red]Ошибка записи в файл[/red]")
    else:
        console.print(" ".join(args))