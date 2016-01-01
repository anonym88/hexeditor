import curses

class Textbox(object):
    def __init__(self, window, message):
        self.window = window
        self.window.clear()
        self.window.box()
        self.window.addstr(1,1,message)
        self.window.refresh()

    def gettext(self):
        curses.echo()
        val = self.window.getstr()
        curses.noecho()
        return val

    def clear(self):
        self.window.clear()
        self.window.refresh()

def popup(window, message):
    if isinstance(message, str):
        message = [ message ]
    window.clear()
    window.box()
    for index, val in enumerate(message):
        ypos = index + 1
        window.addstr(ypos,1,val)
    window.getch()
    window.clear()
