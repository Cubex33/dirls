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
    win.addstr(2, 2, "")
    win.refresh()
    input_str = win.getstr(2, 2).decode("utf-8")
    curses.noecho()
    return input_str

def confirm_box(stdscr, message):
    win = draw_center_box(stdscr, [message, "Y - Да    N - Нет"])
    while True:
        key = win.getch()
        if key in (ord('y'), ord('Y')):
            return True
        if key in (ord('n'), ord('N')):
            return False

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)

    current_path = os.getcwd()
    selected = 0
    offset = 0

    search_mode = False
    search_buffer = ""

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        try:
            files = sorted(os.listdir(current_path))
        except PermissionError:
            files = []

        max_visible = height - 2

        # Скролл
        if selected < offset:
            offset = selected
        elif selected >= offset + max_visible:
            offset = selected - max_visible + 1

        visible_files = files[offset:offset + max_visible]

        # Верхняя строка
        if search_mode:
            stdscr.addstr(0, 0, f"Поиск: {search_buffer}"[:width-1], curses.A_BOLD)
        else:
            stdscr.addstr(0, 0, f"Папка: {current_path}"[:width-1], curses.A_BOLD)

        # Список файлов
        for idx, file in enumerate(visible_files):
            i = offset + idx
            display_name = file[:width-1]
            if os.path.isdir(os.path.join(current_path, file)):
                display_name += "/"
            if i == selected:
                stdscr.addstr(idx + 1, 0, display_name, curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 1, 0, display_name)

        # Нижняя панель
        help_text = "↑↓ Навигация | Enter Открыть | N Новый | R Переим. | Del Удалить | Esc Назад | Q Выход | / Поиск"
        stdscr.addstr(height-1, 0, help_text[:width-1], curses.A_REVERSE)

        key = stdscr.getch()

        # --- Поиск ---
        if search_mode:
            if key in (27, 10):  # Esc или Enter завершают поиск
                search_mode = False
                search_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                search_buffer = search_buffer[:-1]
            elif 32 <= key <= 126:
                search_buffer += chr(key)
            # ищем первое совпадение
            if search_buffer:
                for i, f in enumerate(files):
                    if search_buffer.lower() in f.lower():
                        selected = i
                        if selected < offset:
                            offset = selected
                        elif selected >= offset + max_visible:
                            offset = selected - max_visible + 1
                        break
            continue

        # --- Основные действия ---
        if key == ord('/') and not search_mode:
            search_mode = True
            search_buffer = ""
        elif key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(files) - 1:
            selected += 1
        elif key == 10 and files:  # Enter
            new_path = os.path.join(current_path, files[selected])
            if os.path.isdir(new_path):
                current_path = new_path
                selected = 0
                offset = 0
            else:
                curses.endwin()
                try:
                    os.startfile(new_path)
                except Exception as e:
                    print(f"Не удалось открыть файл: {e}")
                input("Нажмите Enter, чтобы вернуться в менеджер...")
                stdscr = curses.initscr()
                curses.curs_set(0)
                stdscr.keypad(True)
        elif key == 27:  # Esc
            parent = os.path.dirname(current_path)
            if parent and parent != current_path:
                current_path = parent
                selected = 0
                offset = 0
        elif key == curses.KEY_DC and files:  # Delete
            target = os.path.join(current_path, files[selected])
            confirm = confirm_box(stdscr, f"Удалить '{files[selected]}' ?")
            if confirm:
                if os.path.isfile(target):
                    os.remove(target)
                elif os.path.isdir(target):
                    shutil.rmtree(target)
                selected = 0
                offset = 0
        elif key in (ord('n'), ord('N')):
            name = input_box(stdscr, "Имя нового файла:")
            if name:
                open(os.path.join(current_path, name), "w").close()
        elif key in (ord('r'), ord('R')) and files:
            old_name = files[selected]
            new_name = input_box(stdscr, f"Переименовать '{old_name}' в:")
            if new_name:
                os.rename(
                    os.path.join(current_path, old_name),
                    os.path.join(current_path, new_name)
                )
        elif key in (ord('q'), ord('Q')):
            break

    # Выводим текущую директорию при выходе
    print(current_path)

curses.wrapper(main)