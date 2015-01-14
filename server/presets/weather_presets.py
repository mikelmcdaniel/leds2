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

  def draw(self, pixels, seconds_past):
    self._iterate(seconds_past)
    pos = len(pixels) * (0.9 + self.pos * 0.35)
    pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(250, 180, 0))


class Moon(object):
  def __init__(self):
    self.pos = None
    self.width = None

  @time_memoized(3600)
  def get_moonrise_moonset(self):
    return weather.get_moon_info()

  def _iterate(self, seconds_past):
    moonrise, moonset = self.get_moonrise_moonset()
    pos = weather.get_moon_position(weather.get_seconds(), moonrise, moonset)
    if pos is None:
      self.pos = 0.0  # arbitrary value
      self.width = 0.0
    else:
      self.pos = pos
      self.width = 5.0

  def draw(self, pixels, seconds_past):
    self._iterate(seconds_past)
    pos = len(pixels) * (0.35 + self.pos * 0.45)
    pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(230, 230, 230))

class Cloud(object):
  def __init__(self):
    self.pos = random.random()
    # Velocity should make it take 1-3 minutes to cycle around led strip
    # given 20fps
    self.velocity = 1.0 / 120 + 1.0 / 240 * random.random()
    self.width = 6 + 18 * random.random()

  def draw(self, pixels, seconds_past):
    self.pos = (self.pos + self.velocity * seconds_past) % 1.0
    pos = len(pixels) * self.pos
    pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(80, 80, 80, 0.5))


class RainDrop(object):
  def __init__(self):
    self.pos = random.random()
    self.width = random.random()
    self.fade_rate = 0.2 + 0.1 * random.random()

  def _iterate(self, seconds_past):
    self.width *= self.fade_rate**seconds_past
    if self.width < 0.2:
      self.pos = random.random()
      self.width = 0.8

  def draw(self, pixels, seconds_past):
    self._iterate(seconds_past)
    pos = len(pixels) * self.pos
    pixels.draw_line(pos - self.width / 2, pos + self.width / 2, led_controller.RGB(0, 0, 255))

class WeatherPreset(presets.Preset):
  def __init__(self, name='Weather'):
    super(WeatherPreset, self).__init__(name)
    self.sun = Sun()
    self.moon = Moon()
    self.clouds = [Cloud() for _ in xrange(10)]
    self.rain_drops = [RainDrop() for _ in xrange(100)]

  # TODO: Update this asynchronously.
  @time_memoized(30 * 60)
  def get_weather(self):
    return weather.get_weather()

  def draw(self, pixels, seconds_past):
    weather = self.get_weather()
    self.sun.draw(pixels, seconds_past)
    self.moon.draw(pixels, seconds_past)
    if weather.is_cloudy:
      for cloud in itertools.islice(self.clouds, 0, int(weather.is_cloudy * len(self.clouds))):
        cloud.draw(pixels, seconds_past)
    if weather.is_rainy:
      for rain_drop in itertools.islice(self.rain_drops, 0, int(weather.is_rainy * len(self.rain_drops))):
        rain_drop.draw(pixels, seconds_past)


presets.PRESETS.append(WeatherPreset())

