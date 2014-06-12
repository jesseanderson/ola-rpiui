import math
import kivy
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

_CELL_WIDTH = 32
_CELL_HEIGHT = 32
_DMX_CHANNELS = 512

class MonitorCell(GridLayout):
  alpha = NumericProperty(0)

class MonitorScreen(Screen):
  """This screen displays the values of as many DMX channels as will fit
     on the screen.
  """
  #TODO: Make cells look much nicer
  def __init__(self, **kwargs):
    super(MonitorScreen, self).__init__(**kwargs)
    self.channels = []
    for channel_index in range(_DMX_CHANNELS):
      channel = MonitorCell(width=_CELL_WIDTH,height=_CELL_HEIGHT)
      channel.ids.channel.text = str(channel_index)
      self.channels.append(channel)
      self.ids.grid.add_widget(channel)

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
