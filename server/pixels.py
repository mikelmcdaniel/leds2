import colors

class Pixels(list):
  def __init__(self, num_pixels, default_color=colors.RGB(0xcc, 0x45, 0x18)):
    super(Pixels, self).__init__()
    self.extend(default_color for _ in xrange(num_pixels))

  def draw_line(self, start, stop, rgba):
    if start > stop:
      start, stop = stop, start
    start, stop = start % len(self), stop % len(self)
    if stop == 0:
      stop = len(self)
    if start > stop:
      self.draw_line(0, stop, rgba)
      self.draw_line(start, len(self), rgba)
      return
    istart, istop = int(start), int(stop)
    if istart == istop:
      self[istart] = self[istart].mixed(rgba, stop - start)
    else:  # istop > istart
      # first pixel
      self[istart] = self[istart].mixed(rgba, 1 + int(start) - start)
      # middle pixel(s)
      for j in xrange(istart + 1, istop):
        self[j] = self[j].mixed(rgba, 1.0)
      # last pixel
      if istop < len(self):
        alpha = stop - istop
        if alpha > 0:
          self[istop] = self[istop].mixed(rgba, alpha)
