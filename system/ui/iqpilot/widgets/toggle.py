"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
from collections.abc import Callable

import pyray as rl
from openpilot.common.params import Params
from openpilot.system.ui.lib.application import MousePos
from openpilot.system.ui.widgets.toggle import Toggle
from openpilot.system.ui.iqpilot.lib.styles import style

KNOB_PADDING = 10
KNOB_RADIUS = style.TOGGLE_BG_HEIGHT / 2 - KNOB_PADDING

# Track colors: grey when off, teal gradient (left -> right) when on.
OFF_COLOR = rl.Color(58, 61, 68, 255)
ON_START = rl.Color(52, 231, 200, 255)    # #34E7C8
ON_END = rl.Color(4, 140, 155, 255)       # #048C9B
OFF_DISABLED = rl.Color(45, 47, 52, 255)
ON_START_DISABLED = rl.Color(40, 110, 100, 255)
ON_END_DISABLED = rl.Color(18, 78, 86, 255)
KNOB_ON = rl.WHITE
KNOB_DISABLED = rl.Color(150, 150, 150, 255)
TRACK_BORDER = rl.Color(0, 0, 0, 45)


class IQToggle(Toggle):
  def __init__(self, initial_state=False, callback: Callable[[bool], None] | None = None, param: str | None = None):
    self.param_key = param
    self.params = Params()
    if self.param_key:
      initial_state = self.params.get_bool(self.param_key)
    Toggle.__init__(self, initial_state, callback)

  def set_rect(self, rect: rl.Rectangle):
    self._rect = rl.Rectangle(rect.x, rect.y, style.TOGGLE_WIDTH, style.TOGGLE_HEIGHT)

  def _handle_mouse_release(self, mouse_pos: MousePos):
    super()._handle_mouse_release(mouse_pos)
    if self._enabled and self.param_key:
      self.params.put_bool(self.param_key, self._state)

  def _render(self, rect: rl.Rectangle):
    if self.param_key:
      try:
        param_state = self.params.get_bool(self.param_key)
        if param_state != self._state:
          self.set_state(param_state)
      except Exception:
        pass
    self.update()
    self._rect.y -= style.ITEM_PADDING / 2

    # Track color blends grey -> teal gradient as the toggle animates on.
    if self._enabled:
      c_start = self._blend_color(OFF_COLOR, ON_START, self._progress)
      c_end = self._blend_color(OFF_COLOR, ON_END, self._progress)
      knob_color = KNOB_ON
    else:
      c_start = self._blend_color(OFF_DISABLED, ON_START_DISABLED, self._progress)
      c_end = self._blend_color(OFF_DISABLED, ON_END_DISABLED, self._progress)
      knob_color = KNOB_DISABLED

    x = self._rect.x
    y = self._rect.y
    w = style.TOGGLE_WIDTH
    h = style.TOGGLE_BG_HEIGHT
    r = h / 2

    # Gradient pill: rounded end caps + horizontal gradient body
    rl.draw_circle(int(x + r), int(y + r), r, c_start)
    rl.draw_circle(int(x + w - r), int(y + r), r, c_end)
    rl.draw_rectangle_gradient_h(int(x + r), int(y), int(w - 2 * r), int(h), c_start, c_end)

    # Subtle outline for definition
    rl.draw_rectangle_rounded_lines_ex(rl.Rectangle(x, y, w, h), 1.0, 16, 2, TRACK_BORDER)

    # Knob position
    left_edge = x + KNOB_PADDING
    right_edge = x + w - KNOB_PADDING
    knob_travel_distance = right_edge - left_edge - 2 * KNOB_RADIUS
    knob_x = left_edge + KNOB_RADIUS + knob_travel_distance * self._progress
    knob_y = y + h / 2

    # Soft drop shadow under the knob for depth
    rl.draw_circle(int(knob_x), int(knob_y + 4), KNOB_RADIUS + 1, rl.Color(0, 0, 0, 38))
    rl.draw_circle(int(knob_x), int(knob_y + 2), KNOB_RADIUS, rl.Color(0, 0, 0, 30))
    rl.draw_circle(int(knob_x), int(knob_y), KNOB_RADIUS, knob_color)

