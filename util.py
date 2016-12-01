#!/usr/bin/env python3

# Utility Functions


# Create a "color grid" array with optional fill
def make_color_grid(x, y, r=0, g=0, b=0):
    return [[[r, g, b] for i in range(y)] for i in range(x)]


def map_int(v, fl, fh, tl, th):
    fromDistance = fh - fl
    toDistance = th - tl
