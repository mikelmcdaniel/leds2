import colors
import presets
from  presets import attributes

class Tint(presets.Preset):
  def __init__(self, name='Tint'):
    super(Tint, self).__init__(name)
    self.tint_color = attributes.ColorAttribute(
      'tint_color', colors.RGB(0xcc, 0x45, 0x18))
    self.attributes['tint_color'] = self.tint_color

  def draw(self, pixels, seconds_past):
    for j, c in enumerate(pixels):
      pixels[j] = colors.RGB(
        self.tint_color.val.r * c.r / 255,
        self.tint_color.val.g * c.g / 255,
        self.tint_color.val.b * c.b / 255)

presets.PRESETS.append(Tint())
