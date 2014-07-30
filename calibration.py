#!/usr/bin/python

"""This is a calibration utility intended to set an HIDInput with a
   correct bounding box in local configuration.
"""

import kivy
kivy.require('1.8.0')
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

Builder.load_string('''
#:kivy 1.8.0
#:import KivyLexer kivy.extras.highlight.KivyLexer
#:import Factory kivy.factory.Factory

<Layout>:
    canvas.before:
		Color:
			rgb: .2, .2, .2
		Rectangle:
			size: self.size
''')

class Calibration(App):
  def build(self):
    self.title = 'Kivy HID Touchscreen Calibration'
    self.layout = BoxLayout(orientation='vertical')
    self.layout.on_touch_up = self.point_1
    return self.layout

  def run_calibration(self):
    pass

  def point_1(self, event):
    print event

  def point_2(self, event):
    pass

  def point_3(self, event):
    pass

  def point_4(self, event):
    pass

if __name__ == '__main__':
  Calibration().run()

