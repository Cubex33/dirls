import curses
import os
import shutil


def draw_center_box(stdscr, text_lines):
    height, width = stdscr.getmaxyx()

    box_width = max(len(line) for line in text_lines) + 4
    box_height = len(text_lines) + 2

    start_y = height // 2 - box_height // 2
    start_x = width // 2 - box_width // 2

    win = curses.newwin(box_height, box_width, start_y, start_x)
    win.border()

    for i, line in enumerate(text_lines):
        win.addstr(i + 1, 2, line)

    win.refresh()
    return win


def input_box(stdscr, prompt):
    curses.echo()
    win = draw_center_box(stdscr, [prompt, ""])
    value = win.getstr(2, 2).decode("utf-8")
    curses.noecho()
    return value


def confirm_box(stdscr, message):
    win = draw_center_box(stdscr, [message, "Y - Да    N - Нет"])

    while True:
        key = win.getch()
        if key in (ord('y'), ord('Y')):
            return True
        if key in (ord('n'), ord('N')):
            return False


def get_files(path):
    try:
        items = os.listdir(path)
        items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        return items
    except PermissionError:
        return []


def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    current_path = os.getcwd()
    selected = 0
    offset = 0

    search_mode = False
    search_buffer = ""

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        files = get_files(current_path)
        max_visible = height - 3

        if selected >= len(files):
            selected = max(0, len(files) - 1)

        if selected < offset:
            offset = selected
        elif selected >= offset + max_visible:
            offset = selected - max_visible + 1

        visible_files = files[offset:offset + max_visible]

        header = f"[SEARCH] {search_buffer}" if search_mode else f"[DIR] {current_path}"
        stdscr.addstr(0, 0, header[:width - 1], curses.A_BOLD)

        for idx, file in enumerate(visible_files):
            i = offset + idx
            full_path = os.path.join(current_path, file)
            is_dir = os.path.isdir(full_path)

            icon = "[D]" if is_dir else "[F]"
            name = f"{icon} {file}"

            try:
                size = ""
                if not is_dir:
                    size = format_size(os.path.getsize(full_path))
                line = f"{name:<50} {size}"
            except:
                line = name

            color = curses.color_pair(1 if is_dir else 2)

            if i == selected:
                stdscr.addstr(idx + 1, 0, line[:width - 1], curses.color_pair(3))
            else:
                stdscr.addstr(idx + 1, 0, line[:width - 1], color)

        help_text = (
            "UP/DOWN Навигация | ENTER Открыть | "
            "n файл | N папка | r переименовать | "
            "DEL удалить | / поиск | q выход"
        )

        stdscr.addstr(height - 2, 0, help_text[:width - 1], curses.A_REVERSE)
        stdscr.addstr(height - 1, 0, f"Элементов: {len(files)}", curses.A_DIM)

        key = stdscr.getch()

        if search_mode:
            if key in (27, 10):
                search_mode = False
                search_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                search_buffer = search_buffer[:-1]
            elif 32 <= key <= 126:
                search_buffer += chr(key)

            if search_buffer:
                for i, f in enumerate(files):
                    if search_buffer.lower() in f.lower():
                        selected = i
                        break
            continue

        if key == curses.KEY_UP and selected > 0:
            selected -= 1

        elif key == curses.KEY_DOWN and selected < len(files) - 1:
            selected += 1

        elif key == 10 and files:
            target = os.path.join(current_path, files[selected])

            if os.path.isdir(target):
                current_path = target
                selected = 0
                offset = 0
            else:
                curses.endwin()
                try:
                    os.startfile(target)
                except Exception as e:
                    print("Ошибка:", e)
                input("Enter...")
                stdscr = curses.initscr()
                curses.curs_set(0)
                stdscr.keypad(True)

        elif key == 27:
            parent = os.path.dirname(current_path)
            if parent != current_path:
                current_path = parent
                selected = 0
                offset = 0

        elif key == curses.KEY_DC and files:
            target = os.path.join(current_path, files[selected])
            if confirm_box(stdscr, f"Удалить '{files[selected]}' ?"):
                try:
                    if os.path.isfile(target):
                        os.remove(target)
                    else:
                        shutil.rmtree(target)
                except Exception as e:
                    draw_center_box(stdscr, [f"Ошибка: {e}"])
                    stdscr.getch()

        elif key == ord('n'):
            name = input_box(stdscr, "Имя файла:")
            if name:
                open(os.path.join(current_path, name), "w").close()

        elif key == ord('N'):
            name = input_box(stdscr, "Имя папки:")
            if name:
                os.makedirs(os.path.join(current_path, name), exist_ok=True)

        elif key in (ord('r'), ord('R')) and files:
            old = files[selected]
            new = input_box(stdscr, f"Переименовать '{old}':")
            if new:
                os.rename(
                    os.path.join(current_path, old),
                    os.path.join(current_path, new)
                )

        elif key == ord('/'):
            search_mode = True
            search_buffer = ""

        elif key == ord('q'):
            return current_path


if __name__ == "__main__":
    result = curses.wrapper(main)
    if result:
        print(result)