#!/usr/bin/env python3

from neopixel import *

from lights import DeviceObj


# UnicornHat Object
class NeoPixels(DeviceObj):
    def __init__(self,  name, count):
        DeviceObj.__init__(self, name, "neopixel", count)

        # LED strip configuration:
        LED_PIN = 18  # GPIO pin connected to the pixels (must support PWM!).
        LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
        LED_DMA = 5  # DMA channel to use for generating signal (try 5)
        LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
        LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)

        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(count, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

        self.strip.begin()


    def set(self, r, g, b, x=0, y=0):
        DeviceObj.set(self, r, g, b, x, y)

        # Set Pixel
        self.strip.setPixelColor(x, Color(r, g, b))

    def show(self):
        DeviceObj.show(self)

        # Update Display
        self.strip.show()