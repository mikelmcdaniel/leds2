from sys import argv
import os

configs = (
  {
    'name': 'macro_orb',
    'usb_file_name': '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A900XEZM-if00-port0',
    'board_tag': 'atmega328',
    'half_reversed': 0,
    'num_leds': 144,
  },
  {
    'name': 'living_room',
    'usb_file_name': '/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_95232343833351603170-if00',
    'board_tag': 'uno',
    'half_reversed': 1,
    'num_leds': 200,
  },
)

configs = dict((c['name'], c) for c in configs)



config_name = 'living_room'
for config in configs.itervalues():
  if os.path.exists(config['usb_file_name']):
    config_name = config['name']
    break
config = configs[config_name]

def main(argv):
  print configs[config_name][argv[1]]

if __name__ == '__main__':
  main(argv)
