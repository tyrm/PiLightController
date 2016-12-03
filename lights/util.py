#!/usr/bin/env python3

# Utility Functions


# Create a "color grid" array with optional fill
def make_color_grid(x, y, r=0, g=0, b=0):
    return [[[r, g, b] for _ in range(y)] for _ in range(x)]


def scale(value, input_low, input_high, output_low, output_high):
    return ((value - input_low) / (input_high - input_low)) * (output_high - output_low) + output_low
