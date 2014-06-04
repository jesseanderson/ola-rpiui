import unittest
from mock import Mock, MagicMock, patch
from olalistener import UIEvent, OLAListener
from ola.ClientWrapper import SelectServer
from ola.OlaClient import OlaClient, RequestStatus, Universe, Device
from Queue import Queue, Empty
import time

class TestUIEvent(unittest.TestCase):
  """Tests the UIEvent class for passing functions to the UI"""

  def setUp(self):
    """Resets testing variables"""
    self._function_executed = False
    self._args = None

  def uievent_function(self, *args):
    """A function that sets testing variables when executed"""
    self._function_executed = True
    self._args = args

  def test_no_args(self):
    """Tests to ensure that when no args are provided, the function provided
       is still executed and the empty tuple is passed in.
    """
    event = UIEvent(self.uievent_function)
    event.run()
    self.assertTrue(self._function_executed)
    self.assertIs(self._args, ())

  def test_args_list(self):
    """Tests to ensure that when args are provided with a function, 
       the function is executed correctly with those args.
    """
    test_args = [1, 'hello', 2]
    event = UIEvent(self.uievent_function, test_args)
    event.run()
    self.assertTrue(self._function_executed)
    self.assertEquals(self._args, (1,'hello',2))

  def test_none_as_input(self):
    """Tests to see that UIEvent accepts None as a function and
       does not fail.
    """
    event = UIEvent(None)
    event.run()
    self.assertFalse(self._function_executed)
    self.assertIsNone(self._args)

class MockSelectServer(SelectServer):
  def __init__(self):
    pass
  def __del__(self):
    pass
  def Execute(self, f):
    f()
  def Terminate(self):
    pass
  def Reset(self):
    pass
  def StopIfNoEvents(self):
    pass
  def AddReadDescriptor(self, fd, callback):
    pass
  def RemoveReadDescriptor(self, fd):
    pass
  def AddWriteDescriptor(self, fd, callback):
    pass
  def RemoveWriteDescriptor(self, fd):
    pass
  def Run(self):
    pass
  def AddEvent(self):
    pass

class MockOlaClient(OlaClient):
  def __init__(self, our_socket = None, close_callback = None):
    pass
  def GetSocket(self):
    pass
  def SocketReady(self):
    pass
  def FetchPlugins(self, callback):
    pass
  def PluginDescription(self, callback, plugin_id):
    pass
  def FetchDevices(self, callback):
    callback(None,[Device(123,1,"Test Device",None,[],[])])
  def FetchUniverses(self, callback):
    callback(None,[Universe(123,"Test Universe", Universe.LTP)])
  def FetchDmx(self, universe, callback):
    pass
  def SendDmx(self, universe, data, callback=None):
    pass
  def SetUniverseName(self, universe, name, callback=None):
    pass
  def SetUniverseMergeMode(self, universe, merge_mode, callback=None):
    pass
  def RegisterUniverse(self, universe, action, data_callback, callback=None):
    pass
  def PatchPort(self, device_alias, port, is_output, action, universe,
                callback=None):
    callback(None)
  def ConfigureDevice(self, device_alias, request_data, callback):
    pass
  def SendTimeCode(self, time_code_type, hours, minutes, seconds, frames,
                   callback=None):
    pass
  def UpdateDmxData(self, controller, request, callback):
    pass
  def FetchUIDList(self, universe, callback):
    pass
  def RunRDMDiscovery(self, universe, full, callback):
    pass
  def RDMGet(self, universe, uid, sub_device, param_id, callback, data=''):
    pass
  def RDMSet(set, universe, uid, sub_device, param_id, callback, data=''):
    pass
  def SendRamRDMDiscovery(self, universe, uid, sub_device, param_id,
                          callback, data=''):
    pass

class TestOLAListener(unittest.TestCase):
  """Tests the system which gets requests from the UI and evaluates them
     using a selectserver.
  """

  def setUp(self):
    """Creates an OLAListener object with proper mock values"""
    self.ui_queue = Queue()
    self.on_start = MagicMock()
    self.on_stop = MagicMock()
    self.ola_listener = OLAListener(self.ui_queue,
                                    self.create_mock_select_server,
                                    self.create_mock_ola_client,
                                    self.on_start,
                                    self.on_stop)
    self.ola_listener.start()
    time.sleep(0.1) #Give the OLAListenerThread time to initialize

  @staticmethod
  def create_mock_select_server():
    return MockSelectServer()

  @staticmethod
  def create_mock_ola_client():
    return MockOlaClient()

  def clear_ui_queue(self):
    """Executes every UIEvent in the UI Queue, then terminates"""
    try:
      event = self.ui_queue.get(True,0.2)
      event.run()
      self.clear_ui_queue()
    except Empty:
      pass

  def test_pull_universes(self):
    """Tests the OLAListener's pull_universes method"""
    self.callback_executed = False
    def callback(status, universes):
      self.assertEqual(universes[0].id,123) #Mock values
      self.assertEqual(universes[0].name,"Test Universe")
      self.callback_executed = True
    self.ola_listener.pull_universes(callback)
    self.clear_ui_queue()
    self.assertTrue(self.callback_executed)
 
  def test_pull_devices(self):
    """Tests the OLAListener's pull_devices method"""
    self.callback_executed = False
    def callback(status, devices):
      self.assertEqual(devices[0].id,123) #Mock values
      self.assertEqual(devices[0].name,"Test Device")
      self.callback_executed = True
    self.ola_listener.pull_devices(callback)
    self.clear_ui_queue()
    self.assertTrue(self.callback_executed)

  def test_patch(self):
    """Tests the OLAListener's patch method.  Right now, just ensures
       callback is called, more to be added.
    """
    self.callback_executed = False
    def callback(status):
      self.callback_executed = True
    self.ola_listener.patch(1,1,False,2,"Test Patch",callback)
    self.clear_ui_queue()
    self.assertTrue(self.callback_executed)
