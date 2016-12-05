#!/usr/bin/env python3

from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder
from pythonosc import udp_client

from lights import DeviceObj, rgba32


# OSC Grid Object
class OSCGrid(DeviceObj):
    def __init__(self, name, width, height, ip, port):
        DeviceObj.__init__(self, name, "osc_grid", width, height)

        self.osc = udp_client.SimpleUDPClient(ip, port)
        self._buffer = []

    def set(self, r, g, b, x=0, y=0):
        DeviceObj.set(self, r, g, b, x, y)

        # Set Pixel
        builder = osc_message_builder.OscMessageBuilder(address="/light/{0}/{1}/color".format(x, y))

        builder.add_arg(rgba32(r, g, b))

        self._buffer.append(builder.build())

    def show(self):
        DeviceObj.show(self)

        # Update Display
        bundle = osc_bundle_builder.OscBundleBuilder(0)

        for m in self._buffer:
            bundle.add_content(m)

        self.osc.send(bundle.build())

        self._buffer.clear()
