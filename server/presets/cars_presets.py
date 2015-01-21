import itertools
import time

import colors
import random
import presets
import presets.attributes as attributes


RGBA = colors.RGBA


def rainbow_color(n, alpha=1):
  n = int(n)
  if n <  256: return RGBA(255, n, 0, alpha)
  if n <  512: return RGBA(255 - (n - 256), 255, 0, alpha)
  if n <  768: return RGBA(0, 255, (n - 512), alpha)
  if n < 1024: return RGBA(0, 255 - (n - 768), 255, alpha)
  if n < 1280: return RGBA((n - 1024),0 , 255, alpha)
  if n < 1536: return RGBA(255, 0, 255 - (n - 1280), alpha)
  return rainbow_color(n % 1536, alpha)


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
    self.color = (self.color + int(self.xv * 1000 * seconds_past)) % 1536


class Cars(presets.Preset):
  def __init__(self, name='Cars'):
    super(Cars, self).__init__(name)
    self.cars = []
    self.num_cars = attributes.IntAttribute('num_cars', 10)
    self.attributes['num_cars'] = self.num_cars

  def draw(self, pixels, seconds_past):
    num_cars = self.num_cars.val
    self.cars.extend(
      Car(random.random() * len(pixels), 0.01 + random.random() * 0.01, random.randint(0, 1535))
      for _ in xrange(num_cars - len(self.cars)))
    for car in itertools.islice(self.cars, 0, num_cars):
      car.iterate(seconds_past)
      x = car.x * len(pixels)
      pixels.draw_line(x - 1, x + 1, rainbow_color(car.color))

presets.PRESETS.append(Cars())


class ExplosionBit(object):
  def __init__(self, x, xv, color, ttl):
    self.x = x
    self.xv = xv
    self.color = color
    self.ttl = ttl

  def iterate(self, seconds_past):
    self.x += self.xv * seconds_past
    if self.x < 0:
      self.x *= -1
      self.xv *= -1
    elif self.x > 1:
      self.x = 2 - self.x
      self.xv *= -1
    self.color = (self.color + int(1000 * seconds_past)) % 1536


class ExplodingCars(presets.Preset):
  def __init__(self, name='Exploding Cars'):
    super(ExplodingCars, self).__init__(name)
    self.cars = []
    self.explosion_bits = []
    self.num_exploding_cars = attributes.IntAttribute('num_exploding_cars', 5)
    self.attributes['num_exploding_cars'] = self.num_exploding_cars

  def draw(self, pixels, seconds_past):
    num_cars = self.num_exploding_cars.val
    now = time.time()
    self.cars.extend(
      Car(0, 0.01 + random.random() * 0.01, random.randint(0, 1535))
      for _ in xrange(num_cars - len(self.cars)))
    if len(self.cars) > num_cars:
      self.cars = self.cars[:num_cars]

    for j, car_j in enumerate(self.cars):
      for k, car_k in enumerate(itertools.islice(self.cars, j + 1, num_cars), j + 1):
        # if there is a collision:
        if (car_j.x - car_k.x) * (car_j.x + seconds_past * car_j.xv - car_k.x - seconds_past * car_k.xv) < 0:
          self.explosion_bits.extend(ExplosionBit(car_k.x, 0.05 * (-1 + 2 * random.random()), car_k.color, now + 0.1 + random.random()) for _ in xrange(5))
          self.cars[k] = self.cars[-1]
          self.cars.pop()
          break

    for car in self.cars:
      car.iterate(seconds_past)
      x = car.x * len(pixels)
      pixels.draw_line(x - 1, x + 1, rainbow_color(car.color))
    j = 0
    while j < len(self.explosion_bits):
      if self.explosion_bits[j].ttl < now:
        self.explosion_bits[j] = self.explosion_bits[-1]
        self.explosion_bits.pop()
      else:
        j += 1
    for bit in self.explosion_bits:
      bit.iterate(seconds_past)
      x = bit.x * len(pixels)
      pixels.draw_line(x - 0.4, x + 0.4, rainbow_color(bit.color, 0.5))


presets.PRESETS.append(ExplodingCars())
