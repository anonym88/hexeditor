import curses
import curses.ascii
from buffer import BufferStream, StreamToList, fork_stream
from buffer import FileBuffer, ColumnBuffer
from itertools import izip_longest, imap


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

        self.xpos = 0
        self.ypos = 0
        self.numlines = 0
        self.cap = self.config.heightcapacity


        self.pad = curses.newpad(self.cap, self.viewW)
        self.pad.keypad(True)
        self.pad.scrollok(False)

        self.buffers = [ ColumnBuffer() for
            i in xrange(len(self.config)) ]


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

        for index, val in enumerate(self.config.streams):
            stin, stout, col  = val
            stfork.addOutputStream(stin)
            stdraw = self.buffers[index] #StreamToDraw(self, col)
            stout.addOutputStream(stdraw)

        self.filedata.dumpToStream(stfork,
            width=self.config.bytesPerLine)

        self.recomputecols()

        self.redrawbuffers()

        self.pad.move(0,0)

    def _drawstr(self, linenum, column, val):
        colstart, colend = self.config.columns[column]
        colsize = colend - colstart
        if len(val) > colsize:
            raise IndexError("string given is too large for the specified column\n\tSize available: %s, Received: %s" % (colsize,len(val)))

        self._setlines(linenum)
        self.pad.addstr(linenum, colstart, val)

    # Draw the contents of these buffers to the pad
    def redrawbuffers(self):
        #zipiter is an iterator for side-by-side lines
        zipiter = izip_longest(*self.buffers)
        curline = 0
        for alllines in zipiter:
            #alllines is a tuple of each buffer's line
            maxlen = max(map(len, alllines))
            for col, lines in enumerate(alllines):
                for lineoffset, line in enumerate(lines):
                    self._drawstr(curline+lineoffset, col, line)
            curline += maxlen

    # Computes the width of each column, and then sets up the columns
    def recomputecols(self):
        lens = []
        for buff in self.buffers:
            # flatten the list of lists of lines
            lines = _flatten(buff)
            maxlen = max(imap(len, lines))
            lens.append(maxlen)
        self.config.columnlens = lens
        self.config.computecolumns()


class BufferManager(object):
    def __init__(self, numcolumns):
        self.buffers = [ ColumnBuffer() for i in xrange(numcolumns) ]
        self.lens = [ 0 for i in xrange(numcolumns) ]
        self.reallines = []

    # Hookup the streams to the correct buffers
    def init_streams(self, streams):
        for index, stream in enumerate(streams):
            stream.addOutputStream(self.buffers[index])

    def clear(self):
        for buff in self.buffers:
            buff.clear()

    def lineToScreen(self):
        pass

    def screenToLine(self):
        pass

    def getBuffers(self):
        return self.buffers

    def _computemaxlen(self, index):
        buff = self.buffers[index]
        lines = _flatten(buff)
        maxlen = max(imap(len, lines))
        self.lens[index] = maxlen

    def computelens(self):
        for i in xrange(len(self.buffers)):
            self._computemaxlen(i)

    def draw(self, editpad):
        zipiter = izip_longest(*self.buffers)
        curline = 0
        for alllines in zipiter:
            #alllines is a tuple of each buffer's line
            maxlen = max(imap(len, alllines))
            for col, lines in enumerate(alllines):
                for lineoffset, line in enumerate(lines):
                    editpad._drawstr(curline+lineoffset, col, line)
            curline += maxlen




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

class BytesToLineNum(object):
    def __init__(self, bytesPerLine):
        self.bytesPerLine = bytesPerLine
        self.linenum = 0

    def __call__(self, token):
        self.linenum += 1
        val = (self.linenum-1)*self.bytesPerLine
        return str(val)

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


############## Edit Pad Config #################
class EditPadConfig(object):
    def __init__(self, bytesPerLine=8, heightcapacity=100):
        self.bytesPerLine = 8
        self.heightcapacity = 100
        self.columns = []
        self.columngaps = []
        self.columnlens = []
        self.streams = []

    def addcolumn(self, gap):
        self.columngaps.append(gap)

    def addstream(self, instream, outstream, column):
        self.streams.append((instream, outstream, column))

    def computecolumns(self):
        assert(len(self.columnlens) == len(self.columngaps))
        offset = 0
        for l,g in zip(self.columnlens, self.columngaps):
            val = (offset, offset+l)
            self.columns.append(val)
            offset += l + g

    def __len__(self):
        return len(self.columngaps)

def CreateDefaultConfig():
    config = EditPadConfig()

    config.addcolumn(2)
    config.addcolumn(4)
    config.addcolumn(4)

    st1 = BufferStream(BytesToLineNum(config.bytesPerLine))
    st2 = BufferStream(BytesToByteLine)
    st3 = BufferStream(BytesToNormalStr)

    config.addstream(st1, st1, 0)
    config.addstream(st2, st2, 1)
    config.addstream(st3, st3, 2)

    return config

# takes iter<iter<thing>> and flattens to iter<thing>
def _flatten(iterable):
    for inner in iterable:
        for val in inner:
            yield val



