import led_controller
import random

RGB = led_controller.RGB
PRESET_CLASSES = []
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79]


class Preset(object):
  def __init__(self, name):
    self.name = name

  def draw(self, leds):
    pass


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

  def iterate(self):
    self.x += self.xv
    if self.x < 0:
      self.x *= -1
      self.xv *= -1
    elif self.x > 1:
      self.x = 2 - self.x
      self.xv *= -1
    self.color += self.xv * 1000


class Cars(Preset):
  def __init__(self, name='Cars'):
    super(Cars, self).__init__(name)
    self.cars = [Car(0, float(p) / 100000, random.randint(0, 1535))
                 for p in PRIMES[-10:]]

  def draw(self, leds):
    for j in xrange(leds.num_leds):
      leds.pixels[j] = leds.default_color
    for car in self.cars:
      car.iterate()
      # leds.pixels[int(car.x * leds.num_leds)] = rainbow_color(car.color)
      x = car.x * leds.num_leds
      leds.pixels.draw_line(x - 1, x + 1, rainbow_color(car.color))
    # time.sleep(0.01)

PRESET_CLASSES.append(Cars)

