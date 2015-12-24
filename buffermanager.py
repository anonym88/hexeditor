from itertools import izip_longest, imap
from buffer import ColumnBuffer

class BufferManager(object):
    def __init__(self, columngaps):
        numcolumns = len(columngaps)
        self.columngaps = columngaps
        self.buffers = [ ColumnBuffer() for i in xrange(numcolumns) ]
        self.lens = [ 0 for i in xrange(numcolumns) ]

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

# takes iter<iter<thing>> and flattens to iter<thing>
def _flatten(iterable):
    for inner in iterable:
        for val in inner:
            yield val

