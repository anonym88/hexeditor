

class LineWindowManager(object):
    def __init__(self, flen, floader, bpl, buffers, padmanager):
        self.fwin = _Window(0,0)

        self.vwin = _Window(0,0)

        self.flen = flen

        self.floader = floader
        self.vloader = vloader
        self.bpl = bpl
        self.buffers = buffers
        self.padmanager = padmanager

    def move_fwindow(self, start):
        margin = self.viewH
        file_start = start - margin
        file_end = start + self.viewH + margin
        fwin = _Window(file_start, file_end)

        full_win = _Window(0, self.flen+1)
        # Reasoning for + 1: file_end is a non-inclusive bound,
        #   in order for the last line to be loaded it has to
        #   be before file_end

        self.fwin = full_win.compress(fwin)

        byte_win = self.fwin * self.bpl

        self.floader(byte_win.start, byte_win.end)

    # This function is intended to move the view window by
    #   small amounts. (If the given offset is larger than
    #   viewH, then this may result in undefined behavior!)
    def change_vwindow(self, offset):
        # The desired view window
        new_win = self.vwin + offset

        # The lines that the new view window will cover
        line_win = new_win.apply(self.buffers.screenToLine) + self.fwin.start

        if self.fwin.contains(line_win):
            self.padmanager.set_line(new_win.start)
            return

        direction = line_win > self.fwin

        # Get the lines spanned by the current view:
        orig_lines = self.vwin.apply(self.buffers.screenToLine) + self.fwin.start

        # Move the file window
        self.move_fwindow(self, line_win.start)

        offsets = orig_lines - self.fwin

        if direction:
            # The original window must have stopped at a line end
            vend = self.buffers.lineToScreen(offsets.end)
            vend += offset
            vstart = vend - view.H
        else:
            # The original window must have begun at a line start
            vstart = self.buffers.lineToScreen(offsets.start)
            vstart += offset # Add since offset is negative
            vend = vstart + self.viewH

        self.vwin = _Window(vstart, vend)
        self.padmanager.set_line(self.vwin.start)

    # This will jump the view window directly to the given
    #   file line. Note that this cannot end up at a
    #   particular screen line like change_vwindow can.
    def move_vwindow(self, line):
        line_win = _Window(line, line + self.viewH)

        if not self.fwin.contains(line_win):
            self.change_fwindow(line)

        start = self.buffers.lineToScreen(line)
        current = self.vwin.start
        self.change_vwindow(start - current)


class _Window(object):
    def __init__(self, start, end):
        if start > end:
            raise ValueError("Window ends before it starts- %s:%s" % (str(start), str(end))

        self.start = start
        self.end = end

    def contains(self, win):
        return win.start >= self.start and win.end <= self.end

    def compress(self, win):
        x = win.start
        y = win.end
        if x < self.start:
            x = self.start
        if y > self.end:
            y = self.end

        return _Window(x,y)

    def apply(self, func):
        x = func(self.start)
        y = func(self.end)
        return _Window(x,y)

    def __add__(self, val):
        return _Window(self.start + val, self.end + val)

    def __sub__(self, val):
        return self.__add__(-1 * val)

    def __mul__(self, val):
        return _Window(self.start * val, self.end * val)

    def __radd__(self, val):
        return self.__add__(val)

    def __rsub__(self, val):
        return self.__sub__(val)

    def __rmul__(self, val):
        return self.__mul__(val)

    def __iadd__(self, val):
        self.start += val
        self.end += val
        return self

    def __isub__(self, val):
        return self.__iadd__(-1*val)

    def __imul__(self, val):
        self.start *= val
        self.end *= val
        return self

    def __gt__(self, win):
        return self.end > win.end

    def __lt__(self, win):
        return self.start < win.start




