import curses
import curses.ascii
from buffer import BufferStream, StreamToList, fork_stream
from buffer import FileBuffer


"""
The EditPad is the main editor window for the hexeditor.
It keeps track of data, scrolls, and draws it to the screen
"""
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

        self.filedata = None

        self._setupCols()


    def _setupCols(self):
        tw = 3*self.bytesPerLine
        self.columns = [ (0, tw), (tw+4, 2*tw+4)]

    def refresh(self):
        self.pad.refresh(self.ypos, self.xpos, self.viewY, self.viewX, 
            self.viewY + self.viewH - 1, self.viewX + self.viewW - 1)

    def scroll(self, val):
        self.ypos += val
        if self.ypos < 0:
            self.ypos = 0
        if self.ypos > self.numlines:
            self.ypos = self.numlines

    def _setlines(self, linenum):
        if linenum <= self.numlines:
            return
        self.numlines = linenum
        if linenum >= self.cap:
            self.cap = linenum*2
            self.pad.resize(self.cap, self.viewW)

    def loadfile(self, infile):
        self.filedata = FileBuffer(infile)

        # Setup streams
        st1 = BufferStream(fork_stream)
        st2 = BufferStream(BytesToByteLine)
        st3 = BufferStream(BytesToNormalStr)

        draw1 = StreamToDraw(self, 0)
        draw2 = StreamToDraw(self, 1)

        # Connect them
        st1.addOutputStream(st2)
        st1.addOutputStream(st3)

        st2.addOutputStream(draw1)
        st3.addOutputStream(draw2)

        # Write data
        self.filedata.dumpToStream(st1, width=self.bytesPerLine)

        self.pad.move(0,0)

    def drawstr(self, linenum, column, val):
        colstart, colend = self.columns[column]
        colsize = colend - colstart
        if len(val) > colsize:
            raise IndexError("string given is too large for the specified column\n\tSize available: %s, Received: %s" % (colsize,len(val)))

        self._setlines(linenum)
        self.pad.addstr(linenum, colstart, val)


####### Stream Functions ########

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

def intToHexStr(val):
    if val > 255 or val < 0:
        return "XX"

    first = val // 16 # int division
    second = val % 16
    return _itostr(first) + _itostr(second)

# Helper for intToHexStr
def _itostr(val):
    assert(val >= 0 and val <= 15)

    if val <= 9:
        return str(val)
    val -= 10
    val += ord('A')
    return chr(val)

class StreamToDraw(object):
    def __init__(self, editpad, column):
        self.editpad = editpad
        self.column = column
        self.linenum = 0

    def push_token(self, token):
        self.editpad.drawstr(self.linenum, self.column, token)
        self.linenum += 1


