import kivy
from kivy.uix.screenmanager import Screen
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.popup import Popup

class MainScreen(Screen):
  """The settings screen that the app opens to"""

  def __init__(self, onchange_callback, **kwargs):
    """Initializes the listview that contains the universe selection.

       Args:
         onchange_callback: the callback upon a selection change 
                            in the main listview
    """
    super(MainScreen, self).__init__(**kwargs)
    universe_converter = \
      lambda row_index, selectable: {'text': selectable.name,
                                     'size_hint_y': None,
                                     'height': 25}
    list_adapter = ListAdapter(data=[],
                               args_converter=universe_converter,
                               selection_mode='single',
                               allow_empty_selection=False,
                               cls=ListItemButton)
    list_adapter.bind(on_selection_change=onchange_callback)
    self.ids.universe_list_view.adapter = list_adapter

class PatchingPopup(Popup):
  """The popup that handles patching of new universes"""
  #TODO: Better port data formatting

  def __init__(self, ola_listener, **kwargs):
    """Initializes a listview for port selection"""
    super(PatchingPopup, self).__init__(**kwargs)
    port_converter = \
      lambda row_index, selectable: {'text': '{0} ({1})'.format( \
                                                           selectable[1],
                                                           selectable[3]),
                                     'size_hint_y': None,
                                     'height': 25}
    port_adapter = ListAdapter(data=[],
                               args_converter=port_converter,
                               selection_mode='multiple',
                               allow_empty_selection=False,
                               cls=ListItemButton)
    self.ids.device_list.adapter = port_adapter
    ola_listener.pull_devices(self.update_ports)

  def update_ports(self, status, devices):
    """Updates the listview with available ports

       Args:
         status: RequestStatus object indicating whether the 
                 request was successful
         devices: A list of devices
    """
    data = []
    # Data list contains two instances per device, one for input
    # and one for output (breaks ensure this)
    for device in devices:
      for port in device.input_ports:
        if not port.active:
          data.append((device.alias,
                       device.name,
                       port.id,
                       "Input",
                       False))
          break
      for port in device.output_ports:
        if not port.active:
          data.append((device.alias,
                       device.name,
                       port.id,
                       "Output",
                       True))
          break
    self.ids.device_list.adapter.data = data
    self.ids.device_list.populate()
