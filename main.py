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
from kivy.uix.tabbedpanel import TabbedPanel
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

class ScreenTabs(TabbedPanel):
  """Class for the widget that holds all the Screens in a tabbed view"""

  def __init__(self, **kwargs):
    super(ScreenTabs, self).__init__(**kwargs)
    self.previous_tab = self.current_tab

  def on_size(self, inst, value):
    """Ensures that the tabs fill the entire top bar"""
    width = value[0]
    self.tab_width = int(width / len(self.tab_list))

  def on_current_tab(self, *args):
    """When the current tab changes, fire Screen methods for enter/exit"""
    if self.previous_tab.content:
      self.previous_tab.content.on_leave()
    if self.current_tab.content:
      self.current_tab.content.on_enter()
    self.previous_tab = self.current_tab

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
    self.ola_listener = OLAListener(self.ui_queue,
                                    self.create_select_server,
                                    self.create_ola_client,
                                    self.start_ola,
                                    self.stop_ola)
    #Screen creation and layout placing
    self.screen_tabs = ScreenTabs()
    self.monitor_screen = MonitorScreen(self.ola_listener,
                                        name='DMX Monitor')
    self.console_screen = ConsoleScreen(self.ola_listener,
                                        name='DMX Console')
    self.devsets = MainScreen(self.ola_listener,
                              self.change_selected_universe,
                              name='Device Settings')
    self.screen_tabs.ids.monitor_screen.add_widget(self.monitor_screen)
    self.screen_tabs.ids.console_screen.add_widget(self.console_screen)
    self.screen_tabs.ids.settings_screen.add_widget(self.devsets)
    self.layout.add_widget(self.screen_tabs)
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
         adapter: the adapter passed on a listadapter on_selection_change call
    """
    if len(adapter.selection) == 0:
      self.devsets.selected_universe = None
      self.monitor_screen.selected_universe = None
      self.console_screen.change_selected_universe(None)
    else:
      self.devsets.selected_universe = adapter.data[adapter.selection[0].index]
      self.monitor_screen.selected_universe = \
        adapter.data[adapter.selection[0].index]
      self.console_screen.change_selected_universe( \
        adapter.data[adapter.selection[0].index])

  def _update_clock(self, dt):
    self.time = time()

  def olad_listen(self, dt):
    self.ola_listener.listen(self)

if __name__ == '__main__':
    RPiUI().run()
