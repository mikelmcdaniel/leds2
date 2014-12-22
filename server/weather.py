import pywapi
import string
import time
import datetime
import astral

class SimpleWeather(object):
  def __init__(self):
    self.celcius = None
    self.is_sunny = 0
    self.is_rainy = 0
    self.is_foggy = 0
    self.is_cloudy = 0
    self.lightning = 0
    self.is_snowy = 0

'''
Mostly Cloudy
Partly Cloudy
Overcast
Fair
Fog/Mist
A Few Clouds
Light Rain
Haze
Drizzle
Breezy
Light Snow
Unknown Precip
'''
def parse_weather_modifier(modifier):
  if modifier in ['very', 'mostly', 'high', 'heavy']:
    return 0.75
  elif modifier in ['partly', 'little', 'light', 'low']:
    return 0.25
  else:
    return 0.5


def parse_weather(weather_str):
  weather = SimpleWeather()
  weather_str_list = weather_str.lower().replace('/', ' ').split()
  last_word = None
  for word in weather_str_list:
    if 'sun' in word or word == 'fair':
      weather.is_sunny = parse_weather_modifier(last_word)
    elif 'cloud' in word:
      weather.is_cloudy = parse_weather_modifier(last_word)
    elif word == 'overcast':
      weather.is_cloudy = min(parse_weather_modifier(last_word) * 1.25, 1.0)
    elif 'rain' in word:
      weather.is_rainy = parse_weather_modifier(last_word)
    elif 'fog' in word or 'mist' in word:
      weather.is_foggy = parse_weather_modifier(last_word)
    elif 'snow' in word:
      weather.is_snowy = parse_weather_modifier(last_word)
    last_word = word
  return weather

def get_weather(location_id='KSJC', weather_source='noaa'):
  if weather_source == 'noaa':
    noaa_result = pywapi.get_weather_from_noaa(location_id)
    current_weather = parse_weather(string.lower(noaa_result['weather']))
    current_weather.celcius = float(noaa_result['temp_c'])
  elif weather_source == 'yahoo':
    yahoo_result = pywapi.get_weather_from_yahoo(location_id)
    current_weather = parse_weather(string.lower(yahoo_result['condition']['text']))
    current_weather.celcius = float(yahoo_result['condition']['temp'])
  elif weather_source == 'weather_com':
    weather_com_result = pywapi.get_weather_from_weather_com(location_id)
    current_weather = parse_weather(string.lower(weather_com_result['current_conditions']['text']))
    current_weather.celcius = float(weather_com_result['current_conditions']['temperature'])
  return current_weather

def get_seconds(local_time=None):
  if local_time is None:
    local_time = time.localtime()
  seconds = local_time.tm_hour * 3600 + local_time.tm_min * 60 + local_time.tm_sec
  return float(seconds)

def get_sun_seconds(time):
  seconds = time.hour * 3600 + time.minute * 60 + time.second
  return float(seconds)

def get_sun_position(now=None, sunrise=None, sunset=None):
  if now is None:
    now = get_seconds(time.localtime())
  if sunrise is None:
    sunrise = get_sun_info()[0]
  if sunset is None:
    sunset = get_sun_info()[1]
  sun_position = (now - sunrise) / (sunset - sunrise)
  if sun_position < 0 or sun_position > 1:
    return None
  else:
    return sun_position

def get_moon_position(now=None, sunset=None, sunrise=None):
  if now is None:
    now = get_seconds(time.localtime())
  if sunset is None:
    sunset = float(get_sun_info()[1])
  if sunrise is None:
    sunrise = float(get_sun_info()[0])
  if now < sunrise:
    moon_position = (now + (86400 - sunset)) / (sunrise + (86400 - sunset))
  else:
    moon_position = (now - sunset) / (sunrise + (86400 - sunset))
  if moon_position < 0 or moon_position > 1:
    return None
  else:
    return moon_position

def get_sun_info():
  sun_info = astral.Astral()
  location = sun_info['San Francisco']
  timezone = location.timezone
  d = datetime.date.today()
  sun = location.sun(local=True, date=d)
  sunrise = get_sun_seconds(sun['sunrise'])
  sunset = get_sun_seconds(sun['sunset'])
  return float(sunrise), float(sunset)
