import curses
import curses.ascii
from editpad import EditPad
from editconfig import EditPadConfig, CreateDefaultConfig
from textbox import Textbox, popup


class Editor(object):
    def __init__(self, window):
        self.mainwin = window
        self.active = None

    def StartMainLoop(self):
        self.mainmenu = StartWin()
        self.SetActive(self.mainmenu)
        self.MainLoop()

    def MainLoop(self):
        while True:
            cont = self.active.process()
            if not cont:
                break

    def SetActive(self, win):
        if self.active != None and hasattr(self.active, "exit"):
            self.active.exit()

        self.active = win

        if hasattr(win, "enter"):
            win.enter()


class StartWin(object):
    def __init__(self):
        self.window = unbedwin(editor.mainwin, 5, 10)

    def enter(self):
        self.window.box()
        self.window.addstr(1,1,"Welcome! Choose an action:")
        self.window.addstr(2,4,"q - quit")
        self.window.addstr(3,4,"o - open file")
        self.window.addstr(4,4,"n - new file")
        self.window.refresh()

    def exit(self):
        self.window.clear()

    def process(self):
        char = self.window.getch()
        if char == ord('q'):
            return False
        if char == ord('o'):
            selectfile = SelectFileWin()
            editor.SetActive(selectfile)
        return True


class SelectFileWin(object):
    def __init__(self):
        window = unbedwin(editor.mainwin, 5, 10)
        self.textbox = Textbox(window, "File Path: ")

    def process(self):
        val = self.textbox.gettext()
        f = FileWin(val)
        editor.SetActive(f)
        return True

    def exit(self):
        self.textbox.clear()


class FileWin(object):
    def __init__(self, filename):
        self.f = None

        self.initwins(filename)

        try:
            self.f = open(filename, "r+b")
            self.editpad.loadfile(self.f)
        except IOError:
            self.f = None
            popup(self.textwin, ["*** ERROR ***: Could not open file", "Push any key to quit to the main menu"])

    def process(self):
        if self.f == None: # Failed to open the file
            editor.SetActive(editor.mainmenu)
            return True

        self.editpad.refresh()
        char = self.editpad.getch()


        if char == ord('q'):
            editor.SetActive(editor.mainmenu)
        elif char == curses.KEY_UP:
            self.editpad.scroll(-1)
        elif char == curses.KEY_DOWN:
            self.editpad.scroll(1)
        elif char == ord('g'):
            t = Textbox(self.textwin, "Goto Line: ")
            val = t.gettext()
            self.editpad.goto(val)
        elif char >= ord('0') and char <= ord('9'):
            val = char - ord('0')
            self.editpad.activate_plugin(val)
        elif char == ord('`'):
            self.editpad.activate_plugin(-1)
        elif char == ord('\n'):
            self.editpad.set_preview()
        elif char == ord('x'):
            self.editpad.unset_preview()
        return True

    def exit(self):
        if self.f != None:
            self.f.close()
        self.fullwin.clear()
        self.fullwin.refresh()

    def initwins(self, filename):
        self.fullwin = unbedwin(editor.mainwin, 2, 5)
        self.fullwin.clear()
        self.fullwin.addstr(0,0, filename)

        self.boxwin = embedwin(self.fullwin, 1, 0)
        self.boxwin.box()

        config = CreateDefaultConfig()
        self.editpad = EditPad(self.boxwin, 1, config, _plugins)

        self.fullwin.refresh()
        self.editpad.refresh()

        self.textwin = unbedwin(editor.mainwin, 7, 12)


def embedwin(window, vgap, hgap, vgap2=None, hgap2=None):
    height, width = window.getmaxyx()
    if hgap2 == None:
        hgap2 = hgap
    if vgap2 == None:
        vgap2 = vgap

    return window.derwin(height-(vgap+vgap2), width-(hgap+hgap2), vgap, hgap)

def unbedwin(window, vgap, hgap, vgap2=None, hgap2=None):
    height, width = window.getmaxyx()
    y,x = window.getbegyx()
    if hgap2 == None:
        hgap2 = hgap
    if vgap2 == None:
        vgap2 = vgap

    return curses.newwin(height-(vgap+vgap2), width-(hgap+hgap2), x+vgap, y+hgap)

editor = None
_plugins = None

def main(window):
    global editor
    editor = Editor(window)
    editor.StartMainLoop()

def launch(plugins):
    if plugins == None:
        raise TypeError("plugins cannot be None. Use an empty list if no plugins are desired.")

    global _plugins
    _plugins = plugins

    curses.wrapper(main)

def temp(token):
    return 'hi'

def temp2(token):
    return ["Yo - ", "  bleh"]

if __name__ == "__main__":
    launch([ temp, temp2 ])

