import time
import threading

class PresetLedThread(threading.Thread):
  def __init__(self, leds):
    super(PresetLedThread, self).__init__()
    self.daemon = True
    self.leds = leds
    self.next_update_time = 0
    self.presets = {}
    self.cur_presets = []
    self.set_enabled(False)
    self.start()

  def post_update(self):
    self.next_update_time = 0

  def set_enabled(self, enabled):
    self.enabled = enabled

  def set_presets(self, preset_names):
    self.cur_presets = [self.presets[pn] for pn in preset_names]
    self.post_update()

  def register_preset(self, preset):
    assert preset.name not in self.presets
    self.presets[preset.name] = preset

  # TODO Make this thread re-spawn if it dies.
  def run(self):
    while True:
      cur_presets = self.cur_presets
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
        # If the cur_presets have changed underneath us, restart this iteration.
        if self.cur_presets != cur_presets: continue
        self.next_update_time = (time.time() + seconds_per_frame)
        if self.enabled:
          for cur_preset in cur_presets:
            cur_preset.draw(self.leds, seconds_per_frame)
          self.leds.flush()
      else:
        time.sleep(0.2)
