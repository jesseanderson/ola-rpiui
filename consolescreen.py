import kivy
from array import array
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen

_DMX_CHANNELS = 512
SEND_DATA_INTERVAL = 1

Builder.load_file('consolescreen.kv')

class Fader(GridLayout):
  """An individual fader, contains a channel number, a slider for control,
     and a numeric represetation of that value.

     Args:
       ola_listener: A OLAListener object to send ola requests
       channel_number: The index of the channel, typically between
                       1 and 512, inclusive.
  """
  def __init__(self, ola_listener, channel_number, **kwargs):
    super(Fader, self).__init__(**kwargs)
    self.ola_listener = ola_listener
    self.channel_number = channel_number
    self.selected_universe = None
    self.ids.channel_label.text = str(self.channel_number)
    self.ids.channel_value.text = str(int(self.ids.channel_slider.value))
    self.ids.channel_slider.bind(value=self.update_fader_value)

  def send_dmx_request(self, instance, value):
    """Responsible for making the OLAListener call for sending DMX
       upon fader change.
    """
    self.ola_listener.set_dmx_channel(self.selected_universe.id,
                                      self.channel_number,
                                      int(value))

  def update_fader_value(self, instance, value):
    """Updates the fader value below the slider with an accurate value"""
    self.ids.channel_value.text = str(int(value))

class ConsoleScreen(Screen):
  """This screen has a bank of faders for sending DMX on any channel

     Args:
       ola_listener: An OLAListener object to send ola requests
  """
  def __init__(self, ola_listener, **kwargs):
    super(ConsoleScreen, self).__init__(**kwargs)
    self.ola_listener = ola_listener
    self.on_pre_enter = lambda: Clock.schedule_interval(self.send_console_data,
                                                        SEND_DATA_INTERVAL)
    self.on_leave = lambda: Clock.unschedule(self.send_console_data)
    self.channels = []
    self.selected_universe = None
    self.ids.faders.width = 40 * _DMX_CHANNELS
    for channel_index in range(_DMX_CHANNELS):
      channel = Fader(self.ola_listener, channel_index+1)
      self.channels.append(channel)
      self.ids.faders.add_widget(channel)

  def change_selected_universe(self, universe):
    """Give a channel id, sends that id to all faders on the screen"""
    for channel in self.channels:
      channel.selected_universe = universe
    self.selected_universe = universe

  def send_console_data(self, dt):
    """The console will send its current state to the OLA client"""
    data = []
    for channel in self.channels:
      data.append(int(channel.ids.channel_slider.value))
    self.ola_listener.send_dmx(self.selected_universe.id, array('B', data))

  def update_data(self, data):
    """The console screen must remain updated with the actual DMX data,
       so this method will send that data to all the channels on the screen.

       Args:
         data: an array of size 512 containing the dmx data
    """
    for channel in self.channels:
      channel.ids.channel_slider.value = data[channel.channel_number-1]

  def update_console_data(self):
    """Executed when the ScreenManager switches to the console screen,
       ensures all the faders have accurate readings at the time of
       swiching to the new screen.
    """
    if self.selected_universe:
      self.ola_listener.fetch_dmx(self.selected_universe.id,
                                  lambda s,u,d: self.update_data(d))
