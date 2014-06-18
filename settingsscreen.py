import kivy
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.popup import Popup

Builder.load_file('settingsscreen.kv')

class MainScreen(Screen):
  """The settings screen that the app opens to"""

  def __init__(self, ola_listener, onchange_callback, **kwargs):
    """Initializes the listview that contains the universe selection.

       Args:
         ola_listener: an OLAListener object to pass tasks to
         onchange_callback: the callback upon a selection change 
                            in the main listview

       Attributes:
         selected_universe: this object is changed by the parent's 
                            on_change handler for the listview on this screen
    """
    super(MainScreen, self).__init__(**kwargs)
    self.ola_listener = ola_listener
    self.selected_universe = None
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

  def start_ola(self, universe_poll_interval):
    """Enables UI actions upon starting of OLAD.

       Args:
         universe_poll_interval: The interval in seconds between each time
                                 universe list updates.
    """
    self.ids.olad_status.text = "OLAD is Running"
    Clock.schedule_interval(self.display_universes,
                            universe_poll_interval)
    self.ids.universe_list_view.disabled = False
    self.ids.patch_button.disabled = False
    self.ids.unpatch_button.disabled = False

  def stop_ola(self):
    """Disables UI on main screen"""
    self.ids.olad_status.text = "OLAD is Stopped"
    Clock.unschedule(self.display_universes)
    self.ids.universe_list_view.disabled = True
    self.ids.patch_button.disabled = True
    self.ids.unpatch_button.disabled = True

  def display_universes(self, dt):
    """Makes a call to fetch the active universes; then put them in the
       UI queue to be handled by display_universes_callback.

       Args:
         dt: time since last call
    """
    self.ola_listener.pull_universes(self.display_universes_callback)

  def display_universes_callback(self, status, universes):
    """Updates the user interface with the active universes.

       Args:
         status: RequestStatus object indicating whether the request
                 was successful
         universes: A list of Universe objects
    """
    self.ids.universe_list_view.adapter.data = universes
    self.ids.universe_list_view.populate()

  def patch_popup(self):
    """Opens the universe patching interface"""
    self.patching_popup = PatchingPopup(self.ola_listener)
    self.patching_popup.open()

  def unpatch_confirmation(self):
    """Opens the confirmation dialog for unpatching"""
    unpatch_confirmation = ConfirmationPopup(self.ola_listener)
    unpatch_confirmation.ids.confirmation.text = ("Are you sure you\n"
                                                  "want to unpatch the\n"
                                                  "selected universe?")
    unpatch_confirmation.ids.confirmation_button.on_press = \
      self.unpatch_universe_popup(unpatch_confirmation)
    unpatch_confirmation.open()

  def unpatch_universe_popup(self, popup):
    """Creates the appropriate unpatching method for the given popup

       Args:
         popup: The confirmation popup to be closed upon completion
    """
    def unpatch_universe():
      """Makes the unpatching call to the olalistener"""
      self.ola_listener.unpatch(self.selected_universe.id,
                                self.unpatch_callback_popup(popup))
    return unpatch_universe

  def unpatch_callback_popup(self, popup):
    """Creates the appropriate unpatching callback for the given popup

       Args:
         popup: The confirmation popup to be closed upon completion
    """
    def unpatch_callback(status):
      """The callback that will update the UI after an unpatch

         Args:
           status: RequestStatus object indicating success or failure
      """
      if status.Succeeded():
        popup.dismiss()
      else:
        popup.dismiss()
        info_popup = InfoPopup()
        info_popup.title = 'ERROR'
        info_popup.ids.info.text = ("Unpatching Failed!"
                                    "Please try again.")
        info_popup.open()
    return unpatch_callback

class ConfirmationPopup(Popup):
  def __init__(self, ola_listener, **kwargs):
    super(ConfirmationPopup, self).__init__(**kwargs)
    self.ola_listener = ola_listener

class InfoPopup(Popup):
  pass

class PatchingPopup(Popup):
  """The popup that handles patching of new universes"""
  #TODO: Better port data formatting

  def __init__(self, ola_listener, **kwargs):
    """Initializes a listview for port selection"""
    super(PatchingPopup, self).__init__(**kwargs)
    self.ola_listener = ola_listener
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
    self.ola_listener.pull_devices(self.update_ports)

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

  def patch_universe(self):
    """On the UI button press, closes the patching popup
       and makes the patch.
    """
    try:
      universe_id = int(self.ids.universe_id.text)
    except ValueError:
      info_popup = InfoPopup()
      info_popup.title = 'ERROR'
      info_popup.ids.info.text = ("Invalid Universe ID\n"
                                  "The universe ID must be an integer\n"
                                  "between 0 and 4294967295")
      info_popup.open()
      return
    universe_name = self.ids.universe_name.text
    for selection in self.ids.device_list.adapter.selection:
      data = self.ids.device_list.adapter.data[selection.index]
      self.ola_listener.patch(data[0], data[2], data[4],
                              universe_id, universe_name,
                              self.patch_universe_callback)

  def patch_universe_callback(self, status):
    """Displays a success or error popup upon completion of the OLA patching

      Args:
        status: RequestStatus object indicating whether the patch was successful
    """
    if status.Succeeded():
      info_popup = InfoPopup()
      info_popup.title = 'Success!'
      info_popup.ids.info.text = 'Patch completed successfully!'
      info_popup.open()
      self.dismiss()
    else:
      info_popup = InfoPopup()
      info_popup.title = 'ERROR'
      info_popup.ids.info.text = ("Patch Failed!\n"
                                  "Please check your ID and name\n"
                                  "and try again.")
      info_popup.open()
