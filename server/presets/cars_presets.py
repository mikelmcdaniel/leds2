import itertools

import led_controller
import random
import presets
import presets.attributes as attributes

RGB = led_controller.RGB


def rainbow_color(n):
  n = int(n)
  if n <  256: return RGB(255, n, 0)
  if n <  512: return RGB(255 - (n - 256), 255, 0)
  if n <  768: return RGB(0, 255, (n - 512))
  if n < 1024: return RGB(0, 255 - (n - 768), 255)
  if n < 1280: return RGB((n - 1024),0 , 255)
  if n < 1536: return RGB(255, 0, 255 - (n - 1280))
  return rainbow_color(n % 1536)


class Car(object):
  def __init__(self, x, xv, color):
    self.x = x % 1.0
    self.xv = xv
    self.color = color

  def iterate(self, seconds_past):
    self.x += self.xv * seconds_past
    if self.x < 0:
      self.x *= -1
      self.xv *= -1
    elif self.x > 1:
      self.x = 2 - self.x
      self.xv *= -1
    self.color += self.xv * 1000 * seconds_past


class Cars(presets.Preset):
  def __init__(self, name='Cars'):
    super(Cars, self).__init__(name)
    self.cars = [Car(0, float(p) / 5000, random.randint(0, 1535))
                 for p in [41, 43, 47, 53, 59, 61, 67, 71, 73, 79]]
    self.num_cars = attributes.IntAttribute('num_cars', len(self.cars))
    self.attributes['num_cars'] = self.num_cars

  def draw(self, leds, seconds_past):
    for j in xrange(len(leds.pixels)):
      leds.pixels[j] = leds.default_color
    for car in itertools.islice(self.cars, 0, min(self.num_cars.val, len(self.cars))):
      car.iterate(seconds_past)
      x = car.x * leds.num_leds
      leds.pixels.draw_line(x - 1, x + 1, rainbow_color(car.color))


presets.PRESETS.append(Cars())
