import sys
import threading
from ola.ClientWrapper import ClientWrapper, SelectServer
from ola.OlaClient import OlaClient, OLADNotRunningException

class OLAListener(threading.Thread):

  def __init__(self, ui_queue):
    super(OLAListener,self).__init__()
    self.ui_queue = ui_queue
    self.daemon = True #Allows python to terminate upon closing UI
    try:
      self.client = OlaClient()
      self.ola_running = True
    except OLADNotRunningException:
      self.ola_running = False 

  def run(self):
    try:
      self.selectserver = SelectServer()
      self.selectserver.AddReadDescriptor(self.client.GetSocket(),
                                          self.client.SocketReady)
      self.selectserver.Run()
    except OLADNotRunningException:
      self.ola_running = False

  def ola_quit(self, UI):
    UI.set_ola_status('OLAD is Not Running')
    self.ola_running = False

  def ola_start(self, UI):
    UI.set_ola_status('OLAD is Running')
    self.ola_running = True

  def pull_universes(self, callback):
    ''' Executes the get universes requestin the selectserver with a callback 
        that will put the universes in the UI queue
    ''' 
    self.selectserver.Execute(
      lambda:self.client.FetchUniverses(self.universes_queue_callback(callback)))

  def universes_queue_callback(self,callback):
    return lambda status,universes: self.ui_queue.put([callback,status,universes])

