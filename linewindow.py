

class LineWindowManager(object):
    def __init__(self, flen, floader, vloader):
        self.fwin = _Window(0,0)

        self.vwin = _Window(0,0)

        self.flen = flen

        self.floader = floader
        self.vloader = vloader

    def move_fwindow(self, start):
        margin = self.viewH
        file_start = start - margin
        file_end = start + self.viewH + margin
        fwin = _Window(file_start, file_end)

        flen = self._lastdataline()
        full_win = _Window(0,flen+1)
        # Reasoning for + 1: file_end is a non-inclusive bound,
        #   in order for the last line to be loaded it has to
        #   be before file_end

        self.fwin = full_win.compress(fwin)

        byte_win = self.fwin * self.config.bytesPerLine

        self.load_file_piece(byte_win.start, byte_win.end)

    def move_vwindow(self, offset):
        new_win = self.vwin + offset

        line_win = new_win.apply(self.buffers.screenToLine)

        if file_win.contains(line_win):
            self.padmanager.set_line(new_win.start)
            return

        self.move_fwindow(self, line_win.start)



    def incr_vwindow(self):
        ypos = self.padmanager.get_line()

        vstart = ypos + 1
        vend = vstart + self.viewH

        if vend <= self.buffers.screenend():
            self.padmanager.set_line(vstart)
            return

        fend = self.buffers.get_fend()

        if fend >= self._lastdataline() + 1:
            # File window can't increase past end of file
            return

        last_line = fend

        current_line = self.buffers.screenToLineSoft(ypos)
        self.move_fwindow(current_line)

        last_screen = self.buffers.lineToScreenStart(last_line)
        start_screen = last_screen - self.viewH + 1

        self.padmanager.set_line(start_screen)

    def decr_vwindow(self):
        ypos = self.padmanager.get_line()

        if ypos > 0:
            self.padmanager.set_line(ypos - 1)
            return

        vstart = ypos - 1
        vend = vstart + self.viewH

        fstart = self.buffers.get_fstart()

        if fstart <= 0:
            # File window can't decrease before start of file
            return

        current_line = fstart

        self.move_fwindow(current_line)

        start_screen = self.buffers.lineToScreenStart(current_line)
        self.padmanager.set_line(start_screen - 1)

    def jump_vwindow(self, line):
        self.move_fwindow(line)
        start_screen = self.buffers.lineToScreenStart(line)
        self.padmanager.set_line(start_screen)


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




