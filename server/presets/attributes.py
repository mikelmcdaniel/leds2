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

  def set_val(self, v):
    assert isinstance(v, basestring)
    v = self.parser(v)
    self.checker(v)
    self.val = v

  def selector_html(self, html_name=None):
    if html_name is None: html_name = self.name
    return '<input type="text" name="{name}" value="{val}" onchange="this.form.submit()"></input>'.format(
      name=encoded_html_name(self.name), val=self.val)


class IntAttribute(Attribute):
  def __init__(self, name, *args, **kwargs):
    super(IntAttribute, self).__init__(name, parser=int, *args, **kwargs)


class ColorAttribute(Attribute):
  def __init__(self, name, default_val=colors.RGB(0xcc, 0x45, 0x18), *args, **kwargs):
    super(ColorAttribute, self).__init__(
      name, default_val=default_val, parser=colors.parse_color,
      *args, **kwargs)

  def selector_html(self, html_name=None):
    if html_name is None: html_name = self.name
    return '<input type="color" name="{name}" value="#{val}" defaultValue="#{val}" onchange="this.form.submit()"></input>'.format(
      name=encoded_html_name(self.name), val=self.val.html_color_code())

