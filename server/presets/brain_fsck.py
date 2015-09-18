import random

import colors
import presets
from  presets import attributes


RGBA = colors.RGBA


def rainbow_color(n, alpha=1):
  n = int(n)
  if n <  256: return RGBA(255, n, 0, alpha)
  if n <  512: return RGBA(255 - (n - 256), 255, 0, alpha)
  if n <  768: return RGBA(0, 255, (n - 512), alpha)
  if n < 1024: return RGBA(0, 255 - (n - 768), 255, alpha)
  if n < 1280: return RGBA((n - 1024),0 , 255, alpha)
  if n < 1536: return RGBA(255, 0, 255 - (n - 1280), alpha)
  return rainbow_color(n % 1536, alpha)


BF_HELLO_WORLD = (
  '++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.'
  '+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.')


class BrainFsckPreset(presets.Preset):
  def __init__(self, name='Brain Fsck', seconds_per_frame=0.1):
    super(BrainFsckPreset, self).__init__(
      name=name, seconds_per_frame=seconds_per_frame)
    self.code = attributes.StrAttribute('code', BF_HELLO_WORLD)
    self.attributes['code'] = self.code
    self.ops_per_sec = attributes.FloatAttribute('ops_per_sec', 10.0)
    self.attributes['ops_per_sec'] = self.ops_per_sec
    self.num_pending_ops = 0

    self.bf_mem = []
    self.bf_pointer = 0
    self.bf_instr_pointer = 0

  def iterate(self, pixels):
    code = self.code.val
    instr = code[self.bf_instr_pointer % len(code)]
    if instr == '[':
      if self.bf_mem[self.bf_pointer]:
        pass  # enter the loop body
      else:
        paren_balance = 1
        # set j to the place with the matching brace
        # or len(code) - 1 if there isn't one
        for j in xrange(self.bf_instr_pointer + 1, len(code)):
          if code[j] == '[':
            paren_balance += 1
          elif code[j] == ']':
            paren_balance -= 1
          if paren_balance == 0:
            break
        self.bf_instr_pointer = j
    elif instr == ']':
      paren_balance = -1
      # set j to the place with the matching brace minus 1
      # or -1 if there isn't one
      for j in xrange(self.bf_instr_pointer - 1, -1, -1):
        if code[j] == '[':
          paren_balance += 1
        elif code[j] == ']':
          paren_balance -= 1
        if paren_balance == 0:
          break
      self.bf_instr_pointer = j - 1
    elif instr == '+':
      self.bf_mem[self.bf_pointer] += 1
      self.bf_mem[self.bf_pointer] %= 256
    elif instr == '-':
      self.bf_mem[self.bf_pointer] -= 1
      self.bf_mem[self.bf_pointer] %= 256
    elif instr == '>':
      self.bf_pointer += 1
      self.bf_pointer %= len(self.bf_mem)
    elif instr == '<':
      self.bf_pointer -= 1
      self.bf_pointer %= len(self.bf_mem)
    self.bf_instr_pointer = (self.bf_instr_pointer + 1) % len(code)

  def draw(self, pixels, seconds_past):
    if len(self.bf_mem) < len(pixels):
      self.bf_mem.extend(0 for _ in xrange(len(pixels) - len(self.bf_mem)))
    self.num_pending_ops += seconds_past * self.ops_per_sec.val
    for _ in xrange(int(self.num_pending_ops)):
      self.iterate(pixels)
    for j in xrange(len(pixels)):
      k = j % len(self.bf_mem)
      if self.bf_mem[k]:
        pixels[j] = rainbow_color(self.bf_mem[k] * 6)
    pixels[self.bf_pointer % len(pixels)] = (
      pixels[self.bf_pointer % len(pixels)].mixed(RGBA(0, 0, 0), 0.3))
    self.num_pending_ops -= int(self.num_pending_ops)

presets.PRESETS.append(BrainFsckPreset())
