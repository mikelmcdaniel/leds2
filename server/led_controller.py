import itertools
import math
import random
import serial
import threading
import time

import config
import colors

parse_rgb = colors.parse_rgb
RGB = colors.RGB


class PresetLedThread(threading.Thread):
  def __init__(self, leds):
    super(PresetLedThread, self).__init__()
    self.leds = leds
    self.next_update_time = 0
    self.enabled = True

  def post_update(self):
    self.next_update_time = 0

  def set_enabled(self, enabled):
    self.enabled = enabled

  # TODO Make this thread re-spawn if it dies.
  def run(self):
    while True:
      cur_presets = self.leds.cur_presets
      if cur_presets:
        seconds_per_frame = min(
          cur_preset.seconds_per_frame for cur_preset in cur_presets)
        try:
          while self.next_update_time > time.time():
            time.sleep(min(self.next_update_time - time.time(), 0.2))
        except IOError as e:
          if e.errno != 22:  # 22 -> "Invalid Argument"
            raise e
          # Tried to sleep for negative seconds.
        self.next_update_time = (time.time() + seconds_per_frame)
        if self.enabled:
          for cur_preset in cur_presets:
            cur_preset.draw(self.leds, seconds_per_frame)
          self.leds.flush()
      else:
        time.sleep(0.2)

class Pixels(list):
  def __init__(self, num_pixels, default_color=RGB(0xee, 0x33, 0x11)):
    super(Pixels, self).__init__()
    self.extend(default_color for _ in xrange(num_pixels))

  def draw_line(self, start, stop, rgba):
    if start > stop:
      start, stop = stop, start
    start, stop = start % len(self), stop % len(self)
    if stop == 0:
      stop = len(self)
    if start > stop:
      self.draw_line(0, stop, rgba)
      self.draw_line(start, len(self), rgba)
      return
    istart, istop = int(start), int(stop)
    if istart == istop:
      self[istart] = self[istart].mixed(rgba, stop - start)
    else:  # istop > istart
      # first pixel
      self[istart] = self[istart].mixed(rgba, 1 + math.floor(start) - start)
      # middle pixel(s)
      for j in xrange(istart + 1, istop):
        self[j] = self[j].mixed(rgba, 1.0)
      # last pixel
      if istop < len(self):
        alpha = stop - istop
        if alpha > 0:
          self[istop] = self[istop].mixed(rgba, alpha)

# TODO Add locking
class BaseLeds(object):
  def __init__(self, num_leds, default_color=RGB(127, 127, 127)):
    self.num_leds = num_leds
    self.pixels = Pixels(num_leds, default_color)
    self.default_color = default_color
    self.presets = {}
    self.cur_presets = []
    self.preset_thread = PresetLedThread(self)
    self.preset_thread.daemon = True
    self.preset_thread.start()
    self._last_colors = ['%02x%02x%02x' % (p.r, p.g, p.b) for p in self.pixels]
    self.turned_on = False

  def set_presets(self, preset_names):
    self.cur_presets = [self.presets[pn] for pn in preset_names]
    self.preset_thread.post_update()

  def set_preset(self, preset_name):
    "Start a preset (preprogrammed) pattern."
    if preset_name is None:
      self.set_presets([])
    else:
      self.set_presets([preset_name])

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

  def set_power(self, turned_on):
    self.preset_thread.set_enabled(turned_on)
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
    self.usb.write(''.join(msg))
    self.usb.flush()
    if self.turned_on:
      self.flush()

class FakeLeds(BaseLeds):
  pass
