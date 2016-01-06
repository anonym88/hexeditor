from contextlib import contextmanager

_debug = False
_debug_log = []

def activate():
    global _debug
    _debug = True

def deactivate():
    global _debug
    _debug = False

def logQuit(message):
    if _debug:
        _debug_log.append(message)
        raise Exception("Quitting due to Debug message.")

def logCont(message):
    if _debug:
        _debug_log.append(message)


@contextmanager
def debug_context():
    try:
        yield
    finally:
        if len(_debug_log) > 0:
            print "==== DEBUG OUTPUT ===="
            for message in _debug_log:
                print message
            print "==== ------------ ===="
            print ''

