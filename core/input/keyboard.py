import sys

IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty

# универсальные коды
KEY_UP = "UP"
KEY_DOWN = "DOWN"
KEY_LEFT = "LEFT"
KEY_RIGHT = "RIGHT"
KEY_HOME = "HOME"
KEY_END = "END"
KEY_ENTER = "ENTER"
KEY_BACKSPACE = "BACKSPACE"

def get_key():
    if IS_WINDOWS:
        c = msvcrt.getwch()

        # стрелки и спец-коды
        if c in ('\x00', '\xe0'):
            k = msvcrt.getwch()
            return {
                'H': KEY_UP,
                'P': KEY_DOWN,
                'K': KEY_LEFT,
                'M': KEY_RIGHT,
                'G': KEY_HOME,
                'O': KEY_END,
            }.get(k)

        if c == '\r':
            return KEY_ENTER
        if c == '\x08':
            return KEY_BACKSPACE

        return c  # любой Unicode символ

    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            c = sys.stdin.read(1)

            # ESC последовательности (стрелки, Home/End)
            if c == '\x1b':
                seq = sys.stdin.read(2)
                return {
                    "[A": KEY_UP,
                    "[B": KEY_DOWN,
                    "[C": KEY_RIGHT,
                    "[D": KEY_LEFT,
                    "[H": KEY_HOME,
                    "[F": KEY_END,
                }.get(seq)

            if c == '\n':
                return KEY_ENTER
            if ord(c) == 127:
                return KEY_BACKSPACE

            # UTF-8 символы
            if ord(c) >= 0x80:
                # дочитываем дополнительные байты UTF-8
                while True:
                    try:
                        c.encode("utf-8")
                        break
                    except UnicodeEncodeError:
                        c += sys.stdin.read(1)
                return c

            return c

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
