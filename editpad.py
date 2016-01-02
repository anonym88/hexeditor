import curses
import curses.ascii
from buffer import BufferStream, FileBuffer
from padmanager import PadManager
from buffermanager import BufferManager
from linewindow import LineWindowManager


"""
The EditPad is the main editor window for the hexeditor.
It keeps track of data, scrolls, and draws it to the screen
"""
class EditPad(object):
    def __init__(self, refwin, padding, config):
        self.config = config

        self.padmanager = PadManager(refwin, padding, config.heightcapacity)

        # This is here to be in a more global position
        self.viewH = self.padmanager.viewH

        self.buffers = BufferManager(self.config.columngaps)

        self._init_streams()

        self.windowmanager = None

    def refresh(self):
        self.padmanager.refresh()

    def scroll(self, val):
        if val == 1:
            self.windowmanager.incr_vwindow()
        elif val == -1:
            self.windowmanager.decr_vwindow()

    def goto(self, val):
        try:
            byte = int(val, 16)
        except:
            return

        line = byte // self.config.bytesPerLine

        self.windowmanager.move_vwindow(line)

    def getch(self):
        return self.padmanager.pad.getch()

    def loadfile(self, infile):
        self.filedata = FileBuffer(infile)

        self.buffers.clear()

        self.windowmanager = LineWindowManager(
            self._lastdataline(),
            self.load_file_piece,
            self.config.bytesPerLine,
            self.buffers,
            self.padmanager.set_line,
            self.viewH)

        self.windowmanager.move_fwindow(0)
        self.padmanager.set_line(0)


    def load_file_piece(self, start, end):
        # start, end are in bytes
        self.padmanager.clear()
        self.buffers.clear()

        self.filedata.dumpToStream(self.forkstream, self.linestream, start, end,
            width=self.config.bytesPerLine)

        self.buffers.computelens()
        self.buffers.draw(self.padmanager)

    def _lastdataline(self):
        last_byte = len(self.filedata)
        last_line = last_byte // self.config.bytesPerLine

        if last_byte % 8 == 0:
            last_line -= 1
        return last_line

    def _init_streams(self):
        bufferstreams = self.buffers.getBuffers()

        # Setup Main Streams
        stfork = BufferStream(fork_stream)
        self.forkstream = stfork

        for stin, stout, buff in _streamzip(
            self.config.streams[1:], bufferstreams[1:]):
            stfork.addOutputStream(stin)
            stout.addOutputStream(buff)

        # Setup Line Num Stream
        linein, lineout, _ = self.config.streams[0]
        self.linestream = linein
        lineout.addOutputStream(bufferstreams[0])


def _streamzip(streampairs, bufferstreams):
    assert(len(streampairs) == len(bufferstreams))
    for i in xrange(len(streampairs)):
        stin, stout, _ = streampairs[i]
        buf = bufferstreams[i]
        yield stin, stout, buf


####### Stream Functions ########
def fork_stream(token):
    return token

def BytesToByteLine(token):
    byteList = memoryview(token).tolist()
    byteStrs = map(bytesToHex, byteList)
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

def IndexToLineNum(val):
    return '0x' + intToHexStr(val)

def bytesToHex(val):
    if val > 255 or val < 0:
        return "XX"

    first = val // 16 # int division
    second = val % 16
    return _itostr(first) + _itostr(second)

def intToHexStr(val):
    s = ''

    rem = val % 16
    s = _itostr(rem) + s
    val = val // 16

    while val > 0:
        rem = val % 16
        s = _itostr(rem) + s
        val = val // 16

    return s

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

    config.addcolumn(3)
    config.addcolumn(4)
    config.addcolumn(4)

    st1 = BufferStream(IndexToLineNum)
    st2 = BufferStream(BytesToByteLine)
    st3 = BufferStream(BytesToNormalStr)

    config.addstream(st1, st1, 0)
    config.addstream(st2, st2, 1)
    config.addstream(st3, st3, 2)

    return config


