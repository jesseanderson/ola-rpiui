#!/usr/bin/python

"""This is a calibration utility intended to set an HIDInput with a
   correct bounding box in local configuration.
"""

import kivy
kivy.require('1.8.0')
from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.layout import Layout
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

  def run_calibration(self, p1, p2, p3, p4):
    avg_x1 = (p1[0] + p3[0]) / 2
    avg_x2 = (p2[0] + p4[0]) / 2
    avg_y1 = (p1[1] + p2[1]) / 2
    avg_y2 = (p3[1] + p3[1]) / 2
    min_position_x = avg_x1 - (avg_x2 - avg_x1) / 2
    max_position_x = avg_x2 + (avg_x2 - avg_x1) / 2
    min_position_y = avg_y1 - (avg_y2 - avg_y1) / 2
    max_position_y = avg_y2 + (avg_y2 - avg_y1) / 2
    Config.set('input', 'ts', 'hidinput,/dev/input/touchscreen'
                              ',min_position_x=' + str(int(min_position_x)) +
                              ',max_position_x=' + str(int(max_position_x)) +
                              ',min_position_y=' + str(int(min_position_y)) +
                              ',max_position_y=' + str(int(max_position_y)))
    Config.write()

  def point_1(self, event):
    self.layout.on_touch_up = lambda e: self.point_2(e, event.pos)

  def point_2(self, event, p1):
    self.layout.on_touch_up = lambda e: self.point_3(e, p1, event.pos)

  def point_3(self, event, p1, p2):
    self.layout.on_touch_up = lambda e: self.point_4(e, p1, p2, event.pos)

  def point_4(self, event, p1, p2, p3):
    self.run_calibration(p1, p2, p3, event.pos)

if __name__ == '__main__':
  Calibration().run()

