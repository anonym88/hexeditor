import os

# BufferStream represents a push-based stream of data.
# A bufferstream is given a processing function that
#   turns the flow of input tokens into output tokens
# A bufferstream has at least one output stream that it
#   pushes its data into
class BufferStream(object):
    def __init__(self, token_processor):
        self.processor = token_processor
        self.streams = []

    def addOutputStream(self, stream):
        self.streams.append(stream)

    def push_token(self, token, index):
        new_token = BufferStream.do_process(
                        self.processor, token, index)
        if new_token is not None:
            for s in self.streams:
                s.push_token(new_token, index)

    @staticmethod
    def do_process(processor, token, index):
        if hasattr(processor, "want_index"):
            want_index = processor.want_index
        else:
            want_index = False

        if want_index:
            return processor(token, index)
        else:
            return processor(token)


# Currently doesn't do much. This is an abstraction so
#   that it is easy to change how file access works in
#   the future
class FileBuffer(object):
    def __init__(self, infile):
        self.infile = infile
        self._flen = None

    def dumpToStream(self, stream, start, end, width=8):
        self.infile.seek(start)
        remaining = end - start

        toread = width if remaining > width else remaining
        val = self.infile.read(toread)
        while val != '' and remaining > 0:
            ind = end - remaining
            stream.push_token(bytes(val), ind)

            remaining -= len(val)

            toread = width if remaining > width else remaining
            val = self.infile.read(toread)

    def __len__(self):
        if self._flen is None:
            temp = self.infile.tell()
            self.infile.seek(0, os.SEEK_END)
            self._flen = self.infile.tell()
            self.infile.seek(temp)
        return self._flen


class ColumnBuffer(object):
    def __init__(self):
        self.lines = []

    def push_token(self, token, index):
        if isinstance(token, str):
            token = [ token ]
        self.lines.append(token)

    def clear(self):
        self.lines = []

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

    def __iter__(self):
        return iter(self.lines)


