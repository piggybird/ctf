import hashlib


def gen():
    encoded = [0xC41EC3B7, 0xC472C448, 0xC4B7C494, 0xC4F6C465, 0xC532C513,
               0xCDADC4D5, 0xCDCEC576, 0xC5AE00ED, 0xCE15C5BC, 0xC57EC5D7,
               0xC5FCC5F1, 0xC613C594, 0x0152C5F9, 0xC60FC59E, 0xCE46C5F9,
               0xC586C5F0, 0xC5E0C5E2, 0xC5CB01A2, 0xC597C592, 0xC57CC58A,
               0xCDCFC54C]
    buf = []
    for e in encoded:
        buf.append(e & 0xFFFF)
        buf.append(e >> 16)
    n = len(buf)
    for i in range(0, n):
        delta = 0
        for j in range(42, 0, -2):
            delta += i % j + i % (j - 1)
        buf[i] -= delta
    key = unicode('')
    for i in range(0, n):
        j = i % 9
        if j == 0:
            j = 1
        j = i % j
        if j == 1:
            buf[i] ^= 0xCC00
        elif j == 4:
            buf[i] = (buf[i] + 0x100) & 0xFFFF
        elif j == 6:
            buf[i] = ~buf[i] & 0xFFFF
        elif j == 8:
            buf[i] = (buf[i] + 0x3C01) & 0xFFFF
        else:
            buf[i] ^= 0xC3CC
        key += unichr(buf[i])
    # Ensure that the returned string is UTF-8 encoded
    return key.encode('utf-8')


def main():
    key = gen()
    print "Key: " + key
    print "Flag: WhiteHat{%s}" % hashlib.sha1(key.upper()).hexdigest()


if __name__ == "__main__":
    main()
