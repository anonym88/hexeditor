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

    def push_token(self, token):
        new_token = self.processor(token)
        if new_token is not None:
            for s in self.streams:
                s.push_token(new_token)

# An output stream that turns input into a list
class StreamToList(object):
    def __init__(self):
        self.data = []

    def push_token(self, token):
        self.data.append(token)


# Currently doesn't do much. This is an abstraction so
#   that it is easy to change how file access works in
#   the future
class FileBuffer(object):
    def __init__(self, infile):
        self.infile = infile

    def dumpToStream(self, stream, width=8):
        self.infile.seek(0)
        val = self.infile.read(width)
        while val != '':
            stream.push_token(bytes(val))
            val = self.infile.read(width)

def fork_stream(token):
    return token
