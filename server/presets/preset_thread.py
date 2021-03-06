import time
import threading

class PresetLedThread(threading.Thread):
  def __init__(self, leds):
    super(PresetLedThread, self).__init__()
    self.daemon = True
    self.leds = leds
    self.last_update_time = 0
    self.next_update_time = 0
    self.presets = {}
    self.cur_presets = []
    self.set_enabled(False)
    self.start()

  def post_update(self):
    self.next_update_time = time.time()

  def set_enabled(self, enabled):
    self.enabled = enabled

  def set_presets(self, preset_names):
    last_presets = self.cur_presets
    cur_presets = [self.presets[pn] for pn in preset_names]
    for new_preset in set(cur_presets) - set(last_presets):
      new_preset.setup(num_pixels=len(self.leds.pixels))
    self.cur_presets = cur_presets
    for old_preset in set(last_presets) - set(cur_presets):
      old_preset.tear_down()
    self.post_update()

  def register_preset(self, preset):
    assert preset.name not in self.presets
    self.presets[preset.name] = preset

  # TODO Make this thread re-spawn if it dies.
  def run(self):
    while True:
      try:
        cur_presets = self.cur_presets
        if cur_presets and self.enabled:
          seconds_per_frame = min(
            cur_preset.seconds_per_frame for cur_preset in cur_presets)
          try:
            while self.next_update_time > time.time():
              time.sleep(min(self.next_update_time - time.time(), 0.2))
          except IOError as e:
            if e.errno != 22:  # 22 -> "Invalid Argument"
              raise e
            # Tried to sleep for negative seconds.
          # If the cur_presets have changed underneath us, restart this iteration.
          if self.cur_presets != cur_presets: continue
          now = time.time()
          self.next_update_time = (now + seconds_per_frame)
          if self.enabled:
            # Attempt to keep track of the number of seconds_past since the last
            # update.  However, bound it between 0 and 3 * seconds_per_frame.
            seconds_past = min(max(now - self.last_update_time, 0), 3 * seconds_per_frame)
            self.last_update_time = now
            for cur_preset in cur_presets:
              cur_preset.draw(self.leds.pixels, seconds_past)
            self.leds.flush()
        else:
          time.sleep(0.2)
      except Exception as e:
        print 'PRESET THREAD ERROR:', e
        time.sleep(5)

