#!/usr/bin/env python3

import configparser
import logging
import os
import threading
import time
import unicornhat as unicorn

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)8s (%(threadName)-10s) %(message)s',
                    )

logging.info("starting")

app_dir = os.path.split(os.path.abspath(__file__))[0]


# Utility Functions


# Create a "color grid" array with optional fill
def make_color_grid(x, y, r=0, g=0, b=0):
    return [[[r, g, b] for i in range(y)] for i in range(x)]


def map_int(v, fl, fh, tl, th):
    fromDistance = fh - fl
    toDistance = th - tl


# Devices


# Base Device Object
class DeviceObj:
    def __init__(self, manager, name, t, x=1, y=1):
        # Save Parameters
        self.sizeX = x
        self.sizeY = y
        self.name = name
        self.type = t

        # Build Light array
        self._lights = make_color_grid(self.sizeX, self.sizeY)
        self._showBuffer = make_color_grid(self.sizeX, self.sizeY)

        # Store in Devices dictionary
        manager.add_device(self)

        logging.debug("created device [{0} ({1}, {2})]".format(self.name, self.sizeX, self.sizeY))

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


# UnicornHat Object
class UnicornHat(DeviceObj):
    def __init__(self, manager, name, rot=0, bri=1):
        width, height = unicorn.get_shape()
        DeviceObj.__init__(self, manager, name, "unicornhat", width, height)

        # Save Parameters
        self.rotation = rot
        self.brightness = bri

        # Initialize Unicorn Hat
        unicorn.set_layout(unicorn.HAT)
        unicorn.rotation(rot)
        unicorn.brightness(bri)

    def set(self, r, g, b, x=0, y=0):
        DeviceObj.set(self, r, g, b, x, y)

        # Set Pixel
        unicorn.set_pixel(x, y, r, g, b)

    def show(self):
        DeviceObj.show(self)

        # Update Display
        unicorn.show()


class DevicePosition:
    def __init__(self, name, x, y, w, h):
        self.name = name
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def is_inside(self, x, y):
        return (self.x <= x < self.x + self.w) and (self.y <= y < self.y + self.h)

    def translate(self, x, y):
        new_x = x - self.x
        new_y = y - self.y

        return [new_x, new_y]


class DeviceManager:
    def __init__(self):
        self.devices = {}
        self._devicesLock = threading.Lock()

        # Build Devices
        device_config = configparser.ConfigParser()
        devices_file = os.path.join(app_dir, 'config', 'devices.ini')
        device_config.read(devices_file)

        for d in device_config.sections():
            if 'type' in device_config[d]:
                if device_config[d]['type'] == 'unicornhat':
                    if 'rotation' in device_config[d]:
                        rotation = int(device_config[d]['rotation'])
                    else:
                        rotation = 0

                    if 'brightness' in device_config[d]:
                        brightness = float(device_config[d]['brightness'])
                    else:
                        brightness = 1

                    logging.debug(
                        "attempting to init Unicorn Hat [{0} bri:{1} rot:{2}]".format(d, brightness, rotation))
                    UnicornHat(self, d, rotation, brightness)
                else:
                    logging.warning(
                        "device {0} has unsupported type: {1}. ignoring.".format(d, device_config[d]['type']))
            else:
                logging.warning("device {0} doesn't have a type. ignoring.".format(d))

    def add_device(self, d):
        with self._devicesLock:
            self.devices[d.name] = d


# Thread Safe Buffer for Frames
class FrameBuffer:
    def __init__(self):
        self._bufferLock = threading.Lock()
        self._buffer = make_color_grid(8, 8)

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


# Programs


# Frame Maker
# Builds a new frame and pushes into nextFrame buffer
def thread_frame_maker(nf):
    logging.info("starting FrameMaker")
    time.sleep(2)
    nf.set(make_color_grid(8, 8, 255))


# LightWrite
# Compares new frame buffer to current buffer and updates lights
def thread_light_write(cf, nf, dm):
    logging.info("starting LightWrite")

    # List configured devices
    for name in dm.devices:
        logging.info("found device [{0}]".format(dm.devices[name], ))

    while True:
        current_frame = cf.get()
        next_frame = nf.get()

        if current_frame != next_frame:
            size_x = len(next_frame)
            size_y = len(next_frame[0])

            for x in range(size_x):
                for y in range(size_y):
                    if current_frame[x][y] != next_frame[x][y]:
                        r = next_frame[x][y][0]
                        g = next_frame[x][y][1]
                        b = next_frame[x][y][2]

                        dm.devices["test"].set(r, g, b, x, y)

            dm.devices["test"].show()

            cf.set(next_frame)


if __name__ == "__main__":
    # Initialize Devices
    device_manager = DeviceManager()

    # Frame Buffer to pass frames between threads
    current_frame_buffer = FrameBuffer()
    next_frame_buffer = FrameBuffer()

    tlw = threading.Thread(name='LightWrite',
                           target=thread_light_write,
                           args=(current_frame_buffer, next_frame_buffer, device_manager))
    tlw.start()

    tfm = threading.Thread(name='FrameMaker',
                           target=thread_frame_maker,
                           args=(next_frame_buffer,))
    tfm.start()

# Party !
