#!/usr/bin/env python3

from random import randint

from lights import make_color_grid


class LightProgram:
    def __init__(self, w, h):
        self.current_frame = []
        self.last_w = w
        self.last_h = h

    def get_next_frame(self, w, h):
        next_frame = make_color_grid(w, h)

        self.current_frame = next_frame
        return self.current_frame


class LightPoint:
    def __init__(self, w, h):

        self.direction = randint(1, 4)
        if self.direction == 1:
            self.x = randint(0, w - 1)
            self.y = 0
        elif self.direction == 2:
            self.x = 0
            self.y = randint(0, h - 1)
        elif self.direction == 3:
            self.x = randint(0, w - 1)
            self.y = h - 1
        else:
            self.x = w - 1
            self.y = randint(0, h - 1)

        self.colour = []
        for i in range(0, 3):
            self.colour.append(randint(100, 255))


class Cross(LightProgram):
    def __init__(self, w, h):
        LightProgram.__init__(self, w, h)
        self.points = []
        self.max_points = 10

    def get_next_frame(self, w, h):

        next_frame = make_color_grid(w, h)

        for point in self.points:
            if point.direction == 1:
                point.y += 1
                if point.y > h - 1:
                    self.points.remove(point)
            elif point.direction == 2:
                point.x += 1
                if point.x > w - 1:
                    self.points.remove(point)
            elif point.direction == 3:
                point.y -= 1
                if point.y < 0:
                    self.points.remove(point)
            else:
                point.x -= 1
                if point.x < 0:
                    self.points.remove(point)

        # Create New Points of Light
        if len(self.points) < self.max_points and randint(0, 5) > 1:
            self.points.append(LightPoint(w, h))

        for point in self.points:
            next_frame[point.x][point.y] = [point.colour[0], point.colour[1], point.colour[2]]

        return next_frame
