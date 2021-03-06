import colors


def encoded_html_name(name):
  return name


def decoded_html_name(name):
  return name


class Attribute(object):
  def __init__(self, name, default_val='', parser=str, checker=lambda x: ()):
    self.name = name
    self.parser = parser
    self.checker = checker
    self.val = default_val
    self.raw_val = str(default_val)

  def set_val(self, raw):
    assert isinstance(raw, basestring)
    v = self.parser(raw)
    self.checker(v)
    self.val, self.raw_val = v, raw

  def selector_html(self, html_name=None):
    if html_name is None: html_name = self.name
    return '<input type="text" name="{name}" value="{val}" onchange="this.form.submit()"></input>'.format(
      name=encoded_html_name(self.name), val=self.val)


class StrAttribute(Attribute):
  pass


class IntAttribute(Attribute):
  def __init__(self, name, *args, **kwargs):
    super(IntAttribute, self).__init__(name, parser=int, *args, **kwargs)


class FloatAttribute(Attribute):
  def __init__(self, name, *args, **kwargs):
    super(FloatAttribute, self).__init__(name, parser=float, *args, **kwargs)


class ColorAttribute(Attribute):
  def __init__(self, name, default_val=colors.RGB(0xcc, 0x45, 0x18), *args, **kwargs):
    super(ColorAttribute, self).__init__(
      name, default_val=default_val, parser=colors.parse_color,
      *args, **kwargs)

  def selector_html(self, html_name=None):
    if html_name is None: html_name = self.name
    return '<input type="color" name="{name}" value="#{val}" defaultValue="#{val}" onchange="this.form.submit()"></input>'.format(
      name=encoded_html_name(self.name), val=self.val.html_color_code())


class TimeAttribute(Attribute):
  @staticmethod
  def parse_time(string):
    parts = string.split(':', 1)
    assert len(parts) == 2
    hours = int(parts[0])
    minutes = int(parts[1])
    return hours, minutes

  def __init__(self, name, default_val=(0, 0), *args, **kwargs):
    super(TimeAttribute, self).__init__(
      name, default_val=default_val, parser=TimeAttribute.parse_time,
      *args, **kwargs)

  def selector_html(self, html_name=None):
    if html_name is None: html_name = self.name
    return '<input type="time" name="{name}" value="{val}" onfocusout="if (this.value != \'{val}\') this.form.submit();"></input>'.format(
      name=encoded_html_name(self.name),
      val='{:02d}:{:02d}'.format(*self.val))

