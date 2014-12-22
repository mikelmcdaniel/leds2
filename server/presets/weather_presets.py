import collections
import itertools
import math
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

  @time_memoized(3600)
  def get_sunrise_sunset(self):
    return weather.get_sun_info()

  def _iterate(self, seconds_past):
    sunrise, sunset = self.get_sunrise_sunset()
    pos = weather.get_sun_position(weather.get_seconds(), sunrise, sunset)
    if pos is None:
      self.pos = 0.0  # arbitrary value
      self.width = 0.0
    else:
      self.pos = pos
      # Width starts and ends at 5, and is 10 at noon.
      self.width = 5.0 + abs(pos - 0.5) * 10

  def draw(self, leds, seconds_past):
    self._iterate(seconds_past)
    pos = leds.num_leds * (0.9 + self.pos * 0.5)
    leds.pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(200, 200, 0))

class Cloud(object):
  def __init__(self):
    self.pos = random.random()
    # Velocity should make it take 1-3 minutes to cycle around led strip
    # given 20fps
    self.velocity = 1.0 / 120 + 1.0 / 240 * random.random()
    self.width = 6 + 18 * random.random()

  def draw(self, leds, seconds_past):
    self.pos = (self.pos + self.velocity * seconds_past) % 1.0
    pos = leds.num_leds * self.pos
    leds.pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(80, 80, 80))


class RainDrop(object):
  def __init__(self):
    self.pos = None
    self.width = 0
    self.fade_rate = 0.9 + 0.05 * random.random()

  def _iterate(self, seconds_past):
    self.width *= self.fade_rate**seconds_past
    if self.width < 0.2:
      self.pos = random.random()
      self.width = 1

  def draw(self, leds, seconds_past):
    self._iterate(seconds_past)
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

  def draw(self, leds, seconds_past):
    weather = self.get_weather()
    if weather.is_sunny:
      sky_color = led_controller.RGB(30, 30, 100)
    else:
      sky_color = led_controller.RGB(20, 20, 20)
    for j in xrange(leds.num_leds):
      leds.pixels[j] = sky_color
    self.sun.draw(leds, seconds_past)
    if weather.is_rainy:
      for rain_drop in itertools.islice(self.rain_drops, 0, int(weather.is_rainy * len(self.rain_drops))):
        rain_drop.draw(leds, seconds_past)
    weather.is_cloudy = 0.5
    if weather.is_cloudy:
      for cloud in itertools.islice(self.clouds, 0, int(weather.is_cloudy * len(self.clouds))):
        cloud.draw(leds, seconds_past)


presets.PRESETS.append(WeatherPreset())

