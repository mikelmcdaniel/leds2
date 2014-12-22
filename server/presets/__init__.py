import led_controller

# All presets should call PRESETS.append(PresetClassName())
PRESETS = []


class Attribute(object):
  def __init__(self, name, default_val='', parser=str, checker=lambda x: ()):
    self.name = name
    self.parser = parser
    self.checker = checker
    self._val = None
    self.set_val(default_val)

  @property
  def val(self):
    return self._val

  @val.setter
  def val(self, v):
    assert isinstance(v, basestring)
    try:
      v = self.parser(v)
    except Exception as e:
      return str(e)
    error = self.checker(v)
    if error:
      return error
    self._val = v


class Preset(object):
  def __init__(self, name, seconds_per_frame=0.05):
    self.name = name
    self.seconds_per_frame = seconds_per_frame

  def draw(self, leds, seconds_past):
    raise NotImplementedError()


