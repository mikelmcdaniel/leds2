import random
import socket
import subprocess
import sys
import time
import urllib2

def make_server_proc(self, mode):
  return subprocess.Popen(['python2', 'main.py', mode], close_fds=True, env={})

def ping(max_pings=3):
  for j in xrange(max_pings):
    time.sleep(j)
    try:
      page = urllib2.urlopen('http://localhost:5000/ping', timeout=(j + 1))
      if page.read() == 'ok':
        return True
    except (urllib2.URLError, socket.timeout) as e:
      print 'PING ERROR:', e
  return False


def main(argv):
  assert argv[1] in ('debug', 'prod')
  mode = argv[1]
  debug = True if mode == 'debug' else False
  server_proc = make_server_proc(mode)
  while True:
    if server_proc.poll() is not None:
      server_proc = make_server_proc(mode)
    elif not ping():
      server_proc.terminate()
      time.sleep(1)
      server_proc.kill()
      time.sleep(1)
      server_proc = make_server_proc(mode)
    for _ in xrange(random.randint(60, 90)):
      time.sleep(1)
      if server_proc.poll() is not None:
        break

if __name__ == '__main__':
  main(sys.argv)
