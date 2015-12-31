import itertools
import math
import time

import colors
import random
import presets
from  presets import attributes


RGBA = colors.RGBA
BLACK = RGBA(0, 0, 0, 255)


def rainbow_color(n):
  alpha = 1
  n = int(n)
  if n <  256: return RGBA(255, n, 0, alpha)
  if n <  512: return RGBA(255 - (n - 256), 255, 0, alpha)
  if n <  768: return RGBA(0, 255, (n - 512), alpha)
  if n < 1024: return RGBA(0, 255 - (n - 768), 255, alpha)
  if n < 1280: return RGBA((n - 1024),0 , 255, alpha)
  if n < 1536: return RGBA(255, 0, 255 - (n - 1280), alpha)
  return rainbow_color(n % 1536)


class CountDown(presets.Preset):
  def __init__(self, name='CountDown'):
    super(CountDown, self).__init__(name)
    self.time = attributes.TimeAttribute('time')
    self.attributes['time'] = self.time
    self.offset = attributes.IntAttribute('offset', 0)
    self.attributes['offset'] = self.offset

  def draw(self, pixels, seconds_past):
    hours, minutes = self.time.val
    seconds = 60 * (60 * hours + minutes)
    local_seconds = time.time()
    local_time = time.localtime(local_seconds)
    local_seconds = (
      60 * (60 * local_time.tm_hour + local_time.tm_min) +
      local_time.tm_sec + local_seconds % 1.0)
    seconds_per_day = 86400
    seconds_left = (seconds + seconds_per_day - local_seconds) % seconds_per_day
    int_seconds_left = int(seconds_left)


    # special count down for last 10 seconds
    if seconds_left < 10:
      pixels.draw_line(0, len(pixels), RGBA(0, 0, 0, 1))  # make it black!
      section_len = float(len(pixels)) / 10
      section_progress = min(-seconds_left % 1.0 * 2, 1.0)
      for j in xrange(9 - int_seconds_left):
        pixels.draw_line(j * section_len, j * section_len + section_len,
                         rainbow_color(j * 1536 / 10))
      j = 9 - int_seconds_left
      pixels.draw_line(j * section_len, j * section_len + (section_progress) * section_len,
                       rainbow_color(j * 1536 / 10))
    elif seconds_left < 20:  # and seconds_left >= 10
      progress = 1.0 - (seconds_left - 10) / 10
      pixels.draw_line(0, len(pixels), RGBA(0, 0, 0, progress))  # fade to black
    elif seconds_left > seconds_per_day - 30:
      seconds_over = seconds_per_day - seconds_left
      progress = seconds_over / 30
      pixels.draw_line(0, len(pixels), RGBA(0, 0, 0, (1 - progress)**2))
      for _ in xrange(int(progress * 100)):
        i = random.randrange(len(pixels))
        pixels[i] = pixels[i].mixed(rainbow_color(random.randint(0, 1536)), 1 - progress)

    # draw binary count down
    num_bits = int(math.ceil(math.log(seconds_left + 1, 2)))
    offset = self.offset.val - 1
    if seconds_left < seconds_per_day - 3600:  # only draw countdown for < 23 hours
      for j in xrange(num_bits):
        if (1 << j) & int_seconds_left:
          pixels[offset - j] = rainbow_color(seconds_left * 5 + j * 1536.0 / 2)
        else:
          pixels[offset - j] = BLACK


presets.PRESETS.append(CountDown())








