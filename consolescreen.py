"""Defines a Kivy Screen to act as a DMX console."""

import kivy
from array import array
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen

_DMX_CHANNELS_TO_SHOW = 512
SEND_DATA_INTERVAL = 1

Builder.load_file('consolescreen.kv')

class Fader(GridLayout):
  """An individual fader, contains a channel number, a slider for control,
     and a numeric represetation of that value.

     Args:
       ola_listener: A OLAListener object to send ola requests
       on_change: When a fader is moved, this method will be executed,
                  this will improve fluidity of changes
       channel_number: The index of the channel, typically between
                       1 and 512, inclusive.
  """
  def __init__(self, ola_listener, on_change, channel_number, **kwargs):
    super(Fader, self).__init__(**kwargs)
    self.ola_listener = ola_listener
    self.channel_number = channel_number
    self.selected_universe = None
    self.ids.channel_label.text = str(self.channel_number)
    self.ids.channel_value.text = str(int(self.ids.channel_slider.value))
    self.ids.channel_slider.bind(value=self.update_fader_value)
    self.ids.channel_slider.bind(value=lambda i,v: on_change())

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
    self.on_enter = self.switch_in
    self.on_leave = self.switch_out
    self.channels = []
    self.selected_universe = None
    self.ids.faders.width = 40 * _DMX_CHANNELS_TO_SHOW
    for channel_index in range(_DMX_CHANNELS_TO_SHOW):
      channel = Fader(self.ola_listener,
                      self.send_console_data,
                      channel_index+1)
      self.channels.append(channel)
      self.ids.faders.add_widget(channel)

  def switch_in(self):
    """To be executed when the user starts viewing the screen, this will
        schedule regular sending of DMX and start listening for dmx changes.
    """
    self.ola_listener.start_dmx_listener(self.selected_universe.id,
                                         self.update_data)
    Clock.schedule_interval(self.send_console_data, SEND_DATA_INTERVAL)

  def switch_out(self):
    """To be executed when the user leaves the screen, this will stop the
       DMX listener and stop regular sending of DMX
    """
    Clock.unschedule(self.send_console_data)
    self.ola_listener.stop_dmx_listener(self.selected_universe.id,
                                        self.update_data)

  def change_selected_universe(self, universe):
    """Give a channel id, sends that id to all faders on the screen
       and resets all faders to 0.
    """
    for channel in self.channels:
      channel.ids.channel_slider.value = 0
      channel.selected_universe = universe
    self.selected_universe = universe

  def send_console_data(self, dt=0):
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
