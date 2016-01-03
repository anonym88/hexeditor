import curses
import curses.ascii
from buffer import BufferStream, FileBuffer
from padmanager import PadManager
from buffermanager import BufferManager
from linewindow import LineWindowManager
from editconfig import bytesPerLine


"""
The EditPad is the main editor window for the hexeditor.
It keeps track of data, scrolls, and draws it to the screen
"""
class EditPad(object):
    def __init__(self, refwin, padding, config, plugins):
        self.config = config
        bytesPerLine = config.bytesPerLine

        self.padmanager = PadManager(refwin, padding, config.heightcapacity)

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

        line = byte // bytesPerLine

        self.windowmanager.move_vwindow(line)

    def getch(self):
        return self.padmanager.pad.getch()

    def loadfile(self, infile):
        self.filedata = FileBuffer(infile)

        self.buffers.clear()

        self.windowmanager = LineWindowManager(
            self._lastdataline(),
            self.load_file_piece,
            self.buffers,
            self.padmanager)

        self.windowmanager.move_fwindow(0)
        self.padmanager.set_line(0)


    def load_file_piece(self, start, end):
        # start, end are in bytes
        self.padmanager.clear()
        self.buffers.clear()

        self.filedata.dumpToStream(self.forkstream,
            self.linestream, start, end, width=bytesPerLine)

        self.buffers.computelens()
        self.buffers.draw(self.padmanager)

    def _lastdataline(self):
        last_byte = len(self.filedata)
        last_line = last_byte // bytesPerLine

        if last_byte % 8 == 0:
            last_line -= 1
        return last_line

    def _init_streams(self):
        bufferstreams = self.buffers.getBuffers()

        # Setup Main Streams
        stfork = BufferStream(fork_stream)
        stplugin = MutableBufferStream()
        self.forkstream = stfork
        self.pluginstream = stplugin

        # The first index = line stream, setup separately
        # The last index of buffers = plugin buffer, also
        #   setup separately
        for stin, stout, buff in _streamzip(
            self.config.streams[1:], bufferstreams[1:-1]):
            stfork.addOutputStream(stin)
            stout.addOutputStream(buff)

        # Setup Line Num Stream
        linein, lineout = self.config.streams[0]
        self.linestream = linein
        lineout.addOutputStream(bufferstreams[0])

        # Setup Plugin Stream
        stfork.addOutputStream(stplugin)
        stplugin.set_processor(drop_stream)
        plugin_buff = bufferstreams[-1]
        stplugin.set_stream(plugin_buff)


def _streamzip(streampairs, bufferstreams):
    assert(len(streampairs) == len(bufferstreams))
    for i in xrange(len(streampairs)):
        stin, stout = streampairs[i]
        buf = bufferstreams[i]
        yield stin, stout, buf


####### Stream Functions ########
def fork_stream(token):
    return token

def drop_stream(token):
    return ''

# The same as BufferStream, but only supports a single
#   output stream, and can change its processor
class MutableBufferStream(object):
    def __init__(self):
        self.processor = None
        self.stream = None

    def set_stream(self, stream):
        self.stream = stream

    def set_processor(self, processor):
        self.processor = processor

    def push_token(self, token):
        new_token = self.processor(token)
        if new_token is not None:
            self.stream.push_token(new_token)


