from sys import argv, exit
from time import sleep
import serial

import config
import led_controller
import presets
import presets.attributes
import presets.weather_presets
import presets.cars_presets

from flask import Flask, request, redirect, render_template, url_for, Response, send_file
app = Flask(__name__)

USB_FILE_NAME = config.config['usb_file_name']
NUM_LEDS = config.config['num_leds']

PRESETS = []
COLORS = (
  ('red', 'ff0000'),
  ('orange', 'ff1900'),
  ('yellow', 'ff5500'),
  ('green', '00ff00'),
  ('teal', '00ff88'),
  ('blue', '0000ff'),
  ('purple', 'ff00bb'),
  ('gray', '7f7f7f'),
  ('mellow', 'ee3311'),
)

@app.route('/', methods=['POST', 'GET'])
def main():
  preset = request.args.get('preset', '')
  if preset:
    set_preset(preset)

  cur_presets = LEDS.cur_presets
  if cur_presets:
    for cur_preset in cur_presets:
      for key, val in request.args.iteritems():
        key = presets.attributes.decoded_html_name(key)
        if key in cur_preset.attributes:
          cur_preset.attributes[key].set_val(val)
      cur_preset.draw(LEDS, 0.0)
    LEDS.flush()

    selectors_html = ''.join(
      '<form action="" method="get">{}</form>'.format(a.selector_html())
      for cur_preset in cur_presets
      for a in cur_preset.attributes.itervalues())
  else:
    selectors_html = ''

  return render_template(
    'main.html', presets=PRESETS,
    host_url=request.url_root, led_colors=get_colors_html(),
    selectors_html=selectors_html)


@app.route('/favicon.ico')
def favicon():
  return send_file('static/favicon.ico', mimetype='image/x-icon')

@app.route('/preset/<preset>')
def set_preset(preset):
  preset = preset.split(',')
  LEDS.set_presets(preset)
  return Response('ok', mimetype='text/plain')

@app.route('/custom/<colors>')
def custom_colors(colors='ff000000ff000000ff'):
  num_colors = len(colors) / 6
  assert num_colors <= NUM_LEDS
  LEDS.set_preset(None)
  LEDS.default_color = led_controller.parse_rgb(colors[0:6])
  for j in xrange(num_colors):
    LEDS.pixels[j] = led_controller.parse_rgb(colors[j * 6:j * 6 + 6])
  for j in xrange(num_colors, NUM_LEDS):
    LEDS.pixels[j] = LEDS.pixels[j % num_colors]
  LEDS.flush()
  return Response('ok', mimetype='text/plain')

@app.route('/set_color/<offset>/<color>')
def set_color(offset='0', color='ff0000'):
  offset = int(offset)
  assert offset >= 0
  assert offset < LEDS.num_leds
  LEDS.pixels[offset] = led_controller.parse_rgb(color)
  LEDS.flush()
  return Response('ok', mimetype='text/plain')

@app.route('/get_colors')
def get_colors():
  return Response(' '.join(LEDS.get_colors()), mimetype='text/plain')

@app.route('/get_colors_html')
def get_colors_html():
  html = []
  for color in LEDS.get_colors():
    html.append('<span style="background:#{color}">&nbsp;&nbsp;&nbsp;&nbsp;</span>'.format(color=color))
  return Response('\n'.join(html), mimetype='text/plain')

@app.route('/help')
def help():
  help_msg = '''The following endpoints are supported URLs (regex):
<site>/preset/[0-8]
Starts one of the preset programs.

<site>/custom/([0-9a-z]{6})+
Sets all the colors by repeating the html-color codes.
ex: <site>/custom/ff00000000ff sets all leds to red, blue, red, blue, etc.

<site>/set_color/[0-9]+/[0-9a-z]{6}
Set a specific led color according to an html-color code

<site>/get_colors
Returns a list of space-delimited html-color codes representing the current colors of all the leds.

<site>/get_colors_html
Returns a pretty HTML version of <site>/get_colors.

<site>/reset
Reset the LED controller.

<site>/ping
Returns "ok".  This is used for debugging/probing.

<site>/quit
Quits the server (calls exit(0)).
'''
  return Response(help_msg, mimetype='text/plain')

@app.route('/reset')
def reset():
  LEDS.reset()
  return Response('ok', mimetype='text/plain')

@app.route('/ping')
def ping():
  return Response('ok', mimetype='text/plain')

@app.route('/quit')
def quit():
  exit(0)
  return Response('ok', mimetype='text/plain')


if __name__ == '__main__':
  if len(argv) <= 1 or argv[1] not in ('prod', 'debug'):
    print 'Usage: python {} (prod|debug)'.format(argv[0])
    exit(1)
  elif argv[1] == 'prod':
    config.config['debug'] = False
    LEDS = led_controller.Leds(USB_FILE_NAME, NUM_LEDS)
  elif argv[1] == 'debug':
    config.config['debug'] = True
    LEDS = led_controller.FakeLeds(NUM_LEDS)
  for preset in presets.PRESETS:
    LEDS.register_preset(preset)
    PRESETS.append((preset.name, preset.name))
  set_preset('Cars')
  app.run(host='0.0.0.0', port=5000, debug=config.config['debug'], use_reloader=False)
