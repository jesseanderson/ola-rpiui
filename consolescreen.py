"""Defines a Kivy Screen to act as a DMX console."""

import kivy
from array import array
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
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
       selected_universe_service: A UniverseSelectedService object to handle
         the user-selected universe
  """
  def __init__(self, ola_listener, selected_universe_service, **kwargs):
    super(ConsoleScreen, self).__init__(**kwargs)
    self.ola_listener = ola_listener
    self.selected_universe_service = selected_universe_service
    self.selected_universe_service.bind( \
      selected_universe=self.change_selected_universe)
    self.on_enter = self.switch_in
    self.on_leave = self.switch_out
    self.channels = []
    for channel_index in range(_DMX_CHANNELS_TO_SHOW):
      channel = Fader(self.ola_listener,
                      self.send_console_data,
                      channel_index+1)
      self.channels.append(channel)

  def switch_in(self):
    """To be executed when the user starts viewing the screen, this will
        schedule regular sending of DMX and start listening for dmx changes.
    """
    Clock.schedule_interval(self.send_console_data, SEND_DATA_INTERVAL)

  def switch_out(self):
    """To be executed when the user leaves the screen, this will stop the
       DMX listener and stop regular sending of DMX
    """
    Clock.unschedule(self.send_console_data)

  def resize_carousel(self, size):
    """The console screen is broken up into smaller screens that are placed
       on the carousel; when the screen is resized, the number of faders on
       each screen needs to change.

       Args:
         size: [width, height] of the new carousel widget
    """
    width = size[0]
    height = size[1]
    dummy_fader = Fader(self.ola_listener, self.send_console_data, -1)
    channels_per_page = int(width / dummy_fader.width)
    pages = [self.channels[x:x+channels_per_page] for x in
             xrange(0, len(self.channels), channels_per_page)]
    for slide in self.ids.console_car.slides:
      slide.clear_widgets()
    self.ids.console_car.clear_widgets()
    for page in pages:
      slide = StackLayout(size_hint_x=1, size_hint_y=1)
      for cell in page:
        slide.add_widget(cell)
      self.ids.console_car.add_widget(slide)

  def change_selected_universe(self, instance, value):
    """Give a channel id, sends that id to all faders on the screen
       and resets all faders to 0.
    """
    for channel in self.channels:
      channel.ids.channel_slider.value = 0

  def send_console_data(self, dt=0):
    """The console will send its current state to the OLA client"""
    data = []
    for channel in self.channels:
      data.append(int(channel.ids.channel_slider.value))
    self.ola_listener.send_dmx( \
      self.selected_universe_service.selected_universe.id, array('B', data))

  def update_data(self, data):
    """The console screen must remain updated with the actual DMX data,
       so this method will send that data to all the channels on the screen.

       Args:
         data: an array of size 512 containing the dmx data
    """
    for channel in self.channels:
      channel.ids.channel_slider.value = data[channel.channel_number-1]
