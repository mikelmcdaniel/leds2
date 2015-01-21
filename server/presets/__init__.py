import led_controller
import attributes

# All presets should call PRESETS.append(PresetClassName())
PRESETS = []


class Preset(object):
  def __init__(self, name, seconds_per_frame=0.05):
    self.name = name
    self.seconds_per_frame = seconds_per_frame
    self.attributes = {}

  def __hash__(self):
    return hash(self.name)

  def __cmp__(self, other):
    return cmp(self.name, other.name)

  def setup(self, **kwargs):
    pass

  def tear_down(self, **kwargs):
    pass

  def draw(self, pixels, seconds_past):
    raise NotImplementedError()


class SolidColorPreset(Preset):
  def __init__(self, name='Solid Color', seconds_per_frame=300.0, *args, **kwargs):
    super(SolidColorPreset, self).__init__(
      name=name, seconds_per_frame=seconds_per_frame,
      *args, **kwargs)
    self.color = attributes.ColorAttribute('color')
    self.attributes['color'] = self.color

  def draw(self, pixels, seconds_past):
    for j in xrange(len(pixels)):
      pixels[j] = self.color.val

PRESETS.append(SolidColorPreset())
