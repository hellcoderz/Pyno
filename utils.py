def sum_coma(t):
    result = ''
    for i in t:
        result += (i[0] + '=' + 'gen_inputs[' +
                   str(t.index(i)) + '][1]' + ',')
    return result[:-1]


def x_y_pan_scale(x, y, pan_scale, wscale):
    s = pan_scale

    x = int((-wscale[0] / 2 + x) / s[1] - (-wscale[0] / 2 + s[0][0]))
    y = int((-wscale[1] / 2 + y) / s[1] - (-wscale[1] / 2 + s[0][1]))
    return x, y


def centered(init, width, count, number):
    if count > 1:
        c = count - 1
        return (init - width / 2) + width * number / c
    else:
        return init


def point_intersect_quad(point, rect=(0, 0, 10, 10)):
    if (point[0] < max(rect[0], rect[2])
    and point[0] > min(rect[0], rect[2])):
        if (point[1] < max(rect[1], rect[3])
        and point[1] > min(rect[1], rect[3])):
            return True
    return False
