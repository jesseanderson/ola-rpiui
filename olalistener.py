import sys
import threading
import time
from ola.ClientWrapper import ClientWrapper, SelectServer
from ola.OlaClient import OlaClient, OLADNotRunningException

class UIEvent(object):
  """Describes events that the UI needs to execute"""

  def __init__(self, function, args=[]):
    """Args:
         function: the function that will update the UI appropriately
         args: a list of the arguments for that function
    """
    self.function = function
    self.args = args

  def run(self):
    """Executes the UI-level event if the function is not None"""
    if self.function:
      self.function(*self.args)

class OLAListener(threading.Thread):
  """Makes all requested calls to OLA in its own thread."""

  def __init__(self, ui_queue, on_start, on_stop):
    """Initializes OLA objects; determines if OLAD is running upon start.

       Args:
         ui_queue: A Queue where UI events are held.
         on_start: function to execute when OLA starts
         on_stop: function to execute when OLA stops
    """
    super(OLAListener,self).__init__()
    self.ui_queue = ui_queue
    self.start_event = UIEvent(on_start)
    self.stop_event = UIEvent(on_stop)
    self.daemon = True #Thread quits when main thread quits

  def run(self):
    """Initializes and runs an OLA SelectServer"""
    try:
      self.client = OlaClient()
      self.selectserver = SelectServer()
      self.selectserver.AddReadDescriptor(self.client.GetSocket(),
                                          self.client.SocketReady)
      self.ui_queue.put(self.start_event)
      self.selectserver.Run()
    except:
      #TODO: Make a flag of some sort so that stop_event is only put
      # on the queue once.  Also, this will allow me to remove the sleep()
      self.ui_queue.put(self.stop_event)
      time.sleep(1) #Ensures tasks are not put on the queue too quickly.
      self.run()

  def ola_quit(self, UI):
    UI.set_ola_status('OLAD is Not Running')
    self.ola_running = False

  def ola_start(self, UI):
    UI.set_ola_status('OLAD is Running')
    self.ola_running = True

  def pull_universes(self, callback):
    """Executes the get universes request in the selectserver with a callback 
       that will put the universes in the UI queue

        Args:
          callback: The UI callback that will be placed on the 
                    UI queue with the universes
    """
    self.selectserver.Execute(
      lambda:self.client.FetchUniverses(self.universes_queue_callback(callback)))

  def universes_queue_callback(self,callback):
    """Creates an appropriate callback for client.FetchUniverses that
       will put the OLA response directly into the UI queue

       Args:
         callback: The UI callback that will be places on the
                   UI queue with the universes
    """
    def universes_queue_event(status,universes):
      self.ui_queue.put(UIEvent(callback,[status,universes]))
    return universes_queue_event

  def pull_devices(self, callback):
    """Delivers a list of devices.

       Args:
         callback: The UI callback that will be placed on the
                   UI queue with the devices
    """
    self.selectserver.Execute(
      lambda:self.client.FetchDevices(self.devices_queue_callback(callback)))

  def devices_queue_callback(self, callback):
    """Creates an appropriate callback for client.FetchDevices that
       will put the OLA response directly into the UI queue

       Args:
         callback: The UI callback that will be placed on the
                   UI queue with the devices
    """
    def devices_queue_event(status,devices):
      self.ui_queue.put(UIEvent(callback,[status,devices]))
    return devices_queue_event

  def patch(self, device_alias, port, is_output, universe_id, 
            universe_name, callback):
    """Patch a port to a universe.

       Args:
         device_alias: the alias of the device
         port: the id of the port to patch to 
         is_output: select the input or output port
         universe_id: the universe id to patch
         universe_name: the name for this universe
         callback: The function to call once complete, takes one argument, a
           RequestStatus object.
    """
    self.selectserver.Execute(
      lambda:self.client.PatchPort(device_alias, port, is_output,
                                   self.client.PATCH, universe_id, 
                                   self.patch_callback(callback)))
    self.selectserver.Execute(
      lambda:self.client.SetUniverseName(universe_id, universe_name))

  def patch_callback(self, callback):
    """Creates an appropriate callback for client.PatchPort that
       will put the OLA response directly onto the UI queue
    """
    return lambda status:self.ui_queue.put(UIEvent(callback,[status]))
