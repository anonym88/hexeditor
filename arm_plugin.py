def process(token):
    bits = to_bitlist(token)
    cmd1 = bits[:32]
    cmd2 = bits[32:]
    return [ do_process(cmd1), do_process(cmd2) ]



def byteToBits(byte):
    for i in xrange(8):
        yield byte & 1
        byte = byte >> 1

def to_bitlist(token):
    byteList = memoryview(token).tolist()
    bits = []
    for byte in byteList:
        for bit in byteToBits(byte):
            bits.append(bit)

    #[ bit for bit in [ byteToBits(byte) for byte in byteList ] ]
    return bits

def bitsToStr(bits):
    rev = reversed(bits)
    ones = map(str, rev)
    return ''.join(ones)

def do_process(bits):
    assert(len(bits) == 32)

    indices = range(8, 33, 8)
    bts = [ bits[x-8:x] for x in indices ]
    ones = map(bitsToStr, bts)
    return ' '.join(ones)

    xx = reversed(bits[:8])
    xx = map(str, xx)
    return ''.join(xx)

