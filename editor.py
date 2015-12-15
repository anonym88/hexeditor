import curses
import curses.ascii

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

    def loadfile(self):
        ch = self.f.read(1)
        while ch != "":
            self.editpad.addch(ch)
            ch = self.f.read(1)
        self.editpad.pad.move(0,0)



class EditPad(object):
    def __init__(self, refwin, padding, capacity=None):
        ry, rx = refwin.getbegyx()
        rh, rw = refwin.getmaxyx()

        self.viewX = rx + padding
        self.viewY = ry + padding
        self.viewH = rh - 2*padding
        self.viewW = rw - 2*padding

        self.bytesPerLine = 8

        #TODO: fix this in a better way:
        if self.viewW < self.bytesPerLine*6 + 6:
            self.viewW = self.bytesPerLine*6 + 6

        self.xpos = 0
        self.ypos = 0
        self.numlines = 0
        self.cap = 100 if capacity == None else capacity


        self.pad = curses.newpad(self.cap, self.viewW)
        self.pad.keypad(True)
        self.pad.scrollok(False)


    def refresh(self):
        self.pad.refresh(self.ypos, self.xpos, self.viewY, self.viewX, 
            self.viewY + self.viewH - 1, self.viewX + self.viewW - 1)

    def scroll(self, val):
        self.ypos += val
        if self.ypos < 0:
            self.ypos = 0
        if self.ypos > self.numlines:
            self.ypos = self.numlines

    def _addline(self):
        self.numlines += 1
        if self.numlines == self.cap:
            self.cap *= 2
            self.pad.resize(self.cap, self.viewW)

    def addch(self, ch):
        val = ord(ch)
        s = intToHexStr(val)

        self._add_real_ch(ch)
        self.pad.addstr(s+" ")

        y,x = self.pad.getyx()
        if x >= 3*self.bytesPerLine:
            self._addline()
            self.pad.move(y+1, 0)

    def _add_real_ch(self, ch):
        y,x = self.pad.getyx()
        #xstart = self.viewW - 3*self.bytesPerLine - 1
        xstart = 3*self.bytesPerLine + 5
        xpos = xstart + x

        char = curses.unctrl(ch)
        assert(len(char) <= 3)
        while len(char) < 3:
            char += " "
        self.pad.addstr(y, xpos, char)
        self.pad.move(y,x)

    def loadfile(self, infile):
        # Setup streams
        st1 = BufferStream(TokenToBytes)
        st2 = BufferStream(BytesToByteLine)
        st3 = BufferStream(BytesToNormalStr)

        data = StreamToList()
        draw1 = StreamToDraw(self, 0)
        draw2 = StreamToDraw(self, self.bytesPerLine*3 + 4)

        st1.addOutputStream(st2)
        st1.addOutputStream(st3)
        st1.addOutputStream(data)

        st2.addOutputStream(draw1)
        st3.addOutputStream(draw2)

        val = infile.read(self.bytesPerLine)
        while val != '':
            st1.push_token(val)
            val = infile.read(self.bytesPerLine)

        self.bytedata = data.data
        self.pad.move(0,0)



def TokenToBytes(token):
    return bytes(token)

def BytesToByteLine(token):
    byteList = memoryview(token).tolist()
    byteStrs = map(intToHexStr, byteList)
    return ' '.join(byteStrs)

def BytesToNormalStr(token):
    byteList = memoryview(token).tolist()
    byteStrs = map(curses.unctrl, byteList)
    padded = map(_padTo3, byteStrs)
    return ''.join(padded)

# Helper for BytesToNormalStr
def _padTo3(word):
    while len(word) < 3:
        word += ' '
    return word
    #for s in vals:
    #    while len(s) < 3:
    #        s += ' '
    #    yield s

def intToHexStr(val):
    if val > 255 or val < 0:
        return "XX"

    first = val // 16 # int division
    second = val % 16
    return _itostr(first) + _itostr(second)

def _itostr(val):
    assert(val >= 0 and val <= 15)

    if val <= 9:
        return str(val)
    val -= 10
    val += ord('A')
    return chr(val)

class StreamToDraw(object):
    def __init__(self, editpad, xpos):
        self.editpad = editpad
        self.xpos = xpos
        self.linenum = 0

    def push_token(self, token):
        if self.linenum > self.editpad.numlines:
            self.editpad._addline()
        self.editpad.pad.move(self.linenum, self.xpos)
        self.editpad.pad.addstr(token)
        self.linenum += 1

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

