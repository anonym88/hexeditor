
#class PadBuffer(object):
#    def __init__(self, width, parse_func):
#        self.parse_func = parse_func
#        self.chars = []
#        self.hasline = False
#        self.linenum = 0
#        self.linelength = 0
#        self.width = width
#
#    def addchar(self, char):
#        val, newline = self.parse_func(char)
#        self.linelength += len(val)
#        self.chars.append(val)
#
#        if self.linelength >= self.width or newline:
#            self.hasline = True
#
#class PadBuffer(object):
#    def __init__(self, buff

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

