import time
import random

import led_controller
import weather
import presets

class Sun(object):
  def __init__(self):
    self.pos = None
    self.width = None
    self.x = 86400 / 4

  def iterate(self):
    self.x += 100
    pos = weather.get_sun_position(self.x)
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

class WeatherPreset(presets.Preset):
  def __init__(self, name='Weather'):
    super(WeatherPreset, self).__init__(name)
    self.sun = Sun()
    self._next_update_time = 0
    self._last_weather = None

  # TODO: Update this asynchronously.
  def get_weather(self):
    if time.time() >= self._next_update_time:
      self._last_weather = weather.get_weather()
      self._next_update_time = time.time() + (15 * 60) + 5 * random.random()
    return self._last_weather

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
      for _ in xrange(int(weather.is_rainy * leds.num_leds / 5)):
        leds.pixels[random.randint(0, leds.num_leds - 1)] = led_controller.RGB(0, 0, 200)


presets.PRESET_CLASSES.append(WeatherPreset)

