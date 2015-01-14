import itertools
import math
import random
import serial
import threading
import time

import config
import colors
import pixels

parse_rgb = colors.parse_rgb
RGB = colors.RGB



# TODO Add locking
class BaseLeds(object):
  def __init__(self, num_leds, default_color=RGB(127, 127, 127)):
    self.num_leds = num_leds
    self.pixels = pixels.Pixels(num_leds, default_color)
    self.default_color = default_color
    self._last_colors = ['%02x%02x%02x' % (p.r, p.g, p.b) for p in self.pixels]
    self.turned_on = False

  def get_colors(self):
    return self._last_colors

  def flush(self):
    "Send all buffered updates to the LEDs."
    self._last_colors = ['%02x%02x%02x' % (p.r, p.g, p.b) for p in self.pixels]

  def reset(self):
    "Reset (i.e. power-cycle) the LED controller."
    self.pixels = pixels.Pixels(self.num_leds, self.default_color)

  def set_power(self, turned_on):
    self.turned_on = turned_on

class Leds(BaseLeds):
  def __init__(self, usb_device_file, num_leds, *args, **kwargs):
    super(Leds, self).__init__(num_leds=num_leds, *args, **kwargs)
    self.usb_device_file = usb_device_file
    self._init_usb()
    self.last_update_time = 0
    self._half_reversed = config.config['half_reversed']

  def _init_usb(self):
    # writeTimeout=0 makes the flush() operation asynchronous.
    self.usb = serial.Serial(
      port=self.usb_device_file, baudrate=115200, timeout=100, writeTimeout=0)

  def flush(self):
    super(Leds, self).flush()
    msg = []
    if self._half_reversed:
      msg.extend(p.rgb_bytes() for p in itertools.islice(
          self.pixels, 0, len(self.pixels) / 2))
      msg.extend(self.pixels[j].rgb_bytes() for j in xrange(
          len(self.pixels) - 1, len(self.pixels) / 2 - 1, -1))
    else:
      msg.extend(p.rgb_bytes() for p in self.pixels)
    msg = ''.join(msg)
    # Remove any instances of 'YNC' that aren't used to sync.
    msg = msg.replace('YNC', 'YNB')
    msg = ''.join(('YNC', msg, 'S'))
    delay_time = self.last_update_time + 0.005 - time.time()
    if delay_time > 0:
      time.sleep(delay_time)
    self.usb.write(msg)
    self.usb.flush()
    self.last_update_time = time.time()

  def reset(self):
    super(Leds, self).reset()
    self.usb.close()
    self._init_usb()

  def set_power(self, turned_on):
    super(Leds, self).set_power(turned_on)
    msg = ['YNCYNCP']
    msg.append('1' if turned_on else '0')
    msg.append('-' * (len(self.pixels) * 3 + len('SYNC') - len('YNCYNCP') - len('0') - len('S')))
    msg.append('S')
    msg = ''.join(msg)
    delay_time = self.last_update_time + 0.005 - time.time()
    if delay_time > 0:
      time.sleep(delay_time)
    self.usb.write(''.join(msg))
    self.usb.flush()
    self.last_update_time = time.time()
    if self.turned_on:
      self.flush()

class FakeLeds(BaseLeds):
  pass
