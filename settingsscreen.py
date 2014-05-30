import kivy
from kivy.uix.screenmanager import Screen
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListView, ListItemButton

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
