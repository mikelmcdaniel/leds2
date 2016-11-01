import errno
import itertools
import socket
import struct
import time

import colors
import presets
from  presets import attributes


RGB = colors.RGB


class UDP(presets.Preset):
  def __init__(self, name='UDP'):
    super(UDP, self).__init__(name)
    self.colors = [RGB(127, 0, 0)]
    self.udp_port = attributes.IntAttribute('udp_port', 5001)
    self.attributes['udp_port'] = self.udp_port
    self._last_udp_port = None
    self._socket = None

  def _reinit_socket(self):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.01)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', self.udp_port.val))
    if self._socket is not None:
      self._socket.close()
    self._socket = sock

  def _maybe_update_colors(self):
    try:
      data = self._socket.recv(4096)
    except socket.timeout:
      return
    except socket.error as e:
      if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
        return
      else:
        raise e
    # TODO: log this every log(n) for malformed data
    if data and len(data) >= 4:
      version, num_colors = struct.unpack_from('<HH', data[0:4])
      if version == 1:
        if len(data) == 4 + 3 * num_colors:
          colors_ = [RGB(*struct.unpack_from('<BBB', data[j:j+3]))
                     for j in xrange(4, 4 + num_colors * 3, 3)]
          self.colors = colors_

  def draw(self, pixels, unused_seconds_past):
    if self.udp_port.val != self._last_udp_port:
      self._reinit_socket()
    self._maybe_update_colors()
    num_colors = len(self.colors)
    for j in xrange(len(pixels)):
      pixels[j] = self.colors[j % num_colors]

presets.PRESETS.append(UDP())


