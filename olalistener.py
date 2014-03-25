import sys
from ola.ClientWrapper import ClientWrapper, OLADNotRunningException

class OLAListener():

  def __init__(self):
    #Temporary hack to get OLA status to display on startup
    try:
      self.wrapper = ClientWrapper()
      self.client = self.wrapper.Client()
      self.ola_running = False
    except OLADNotRunningException:
      self.ola_running = True
      

  def ola_quit(self, UI):
    UI.set_ola_status('OLAD is not Running')
    self.ola_running = False

  def ola_start(self, UI):
    UI.set_ola_status('OLAD is Running')
    self.ola_running = True

  def listen(self, UI):
    #TODO: better OLAD detection
    try:
      self.wrapper = ClientWrapper()
      self.client = self.wrapper.Client()
      if not self.ola_running:
        self.ola_start(UI)
    except OLADNotRunningException:
      if self.ola_running:
        self.ola_quit(UI)
