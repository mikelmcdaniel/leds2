import itertools
import math
import random
import serial
import threading
import time

import config

def parse_rgb(rgb):
  return RGB(*(int(rgb[j:j + 2], 16) for j in xrange(0, 6, 2)))

class RGB(object):
  def __init__(self, r, g, b):
    r = min(255, max(0, r))
    g = min(255, max(0, g))
    b = min(255, max(0, b))
    (self.r, self.g, self.b) = (r, g, b)

  if config.config['rgb_order'] == 'grb':
    def rgb_bytes(self):
      return '{}{}{}'.format(chr(self.g), chr(self.r), chr(self.b))
  elif config.config['rgb_order'] == 'brg':
    def rgb_bytes(self):
      return '{}{}{}'.format(chr(self.b), chr(self.r), chr(self.g))
  else:
    raise Exception('rgb_order "{}" is not handled.'.format(config.config['rgb_order']))

  def mixed(self, other, alpha):
    return RGB(
        int(alpha * other.r + (1 - alpha) * self.r),
        int(alpha * other.g + (1 - alpha) * self.g),
        int(alpha * other.b + (1 - alpha) * self.b))


class PresetLedThread(threading.Thread):
  def __init__(self, leds):
    super(PresetLedThread, self).__init__()
    self.leds = leds
    self.next_update_time = 0

  # TODO Add proper locking; this triple-checking code is gross.
  # TODO Make this thread re-spawn if it dies.
  def run(self):
    while True:
      if self.leds.cur_preset is not None:
        try:
          time.sleep(self.next_update_time - time.time())
        except IOError as e:
          if e.errno != 22:  # 22 -> "Invalid Argument"
            raise e
          # Tried to sleep for negative seconds.
        if self.leds.cur_preset is not None:
          try:
            self.next_update_time = (
              time.time() + self.leds.cur_preset.seconds_per_frame)
            self.leds.cur_preset.draw(
                self.leds, self.leds.cur_preset.seconds_per_frame)
            self.leds.flush()
          except AttributeError as e:
            if self.leds.cur_preset is not None:
              raise e
      else:
        time.sleep(0.2)

class Pixels(list):
  def __init__(self, num_pixels, default_color=RGB(0xee, 0x33, 0x11)):
    super(Pixels, self).__init__()
    self.extend(default_color for _ in xrange(num_pixels))

  def draw_line(self, start, stop, rgb):
    if start > stop:
      start, stop = stop, start
    start, stop = start % len(self), stop % len(self)
    if stop == 0:
      stop = len(self)
    if start > stop:
      self.draw_line(0, stop, rgb)
      self.draw_line(start, len(self), rgb)
      return
    istart, istop = int(start), int(stop)
    if istart == istop:
      self[istart] = self[istart].mixed(rgb, stop - start)
    else:  # istop > istart
      # first pixel
      self[istart] = self[istart].mixed(rgb, 1 + math.floor(start) - start)
      # middle pixel(s)
      for j in xrange(istart + 1, istop):
        self[j] = rgb
      # last pixel
      if istop < len(self):
        alpha = stop - istop
        if alpha > 0:
          self[istop] = self[istop].mixed(rgb, alpha)

# TODO: Add locking
class BaseLeds(object):
  def __init__(self, num_leds, default_color=RGB(127, 127, 127)):
    self.num_leds = num_leds
    self.pixels = Pixels(num_leds, default_color)
    self.default_color = default_color
    self.presets = {}
    self.cur_preset = None
    self.preset_thread = PresetLedThread(self)
    self.preset_thread.daemon = True
    self.preset_thread.start()
    self._last_colors = ['%02x%02x%02x' % (p.r, p.g, p.b) for p in self.pixels]

  def set_preset(self, preset_name):
    "Start a preset (preprogrammed) pattern."
    if preset_name is None:
      self.cur_preset = None
    else:
      self.cur_preset = self.presets[preset_name]

  def register_preset(self, preset):
    assert preset.name not in self.presets
    self.presets[preset.name] = preset

  def get_colors(self):
    return self._last_colors

  def flush(self):
    "Send all buffered updates to the LEDs."
    self._last_colors = ['%02x%02x%02x' % (p.r, p.g, p.b) for p in self.pixels]

  def reset(self):
    "Reset (i.e. power-cycle) the LED controller."
    self.pixels = Pixels(self.num_leds, self.default_color)


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
    msg = ['YNC']
    if self._half_reversed:
      msg.extend(p.rgb_bytes() for p in itertools.islice(
          self.pixels, 0, len(self.pixels) / 2))
      msg.extend(self.pixels[j].rgb_bytes() for j in xrange(
          len(self.pixels) - 1, len(self.pixels) / 2 - 1, -1))
    else:
      msg.extend(p.rgb_bytes() for p in self.pixels)
    msg.append('S')
    self.usb.write(''.join(msg))
    self.usb.flush()
    self.last_update_time = time.time()

  def reset(self):
    super(Leds, self).reset()
    self.usb.close()
    self._init_usb()


class FakeLeds(BaseLeds):
  pass
