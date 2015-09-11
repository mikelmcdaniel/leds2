import json
import os
from sys import argv, exit
from time import sleep
import serial

import colors
import config
import led_controller
import presets
import presets.attributes
import presets.all_presets
import presets.preset_thread

from flask import Flask, request, redirect, render_template, url_for, Response, send_file
app = Flask(__name__)

class Globals(object):
  def __init__(self, debug):
    self.usb_file_name = config.config['usb_file_name']
    self.num_leds = config.config['num_leds']
    self.variables_save_file = os.path.expanduser(
      config.config.get('variables_save_file', '~/.leds2'))
    self.presets = []
    if debug:
      self.leds = led_controller.FakeLeds(self.num_leds)
    else:
      self.leds = led_controller.Leds(self.usb_file_name, self.num_leds)
    self.preset_thread = presets.preset_thread.PresetLedThread(self.leds)
    self.variables = {}

def set_preset_vars(presets, variables):
  for preset in presets:
    for key, raw_val in variables.iteritems():
      if key in preset.attributes and raw_val != preset.attributes[key].raw_val:
        preset.attributes[key].set_val(raw_val)

def get_preset_vars(presets):
  variables = {}
  for preset in presets:
    variables.update(preset.attributes)
  return variables

def set_global_vars(global_vars, presets, variables, variables_save_file):
  if any(val != global_vars.get(key) for key, val in variables.iteritems()):
    global_vars.update(variables)
    if presets:
      set_preset_vars(presets, variables)
    if variables.get('presets'):
      set_presets(variables['presets'])
    if variables.get('set_power'):
      set_power(variables['set_power'])
    vars_dump = json.dumps(global_vars)
    with open(variables_save_file, 'w') as f:
      f.write(vars_dump)

@app.route('/', methods=['POST', 'GET'])
def main():
  set_global_vars(
    GLOBALS.variables, presets.PRESETS,
    request.args,
    GLOBALS.variables_save_file)

  selectors_html = []
  cur_preset_names = [preset.name for preset in GLOBALS.preset_thread.cur_presets]
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

  rendered_html = render_template(
    'main.html', presets=GLOBALS.presets,
    host_url=request.url_root, led_colors=get_colors_html(), turned_on=GLOBALS.leds.turned_on,
    selectors_html=selectors_html)

  if request.args:
    GLOBALS.preset_thread.post_update()

  return rendered_html


@app.route('/favicon.ico')
def favicon():
  return send_file('static/favicon.ico', mimetype='image/x-icon')

@app.route('/set_power/<turned_on>')
def set_power(turned_on):
  set_global_vars(GLOBALS.variables, None, {'set_power': turned_on}, GLOBALS.variables_save_file)
  turned_on = turned_on not in ('0', 0, False, 'off', 'false', 'False')
  GLOBALS.preset_thread.set_enabled(turned_on)
  GLOBALS.leds.set_power(turned_on)
  return Response('ok', mimetype='text/plain')

@app.route('/toggle_power')
def toggle_power():
  return set_power(str(not GLOBALS.leds.turned_on))

@app.route('/presets/<presets>')
def set_presets(presets):
  set_global_vars(GLOBALS.variables, None, {'presets': presets}, GLOBALS.variables_save_file)
  presets = presets.replace('%2C', ',').split(',')
  GLOBALS.preset_thread.set_presets(presets)
  return Response('ok', mimetype='text/plain')

@app.route('/custom/<color_list>')
def custom(color_list):
  if GLOBALS.preset_thread.cur_presets:
    GLOBALS.preset_thread.set_presets([])
  color_list = color_list.lower()
  color_list = [
    colors.parse_rgb(color_list[j:j + 6])
    for j in xrange(0, len(color_list), 6)]
  for j in xrange(len(GLOBALS.leds.pixels)):
    GLOBALS.leds.pixels[j] = color_list[j % len(color_list)]
  GLOBALS.leds.flush()
  return Response('ok', mimetype='text/plain')

@app.route('/get_colors')
def get_colors():
  return Response(' '.join(GLOBALS.leds.get_colors()), mimetype='text/plain')

@app.route('/get_colors_html')
def get_colors_html():
  html = []
  for color in GLOBALS.leds.get_colors():
    html.append('<span style="background:#{color}">&nbsp;&nbsp;&nbsp;&nbsp;</span>'.format(color=color))
  return Response('\n'.join(html), mimetype='text/plain')

@app.route('/help')
def help():
  help_msg = '''The following endpoints are supported URLs (regex):
<site>/help
Display this help message.

<site>/presets/[A-Za-z ,]+
Starts one or more of the presets programs.

<site>/set_power/(on|off|true|false|True|False|1|0)
Set the power of the led strips to be on or off.

<site>/toggle_power
Toggles the power of the led strips to be on or off.

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
  GLOBALS.leds.reset()
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
  elif argv[1] == 'debug':
    config.config['debug'] = True
  GLOBALS = Globals(config.config['debug'])
  for preset in presets.PRESETS:
    GLOBALS.preset_thread.register_preset(preset)
    GLOBALS.presets.append(preset.name)
  try:
    with open(GLOBALS.variables_save_file, 'r') as f:
      variables = json.loads(f.read())
    set_global_vars(GLOBALS.variables, presets.PRESETS, variables, GLOBALS.variables_save_file)
  except IOError:
    set_presets('Solid Color,Cars')
  app.run(host='0.0.0.0', port=5000, debug=config.config['debug'], use_reloader=False)
