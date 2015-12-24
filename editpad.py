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

        self.buffers = BufferManager(self.config.columngaps)

        self.filewindow = (0,0)


    def refresh(self):
        self.pad.refresh(self.ypos, self.xpos, self.viewY, self.viewX, 
            self.viewY + self.viewH - 1, self.viewX + self.viewW - 1)

    def scroll(self, val):
        self.move_vwindow(val)

    def _setlines(self, linenum):
        if linenum <= self.numlines:
            return
        self.numlines = linenum
        if linenum >= self.cap:
            self.cap = linenum*2
            self.pad.resize(self.cap, self.viewW)

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

        self.do_move_window_pos(0)

    def drawstr(self, ypos, xpos, val):
        self._setlines(ypos)
        self.pad.addstr(ypos, xpos, val)

    def load_file_piece(self, start, end):
        # All in file-space
        self.numlines = 0
        self.pad.clear()
        self.buffers.clear()
        self.filedata.dumpToStream(self.forkstream, start, end,
            width=self.config.bytesPerLine)

        try:
            self.buffers.computelens()
        except ValueError:
            msg = "Data:\nfilewindow: %s\nload pos: %s\nypos: %s, numlines: %s"
            fullmsg= msg % (str(self.filewindow), str((start, end)), str(self.ypos), str(self.numlines))
            raise Exception(fullmsg)
        self.buffers.draw(self)

    def move_vwindow(self, amount):
        fstart, fend = self.filewindow

        curpos = fstart + self.ypos

        if fend - fstart < self.viewH:
            vstart = fstart
            vend = fend
        else:
            vstart = curpos + amount
            if vstart < 0: vstart = 0

            vend = vstart + self.viewH

            # The last line that has data
            last_line = len(self.filedata) // self.config.bytesPerLine
            hard_end = last_line + 1
            if vend > hard_end:
                vend = hard_end
                vstart = vend - self.viewH

        moved = False
        if vstart < fstart or vend > fend:
            self.do_move_window_pos(vstart)
            # filewindow has changed now, so reload
            fstart,fend = self.filewindow
            moved = True

        # Actually move!
        self.ypos = vstart - fstart

        self.pad.addstr(self.ypos, 60, str((vstart, vend)))
        self.pad.addstr(self.ypos, 75, str((fstart, fend)))
        self.pad.addstr(self.ypos, 85, str(self.ypos))
        self.pad.addstr(self.ypos, 95, str(len(self.filedata)))
        self.pad.addstr(self.ypos, 105, str(last_line))
        self.pad.addstr(self.ypos, 112, str(moved))

        return
        # In file-space
        fstart_f, fend_f = self.filewindow
        # Convert to pad-space # TODO: needs multiline adjust
        fstart = fstart_f // self.config.bytesPerLine
        fend = ((fend_f - 1) // self.config.bytesPerLine) + 1
        # In pad-space

        py = self.ypos + amount + fstart
        vend = py + self.viewH

        vend_f = vend * self.config.bytesPerLine # TODO: Needs multiline adjust
        if vend_f > len(self.filedata):
            vend = len(self.filedata) // self.config.bytesPerLine
        vstart = vend - self.viewH

        if vstart < 0:
            vstart = 0
            vend = vstart + self.viewH

        if vstart < fstart or vend >= fend:
            vstart_f = vstart * self.config.bytesPerLine
            self.do_move_window_pos(vstart_f)
        else:
            self.ypos = vstart - fstart

        self.pad.addstr(self.ypos, 60, str((vstart, vend)))
        self.pad.addstr(self.ypos, 75, str((fstart, fend)))
        self.pad.addstr(self.ypos, 90, str(self.ypos))
        self.pad.addstr(self.ypos, 100, str(len(self.filedata)))


    def do_move_window_pos(self, start):
        # Loads a new window of data
        # Ensures that there is a buffer of lines loaded
        #   arounded the window that will be loaded

        # start: the file line that loading will be based off

        margin = self.viewH
        file_start = start - margin
        file_end = start + self.viewH + margin

        flen = len(self.filedata) // self.config.bytesPerLine
        if file_start < 0: file_start = 0
        if file_end > flen + 1: file_end = flen + 1
        # Reasoning for + 1: file_end is a non-inclusive bound,
        #   in order for the last line to be loaded it has to
        #   be before file_end

        self.filewindow = (file_start, file_end)

        file_start_b = file_start * self.config.bytesPerLine
        file_end_b = file_end * self.config.bytesPerLine

        self.load_file_piece(file_start_b, file_end_b)

        return

        windowsize = self.viewH * self.config.bytesPerLine
        file_start = start - windowsize
        file_end = start + 2*windowsize

        flen = len(self.filedata)
        if file_start < 0: file_start = 0
        if file_end > flen: file_end = flen

        self.filewindow = (file_start, file_end)

        # since the file needs to be reloaded, the pad is
        #   redrawn and we need to move ypos
        self.ypos = (start - file_start) // self.config.bytesPerLine
        # TODO: above line completely breaks when multiline
        #   data is in buffers

        self.load_file_piece(file_start, file_end)


class BufferManager(object):
    def __init__(self, columngaps):
        numcolumns = len(columngaps)
        self.columngaps = columngaps
        self.buffers = [ ColumnBuffer() for i in xrange(numcolumns) ]
        self.lens = [ 0 for i in xrange(numcolumns) ]

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

        self.columns = []
        val = 0
        for i in xrange(len(self.buffers)):
            self.columns.append(val)
            val += self.lens[i] + self.columngaps[i]

    def draw(self, editpad):
        zipiter = izip_longest(*self.buffers)
        curline = 0
        for alllines in zipiter:
            #alllines is a tuple of each buffer's line
            maxlen = max(imap(len, alllines))
            for col, lines in enumerate(alllines):
                for lineoffset, line in enumerate(lines):
                    yval = curline + lineoffset
                    xval = self.columns[col]
                    editpad.drawstr(yval, xval, line)
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

# takes iter<iter<thing>> and flattens to iter<thing>
def _flatten(iterable):
    for inner in iterable:
        for val in inner:
            yield val



