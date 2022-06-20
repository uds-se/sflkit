def middle(x, y, z):
    m = z
    if y < z:
        if x < y:
            m = y
        elif x < z:
            m = y  # bug
    else:
        if x > y:
            m = y
        elif x > z:
            m = x
    return m
