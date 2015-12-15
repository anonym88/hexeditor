import curses
import curses.ascii
from buffer import BufferStream, StreamToList, fork_stream
from buffer import FileBuffer


"""
The EditPad is the main editor window for the hexeditor.
It keeps track of data, scrolls, and draws it to the screen
"""
class EditPad(object):
    def __init__(self, refwin, padding, config):
        self.config = config

        ry, rx = refwin.getbegyx()
        rh, rw = refwin.getmaxyx()

        self.viewX = rx + padding
        self.viewY = ry + padding
        self.viewH = rh - 2*padding
        self.viewW = rw - 2*padding

        #TODO: fix this in a better way:
        if self.viewW < self.config.bytesPerLine*6 + 6:
            self.viewW = self.config.bytesPerLine*6 + 6

        self.xpos = 0
        self.ypos = 0
        self.numlines = 0
        self.cap = self.config.heightcapacity


        self.pad = curses.newpad(self.cap, self.viewW)
        self.pad.keypad(True)
        self.pad.scrollok(False)

        self.filedata = None

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

        stfork = BufferStream(fork_stream)

        for stin, stout, col in self.config.streams:
            stfork.addOutputStream(stin)
            stdraw = StreamToDraw(self, col)
            stout.addOutputStream(stdraw)

        self.filedata.dumpToStream(stfork,
            width=self.config.bytesPerLine)

        self.pad.move(0,0)

    def drawstr(self, linenum, column, val):
        colstart, colend = self.config.columns[column]
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


############## Edit Pad Config #################
class EditPadConfig(object):
    def __init__(self, bytesPerLine=8, heightcapacity=100):
        self.bytesPerLine = 8
        self.heightcapacity = 100
        self.columns = []
        self.streams = []

    def addcolumn(self, start, end):
        self.columns.append((start, end))

    def addstream(self, instream, outstream, column):
        self.streams.append((instream, outstream, column))

def CreateDefaultConfig():
    config = EditPadConfig()

    tw = 3*config.bytesPerLine
    config.addcolumn(0,tw)
    config.addcolumn(tw+4,2*tw+4)

    st1 = BufferStream(BytesToByteLine)
    st2 = BufferStream(BytesToNormalStr)

    config.addstream(st1, st1, 0)
    config.addstream(st2, st2, 1)

    return config




