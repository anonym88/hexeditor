def process(token):
    bits = to_bitlist(token)
    cmd1 = BitString(bits[:32])
    cmd2 = BitString(bits[32:])
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

    return bits


class BitString(object):
    def __init__(self, bits):
        self.bits = bits

    def __iter__(self):
        return iter(self.bits)

    def __len__(self):
        return len(self.bits)

    def __getitem__(self, indices):
        if isinstance(indices, slice):
            new_bits = self.bits[indices]
        else:
            new_bits = [ self.bits[indices] ]
        return BitString(new_bits)

    def __str__(self):
        rev = reversed(self.bits)
        ones = map(str, rev)
        return ''.join(ones)

    def __eq__(self, other):
        if isinstance(other, str):
            if len(other) != len(self):
                return False
            rev = reversed(other)
            for b,s in zip(self.bits, rev):
                x0 = b == 0 and s == '0'
                x1 = b == 1 and s == '1'
                val = x0 or x1
                if not val: return False
            return True

        return NotImplemented


def getBitString(bits):
    assert(len(bits) == 32)

    indices = range(8, 33, 8)
    bts = [ bits[x-8:x] for x in indices ]
    ones = map(str, bts)
    return ' '.join(ones)




def do_process(bits):
    assert(len(bits) == 32)

    if bits[25:28] == "101":
        return "Branch"
    if bits[25:28] == "000":
        return "Proc Data"
    if bits[26:28] == "01":
        return "Memory"

    return getBitString(bits)


