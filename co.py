import argparse
import collections
import curses
import itertools
import locale
import os
import re
import sys
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
    curses.curs_set(1)
    curses.use_default_colors()
    curses.raw()
    stdscr.keypad(True)

    with open(filename, "r") as f:
        lines = [line.rstrip("\n") for line in f]

    padding = []
    for line in lines:
        m = re.match("^\s+", line)
        if m is not None:
            g = m.group()
            print(len(g))
            if len(g) != 0:
                padding.append(len(g))
    counts = [x[0] for x in collections.Counter(padding).most_common()[:4]]
    differences = [abs(x - y) for x, y in itertools.combinations(counts, 2)]
    mod4 = sum(1 for d in differences if d % 4 == 0)
    mod2 = sum(1 for d in differences if d % 2 == 0 and d % 4 != 0)
    TAB_SPACES_LENGTH = 4 if mod4 > mod2 else 2

    y, x = 0, 0
    scroll = 0
    status = "^S Save. ^W Quit. Arrow keys to navigate."
    x_memory = 0

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
        if lines != []:
            positions = char_widths(lines[y])
        else:
            positions = [0]
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

        c = stdscr.get_wch()

        def is_whitespace() -> bool:
            m = re.match("^\s+", lines[y])
            if m is not None:
                g = m.group()
                return len(g) == x
            else:
                return False

        if isinstance(c, str):
            if c == '\b' or c == '\x7f':
                status = ""
                if is_whitespace() or (len(lines[y][:x]) <= 4 and set(lines[y][:x]) == set(" ")):
                    go_back = TAB_SPACES_LENGTH
                else:
                    go_back = 1
                try:
                    for _ in range(go_back):
                        if go_back > 1:
                            re.match("\s", lines[y][x - 1]).group()
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
                except:
                    pass
            elif c == "\n":
                status = ""
                new_line = lines[y][x:]
                lines[y] = lines[y][:x]
                lines.insert(y + 1, new_line)
                y += 1
                x = 0
                if y >= scroll + max_y:
                    scroll += 1
            elif c == "\x01":
                status = ""
                x = 0
            elif c == "\x05":
                status = ""
                x = len(lines[y])
            elif c == "\x09":
                go_forward = TAB_SPACES_LENGTH if x == 0 or is_whitespace() else 1
                for _ in range(go_forward):
                    status = ""
                    try:
                        lines[y] = lines[y][:x] + chr(32) + lines[y][x:]
                    except:
                        lines = [chr(32)]
                    x += 1
                    if x >= max_x:
                        x = max_x - 1
            elif c == "\x13":
                status = "Saved."
                try:
                    with open(filename, "w", newline="\n") as f:
                        f.writelines(line + "\n" for line in lines)
                except Exception as e:
                    pass
            elif c == "\x16":
                status = "Pasted."
            elif c == "\x17":
                status = "Exiting."
                break
            elif c == "\x0B":
                status = "Deleted line."
                del lines[y]
            else:
                status = ""
                try:
                    lines[y] = lines[y][:x] + c + lines[y][x:]
                except:
                    lines = [c]
                x += 1
                if x >= max_x:
                    x = max_x - 1
        elif isinstance(c, int):
            if c == curses.KEY_UP:
                status = ""
                if y > 0:
                    y -= 1
                    if y < scroll:
                        scroll -= 1
                x = x_memory if x_memory > x else x
                x = min(x, len(lines[y]))
            elif c == curses.KEY_DOWN:
                status = ""
                if y < len(lines) - 1:
                    y += 1
                    if y >= scroll + max_y:
                        scroll += 1
                x = x_memory if x_memory > x else x
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
                x_memory = x if x < x_memory else x_memory
            elif c == curses.KEY_RIGHT:
                status = ""
                if x < len(lines[y]):
                    x += 1
                elif y < len(lines) - 1:
                    y += 1
                    x = 0
                    if y >= scroll + max_y:
                        scroll += 1
                x_memory = x if x > x_memory else x_memory
            elif c == curses.KEY_DC:
                status = ""
                if x < len(lines[y]):
                    lines[y] = lines[y][:x] + lines[y][x + 1 :]
                elif y < len(lines) - 1:
                    lines[y] += lines[y + 1]
                    del lines[y + 1]
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


if __name__ == "__main__":
    main()
