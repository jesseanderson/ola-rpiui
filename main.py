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
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListView, ListItemButton
from olalistener import OLAListener, UIEvent

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

class PatchingScreen(Screen):
  pass

class ConsoleScreen(Screen):
  pass

class RDMSettingsScreen(Screen):
  pass

class RDMTestsScreen(Screen):
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
    self.ola_listener = OLAListener(self.ui_queue,
                                    self.start_ola,
                                    self.stop_ola)
    self.ola_listener.start()
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
    self.sm.add_widget(PatchingScreen(name='Device Patching'))
    self.sm.add_widget(ConsoleScreen(name='DMX Console'))
    self.sm.add_widget(RDMSettingsScreen(name='RDM Settings'))
    self.sm.add_widget(RDMTestsScreen(name='RDM Tests'))
    self.layout.add_widget(self.sm)
    self.screens = {}
    self.available_screens = ['Device Settings','Device Patching',
      'DMX Console', 'RDM Settings', 'RDM Tests']
    self.screen_names = self.available_screens
    self.go_next_screen()
    Clock.schedule_interval(lambda dt: self.display_tasks(),
                            self.EVENT_POLL_INTERVAL)
    Clock.schedule_interval(self._update_clock, 1 / 60.)
    return self.layout

  def on_pause(self):
    return True

  def on_resume(self):
    pass

  def start_ola(self):
    """Executed when OLAD starts, enables proper UI actions"""
    self.devsets.ids.olad_status.text = "OLAD is Running"
    Clock.schedule_interval(self.display_universes,
                            self.UNIVERSE_POLL_INTERVAL)
    self.devsets.ids.universe_list_view.disabled = False

  def stop_ola(self):
    """Executed when OLAD stops, disables proper UI actions"""
    self.devsets.ids.olad_status.text = "OLAD is Stopped"
    Clock.unschedule(self.display_universes)
    self.devsets.ids.universe_list_view.disabled = True

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
