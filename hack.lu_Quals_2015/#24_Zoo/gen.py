import socket
import z3
import random
import re


def find_chars(hi, low):
    # Generate 3 characters from the expected value of y and x
    valid_char = ""

    for i in range(0x20, 0x80):
        valid_char += chr(i)
    s0 = hi >> 3
    s2 = ((hi & 7) << 3) | ((low >> 6) & 7)
    s1 = low & 0x3F

    s0 ^= 0x20
    s1 ^= 0x20
    s2 ^= 0x20

    if chr(s0) not in valid_char:
        s0 += 0x40
    if chr(s1) not in valid_char:
        s1 += 0x40
    if chr(s2) not in valid_char:
        s2 += 0x40
    if chr(s0) not in valid_char or chr(s1) not in valid_char or chr(s2) not in valid_char:
        return None
    return chr(s0) + chr(s1) + chr(s2)


def extract_word(buf):
    if buf is None or len(buf) < 2:
        return 0
    result = 0
    for i in range(0, 2):
        ch = ord(buf[1 - i])
        result = (result << 8) | ch
    return result


def extract_dword(buf):
    if buf is None or len(buf) < 4:
        return 0
    result = 0
    for i in range(0, 4):
        ch = ord(buf[3 - i])
        result = (result << 8) | ch
    return result


def dword_to_str(val):
    result = ""
    tmp = val
    for i in range(0, 4):
        result += chr(tmp & 0xFF)
        tmp >>= 8
    return result


def checksum_user_name(user_name):
    s = 0
    name = user_name + chr(0)
    for i in range(0, 8):
        s += extract_word(name[i * 2:])
    return s & 0xFFFF


def gen_remain(user_name):
    h = checksum_user_name(user_name)
    H1 = (h & 0xFF) + 0x100
    H2 = (h >> 8) + 0x100

    A = z3.Int('A')
    B = z3.Int('B')
    C = z3.Int('C')
    s = z3.Solver()
    s.add(A >= 0, B >= 0, C >= 0, A + (2 * B) + (3 * C) == H1, (2 * A) + B == H2)
    if s.check() != z3.sat:
        return None

    a_val = s.model()[A].as_long()
    b_val = s.model()[B].as_long()
    c_val = s.model()[C].as_long()
    while True:
        x = 0
        y = 0
        a = a_val
        b = b_val
        c = c_val
        result = ""
        while x != H1 or y != H2:
            if a == 0 and b == 0 and c == 0:
                result = ""
                break
            if x > H1 or y > H2:
                result = ""
                break
            dx = random.randrange(1, 3)
            if dx == 1:
                if a == 0:
                    continue
                x += 1
                y += 2
                a -= 1
            elif dx == 2:
                if b == 0:
                    continue
                x += 2
                y += 1
                b -= 1
            elif dx == 3:
                if c == 0:
                    continue
                x += 3
                c -= 1
            s = find_chars(y, x)
            if s is None:
                result = ""
                break
            result += s
        if len(result) > 0:
            return result + find_chars(H2, H1)


def gen(user_name):
    lic = dword_to_str(extract_dword(user_name) ^ 0x0023002B)
    remain = gen_remain(user_name)
    if remain is None:
        return None
    lic += remain
    return lic


def scan_name(data):
    m = re.search("(hello )([a-z]*)!", data)
    if m is None:
        return None
    return m.group(2)


def solve(server, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, port))

    while True:
        data_line = client_socket.recv(2048)
        if data_line is None or len(data_line) == 0:
            break
        print data_line

        # scan name
        name = scan_name(data_line)
        if name is None:
            pass
        else:
            lic = gen(name)
            if lic is not None and len(lic) > 0:
                client_socket.send(lic + "\n")
            else:
                print "Generation failed"
                return


def main():
    solve("school.fluxfingers.net", 1532)


if __name__ == "__main__":
    main()
