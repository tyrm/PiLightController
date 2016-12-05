#!/usr/bin/env python3

import threading


# Utility Functions


def decode_rgba32(c):
    red = (c & 0xFF0000) >> 16
    green = (c & 0xFF00) >> 8
    blue = c & 0xFF

    return [red, green, blue, 0]


# Create a "color grid" array with optional fill
def make_color_grid(x, y, r=0, g=0, b=0):
    return [[[r, g, b] for _ in range(y)] for _ in range(x)]


def rgba32(r, g, b):
    color = b
    color += g << 8
    color += r << 16

    return color


def scale(value, input_low, input_high, output_low, output_high):
    return ((value - input_low) / (input_high - input_low)) * (output_high - output_low) + output_low


# Base Device Object
class DeviceObj:
    def __init__(self, name, t, x=1, y=1):
        # Save Parameters
        self.width = x
        self.height = y
        self.name = name
        self.type = t

        # Build Light array
        self._lights = make_color_grid(self.width, self.height)
        self._showBuffer = make_color_grid(self.width, self.height)

    def __str__(self):
        return "{0} ({1}, {2}x{3})".format(self.name, self.type, self.width, self.height)

    def get(self, x=0, y=0):
        r = self._lights[x][y][0]
        g = self._lights[x][y][1]
        b = self._lights[x][y][2]
        return [r, g, b]

    def get_size(self):
        return [self.width, self.height]

    def set(self, r, g, b, x=0, y=0):
        self._showBuffer[x][y][0] = r
        self._showBuffer[x][y][1] = g
        self._showBuffer[x][y][2] = b

    def show(self):
        self._lights = self._showBuffer


# Thread Safe Buffer for Frames
class FrameBuffer:
    def __init__(self, x, y):
        self._bufferLock = threading.Lock()
        self._buffer = make_color_grid(x, y)

    def set(self, b):
        with self._bufferLock:
            self._buffer = b

    def get(self):
        with self._bufferLock:
            return self._buffer

    def set_pixel(self, x, y, r, g, b):
        self._buffer[x][y] = [r, g, b]

    def get_size(self):
        with self._bufferLock:
            width = len(self._buffer)
            height = len(self._buffer[0])

            return [width, height]
