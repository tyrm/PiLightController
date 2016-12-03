#!/usr/bin/env python3

import threading

import lights.util

# Base Device Object
class DeviceObj:
    def __init__(self, name, t, x=1, y=1):
        # Save Parameters
        self.sizeX = x
        self.sizeY = y
        self.name = name
        self.type = t

        # Build Light array
        self._lights = util.make_color_grid(self.sizeX, self.sizeY)
        self._showBuffer = util.make_color_grid(self.sizeX, self.sizeY)

    def __str__(self):
        return "{0} ({1}, {2}x{3})".format(self.name, self.type, self.sizeX, self.sizeY)

    def get(self, x=0, y=0):
        r = self._lights[x][y][0]
        g = self._lights[x][y][1]
        b = self._lights[x][y][2]
        return [r, g, b]

    def get_size(self):
        return [self.sizeX, self.sizeY]

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
        self._buffer = util.make_color_grid(x, y)

    def set(self, b):
        with self._bufferLock:
            self._buffer = b

    def get(self):
        with self._bufferLock:
            return self._buffer

    def get_size(self):
        size_x = len(self._buffer)
        size_y = len(self._buffer[0])

        return [size_x, size_y]