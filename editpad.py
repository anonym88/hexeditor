import curses
import curses.ascii
from buffer import BufferStream, FileBuffer
from padmanager import PadManager
from buffermanager import BufferManager


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

        self.filewindow = (0,0)

    def refresh(self):
        self.padmanager.refresh()

    def scroll(self, val):
        self.move_vwindow(val)

    def getch(self):
        return self.padmanager.pad.getch()

    def loadfile(self, infile):
        self.filedata = FileBuffer(infile)

        self.buffers.clear()

        stfork = BufferStream(fork_stream)
        self.forkstream = stfork

        bufferstreams = self.buffers.getBuffers()
        for index, val in enumerate(self.config.streams):
            stin, stout, col  = val
            stfork.addOutputStream(stin)
            stout.addOutputStream(bufferstreams[index])

        self.move_fwindow(0)
        self.padmanager.set_line(0)

    def load_file_piece(self, start, end):
        # start, end are in bytes
        self.padmanager.clear()
        self.buffers.clear()

        self.filedata.dumpToStream(self.forkstream, start, end,
            width=self.config.bytesPerLine)

        self.buffers.computelens()
        self.buffers.draw(self.padmanager)

    def move_vwindow(self, amount):
        fstart, fend = self.filewindow

        curpos = fstart + self.padmanager.get_line()

        if fend - fstart < self.viewH:
            vstart = fstart
            vend = fend
        else:
            vstart = curpos + amount
            if vstart < 0: vstart = 0

            vend = vstart + self.viewH

            # The last line that has data
            last_line = self._lastdataline()
            hard_end = last_line + 1
            if vend > hard_end:
                vend = hard_end
                vstart = vend - self.viewH

        moved = False
        if vstart < fstart or vend > fend:
            self.move_fwindow(vstart)
            # filewindow has changed now, so reload
            fstart,fend = self.filewindow
            moved = True

        # Actually move!
        ypos = vstart - fstart
        self.padmanager.set_line(ypos)

    def move_fwindow(self, start):
        # Loads a new window of data
        # Ensures that there is a buffer of lines loaded
        #   arounded the window that will be loaded

        # start: the file line that loading will be based off

        margin = self.viewH
        file_start = start - margin
        file_end = start + self.viewH + margin

        flen = self._lastdataline()
        if file_start < 0: file_start = 0
        if file_end > flen + 1: file_end = flen + 1
        # Reasoning for + 1: file_end is a non-inclusive bound,
        #   in order for the last line to be loaded it has to
        #   be before file_end

        self.filewindow = (file_start, file_end)

        file_start_b = file_start * self.config.bytesPerLine
        file_end_b = file_end * self.config.bytesPerLine

        self.load_file_piece(file_start_b, file_end_b)

    def _lastdataline(self):
        last_byte = len(self.filedata)
        last_line = last_byte // self.config.bytesPerLine

        if last_byte % 8 == 0:
            last_line -= 1
        return last_line



####### Stream Functions ########
def fork_stream(token):
    return token

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
        #self.linenum += 1
        #val = (self.linenum-1)*self.bytesPerLine
        #return str(val)
        return "??"

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


