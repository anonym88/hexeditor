from editconfig import bytesPerLine

class LineWindowManager(object):
    def __init__(self, flen, floader, buffers, padmanager):

        self.flen = flen
        self.full_win = _Window(0, flen+1)
        # Reasoning for + 1: file_end is a non-inclusive bound,
        #   in order for the last line to be loaded it has to
        #   be before file_end

        self.floader = floader
        self.buffers = buffers
        self.padmanager = padmanager
        self.viewH = padmanager.viewH

        self.fwin = _Window(0,0)
        self.vwin = _Window(0,self.viewH)

        self.cursor = 0

    def decr_cursor(self):
        if self.cursor <= 0:
            self.decr_vwindow()
        else:
            self.cursor -= 1
        self.do_hl()

    def incr_cursor(self):
        if self.cursor >= self.viewH - 1:
            self.incr_vwindow()
        else:
            self.cursor += 1
        self.do_hl()

    def do_hl(self):
        pos = self.cursor + self.vwin.start
        rng = self.buffers.screenToScreenRange(pos)
        lines = range(*rng)

        #self.padmanager.drawstr(self.cursor + self.vwin.start, 80, str(lines))

        self.padmanager.highlight_lines(lines, pos)

    def move_fwindow(self, start):
        margin = self.viewH
        file_start = start - margin
        file_end = start + self.viewH + margin
        fwin = _Window(file_start, file_end)

        self.fwin = self.full_win.compress(fwin)

        byte_win = self.fwin * bytesPerLine

        self.floader(byte_win.start, byte_win.end)

    def incr_vwindow(self):
        new_win = self.vwin + 1

        if new_win.end <= self.buffers.screenend():
            self.padmanager.set_line(new_win.start)
            self.vwin = new_win
            return

        if self.fwin.end >= self.flen + 1:
            # File window can't increase past end of file
            return

        last_line = self.fwin.end

        current_line = self.buffers.screenToLine(self.vwin.start) + self.fwin.start

        self.move_fwindow(current_line)

        last_screen = self.buffers.lineToScreen(last_line - self.fwin.start)
        start_screen = last_screen - self.viewH + 1

        self.padmanager.set_line(start_screen)
        self.vwin = _Window(start_screen, start_screen + self.viewH)

    def decr_vwindow(self):
        new_win = self.vwin - 1

        if new_win.start >= 0:
            self.padmanager.set_line(new_win.start)
            self.vwin = new_win
            return

        if self.fwin.start <= 0:
            # File window can't decrease before start of file
            return

        current_line = self.fwin.start

        self.move_fwindow(current_line)

        start_screen = self.buffers.lineToScreen(current_line - self.fwin.start)
        self.padmanager.set_line(start_screen - 1)
        self.vwin = _Window(start_screen - 1, start_screen + self.viewH - 1)

    # This will jump the view window directly to the given
    #   file line.
    def move_vwindow(self, line):
        # If out of bounds just move to the beginning/end
        if line < 0:
            return self.move_vwindow(0)
        if line > self.flen:
            return self.move_vwindow(self.flen)

        line_win = _Window(line, line + self.viewH)

        # Load a new piece of file if needed
        if not self.fwin.contains(line_win):
            self.move_fwindow(line)

        start_screen = self.buffers.lineToScreen(line - self.fwin.start)
        new_win = _Window(start_screen, start_screen + self.viewH)
        full_win = _Window(0, self.buffers.screenend())

        # Make sure the view window doesn't end up out of bounds on the bottom
        new_win = full_win.align_shift(new_win)

        self.padmanager.set_line(new_win.start)
        self.vwin = new_win

        # Set the highlighting
        self.cursor = start_screen - self.vwin.start
        self.do_hl()


    def current_line(self):
        offset = self.buffers.screenToLine(self.vwin.start)
        return offset + self.fwin.start


class _Window(object):
    def __init__(self, start, end):
        if start > end:
            raise ValueError("Window ends before it starts- %s:%s" % (str(start), str(end)))

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

    # Returns a window that is 'win' shifted so that it fits
    #   inside of 'self'. This preserves the start end gap,
    #   unlike compress
    # If 'win' is larger than 'self', lines the start values up
    # ex: x=[0 -> 4], y=[3 -> 5]
    #   x.align_shift(y) = [2 -> 4]
    #   y.align_shift(x) = [3 -> 7]
    def align_shift(self, win):
        if win.start < self.start:
            win = win + (self.start - win.start)
        elif win.end > self.end:
            win = win + (self.end - win.end)
        return win

    def __add__(self, val):
        return _Window(self.start + val, self.end + val)

    def __sub__(self, val):
        return self.__add__(-1 * val)

    def __mul__(self, val):
        return _Window(self.start * val, self.end * val)

    def __radd__(self, val):
        return self.__add__(val)

    def __rsub__(self, val):
        return (-1 * self) + val

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

    def __str__(self):
        return "[%i -> %i]" % (self.start, self.end)


