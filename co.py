import argparse
import curses
import locale
import os
import sys
import termios
import unicodedata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The file to edit")
    args = parser.parse_args()

    if not os.path.isfile(args.filename):
        print(f"co: No such file '{args.filename}'")
        sys.exit(1)

    curses.wrapper(editor, args.filename)


def editor(stdscr, filename):
    locale.setlocale(locale.LC_ALL, "")
    try:
        fd = sys.stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        new_attrs = termios.tcgetattr(fd)
        new_attrs[0] &= ~(termios.IXON | termios.IXOFF)
        termios.tcsetattr(fd, termios.TCSANOW, new_attrs)

        curses.curs_set(1)
        curses.use_default_colors()
        stdscr.keypad(True)

        with open(filename, "r") as f:
            lines = [line.rstrip("\n") for line in f]

        y, x = 0, 0
        scroll = 0
        status = "^S Save. ^W Quit. Arrow keys to navigate."

        def char_width(char):
            width = unicodedata.east_asian_width(char)
            if width in ["W", "F"]:
                return 2
            elif width in ["N", "Na", "H"]:
                return 1
            elif width == "A":
                return 2
            return 1

        def char_widths(string):
            positions = []
            current_pos = 0
            for char in string:
                positions.append(current_pos)
                current_pos += char_width(char)
            positions.append(current_pos)
            return positions

        while True:
            positions = char_widths(lines[y])
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()
            max_y -= 1

            start_line = scroll
            end_line = scroll + max_y

            for idx, line in enumerate(lines[start_line:end_line], start=start_line):
                try:
                    stdscr.addstr(idx - scroll, 0, line[:max_x])
                except curses.error:
                    pass

            stdscr.addstr(max_y, 0, status[:max_x], curses.A_REVERSE)

            stdscr.move(y - scroll, positions[x])
            stdscr.refresh()

            c = stdscr.getch()

            if c == curses.KEY_UP:
                status = ""
                if y > 0:
                    y -= 1
                    if y < scroll:
                        scroll -= 1
                x = min(x, len(lines[y]))
            elif c == curses.KEY_DOWN:
                status = ""
                if y < len(lines) - 1:
                    y += 1
                    if y >= scroll + max_y:
                        scroll += 1
                x = min(x, len(lines[y]))
            elif c == curses.KEY_LEFT:
                status = ""
                if x > 0:
                    x -= 1
                elif y > 0:
                    y -= 1
                    x = len(lines[y])
                    if y < scroll:
                        scroll -= 1
            elif c == curses.KEY_RIGHT:
                status = ""
                if x < len(lines[y]):
                    x += 1
                elif y < len(lines) - 1:
                    y += 1
                    x = 0
                    if y >= scroll + max_y:
                        scroll += 1
            elif c in (curses.KEY_BACKSPACE, 127):
                status = ""
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
                status = ""
                if x < len(lines[y]):
                    lines[y] = lines[y][:x] + lines[y][x + 1 :]
                elif y < len(lines) - 1:
                    lines[y] += lines[y + 1]
                    del lines[y + 1]
            elif c in (curses.KEY_ENTER, 10, 13):
                status = ""
                new_line = lines[y][x:]
                lines[y] = lines[y][:x]
                lines.insert(y + 1, new_line)
                y += 1
                x = 0
                if y >= scroll + max_y:
                    scroll += 1
            elif c == 1:
                status = ""
                x = 0
            elif c == 5:
                status = ""
                x = len(lines[y])
            elif c == 11:
                status = "Deleted line."
                del lines[y]
            elif c == 19:
                status = "Saved."
                try:
                    with open(filename, "w", newline="\n") as f:
                        f.writelines(line + "\n" for line in lines)
                except Exception as e:
                    pass
            elif c == 23:
                status = "Exiting."
                break
            elif 0 <= c <= 255 and chr(c).isprintable():
                status = ""
                try:
                    lines[y] = lines[y][:x] + chr(c) + lines[y][x:]
                except:
                    lines = [chr(c)]
                x += 1
                if x >= max_x:
                    x = max_x - 1
            elif c == curses.KEY_RESIZE:
                pass
            else:
                pass

            scroll = max(0, min(scroll, len(lines) - max_y))
            x = min(x, len(lines[y]))
            if y - scroll < 0:
                scroll = y
            elif y - scroll >= max_y:
                scroll = y - max_y + 1
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_attrs)


if __name__ == "__main__":
    main()
