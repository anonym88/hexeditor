import curses
import curses.ascii
import curses.textpad

	

def process(val, screen):
    #if not curses.ascii.isctrl(val):
    #    s = curses.ascii.unctrl(val)
    #    screen.addstr(s)
    #if not curses.ascii.isctrl(val):
    screen.addch(val)

def validate(char):
    # Translate backspace into what it wants to see:
    if char == curses.ascii.DEL:
        return curses.KEY_BACKSPACE
    if char == curses.KEY_DC:
        return curses.ascii.EOT
    if char == curses.KEY_HOME:
        return ord('?')
    if char == curses.KEY_END:
        return ord('!')
    if char == curses.KEY_DOWN:
        return ord('*')
    if char == curses.KEY_UP:
        return ord('%')
    return char

def do_thing(char, screen):
    print curses.unctrl(char)

@curses.wrapper
def start(screen):
    #do_thing(curses.ascii.DEL, screen)
    #do_thing(curses.ascii.BS, screen)

    #screen.getch()
    #return

    textbox = curses.textpad.Textbox(screen)
    textbox.stripspaces = True
    contents = textbox.edit(validate)
    #while True:
    #    val = screen.getch()
    #    if val == ord('q'):
    #        break
    #    else:
    #        process(val, screen)


