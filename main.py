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
from ola.OlaClient import OlaClient, Universe
from ola.ClientWrapper import SelectServer

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
    self.selected_universe = None
    self.layout = BoxLayout(orientation='vertical')
    self.ola_listener = OLAListener(self.ui_queue,
                                    self.create_select_server,
                                    self.create_ola_client,
                                    self.start_ola,
                                    self.stop_ola)
    self.ab = ActionBar()
    self.layout.add_widget(self.ab)
    #Screen creation and layout placing
    self.sm = ScreenManager(transition=SlideTransition())
    self.devsets = MainScreen(self.ola_listener,
                              self.change_selected_universe,
                              name='Device Settings')
    self.sm.add_widget(self.devsets)
    self.monitor_screen = MonitorScreen(name='DMX Monitor')
    self.sm.add_widget(self.monitor_screen)
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
    self.ola_listener.start()
 
  def on_stop(self):
    """Executed when the application quits"""
    self.ola_listener.stop()

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
    self.devsets.start_ola(self.UNIVERSE_POLL_INTERVAL)

  def stop_ola(self):
    """Executed when OLAD stops, disables proper UI actions"""
    self.devsets.stop_ola()

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

  def change_selected_universe(self, adapter):
    """Changes the UI-level selected universe.

       Args:
         adapter: the adapter passed upon a listadapter on_selection_change call
    """
    if len(adapter.selection) == 0:
      self.selected_universe = None
      self.devsets.selected_universe = None
    else:
      if self.selected_universe:
        self.ola_listener.stop_dmx_listener(self.selected_universe.id, None, None)
      self.selected_universe = adapter.data[adapter.selection[0].index]
      self.devsets.selected_universe = adapter.data[adapter.selection[0].index]
      self.ola_listener.fetch_dmx(self.selected_universe.id,
                                  lambda s,u,d: self.monitor_screen.update_data(d))
      self.ola_listener.start_dmx_listener(self.selected_universe.id,
                                           self.monitor_screen.update_data, None)

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
