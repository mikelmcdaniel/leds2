from sys import argv, exit
from time import sleep
import serial

import config
import led_controller
import presets
import presets.attributes
import presets.all_presets

from flask import Flask, request, redirect, render_template, url_for, Response, send_file
app = Flask(__name__)

USB_FILE_NAME = config.config['usb_file_name']
NUM_LEDS = config.config['num_leds']

PRESETS = []

@app.route('/', methods=['POST', 'GET'])
def main():
  preset_list = request.args.get('presets', '')
  if preset_list:
    set_presets(preset_list)

  turned_on = request.args.get('set_power', '')
  if turned_on:
    set_power(turned_on)

  for preset in presets.PRESETS:
    for key, val in request.args.iteritems():
      key = presets.attributes.decoded_html_name(key)
      if key in preset.attributes:
        preset.attributes[key].set_val(val)

  selectors_html = []
  cur_preset_names = [preset.name for preset in LEDS.cur_presets]
  for preset in presets.PRESETS:
    new_preset_names = list(cur_preset_names)
    if preset.name in cur_preset_names:
      checked = 'checked'
      new_preset_names.remove(preset.name)
    else:
      checked = ''
      new_preset_names.append(preset.name)
    new_preset_names = ','.join(new_preset_names)
    selectors_html.append('<div>\n')
    selectors_html.append(preset.name)
    selectors_html.append('\t<form action="" method="get"><input type="checkbox" name="presets" autofocus value="{new_presets}" {checked} onchange="this.checked=true; this.form.submit()"></input></form>\n'.format(new_presets=new_preset_names, checked=checked))
    for a in preset.attributes.itervalues():
      selectors_html.append('\t<form action="" method="get">{}</form>\n'.format(a.selector_html()))
    selectors_html.append('</div>\n')
  selectors_html = ''.join(selectors_html)

  return render_template(
    'main.html', presets=PRESETS,
    host_url=request.url_root, led_colors=get_colors_html(), turned_on=LEDS.turned_on,
    selectors_html=selectors_html)


@app.route('/favicon.ico')
def favicon():
  return send_file('static/favicon.ico', mimetype='image/x-icon')

@app.route('/set_power/<turned_on>')
def set_power(turned_on):
  turned_on = turned_on not in ('0', 0, False, 'off', 'false', 'False')
  LEDS.set_power(turned_on)
  return Response('ok', mimetype='text/plain')

@app.route('/presets/<presets>')
def set_presets(presets):
  presets = presets.replace('%2C', ',').split(',')
  LEDS.set_presets(presets)
  return Response('ok', mimetype='text/plain')

@app.route('/custom/<colors>')
def custom_colors(colors='ff000000ff000000ff'):
  num_colors = len(colors) / 6
  assert num_colors <= NUM_LEDS
  LEDS.set_presets(None)
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
<site>/presets/[A-Za-z ,]+
Starts one of the presets programs.

<site>/set_power/(on|off)
Set the power of the led strips to be on (1) or off (0).

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
    PRESETS.append(preset.name)
  set_presets('Solid Color,Cars')
  app.run(host='0.0.0.0', port=5000, debug=config.config['debug'], use_reloader=False)
