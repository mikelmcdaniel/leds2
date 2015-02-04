import random

import colors
import presets
from  presets import attributes


RGBA = colors.RGBA


class FadePreset(presets.Preset):
  def __init__(self, name='Fade', seconds_per_frame=0.1):
    super(FadePreset, self).__init__(
      name=name, seconds_per_frame=seconds_per_frame)
    self.speed = attributes.FloatAttribute('speed', 10.0)
    self.attributes['speed'] = self.speed
    self.pending_updates = 0

  def draw(self, pixels, seconds_past):
    self.pending_updates += seconds_past * self.speed.val
    for _ in xrange(int(self.pending_updates)):
      j = random.randint(0, len(pixels) - 1)
      k = (j + 1) % len(pixels)
      diff = min(random.randint(10, 50), 255 - pixels[j].r, pixels[k].r)
      pixels[j].r += diff
      pixels[k].r -= diff
      diff = min(random.randint(10, 50), 255 - pixels[j].g, pixels[k].g)
      pixels[j].g += diff
      pixels[k].g -= diff
      diff = min(random.randint(10, 50), 255 - pixels[j].b, pixels[k].b)
      pixels[j].b += diff
      pixels[k].b -= diff
    self.pending_updates -= int(self.pending_updates)

presets.PRESETS.append(FadePreset())
