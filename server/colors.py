import config


def parse_color(color_str):
  color_str = color_str.strip('#').lower()
  assert len(color_str) == 6
  return RGB(*(int(color_str[j:j + 2], 16) for j in xrange(0, 6, 2)))


def parse_rgb(color_str):
  return parse_color(color_str)


class RGBA(object):
  def __init__(self, r, g, b, a=1.0):
    r = min(255, max(0, r))
    g = min(255, max(0, g))
    b = min(255, max(0, b))
    a = min(1, max(0, a))
    (self.r, self.g, self.b, self.a) = (r, g, b, a)

  def html_color_code(self):
    return '%02x%02x%02x' % (self.r, self.g, self.b)

  if config.config['rgb_order'] == 'grb':
    def rgb_bytes(self):
      return '{}{}{}'.format(chr(self.g), chr(self.r), chr(self.b))
  elif config.config['rgb_order'] == 'brg':
    def rgb_bytes(self):
      return '{}{}{}'.format(chr(self.b), chr(self.r), chr(self.g))
  else:
    raise Exception('rgb_order "{}" is not handled.'.format(config.config['rgb_order']))

  def mixed(self, other, alpha):
    alpha *= other.a
    return RGBA(
        int(alpha * other.r + (1 - alpha) * self.r),
        int(alpha * other.g + (1 - alpha) * self.g),
        int(alpha * other.b + (1 - alpha) * self.b),
        alpha)

RGB = RGBA
