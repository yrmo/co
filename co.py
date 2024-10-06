import curses
import sys


def main(stdscr, filename):
    curses.curs_set(1)
    curses.use_default_colors()
    stdscr.keypad(True)
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = [""]
    y, x = 0, 0
    scroll = 0
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        max_y -= 1
        start_line = scroll
        end_line = scroll + max_y
        for idx, line in enumerate(lines[start_line:end_line], start=start_line):
            try:
                stdscr.addstr(idx - scroll, 0, line.rstrip("\n")[:max_x])
            except curses.error:
                pass
        stdscr.move(y - scroll, x)
        c = stdscr.getch()
        if c == curses.KEY_UP:
            if y > 0:
                y -= 1
                if y < scroll:
                    scroll -= 1
            x = min(x, len(lines[y]))
        elif c == curses.KEY_DOWN:
            if y < len(lines) - 1:
                y += 1
                if y >= scroll + max_y:
                    scroll += 1
            x = min(x, len(lines[y]))
        elif c == curses.KEY_LEFT:
            if x > 0:
                x -= 1
            elif y > 0:
                y -= 1
                x = len(lines[y])
                if y < scroll:
                    scroll -= 1
        elif c == curses.KEY_RIGHT:
            if x < len(lines[y]):
                x += 1
            elif y < len(lines) - 1:
                y += 1
                x = 0
                if y >= scroll + max_y:
                    scroll += 1
        elif c in (curses.KEY_BACKSPACE, 127):
            if x > 0:
                lines[y] = lines[y][: x - 1] + lines[y][x:]
                x -= 1
            elif y > 0:
                x = len(lines[y - 1])
                lines[y - 1] += lines[y]
                del lines[y]
                y -= 1
                if y < scroll:
                    scroll = max(0, scroll - 1)
        elif c == curses.KEY_DC:
            if x < len(lines[y]):
                lines[y] = lines[y][:x] + lines[y][x + 1 :]
            elif y < len(lines) - 1:
                lines[y] += lines[y + 1]
                del lines[y + 1]
        elif c in (curses.KEY_ENTER, 10, 13):
            new_line = lines[y][x:]
            lines[y] = lines[y][:x]
            lines.insert(y + 1, new_line)
            y += 1
            x = 0
            if y >= scroll + max_y:
                scroll += 1
        elif c == 24:
            with open(filename, "w") as f:
                f.writelines("".join(lines))
            break
        elif 0 <= c <= 255 and chr(c).isprintable():
            lines[y] = lines[y][:x] + chr(c) + lines[y][x:]
            x += 1
            if x >= max_x:
                x = max_x - 1
        elif c == curses.KEY_RESIZE:
            pass
        scroll = max(0, min(scroll, len(lines) - max_y))
        x = min(x, len(lines[y]))
        if y - scroll < 0:
            scroll = y
        elif y - scroll >= max_y:
            scroll = y - max_y + 1


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "untitled.txt"
    curses.wrapper(main, filename)
