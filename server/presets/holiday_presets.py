import attributes
import itertools
import time
import colors
import random
import presets


RGB = colors.RGB

def sign(x):
  if x > 0:
    return 1
  elif x < 0:
    return -1
  return 0

class Mistletoe(object):
  def __init__(self):
    self.ttl = 0
    self.pos = 0
    self.desired_pos = None
    self.color = None

  def draw(self, pixels, seconds_past):
    if time.time() > self.ttl:
      self.ttl = time.time() + random.randint(10, 3 * 60)
      self.desired_pos = int(random.random() * len(pixels)) + 0.5
      self.berry_color = RGB(255, 0, 0) if random.random() > 0.5 else RGB(200, 200, 200)

    diff = self.desired_pos - self.pos
    velocity = 1.5
    # Move in the direction of the desired_pos, but not past it.
    self.pos += sign(diff) * velocity if abs(diff) > velocity else diff

    pixels.draw_line(self.pos - 1.5, self.pos + 1.5, RGB(0, 180, 0))
    pixels.draw_line(self.pos - 0.5, self.pos + 0.5, self.berry_color)

class MistletoePreset(presets.Preset):
  def __init__(self, name='Mistletoe', seconds_per_frame=0.05):
    super(MistletoePreset, self).__init__(name, seconds_per_frame)
    self.mistletoes = []
    self.num_mistletoes = attributes.IntAttribute('num_mistletoes', 2)
    self.attributes['num_mistletoes'] = self.num_mistletoes

  def draw(self, pixels, seconds_past):
    self.mistletoes.extend(
      Mistletoe()
      for _ in xrange(self.num_mistletoes.val - len(self.mistletoes)))
    for m in itertools.islice(self.mistletoes, 0, self.num_mistletoes.val):
      m.draw(pixels, seconds_past)

presets.PRESETS.append(MistletoePreset())


class XmasPreset(presets.Preset):
  def __init__(self, name='Xmas', seconds_per_frame=300.0, *args, **kwargs):
    super(XmasPreset, self).__init__(
      name=name, seconds_per_frame=seconds_per_frame,
      *args, **kwargs)

  def draw(self, pixels, seconds_past):
    for j in xrange(0, len(pixels), 2):
      pixels[j] = RGB(255, 0, 0)
    for j in xrange(1, len(pixels), 2):
      pixels[j] = RGB(0, 255, 0)

presets.PRESETS.append(XmasPreset())
