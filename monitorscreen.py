"""Defines a Kivy Screen to act as a Monitor for DMX on a universe."""

import math
import kivy
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label

_CELL_WIDTH = 32
_CELL_HEIGHT = 32
_DMX_CHANNELS = 512

Builder.load_file('monitorscreen.kv')

class MonitorCell(GridLayout):
  alpha = NumericProperty(0)

class MonitorScreen(Screen):
  """This screen displays the values of as many DMX channels as will fit
     on the screen.
  """
  def __init__(self, ola_listener, **kwargs):
    """Args:
         ola_listener: an OLAListener object with which to register
                       and unregister DMX listening.
    """
    super(MonitorScreen, self).__init__(**kwargs)
    self.ola_listener = ola_listener
    self.on_pre_enter = self.register_dmx_listener
    self.on_leave = self.unregister_dmx_listener
    self.channels = []
    self.selected_universe = None
    for channel_index in range(_DMX_CHANNELS):
      channel = MonitorCell(width=_CELL_WIDTH,height=_CELL_HEIGHT)
      channel.ids.channel.text = str(channel_index+1)
      self.channels.append(channel)

  def resize_carousel(self, size):
    """The monitor screen is broken up into smaller screens that are loaded
       individually; when the screen is resized, they update the number on
       each screen.

       Args:
         size: [width, height] of the Carousel widget
    """
    width = size[0]
    height = size[1]
    channels_per_page = int(width / _CELL_WIDTH) * int(height / _CELL_HEIGHT)
    pages = [self.channels[x:x+channels_per_page] for x in 
             xrange(0, len(self.channels), channels_per_page)]
    for slide in self.ids.monitor_car.slides:
      slide.clear_widgets()
    self.ids.monitor_car.clear_widgets()
    for page in pages:
      slide = StackLayout(size_hint_x=1, size_hint_y=1)
      for cell in page:
        slide.add_widget(cell)
      self.ids.monitor_car.add_widget(slide)
      

  def update_data(self, data):
    """Takes the new data and displays it in all 512 cells

       Args:
         data: an array of size 512 containing the dmx data
    """
    index = 0
    for channel in data:
      self.channels[index].ids.data.text = str(channel)
      self.channels[index].alpha = float(channel) / _DMX_CHANNELS
      index = index + 1

  def update_grid_height(self):
    """The grid height must be as high as its last visible child in order
       for the ScrollView to work as intended.
    """
    self.ids.grid.height = _CELL_HEIGHT * math.ceil(float(_DMX_CHANNELS) /
                             (self.ids.monitor.width / _CELL_WIDTH))

  def unregister_dmx_listener(self):
    """Executed when the ScreenManager switches away from the monitor screen"""
    if self.selected_universe:
      self.ola_listener.stop_dmx_listener(self.selected_universe.id,
                                          None, None)

  def register_dmx_listener(self):
    """Executed when the ScreenManager switches to the monitor screen"""
    if self.selected_universe:
      self.ola_listener.fetch_dmx(self.selected_universe.id,
                                  lambda s,u,d: self.update_data(d))
      self.ola_listener.start_dmx_listener(self.selected_universe.id,
                                           self.update_data, None)

