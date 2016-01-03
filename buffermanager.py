from itertools import izip_longest, imap
from buffer import ColumnBuffer
from bisect import bisect_left, bisect_right

class BufferManager(object):
    def __init__(self, columngaps):
        numcolumns = len(columngaps)
        self.columngaps = columngaps
        self.buffers = [ ColumnBuffer() for i in xrange(numcolumns) ]
        self.lens = [ 0 for i in xrange(numcolumns) ]

        self.screenpos = []
        self.linepos = {}

    def clear(self):
        for buff in self.buffers:
            buff.clear()
        self.screenpos = []
        self.linepos.clear()

    def clear_plugin(self):
        self.buffers[-1].clear()
        self.screenpos = []
        self.linepos.clear()

    def lineToScreen(self, line):
        return self.screenpos[line]

    def screenToScreenRange(self, screenLine):
        line = self.screenToLine(screenLine)
        return self.screenpos[line], self.screenpos[line+1]

    def screenToLine(self, screenLine):
        return _largest_lt(self.screenpos, screenLine)

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
        for linenum, alllines in enumerate(zipiter):
            #alllines is a tuple of each buffer's line
            maxlen = max(imap(len, alllines))

            # Draw everything
            for col, lines in enumerate(alllines):
                for lineoffset, line in enumerate(lines):
                    yval = curline + lineoffset
                    xval = self.columns[col]
                    editpad.drawstr(yval, xval, line)

            # Record the screen position
            self.screenpos.append(curline)
            self.linepos[curline] = linenum

            curline += maxlen
        # Add the end, so the difference can be told between
        #   the last line and off the screen
        self.screenpos.append(curline)
        self.linepos[curline] = linenum

    def screenend(self):
        return self.screenpos[-1]

    def lineend(self):
        return len(self.screenpos)


# takes iter<iter<thing>> and flattens to iter<thing>
def _flatten(iterable):
    for inner in iterable:
        for val in inner:
            yield val

def _largest_lt(array, val):
    x = bisect_left(array, val)
    if array[x] == val:
        return x
    return x - 1



