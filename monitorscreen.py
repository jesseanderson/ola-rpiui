import kivy
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label

class MonitorScreen(Screen):
  """This screen displays the values of as many DMX channels as will fit
     on the screen.
  """
  def __init__(self, **kwargs):
    super(MonitorScreen, self).__init__(**kwargs)
    self.channels = []
    for channel_index in range(512):
      channel = Label(text='X',size_hint=(None,None),width=32,height=32)
      self.channels.append(channel)
      self.ids.grid.add_widget(channel)

  def go_previous_page(self):
    pass

  def go_next_page(self):
    pass
