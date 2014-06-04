#!/usr/bin/python
import kivy
kivy.require('1.8.0')
from time import time
from Queue import Queue, Empty
from kivy.app import App
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
  ListProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.actionbar import ActionBar
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListView, ListItemButton
from olalistener import OLAListener, UIEvent
from settingsscreen import MainScreen, PatchingPopup
from monitorscreen import MonitorScreen
from consolescreen import ConsoleScreen
from ola.OlaClient import OlaClient
from ola.ClientWrapper import SelectServer

class InfoPopup(Popup):
  pass

class RPiUI(App):
  """Class for drawing and handling the Kivy application itself."""
  EVENT_POLL_INTERVAL = 1 / 20
  UNIVERSE_POLL_INTERVAL = 1 / 10
  index = NumericProperty(-1)
  time = NumericProperty(0)
  current_title = StringProperty()
  screen_names = ListProperty([])

  def build(self):
    """Initializes the user interface and starts timed events."""
    #TODO: Reorganize and consolidate; make necessary helper functions
    self.title = 'Open Lighting Architecture'
    self.ui_queue = Queue()
    self.layout = BoxLayout(orientation='vertical')
    self.selected_universe = None
    #ActionBar creation and layout placing
    self.ab = ActionBar()
    self.layout.add_widget(self.ab)
    #Screen creation and layout placing
    self.sm = ScreenManager(transition=SlideTransition())
    self.devsets = MainScreen(self.change_selected_universe,
                              name='Device Settings')
    self.sm.add_widget(self.devsets)
    self.sm.add_widget(MonitorScreen(name='DMX Monitor'))
    self.sm.add_widget(ConsoleScreen(name='DMX Console'))
    self.layout.add_widget(self.sm)
    self.screens = {}
    self.available_screens = ['Device Settings','DMX Monitor','DMX Console']
    self.screen_names = self.available_screens
    self.go_next_screen()
    Clock.schedule_interval(lambda dt: self.display_tasks(),
                            self.EVENT_POLL_INTERVAL)
    Clock.schedule_interval(self._update_clock, 1 / 60.)
    return self.layout

  def on_start(self):
    """Executed after build()"""
    self.ola_listener = OLAListener(self.ui_queue,
                                    self.create_select_server,
                                    self.create_ola_client,
                                    self.start_ola,
                                    self.stop_ola)
    self.ola_listener.start()

  def on_stop(self):
    pass

  def on_pause(self):
    """Pausing is not allowed; the application will close instead"""
    return False

  def on_resume(self):
    """Because pausing is not allowed, nothing to do here"""
    pass

  @staticmethod
  def create_select_server():
    return SelectServer()

  @staticmethod
  def create_ola_client():
    return OlaClient()

  def start_ola(self):
    """Executed when OLAD starts, enables proper UI actions"""
    self.devsets.ids.olad_status.text = "OLAD is Running"
    Clock.schedule_interval(self.display_universes,
                            self.UNIVERSE_POLL_INTERVAL)
    self.devsets.ids.universe_list_view.disabled = False
    self.devsets.ids.patch_button.disabled = False

  def stop_ola(self):
    """Executed when OLAD stops, disables proper UI actions"""
    self.devsets.ids.olad_status.text = "OLAD is Stopped"
    Clock.unschedule(self.display_universes)
    self.devsets.ids.universe_list_view.disabled = True
    self.devsets.ids.patch_button.disabled = True

  def display_tasks(self):
    """Polls for events that need to update the UI, 
       then updates the UI accordingly.
    """
    try:
      event = self.ui_queue.get(False)
      event.run()
      self.display_tasks()
    except Empty:
      pass

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
    self.devsets.ids.universe_list_view.adapter.data = universes
    self.devsets.ids.universe_list_view.populate()

  def change_selected_universe(self, adapter):
    """Changes the UI-level selected universe.

       Args:
         adapter: the adapter passed upon a listadapter on_selection_change call
    """
    if len(adapter.selection) == 0:
      self.selected_universe = None
    else:
      self.selected_universe = adapter.data[adapter.selection[0].index]

  def patch_popup(self):
    """Opens the universe patching interface"""
    self.patching_popup = PatchingPopup(self.ola_listener)
    self.patching_popup.open()

  def patch_universe(self):
    """On the UI button press, closes the patching popup
       and makes the patch.
    """
    if self.patching_popup:
      try:
        universe_id = int(self.patching_popup.ids.universe_id.text)
      except ValueError:
        info_popup = InfoPopup()
        info_popup.title = 'ERROR'
        info_popup.ids.info.text = ("Invalid Universe ID\n"
                                    "The universe ID must be an integer\n"
                                    "between 0 and 4294967295")
        info_popup.open()
        return
      universe_name = self.patching_popup.ids.universe_name.text
      for selection in self.patching_popup.ids.device_list.adapter.selection:
        data = self.patching_popup.ids.device_list.adapter.data[selection.index]
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
      self.patching_popup.dismiss()
    else:
      info_popup = InfoPopup()
      info_popup.title = 'ERROR'
      info_popup.ids.info.text = ("Patch Failed!\n"
                                  "Please check your ID and name\n"
                                  "and try again.")
      info_popup.open()

  def go_previous_screen(self):
    """Changes the UI to view the screen to the left of the current one"""
    self.index = (self.index - 1) % len(self.available_screens)
    SlideTransition.direction = 'right'
    self.sm.current = self.screen_names[self.index]
    self.current_title = self.screen_names[self.index]

  def go_next_screen(self):
    """Changes the UI to view the screen to the right of the current one"""
    self.index = (self.index + 1) % len(self.available_screens)
    SlideTransition.direction = 'left'
    self.sm.current = self.screen_names[self.index]
    self.current_title = self.screen_names[self.index]

  def _update_clock(self, dt):
    self.time = time()

  def olad_listen(self, dt):
    self.ola_listener.listen(self)

if __name__ == '__main__':
    RPiUI().run()
