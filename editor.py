import curses
import curses.ascii
from editpad import EditPad

from buffer import BufferStream, StreamToList


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
        self.window = unbedwin(editor.mainwin, 5, 10)
        self.window.clear()
        self.window.box()
        self.window.addstr(1,1,"File Path: ")
        self.window.refresh()

    def process(self):
        curses.echo()
        #curses.nocbreak()
        val = self.window.getstr()
        f = FileWin(val)
        editor.SetActive(f)
        return True

    def exit(self):
        self.window.clear()
        self.window.refresh()
        curses.noecho()


class FileWin(object):
    def __init__(self, filename):
        self.f = None

        self.initwins(filename)

        try:
            self.f = open(filename, "r+b")
            #self.loadfile()
            self.editpad.loadfile(self.f)
        except IOError:
            self.f = None
            self.editpad.pad.addstr("*** ERROR ***: Could not open file")
            self.editpad.pad.move(2,0)
            self.editpad.pad.addstr("Push any key to quit to the main menu")

    def process(self):
        self.editpad.refresh()
        char = self.editpad.pad.getch()

        if self.f == None: # Failed to open the file
            editor.SetActive(editor.mainmenu)
            return True

        if char == ord('q'):
            editor.SetActive(editor.mainmenu)
        if char == curses.KEY_UP:
            self.editpad.scroll(-1)
        if char == curses.KEY_DOWN:
            self.editpad.scroll(1)
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

        self.editpad = EditPad(self.boxwin, 1)

        self.fullwin.refresh()
        self.editpad.refresh()


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

def main(window):
    global editor
    editor = Editor(window)

    startwin = StartWin()
    editor.SetActive(startwin)

    editor.StartMainLoop()


if __name__ == "__main__":
    curses.wrapper(main)

