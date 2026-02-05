import sys
import shutil
import core.fs.fs as fs
from core.input.keyboard import *

about = "Системный текстовый редактор"

CTRL_S = chr(19)
CTRL_X = chr(24)

def enter_alt_screen():
    # Переход в альтернативный буфер и скрытие курсора
    sys.stdout.write("\x1b[?1049h\x1b[?25l")
    sys.stdout.flush()

def exit_alt_screen():
    # Возврат в основной буфер и показ курсора
    sys.stdout.write("\x1b[?1049l\x1b[?25h")
    sys.stdout.flush()

def clear():
    sys.stdout.write("\x1b[2J\x1b[H")

def move(y, x):
    sys.stdout.write(f"\x1b[{y};{x}H")

def clamp(v, a, b):
    return max(a, min(b, v))

def draw(lines, cx, cy, rowoff, filename, dirty):
    cols, rows = shutil.get_terminal_size()
    # Оставляем место под статус-бар
    view_height = rows - 2 

    # Вместо полной очистки через clear(), просто возвращаемся в начало 
    # и перерисовываем, это убирает мерцание
    move(1, 1)
    
    for y in range(view_height):
        i = y + rowoff
        if i < len(lines):
            # Обрезаем строку по ширине экрана, чтобы не ломать разметку
            line_content = lines[i][:cols]
            sys.stdout.write(line_content + "\x1b[K\n") # \x1b[K очищает строку до конца
        else:
            sys.stdout.write("~\x1b[K\n")

    # Рисуем статус-бар
    sys.stdout.write("\x1b[7m" + "-" * cols + "\x1b[0m\n") # Инверсия цвета для красоты
    status = f" {filename}{'*' if dirty else ''} | Ctrl+S: Save | Ctrl+X: Exit | Ln {cy+1}, Col {cx+1}"
    sys.stdout.write("\x1b[7m" + status[:cols].ljust(cols) + "\x1b[0m")
    
    # Показываем курсор в нужной позиции
    move(cy - rowoff + 1, cx + 1)
    sys.stdout.write("\x1b[?25h") # Включаем курсор перед отрисовкой позиции
    sys.stdout.flush()

def execute(args, kernel, console):
    if not args:
        console.print("[red]Укажите файл[/red]")
        return

    filename = args[0]
    text = fs.read_file(filename) or ""
    lines = text.split("\n") if text else [""]

    cx = cy = rowoff = 0
    dirty = False

    enter_alt_screen()
    try:
        while True:
            draw(lines, cx, cy, rowoff, filename, dirty)
            k = get_key()

            if k == CTRL_X:
                if dirty:
                    # Быстрое уведомление в статус-баре вместо print
                    dirty = False 
                    continue
                break

            if k == CTRL_S:
                fs.write_file(filename, "\n".join(lines))
                dirty = False
                continue

            # --- Логика перемещения и правки (оставляем твою, она идеальна) ---
            if k == KEY_UP:
                cy = clamp(cy - 1, 0, len(lines) - 1)
            elif k == KEY_DOWN:
                cy = clamp(cy + 1, 0, len(lines) - 1)
            elif k == KEY_LEFT:
                cx = clamp(cx - 1, 0, len(lines[cy]))
            elif k == KEY_RIGHT:
                cx = clamp(cx + 1, 0, len(lines[cy]))
            elif k == KEY_HOME:
                cx = 0
            elif k == KEY_END:
                cx = len(lines[cy])
            elif k == KEY_BACKSPACE:
                if cx > 0:
                    lines[cy] = lines[cy][:cx-1] + lines[cy][cx:]
                    cx -= 1
                    dirty = True
                elif cy > 0:
                    cx = len(lines[cy - 1])
                    lines[cy - 1] += lines[cy]
                    lines.pop(cy)
                    cy -= 1
                    dirty = True
            elif k == KEY_ENTER:
                lines.insert(cy + 1, lines[cy][cx:])
                lines[cy] = lines[cy][:cx]
                cy += 1
                cx = 0
                dirty = True
            elif isinstance(k, str) and k.isprintable():
                lines[cy] = lines[cy][:cx] + k + lines[cy][cx:]
                cx += 1
                dirty = True

            # Коррекция курсора и скроллинга
            cx = clamp(cx, 0, len(lines[cy]))
            _, rows = shutil.get_terminal_size()
            view_height = rows - 2
            if cy < rowoff:
                rowoff = cy
            elif cy >= rowoff + view_height:
                rowoff = cy - view_height + 1
    finally:
        exit_alt_screen()