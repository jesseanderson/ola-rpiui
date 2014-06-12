import math
import kivy
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label

class MonitorScreen(Screen):
  """This screen displays the values of as many DMX channels as will fit
     on the screen.
  """
  #TODO: Make cells look much nicer
  def __init__(self, **kwargs):
    super(MonitorScreen, self).__init__(**kwargs)
    self.channels = []
    for channel_index in range(512):
      channel = Label(text='X',size_hint=(None,None),width=32,height=32)
      self.channels.append(channel)
      self.ids.grid.add_widget(channel)

  def update_data(self, data):
    """Takes the new data and displays it in all 512 cells

       Args:
         data: an array of size 512 containing the dmx data
    """
    index = 0
    for channel in data:
      self.channels[index].text = str(channel)
      index = index + 1

  def update_grid_height(self):
    """The grid height must be as high as its last visible child in order
       for the ScrollView to work as intended.
    """
    self.ids.grid.height = 32 * math.ceil(512.0 / (self.ids.monitor.width / 32))
