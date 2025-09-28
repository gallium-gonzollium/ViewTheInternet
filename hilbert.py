def _rot(n, x, y, rx, ry):
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        x, y = y, x
    return x, y

def xy2d(n, x, y):
    d = 0
    s = n // 2
    while s > 0:
        rx = 1 if (x & s) else 0
        ry = 1 if (y & s) else 0
        d += s * s * ((3 * rx) ^ ry)
        x, y = _rot(s * 2, x, y, rx, ry)
        s //= 2
    return d

def int_to_ipv4(i):
    i &= 0xFFFFFFFF
    return f"{(i>>24)&0xFF}.{(i>>16)&0xFF}.{(i>>8)&0xFF}.{i&0xFF}"
