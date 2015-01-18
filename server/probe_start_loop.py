import random
import subprocess
import sys
import threading
import time
import urllib2

class ServerThread(threading.Thread):
  def __init__(self, debug=False):
    super(ServerThread, self).__init__()
    self.setDaemon(True)
    mode = 'debug' if debug else 'prod'
    self.server_proc = subprocess.Popen(['python2', 'main.py', mode], close_fds=True, env={})
    self.start()

  def run(self):
    self.server_proc.communicate()

  def kill_server(self):
    self.server_proc.kill()


def attempt_ping(max_pings=3):
  for j in xrange(max_pings):
    time.sleep(j)
    try:
      page = urllib2.urlopen('http://localhost:5000/ping', timeout=(j + 1))
      if page.read() == 'ok':
        return True
    except urllib2.URLError:
      pass
  return False


def main(argv):
  assert argv[1] in ('debug', 'prod')
  debug = True if argv[1] == 'debug' else False
  st = ServerThread(debug)
  while True:
    print 'foo'
    if True or not attempt_ping():
      st.kill_server()
      st = ServerThread(debug)
      time.sleep(5)
    time.sleep(120 + random.random() * 60)

if __name__ == '__main__':
  main(sys.argv)
