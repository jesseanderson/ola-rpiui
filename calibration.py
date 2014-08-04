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
from evdev import InputDevice, ecodes
import time

INPUT_DEVICE_PATH = '/dev/input/touchscreen'

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
    self.input_device = InputDevice(INPUT_DEVICE_PATH)
    return self.layout

  def on_start(self):
    self.point_1()

  def run_calibration(self, p1, p2, p3, p4):
    avg_x1 = (p1[1] + p3[1]) / 2
    avg_x2 = (p2[1] + p4[1]) / 2
    avg_y1 = (p1[0] + p2[0]) / 2
    avg_y2 = (p3[0] + p4[0]) / 2
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

  def pull_coord(self):
    x_list = []
    y_list = []
    touch_started = False
    touch_completed = False
    while not touch_completed:
      time.sleep(0.1)
      try:
        for event in self.input_device.read():
          if event.type == ecodes.EV_ABS:
            touch_started = True
            if event.code == 0:
              x_list.append(event.value)
            if event.code == 1:
              y_list.append(event.value)
      except:
        if touch_started:
          touch_completed = True
    return (sum(x_list)/len(x_list), sum(y_list)/len(y_list))

  def point_1(self):
    p1 = self.pull_coord()
    self.point_2(p1)

  def point_2(self, p1):
    p2 = self.pull_coord()
    self.point_3(p1, p2)

  def point_3(self, p1, p2):
    p3 = self.pull_coord()
    self.point_4(p1, p2, p3)

  def point_4(self, p1, p2, p3):
    p4 = self.pull_coord()
    self.run_calibration(p1, p2, p3, p4)

if __name__ == '__main__':
  Calibration().run()

