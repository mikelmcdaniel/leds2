import itertools
import math
import time

import numpy
import cv2

import colors
import presets
from presets import attributes

class CameraPreset(presets.Preset):
  def __init__(self, name='Camera'):
    super(CameraPreset, self).__init__(name)
    self._load_config()
    self.frame_ratio = 5
    self.camera = None
    self.width = None
    self.height = None
    self.masks = None
    self.mask_sums = None
    self.camera_num = attributes.IntAttribute('camera_num', 0)
    self.attributes['camera_num'] = self.camera_num


  def _load_config(self, config_file='camera_preset_config.txt'):
    try:
      numbers = map(float, open(config_file).read().split())
    except IOError:
      numbers = [0, 0, 0, 1, 1, 1, 1, 0]
    # top-left, top-right, bottom-right, bottom-left
    self.corners = numpy.array([[numbers[2 * j], numbers[2 * j + 1]] for j in xrange(4)])
    self.center = self.corners.mean(axis=0)

  def setup(self, num_pixels, **kwargs):
    super(CameraPreset, self).setup(num_pixels=num_pixels, **kwargs)
    self.camera = cv2.VideoCapture(self.camera_num.val)
    self.width = int(self.camera.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)) / self.frame_ratio
    self.height = int(self.camera.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)) / self.frame_ratio
    # Generate masks
    self.masks = []
    self.mask_sums = []
    center_x, center_y = self.center[0] * self.width, self.center[1] * self.height
    tau = 2 * math.pi
    half_pi = 0.5 * math.pi
    num_partitions = 40
    for j in xrange(num_partitions):
      mask = numpy.zeros((self.height, self.width)).astype(numpy.bool)
      for y in xrange(self.height):
        normalized_y = y - center_y
        for x in xrange(self.width):
          normalized_x = x - center_x
          partition_num = int(num_partitions * ((math.atan2(normalized_y, normalized_x) + half_pi) % tau) / tau)
          if partition_num == j:
            mask[y, x] = True
      self.masks.append(mask)
      mask_sum = max(mask.sum(), 1.0)
      print 'FOO', j, mask_sum
      self.mask_sums.append(mask_sum)

  def tear_down(self, **kwargs):
    super(CameraPreset, self).tear_down(**kwargs)
    self.camera.release()
    self.camera = None

  def get_frame(self):
    # Horrible timing hack to ensure that the frame you get is recent.
    # This is to get around the fact that frames are buffered and the FPS
    # and position-in-time metrics for the frames/camera aren't retrievable.
    max_captures = 10
    captures = 0
    capture_time = 0.0
    while capture_time < 0.05 and captures < max_captures:
      start = time.time()
      ret = self.camera.grab()
      capture_time = time.time() - start
      captures += 1
    ret, frame = self.camera.retrieve()
    assert ret
    frame = frame[::self.frame_ratio, ::self.frame_ratio]
    return frame.astype(numpy.float64) / 255

  def draw(self, pixels, seconds_past):
    frame = self.get_frame()
    line_len = float(len(pixels)) / len(self.masks)
    for j, (mask, mask_sum) in enumerate(itertools.izip(self.masks, self.mask_sums)):
      r = int(0.8 * 255 * (frame[:, :, 2] * mask).sum() / mask_sum)
      g = int(0.5 * 255 * (frame[:, :, 1] * mask).sum() / mask_sum)
      b = int(0.3 * 255 * (frame[:, :, 0] * mask).sum() / mask_sum)
      pixels.draw_line(j * line_len, (j + 1) * line_len, colors.RGB(r, g, b, 0.5))


presets.PRESETS.append(CameraPreset())
