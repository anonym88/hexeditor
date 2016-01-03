import curses
import curses.ascii
from buffer import BufferStream, MutableBufferStream, FileBuffer
from padmanager import PadManager
from buffermanager import BufferManager
from linewindow import LineWindowManager
import editconfig


"""
The EditPad is the main editor window for the hexeditor.
It keeps track of data, scrolls, and draws it to the screen
"""
class EditPad(object):
    def __init__(self, refwin, padding, config, plugins):
        self.config = config
        self.plugins = plugins
        editconfig.bytesPerLine = config.bytesPerLine

        self.padmanager = PadManager(refwin, padding, config.heightcapacity)

        self.buffers = BufferManager(self.config.columngaps)

        self._init_streams()

        self.windowmanager = None

    def refresh(self):
        self.padmanager.refresh()

    def scroll(self, val):
        if val == 1:
            self.windowmanager.incr_cursor()
        elif val == -1:
            self.windowmanager.decr_cursor()

    def goto(self, val):
        try:
            byte = int(val, 16)
        except:
            return

        line = byte // editconfig.bytesPerLine

        self.windowmanager.move_vwindow(line)

    def unset_preview(self):
        current_line = self.windowmanager.current_line()

        # Add the value to the preview stream
        self.previewstream.remove(current_line)

        # Refresh
        self._do_preview_redump(current_line)

    def set_preview(self):
        current_line = self.windowmanager.current_line()

        # Get the plugin value
        screen_line = self.windowmanager.current_screenline()
        plugin_buff = self.buffers.getBuffers()[-1]
        plugin_val = plugin_buff[screen_line]

        # Add the value to the preview stream
        self.previewstream.add(current_line, plugin_val)

        # Refresh
        self._do_preview_redump(current_line)

    def _do_preview_redump(self, current_line):
        self.buffers.clear_preview()
        self._redump_data(self.previewstream)

        # Return highlighting
        self.windowmanager.move_vwindow(current_line)


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
        self.padmanager.highlight_lines([0], 0)


    def load_file_piece(self, start, end):
        # start, end are in bytes
        self.padmanager.clear()
        self.buffers.clear()

        self.filedata.dumpToStream(self.forkstream,
            start, end,
            width=editconfig.bytesPerLine)

        self.buffers.computelens()
        self.buffers.draw(self.padmanager)

    def activate_plugin(self, index):
        # Validate
        if index < -1 or index > len(self.plugins):
            return

        # Get the plugin to activate
        # The 0'th plugin is just empty
        # The -1'th plugin is ascii preview
        if index == 0:
            plugin = drop_stream
        elif index == -1:
            plugin = editconfig.BytesToNormalStr
        else:
            plugin = self.plugins[index - 1]

        # Push the plugin into the stream
        self.pluginstream.set_processor(plugin)

        # Store current line
        current_line = self.windowmanager.current_line()

        # Stream the file through the plugin
        self.buffers.clear_plugin()
        self._redump_data(self.pluginstream)

        # Adjust the view window
        self.windowmanager.move_vwindow(current_line)


    def _lastdataline(self):
        last_byte = len(self.filedata)
        last_line = last_byte // editconfig.bytesPerLine

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

        # The last index of buffers = plugin buffer, which is
        #   setup separately
        for stin, stout, buff in _streamzip(
            self.config.streams, bufferstreams[:-1]):
            stfork.addOutputStream(stin)
            stout.addOutputStream(buff)

        # Setup Plugin Stream
        stfork.addOutputStream(stplugin)
        stplugin.set_processor(drop_stream)
        plugin_buff = bufferstreams[-1]
        stplugin.set_stream(plugin_buff)

        # Grab the preview stream
        self.previewstream = self.config.streams[2][0]

    def _redump_data(self, stream):
        # Redump the file through the stream
        fwin = self.windowmanager.fwin
        bpl = editconfig.bytesPerLine
        self.filedata.dumpToStream(stream,
            fwin.start * bpl, fwin.end * bpl,
            width=editconfig.bytesPerLine)

        # Redraw
        self.padmanager.clear()
        self.buffers.draw(self.padmanager)

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


