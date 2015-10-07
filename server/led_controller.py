"""This class represents LEDs, including their buffered and actual states."""

import itertools
import math
import random
import serial
import StringIO
import threading
import time

import config
import colors
import pixels


parse_rgb = colors.parse_rgb


class BaseLeds(object):
  def __init__(self, num_leds, default_color=colors.RGB(127, 127, 127)):
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
    self.pixels = pixels.Pixels(len(self.pixels), self.default_color)

  def set_power(self, turned_on):
    self.turned_on = turned_on


class Leds(BaseLeds):
  __CHECK_SUM_BYTES = [2, 3, 5, 7, 11, 13, 17, 19]
  def __init__(self, usb_device_file, num_leds, **kwargs):
    super(Leds, self).__init__(num_leds=num_leds, **kwargs)
    self.usb_device_file = usb_device_file
    self._init_usb()
    self.next_update_time = 0
    self._half_reversed = config.config['half_reversed']
    self._lock = threading.Lock()

  def _init_usb(self):
    # writeTimeout=0 makes the flush() operation asynchronous.
    self.usb = serial.Serial(
      port=self.usb_device_file, baudrate=115200, timeout=100, writeTimeout=0)

  def _write_data(self, msg):
    check_sum = sum((j + 1) * ord(c) * self.__CHECK_SUM_BYTES[j % 8]
                    for j, c in enumerate(msg))
    parts = ['YNC']
    parts.append(msg)
    parts.append(chr(check_sum % 256))
    parts.append(chr(check_sum / 256 % 256))
    parts.append('S')
    msg_data = ''.join(parts)
    with self._lock:
      # Force a delay if necessary since the Arduino can only handle a
      # certain bandwidth.
      delay_time = self.next_update_time - time.time()
      if delay_time > 0:
        time.sleep(delay_time)
      self.usb.write(msg_data)
      self.usb.flush()
      self.next_update_time = time.time() + 0.005

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
    # Remove accidental occurences of 'YNC' to avoid SYNCing issues
    msg = ''.join(msg).replace('YNC', 'XMB')
    self._write_data(msg)

  def reset(self):
    super(Leds, self).reset()
    with self._lock:
      self.usb.close()
      self._init_usb()

  def set_power(self, turned_on):
    super(Leds, self).set_power(turned_on)
    msg = ['YNCP']
    msg.append('1' if turned_on else '0')
    msg.append('-' * (len(self.pixels) * 3 - len('YNCP') - len('0')))
    msg = ''.join(msg)
    self._write_data(msg)
    if self.turned_on:
      self.flush()


class FakeLeds(Leds):
  def __init__(self, num_leds, **kwargs):
    super(FakeLeds, self).__init__(
      usb_device_file='fake_leds_{}'.format(id(self)),
      num_leds=num_leds, **kwargs)

  def _init_usb(self):
    self.usb = StringIO.StringIO()

  def _write_data(self, msg):
    super(FakeLeds, self)._write_data(msg)
    self.usb.truncate(0)
