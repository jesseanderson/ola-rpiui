import kivy
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen

_DMX_CHANNELS = 512

Builder.load_file('consolescreen.kv')

class Fader(GridLayout):
  def __init__(self, **kwargs):
    super(Fader, self).__init__(**kwargs)
    self.ids.channel_slider.bind(value=self.update_fader_value)

  def update_fader_value(self, instance, value):
    self.ids.channel_value.text = str(int(value))

class ConsoleScreen(Screen):
  """This screen has a bank of faders for sending DMX on any channel"""
  def __init__(self, **kwargs):
    super(ConsoleScreen, self).__init__(**kwargs)
    self.channels = []
    self.ids.faders.width = 40 * _DMX_CHANNELS
    for channel_index in range(_DMX_CHANNELS):
      channel = Fader()
      channel.ids.channel_label.text = str(channel_index+1)
      channel.ids.channel_value.text = str(int(channel.ids.channel_slider.value))
      self.channels.append(channel)
      self.ids.faders.add_widget(channel)
      
