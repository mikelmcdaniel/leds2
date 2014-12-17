import collections
import itertools
import time
import random

import led_controller
import weather
import presets

def time_memoized(check_interval):
  next_update_time = collections.defaultdict(int)
  last_result = {}
  def time_memoizer(func):
    def time_memoized(*args):
      if time.time() >= next_update_time[args]:
        last_result[args] = func(*args)
        next_update_time[args] = time.time() + check_interval
      return last_result[args]
    return time_memoized
  return time_memoizer

class Sun(object):
  def __init__(self):
    self.pos = None
    self.width = None
    self.x = 86400 / 4

  @time_memoized(3600)
  def get_sunrise_sunset(self):
    return weather.get_sun_info()

  def iterate(self):
    self.x += 100
    sunrise, sunset = self.get_sunrise_sunset()
    pos = weather.get_sun_position(self.x, sunrise, sunset)
    if pos is None:
      self.pos = 0.0  # arbitrary value
      self.width = 0.0
    else:
      self.pos = pos
      # Width starts and ends at 5, and is 10 at noon.
      self.width = 5.0 + abs(pos - 0.5) * 10

  def draw(self, leds):
    pos = leds.num_leds * (0.9 + self.pos * 0.5)
    leds.pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(200, 200, 0))

class Cloud(object):
  def __init__(self):
    self.pos = random.random()
    # Velocity should make it take 1-3 minutes to cycle around led strip
    # given 20fps
    self.velocity = 1.0 / 1200 + 1.0 / 2400 * random.random()
    self.width = 6 + 18 * random.random()

  def iterate(self):
    self.pos = (self.pos + self.velocity) % 1.0

  def draw(self, leds):
    pos = leds.num_leds * self.pos
    leds.pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(60, 60, 60))


class RainDrop(object):
  def __init__(self):
    self.pos = None
    self.width = 0
    self.fade_rate = 0.9 + 0.05 * random.random()

  def iterate(self):
    self.width *= self.fade_rate
    if self.width < 0.2:
      self.pos = random.random()
      self.width = 1

  def draw(self, leds):
    pos = leds.num_leds * self.pos
    leds.pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(0, 0, 255))

class WeatherPreset(presets.Preset):
  def __init__(self, name='Weather'):
    super(WeatherPreset, self).__init__(name)
    self.sun = Sun()
    self.clouds = [Cloud() for _ in xrange(10)]
    self.rain_drops = [RainDrop() for _ in xrange(100)]

  # TODO: Update this asynchronously.
  @time_memoized(30 * 60)
  def get_weather(self):
    return weather.get_weather()

  def draw(self, leds):
    weather = self.get_weather()
    if weather.is_sunny:
      sky_color = led_controller.RGB(30, 30, 100)
    else:
      sky_color = led_controller.RGB(20, 20, 20)
    for j in xrange(leds.num_leds):
      leds.pixels[j] = sky_color
    self.sun.iterate()
    self.sun.draw(leds)
    if weather.is_rainy:
      for rain_drop in itertools.islice(self.rain_drops, 0, int(weather.is_rainy * len(self.rain_drops))):
        rain_drop.iterate()
        rain_drop.draw(leds)
    weather.is_cloudy = 0.5
    if weather.is_cloudy:
      for cloud in itertools.islice(self.clouds, 0, int(weather.is_cloudy * len(self.clouds))):
        cloud.iterate()
        cloud.draw(leds)


presets.PRESET_CLASSES.append(WeatherPreset)

