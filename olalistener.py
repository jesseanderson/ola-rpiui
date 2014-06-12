import sys
import threading
import time

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

  def __init__(self, ui_queue, selectserver_builder, ola_client_builder,
               on_start, on_stop):
    """Initializes OLA objects; determines if OLAD is running upon start.

       Args:
         ui_queue: A Queue where UI events are held.
         selectserver_builder: Builds a SelectServer object for OLA tasks
         ola_client_builder: Builds the OLA Client itself
         on_start: UI Method to execute upon the starting of OLAD
         on_stop: UI Method to execute upon the stopping of OLAD 
    """
    super(OLAListener,self).__init__()
    self.ui_queue = ui_queue
    self.create_select_server = selectserver_builder
    self.create_ola_client = ola_client_builder
    self.start_event = UIEvent(on_start)
    self.stop_event = UIEvent(on_stop)
    self.selectserver = None

  def run(self):
    """Initializes and runs an OLA SelectServer"""
    self._stopped = False
    while not self._stopped:
      try:
        self.client = self.create_ola_client()
        self.selectserver = self.create_select_server()
        self.selectserver.AddReadDescriptor(self.client.GetSocket(),
                                            self.client.SocketReady)
        self.ui_queue.put(self.start_event)
        self.selectserver.Run()
        self._stopped = True
      except:
        #TODO: Make a flag of some sort so that stop_event is only put
        # on the queue once.  Also, this will allow me to remove the sleep()
        self.ui_queue.put(self.stop_event)
        self.selectserver = None
        time.sleep(1) #Ensures tasks are not put on the queue too quickly.

  def stop(self):
    """Terminates the OLAListener thread if it is running"""
    self._stopped = True
    if self.selectserver:
      self.selectserver.Terminate()

  def create_olaclient_callback(self, task, args):
    """Creates the necessary function for use client task execution.

       Args:
         task: function to execute
         args: a list of args for that function
    """
    return lambda: task(*args)

  def pull_universes(self, callback):
    """Executes the get universes request in the selectserver with a callback 
       that will put the universes in the UI queue

        Args:
          callback: The UI callback that will be placed on the 
                    UI queue with the universes
    """
    self.selectserver.Execute(
      lambda: self.client.FetchUniverses(
        lambda status, universes: 
          self.ui_queue.put(UIEvent(callback, [status,universes]))))


  def pull_devices(self, callback):
    """Delivers a list of devices.

       Args:
         callback: The UI callback that will be placed on the
                   UI queue with the devices
    """
    self.selectserver.Execute(
      lambda: self.client.FetchDevices(
        lambda status, devices:
          self.ui_queue.put(UIEvent(callback, [status,devices]))))

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
    def patch_callback(callback):
      """Creates an appropriate callback for client.PatchPort that
         will put the OLA response directly onto the UI queue
      """
      return lambda status:self.ui_queue.put(UIEvent(callback,[status]))

    self.selectserver.Execute(
      lambda:self.client.PatchPort(device_alias, port, is_output,
                                   self.client.PATCH, universe_id, 
                                   patch_callback(callback)))
    self.selectserver.Execute(
      lambda:self.client.SetUniverseName(universe_id, universe_name))

  def unpatch(self, universe_id, callback):
    """Unpatches a universe.

       Args:
         universe_id: the universe id to unpatch
         callback: The function to call once complete, takes one argument, a
           RequestStatus object.
    """

    def unpatch_callback(callback):
      """Creates an appropriate callback for client.PatchPort that
         will put the OLA response directly onto the UI queue
      """
      return lambda status:self.ui_queue.put(UIEvent(callback,[status]))

    def devices_callback(status, devices):
      """We need a list of devices in order to find the port
         of the universe we are unpatching
      """
      for device in devices:
        for port in device.input_ports:
          if port.universe == universe_id:
            self.selectserver.Execute(
              self.create_olaclient_callback(self.client.PatchPort, 
                                             [device.alias, port.id, False,
                                              self.client.UNPATCH, universe_id,
                                              unpatch_callback(callback)]))
        for port in device.output_ports:
          if port.universe == universe_id:
            self.selectserver.Execute(
              self.create_olaclient_callback(self.client.PatchPort,
                                             [device.alias, port.id, True,
                                              self.client.UNPATCH, universe_id,
                                              unpatch_callback(callback)]))
    self.selectserver.Execute(
      lambda: self.client.FetchDevices(devices_callback))

  def start_dmx_listener(self, universe, data_callback, callback):
    """Starts a listener that will call data_callback every time
       there is new DMX data.

       Args:
         universe: The universe id to listen for
         data_callback: The function to call every time there is new data
         callback: The callback for when the request is complete
    """
    self.selectserver.Execute(
      lambda:self.client.RegisterUniverse(universe, self.client.REGISTER, \
        lambda data: self.ui_queue.put(UIEvent(data_callback,[data])),
        lambda status: self.ui_queue.put(UIEvent(callback,[status]))))
