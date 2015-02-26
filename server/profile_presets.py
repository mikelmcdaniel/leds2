import sys
import cProfile

import led_controller
import presets
import presets.all_presets

def run_preset(preset, num_iterations=10**4):
  leds = led_controller.FakeLeds(200)
  seconds_per_frame = preset.seconds_per_frame
  for _ in xrange(num_iterations):
    preset.draw(leds.pixels, seconds_per_frame)
  del leds

def profile_presets():
  global PRESET
  for preset in presets.PRESETS:
    PRESET = preset
    print '***', preset.name
    try:
      cProfile.run('run_preset(PRESET)')
    except Exception as e:
      print 'Exception:', e


def main(argv):
  profile_presets()

if __name__ == '__main__':
  main(sys.argv)
