#!/usr/bin/env python3

import configparser
import logging
import os
import threading
import time

import lights
from lights.device_unicornhat import UnicornHat
from lights.device_osc_grid import OSCGrid
import lights.programs as light_programs

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)8s (%(threadName)-10s) %(message)s',
                    )

logging.info("starting")

app_dir = os.path.split(os.path.abspath(__file__))[0]


class DevicePosition:
    def __init__(self, name, x, y, w, h):
        self.name = name
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def get_last_position(self):
        last_x = self.x + self.w - 1
        last_y = self.y + self.h - 1

        return [last_x, last_y]

    def is_inside(self, x, y):
        return (self.x <= x < self.x + self.w) and (self.y <= y < self.y + self.h)

    def translate(self, x, y):
        new_x = x - self.x
        new_y = y - self.y

        return [new_x, new_y]


class DeviceManager:
    def __init__(self, df):
        self.devices = {}
        self.devices_lock = threading.Lock()
        self.layout = []
        self.layout_lock = threading.Lock()

        # Build Devices
        device_config = configparser.ConfigParser()
        device_config.read(df)

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
                        "attempting to init Unicorn Hat [{0} 8x8 bri:{1} rot:{2}]".format(d, brightness, rotation))
                    self.add_device(UnicornHat(d, rotation, brightness))
                elif device_config[d]['type'] == 'osc_grid':
                    host = device_config[d]['host']
                    if 'port' in device_config[d]:
                        port = int(device_config[d]['port'])
                    else:
                        port = 5005
                    width = int(device_config[d]['width'])
                    height = int(device_config[d]['height'])

                    logging.debug(
                        "attempting to init OSC Grid [{0} {1}x{2} host:{3} port:{4}]".format(d, width, height, host,
                                                                                             port))
                    self.add_device(OSCGrid(d, width, height, host, port))
                else:
                    logging.warning(
                        "device {0} has unsupported type: {1}. ignoring.".format(d, device_config[d]['type']))
            else:
                logging.warning("device {0} doesn't have a type. ignoring.".format(d))

    def add_device(self, d):
        with self.devices_lock:
            logging.debug("adding device [{0}] to device manager".format(d.name, ))
            self.devices[d.name] = d
        self.add_location(d.name, 0, 0)

    def add_location(self, name, x, y):
        with self.layout_lock:
            logging.debug("adding device [{0}] to layout ".format(name, ))
            w, h = self.get_device_size(name)
            self.layout.append(DevicePosition(name, x, y, w, h))

    def get_device_size(self, name):
        with self.devices_lock:
            return self.devices[name].get_size()

    def get_devices_at(self, x, y):
        device_list = []

        with self.layout_lock:
            for device in self.layout:
                if device.is_inside(x, y):
                    device_list.append(device)

        return device_list

    def get_layout_size(self):
        max_x = 0
        max_y = 0
        for position in self.layout:
            last_x, last_y = position.get_last_position()

            if max_x < last_x + 1:
                max_x = last_x + 1
            if max_y < last_y + 1:
                max_y = last_y + 1

        return [max_x, max_y]

    def show_all(self):
        with self.devices_lock:
            for device in self.devices:
                self.devices[device].show()


# Threadsafe Config
class RunningConfig:
    def __init__(self):
        self.mode = "cross"
        self.mode_lock = threading.Lock()

        self.trigger_source = "timer"
        self.trigger_timer_length = 0.03
        self.trigger_lock = threading.Lock()

    def get_mode(self):
        with self.mode_lock:
            return self.mode

    def get_trigger_source(self):
        with self.trigger_lock:
            return self.trigger_source

    def get_trigger_timer_length(self):
        with self.trigger_lock:
            return self.trigger_timer_length

    def set_mode(self, m):
        with self.mode_lock:
            self.mode = m

    def set_trigger_source(self, s):
        with self.trigger_lock:
            self.mode = s

    def set_trigger_timer_length(self, l):
        with self.trigger_lock:
            self.trigger_timer_length = l


# Threads


def thread_trigger(rc, bng):
    logging.info("starting Trigger")

    while True:
        trigger_source = rc.get_trigger_source()
        if trigger_source is "timer":
            time.sleep(rc.get_trigger_timer_length())
            bng.set()


# Frame Maker
# Builds a new frame and pushes into nextFrame buffer
def thread_frame_maker(rc, bng, nf, dm, prg):
    logging.info("starting FrameMaker")

    while True:
        bng.wait()
        size_x, size_y = dm.get_layout_size()

        mode = rc.get_mode()

        if mode is "cross":
            nf.set(prg["cross"].get_next_frame(size_x, size_y))

        bng.clear()


# LightWrite
# Compares new frame buffer to current buffer and updates lights
def thread_light_write(cf, nf, dm):
    logging.info("starting LightWrite")

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

                        update_list = dm.get_devices_at(x, y)

                        for device in update_list:
                            offset_x = device.x
                            offset_y = device.y

                            dm.devices[device.name].set(r, g, b, x - offset_x, y - offset_y)


            dm.show_all()

            cf.set(next_frame)


if __name__ == "__main__":
    running_config = RunningConfig()

    # Initialize Devices
    devices_file = os.path.join(app_dir, 'config', 'devices.ini')
    device_manager = DeviceManager(devices_file)

    # Frame Bufferd
    buff_init_x, buff_init_y = device_manager.get_layout_size()

    current_frame_buffer = lights.FrameBuffer(buff_init_x, buff_init_y)
    next_frame_buffer = lights.FrameBuffer(buff_init_x, buff_init_y)

    # Programs
    programs = dict()
    programs["cross"] = light_programs.Cross(buff_init_x, buff_init_y)

    # Events
    bang = threading.Event()

    tlw = threading.Thread(name='LightWrite',
                           target=thread_light_write,
                           args=(current_frame_buffer, next_frame_buffer, device_manager))
    tlw.start()

    tfm = threading.Thread(name='FrameMaker',
                           target=thread_frame_maker,
                           args=(running_config, bang, next_frame_buffer, device_manager, programs))
    tfm.start()

    ttr = threading.Thread(name='Trigger',
                           target=thread_trigger,
                           args=(running_config, bang))
    ttr.start()

# Party !
