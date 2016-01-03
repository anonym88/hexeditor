import curses
import curses.ascii

class PadManager(object):
    def __init__(self, refwin, padding, heightcapacity):
        ry, rx = refwin.getbegyx()
        rh, rw = refwin.getmaxyx()

        self.viewX = rx + padding
        self.viewY = ry + padding
        self.viewH = rh - 2*padding
        self.viewW = rw - 2*padding

        self.xpos = 0
        self.ypos = 0
        self.numlines = 0
        self.cap = heightcapacity

        self.pad = curses.newpad(self.cap, self.viewW)
        self.pad.keypad(True)
        self.pad.scrollok(False)

        self.hl_lines = [ 0 ]

    def refresh(self):
        self.pad.refresh(self.ypos, self.xpos,
            self.viewY, self.viewX,
            self.viewY + self.viewH - 1,
            self.viewX + self.viewW - 1)

    def clear(self):
        self.numlines = 0
        self.pad.clear()

    def drawstr(self, ypos, xpos, val):
        self._setlines(ypos)
        self.pad.addstr(ypos, xpos, val)

    def get_line(self): return self.ypos

    def set_line(self, line):
        self.ypos = line

    def highlight_lines(self, pad_lines, cursor_line):
        assert(cursor_line in pad_lines)

        # Set currently highlighted to normal
        for line in self.hl_lines:
            self.pad.chgat(line, 0, curses.A_NORMAL)

        self.hl_lines = pad_lines

        # Highlight lines
        for line in self.hl_lines:
            self.pad.chgat(line, 0, curses.A_BOLD)

        # Highlight cursor
        self.pad.chgat(cursor_line, 0, 1,
            curses.A_REVERSE)
        self.pad.move(cursor_line, 0)

    def _setlines(self, linenum):
        if linenum <= self.numlines:
            return
        self.numlines = linenum
        if linenum >= self.cap:
            self.cap = linenum*2
            self.pad.resize(self.cap, self.viewW)

