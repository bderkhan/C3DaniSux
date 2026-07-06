"""
Copyright (c) 2021-, IQ.Pilot contributors.

This file is part of IQ.Pilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import time
from collections.abc import Callable

import pyray as rl
from openpilot.common.params import Params, UnknownKeyName
from openpilot.system.ui.lib.application import gui_app, MousePos, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.iqpilot.widgets.toggle import IQToggle
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.button import Button, ButtonStyle
from openpilot.system.ui.widgets.label import gui_label
from openpilot.system.ui.widgets.list_view import ListItem, ToggleAction, ItemAction, MultipleButtonAction, ButtonAction, \
                                                  _resolve_value, BUTTON_WIDTH, BUTTON_HEIGHT, TEXT_PADDING, DualButtonAction
from openpilot.system.ui.widgets.scroller_tici import LineSeparator, LINE_COLOR, LINE_PADDING
from openpilot.system.ui.iqpilot.lib.styles import style
from openpilot.system.ui.iqpilot.widgets.option_control import IQOptionControl, LABEL_WIDTH


class Spacer(Widget):
  def __init__(self, height: int = 1):
    super().__init__()
    self._rect = rl.Rectangle(0, 0, 0, height)

  def set_parent_rect(self, parent_rect: rl.Rectangle) -> None:
    super().set_parent_rect(parent_rect)
    self._rect.width = parent_rect.width

  def _render(self, _):
    rl.draw_rectangle(int(self._rect.x), int(self._rect.y), int(self._rect.x + self._rect.width), int(self._rect.y), rl.Color(0,0,0,0))


class IQToggleAction(ToggleAction):
  def __init__(self, initial_state: bool = False, width: int = style.TOGGLE_WIDTH, enabled: bool | Callable[[], bool] = True,
               callback: Callable[[bool], None] | None = None, param: str | None = None):
    ToggleAction.__init__(self, initial_state, width, enabled, callback)
    self.toggle = IQToggle(initial_state=initial_state, callback=callback, param=param)


class SafeIQToggleAction(IQToggleAction):
  """Toggle action that tolerates a param missing from the compiled params registry."""

  def __init__(self, param: str, default_on: bool = True, width: int = style.TOGGLE_WIDTH,
               enabled: bool | Callable[[], bool] = True, callback: Callable[[bool], None] | None = None):
    self._param = param
    self._default_on = default_on
    self._params = Params()
    self._user_callback = callback

    def _safe_callback(state: bool):
      try:
        self._params.put_bool(self._param, state)
      except UnknownKeyName:
        return
      if self._user_callback:
        self._user_callback(state)

    try:
      initial_state = self._params.get_bool(param)
    except UnknownKeyName:
      initial_state = default_on
    super().__init__(initial_state=initial_state, width=width, enabled=enabled, callback=_safe_callback, param=param)

  def _refresh_checked(self):
    try:
      self.toggle.set_state(self._params.get_bool(self._param))
    except UnknownKeyName:
      self.toggle.set_state(self._default_on)

  def _render(self, rect: rl.Rectangle) -> bool:
    self._refresh_checked()
    return super()._render(rect)


class IQButton(Button):
  def _update_state(self):
    super()._update_state()
    if self.enabled:
      if self.is_pressed:
        self._background_color = style.BUTTON_OFF_PRESSED
      else:
        self._background_color = style.BUTTON_ENABLED_OFF
    else:
      self._background_color = style.BUTTON_DISABLED
      self._label.set_text_color(style.BUTTON_TEXT_DISABLED)


class NavSectionButton(IQButton):
  """A clean navigable section row: icon (left) + label + chevron (right), full width."""

  def __init__(self, text, icon_path: str | None = None, click_callback: Callable | None = None):
    super().__init__(text, click_callback=click_callback, button_style=ButtonStyle.NORMAL, text_padding=0)
    self._text_src = text
    self._icon = gui_app.texture(icon_path, 64, 64, keep_aspect_ratio=True) if icon_path else None
    self._chevron = gui_app.texture("icons/iq/chevron_right.png", 50, 50, keep_aspect_ratio=True)
    self._border_radius = 40

  def _render(self, _):
    rect = self._rect
    roundness = self._border_radius / (min(rect.width, rect.height) / 2)
    rl.draw_rectangle_rounded(rect, roundness, 10, self._background_color)

    cy = rect.y + rect.height / 2
    x = rect.x + 44
    if self._icon:
      rl.draw_texture(self._icon, int(x), int(cy - self._icon.height / 2), rl.WHITE)
      x += self._icon.width + 30

    text = self._text_src() if callable(self._text_src) else self._text_src
    font = gui_app.font(FontWeight.MEDIUM)
    fs = 58
    ts = measure_text_cached(font, text, fs)
    rl.draw_text_ex(font, text, rl.Vector2(int(x), int(cy - ts.y / 2)), fs, 0, rl.WHITE)

    rl.draw_texture(self._chevron, int(rect.x + rect.width - 44 - self._chevron.width),
                    int(cy - self._chevron.height / 2), rl.Color(170, 172, 178, 255))


class IQSimpleButtonAction(ItemAction):
  def __init__(self, button_text: str | Callable[[], str], callback: Callable | None = None,
               enabled: bool | Callable[[], bool] = True, button_width: int = style.SIMPLE_BUTTON_WIDTH):
    super().__init__(width=button_width, enabled=enabled)
    self.button_action = IQButton(button_text, click_callback=callback, button_style=ButtonStyle.NORMAL,
                                  border_radius=48)

  def set_touch_valid_callback(self, touch_callback: Callable[[], bool]) -> None:
    super().set_touch_valid_callback(touch_callback)
    self.button_action.set_touch_valid_callback(touch_callback)

  def _render(self, rect: rl.Rectangle) -> bool | int | None:
    self.button_action.set_enabled(self.enabled)
    return self.button_action.render(rect)


class IQButtonAction(ButtonAction):
  def __init__(self, text: str | Callable[[], str], width: int = style.BUTTON_ACTION_WIDTH, enabled: bool | Callable[[], bool] = True):
    super().__init__(text=text, width=width, enabled=enabled)
    self._value_color: rl.Color = style.ITEM_TEXT_VALUE_COLOR
    self._loading = False

  def set_value(self, value: str | Callable[[], str], color: rl.Color = style.ITEM_TEXT_VALUE_COLOR):
    self._value_source = value
    self._value_color = color

  def set_loading(self, loading: bool):
    self._loading = loading

  def _render(self, rect: rl.Rectangle) -> bool:
    """Duplicate of ButtonAction._render, with additional value rendering"""
    self._button.set_text(self.text)
    self._button.set_enabled(_resolve_value(self.enabled))
    button_rect = rl.Rectangle(rect.x + rect.width - BUTTON_WIDTH, rect.y + (rect.height - BUTTON_HEIGHT) / 2, BUTTON_WIDTH, BUTTON_HEIGHT)
    self._button.render(button_rect)

    value_rect = rl.Rectangle(rect.x, rect.y, rect.width - BUTTON_WIDTH - TEXT_PADDING, rect.height)
    if self._loading:
      # Teal spinner in the value slot (next to the button) while an action is in progress
      cx = value_rect.x + value_rect.width - 28
      cy = rect.y + rect.height / 2
      ang = (rl.get_time() * 280) % 360
      rl.draw_ring(rl.Vector2(cx, cy), 16, 24, 0, 360, 40, rl.Color(255, 255, 255, 26))
      rl.draw_ring(rl.Vector2(cx, cy), 16, 24, ang, ang + 100, 28, rl.Color(16, 185, 169, 255))
    elif self.value:
      if measure_text_cached(self._font, self.value, style.ITEM_TEXT_FONT_SIZE).x > value_rect.width:
        self._value_label.set_text(self.value)
        self._value_label.set_font_size(style.ITEM_TEXT_FONT_SIZE)
        self._value_label.set_text_color(self._value_color)
        self._value_label.render(value_rect)
      else:
        gui_label(value_rect, self.value, font_size=style.ITEM_TEXT_FONT_SIZE, color=self._value_color,
                  font_weight=FontWeight.NORMAL, alignment=rl.GuiTextAlignment.TEXT_ALIGN_LEFT,
                  alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE)

    pressed = self._pressed
    self._pressed = False
    return pressed


class IQDualButtonAction(DualButtonAction):
  def __init__(self, left_text: str | Callable[[], str], right_text: str | Callable[[], str], left_callback: Callable | None = None,
               right_callback: Callable | None = None, enabled: bool | Callable[[], bool] = True, border_radius: int = 40):
    DualButtonAction.__init__(self, left_text, right_text, left_callback, right_callback, enabled)
    # Neutral left action uses IQButton (lighter grey + IQ press states); right keeps its style (e.g. DANGER).
    self.left_button = IQButton(left_text, click_callback=left_callback, button_style=ButtonStyle.NORMAL, text_padding=0)
    self.left_button._border_radius = self.right_button._border_radius = border_radius

  def _render(self, rect: rl.Rectangle):
    button_spacing = 20
    button_height = 150
    button_width = (rect.width - button_spacing) / 2
    button_y = rect.y + (rect.height - button_height) / 2

    left_rect = rl.Rectangle(rect.x, button_y, button_width, button_height)
    right_rect = rl.Rectangle(rect.x + button_width + button_spacing, button_y, button_width, button_height)

    # expand one to full width if other is not visible
    if not self.left_button.is_visible:
      right_rect.x = rect.x
      right_rect.width = rect.width
    elif not self.right_button.is_visible:
      left_rect.width = rect.width

    # Render buttons
    self.left_button.render(left_rect)
    self.right_button.render(right_rect)


# Segmented (multi-button) control — dark container with a teal "active" pill + soft glow
SEG_CONTAINER_BG = rl.Color(42, 45, 52, 255)
SEG_CONTAINER_BORDER = rl.Color(255, 255, 255, 22)
SEG_ACTIVE = rl.Color(18, 191, 173, 255)
SEG_TEXT_SELECTED = rl.Color(8, 16, 16, 255)
SEG_H_PAD = 8
SEG_V_PAD = 9
SEG_TEXT_PAD = 16


class IQMultipleButtonAction(MultipleButtonAction):
  def __init__(self, buttons: list[str | Callable[[], str]], button_width: int, selected_index: int = 0, callback: Callable | None = None,
               param: str | None = None):
    MultipleButtonAction.__init__(self, buttons, button_width, selected_index, callback)
    self.param_key = param
    self.params = Params()
    if self.param_key:
      self.selected_button = int(self.params.get(self.param_key, return_default=True))
    self._anim_x: float | None = None
    self._double_click_callbacks: dict[int, Callable] = {}
    self._last_click_button: int = -1
    self._last_click_time: float = 0.0

  def set_double_click_callback(self, button_index: int, callback: Callable) -> None:
    self._double_click_callbacks[button_index] = callback

  def _render(self, rect: rl.Rectangle):

    button_y = rect.y + (rect.height - style.BUTTON_HEIGHT) / 2

    segment_width = rect.width / len(self.buttons)
    track_rect = rl.Rectangle(rect.x, button_y, rect.width, style.BUTTON_HEIGHT)

    selected_enabled = self._is_button_enabled(self.selected_button)

    # Dark container
    rl.draw_rectangle_rounded(track_rect, 0.35, 20, SEG_CONTAINER_BG)
    border_color = SEG_CONTAINER_BORDER if self.enabled else style.MBC_DISABLED
    rl.draw_rectangle_rounded_lines_ex(track_rect, 0.35, 20, 2, border_color)

    # Animated active pill
    target_x = track_rect.x + self.selected_button * segment_width
    if self._anim_x is None:
      self._anim_x = target_x
    self._anim_x += (target_x - self._anim_x) * 0.2

    hl = rl.Rectangle(self._anim_x + SEG_H_PAD, button_y + SEG_V_PAD,
                      segment_width - 2 * SEG_H_PAD, style.BUTTON_HEIGHT - 2 * SEG_V_PAD)

    if selected_enabled:
      # Soft teal glow behind the active pill
      for grow, alpha in ((16, 16), (10, 28), (5, 44)):
        glow = rl.Rectangle(hl.x - grow, hl.y - grow, hl.width + 2 * grow, hl.height + 2 * grow)
        rl.draw_rectangle_rounded(glow, 0.6, 20, rl.Color(SEG_ACTIVE.r, SEG_ACTIVE.g, SEG_ACTIVE.b, alpha))
      rl.draw_rectangle_rounded(hl, 0.6, 20, SEG_ACTIVE)
    else:
      rl.draw_rectangle_rounded(hl, 0.6, 20, style.MBC_DISABLED)

    # Labels
    for i, _text in enumerate(self.buttons):
      button_x = track_rect.x + i * segment_width
      button_enabled = self._is_button_enabled(i)

      text = _resolve_value(_text, "")
      font_size = 40
      max_text_width = max(1, segment_width - SEG_TEXT_PAD * 2)
      text_size = measure_text_cached(self._font, text, font_size)
      while text_size.x > max_text_width and font_size > 30:
        font_size -= 2
        text_size = measure_text_cached(self._font, text, font_size)
      text_x = button_x + (segment_width - text_size.x) / 2
      text_y = button_y + (style.BUTTON_HEIGHT - text_size.y) / 2

      if i == self.selected_button and selected_enabled:
        text_color = SEG_TEXT_SELECTED
      elif button_enabled:
        text_color = style.ITEM_TEXT_COLOR
      else:
        text_color = style.MBC_DISABLED
      rl.draw_text_ex(self._font, text, rl.Vector2(text_x, text_y), font_size, 0, text_color)

  def _handle_mouse_release(self, mouse_pos: MousePos):
    if self.enabled:
      button_y = self._rect.y + (self._rect.height - style.BUTTON_HEIGHT) / 2
      segment_width = self._rect.width / len(self.buttons)
      for i in range(len(self.buttons)):
        button_rect = rl.Rectangle(self._rect.x + i * segment_width, button_y, segment_width, style.BUTTON_HEIGHT)
        if rl.check_collision_point_rec(mouse_pos, button_rect):
          if not self._is_button_enabled(i):
            break
          self.selected_button = i
          if self.callback:
            self.callback(i)
          break

    if self.param_key:
      self.params.put(self.param_key, self.selected_button)

    if not self._double_click_callbacks:
      return

    button_y = self._rect.y + (self._rect.height - style.BUTTON_HEIGHT) / 2
    clicked_button = -1
    segment_width = self._rect.width / len(self.buttons)
    for i in range(len(self.buttons)):
      button_rect = rl.Rectangle(self._rect.x + i * segment_width, button_y, segment_width, style.BUTTON_HEIGHT)
      if rl.check_collision_point_rec(mouse_pos, button_rect):
        clicked_button = i
        break

    if clicked_button < 0:
      return

    now = time.monotonic()
    if clicked_button == self._last_click_button and (now - self._last_click_time) < 0.5:
      if clicked_button in self._double_click_callbacks:
        self._double_click_callbacks[clicked_button]()
      self._last_click_button = -1
      self._last_click_time = 0.0
    else:
      self._last_click_button = clicked_button
      self._last_click_time = now


class IQListItem(ListItem):
  def __init__(self, title: str | Callable[[], str] = "", icon: str | None = None, description: str | Callable[[], str] | None = None,
               description_visible: bool = False, callback: Callable | None = None,
               action_item: ItemAction | None = None, inline: bool = True, title_color: rl.Color = style.ITEM_TEXT_COLOR):
    ListItem.__init__(self, title, icon, description, description_visible, callback, action_item)
    self.title_color = title_color
    self.inline = inline
    if not self.inline:
      self._rect.height += style.ITEM_BASE_HEIGHT/1.75
    self.title_badge: tuple[str, rl.Color] | None = None
    self._right_value_source: str | Callable[[], str] | None = None
    self._right_value_font = gui_app.font(FontWeight.NORMAL)
    self._right_value_color: rl.Color = style.ITEM_TEXT_VALUE_COLOR

  def set_title(self, title: str | Callable[[], str] = ""):
    self._title = title

  def set_right_value(self, value: str | Callable[[], str], color: rl.Color = style.ITEM_TEXT_VALUE_COLOR):
    self._right_value_source = value
    self._right_value_color = color

  @property
  def right_value(self) -> str:
    if self._right_value_source is None:
      return ""
    return str(_resolve_value(self._right_value_source, ""))

  def _update_state(self):
    prev_desc = self._prev_description
    super()._update_state()
    if self.description_visible and self._prev_description != prev_desc:
      content_width = int(self._rect.width - style.ITEM_PADDING * 2)
      self._rect.height = self.get_item_height(self._font, content_width)

  def get_item_height(self, font: rl.Font, max_width: int) -> float:
    height = super().get_item_height(font, max_width)

    if self.description_visible:
      height += style.ITEM_PADDING * 1.5

    if not self.inline:
      height += style.ITEM_BASE_HEIGHT / 1.75

    return height

  def show_description(self, show: bool):
    self._set_description_visible(show)

  def get_right_item_rect(self, item_rect: rl.Rectangle) -> rl.Rectangle:
    if not self.action_item:
      return rl.Rectangle(0, 0, 0, 0)

    if not self.inline:
      text_size = measure_text_cached(self._font, self.title, style.ITEM_TEXT_FONT_SIZE)
      action_y = item_rect.y + text_size.y + style.ITEM_PADDING * 3
      return rl.Rectangle(item_rect.x + style.ITEM_PADDING, action_y, item_rect.width - (style.ITEM_PADDING * 2), style.BUTTON_HEIGHT)

    right_width = self.action_item.get_width_hint()
    if right_width == 0:
      return rl.Rectangle(item_rect.x + style.ITEM_PADDING, item_rect.y, item_rect.width - (style.ITEM_PADDING * 2), style.ITEM_BASE_HEIGHT)

    content_width = item_rect.width - (style.ITEM_PADDING * 2)
    title_width = measure_text_cached(self._font, self.title, style.ITEM_TEXT_FONT_SIZE).x
    right_width = min(content_width - title_width, right_width)
    if isinstance(self.action_item, ToggleAction) or isinstance(self.action_item, IQSimpleButtonAction):
      action_x = item_rect.x
    else:
      action_x = item_rect.x + item_rect.width - right_width
    action_y = item_rect.y
    return rl.Rectangle(action_x, action_y, right_width, style.ITEM_BASE_HEIGHT)

  def _draw_title_badge(self, x: float, cy: float):
    """Draw an optional rounded status chip just after the title text."""
    label, color = self.title_badge
    font = gui_app.font(FontWeight.MEDIUM)
    fs = 30
    ts = measure_text_cached(font, label, fs)
    pad_x = 18
    chip = rl.Rectangle(x, cy - (ts.y + 16) / 2, ts.x + pad_x * 2, ts.y + 16)
    rl.draw_rectangle_rounded(chip, 0.5, 12, color)
    lum = 0.299 * color.r + 0.587 * color.g + 0.114 * color.b
    txt_color = rl.Color(10, 14, 16, 255) if lum > 140 else rl.WHITE
    rl.draw_text_ex(font, label, rl.Vector2(chip.x + pad_x, cy - ts.y / 2), fs, 0, txt_color)

  def _render(self, _):
    if not self.is_visible:
      return

    # Don't draw items that are not in parent's viewport
    if (self._rect.y + self.rect.height) <= self._parent_rect.y or self._rect.y >= (self._parent_rect.y + self._parent_rect.height):
      return

    content_x = self._rect.x + style.ITEM_PADDING
    text_x = content_x
    left_action_item = isinstance(self.action_item, ToggleAction) or isinstance(self.action_item, IQSimpleButtonAction)

    if left_action_item:
      item_height = style.SIMPLE_BUTTON_HEIGHT if isinstance(self.action_item, IQSimpleButtonAction) else style.TOGGLE_HEIGHT
      left_rect = rl.Rectangle(
        content_x,
        self._rect.y + (style.ITEM_BASE_HEIGHT - item_height) // 2,
        self.action_item.rect.width,
        item_height
      )
      text_x = left_rect.x + left_rect.width + style.ITEM_PADDING * 1.5

      # Draw title
      if self.title:
        self._text_size = measure_text_cached(self._font, self.title, style.ITEM_TEXT_FONT_SIZE)
        item_y = self._rect.y + (style.ITEM_BASE_HEIGHT - self._text_size.y) // 2
        rl.draw_text_ex(self._font, self.title, rl.Vector2(text_x, item_y), style.ITEM_TEXT_FONT_SIZE, 0, self.title_color)

      value_text = self.right_value
      if value_text:
        # area from after the title to the right edge of the row
        value_rect = rl.Rectangle(
          text_x,  # start at the beginning of the text area
          self._rect.y,
          self._rect.width - (text_x - self._rect.x) - style.ITEM_PADDING,
          style.ITEM_BASE_HEIGHT,
        )
        if value_rect.width > 0:
          gui_label(value_rect, value_text, font_size=style.ITEM_TEXT_FONT_SIZE, color=self._right_value_color, font_weight=FontWeight.NORMAL,
                    alignment=rl.GuiTextAlignment.TEXT_ALIGN_RIGHT, alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE)

      # Render toggle and handle callback
      if self.action_item.render(left_rect) and self.action_item.enabled:
        if self.callback:
          self.callback()

    else:
      if self.title:
        # Draw main text
        self._text_size = measure_text_cached(self._font, self.title, style.ITEM_TEXT_FONT_SIZE)
        item_y = self._rect.y + (style.ITEM_BASE_HEIGHT - self._text_size.y) // 2 if self.inline else self._rect.y + style.ITEM_PADDING * 1.5
        rl.draw_text_ex(self._font, self.title, rl.Vector2(text_x, item_y), style.ITEM_TEXT_FONT_SIZE, 0, self.title_color)
        if self.title_badge:
          self._draw_title_badge(text_x + self._text_size.x + 24, item_y + self._text_size.y / 2)

      # Draw right item if present
      if self.action_item:
        right_rect = self.get_right_item_rect(self._rect)
        if self.action_item.render(right_rect) and self.action_item.enabled:
          # Right item was clicked/activated
          if self.callback:
            self.callback()

    # Draw description if visible
    if self.description_visible:
      content_width = int(self._rect.width - style.ITEM_PADDING * 2)
      description_height = self._html_renderer.get_total_height(content_width)

      desc_y = self._rect.y + style.ITEM_DESC_V_OFFSET
      if not self.inline and self.action_item:
        desc_y = self.action_item.rect.y + style.ITEM_DESC_V_OFFSET - style.ITEM_PADDING * 0.5

      description_rect = rl.Rectangle(self._rect.x + style.ITEM_PADDING, desc_y, content_width, description_height)
      self._html_renderer.render(description_rect)


def simple_button_item_iq(button_text: str | Callable[[], str], callback: Callable | None = None,
                          enabled: bool | Callable[[], bool] = True, button_width: int = style.SIMPLE_BUTTON_WIDTH) -> IQListItem:
  action = IQSimpleButtonAction(button_text=button_text, enabled=enabled, callback=callback, button_width=button_width)
  return IQListItem(title="", callback=callback, description="", action_item=action)


def toggle_item_iq(title: str | Callable[[], str], description: str | Callable[[], str] | None = None, initial_state: bool = False,
                   callback: Callable | None = None, icon: str = "", enabled: bool | Callable[[], bool] = True, param: str | None = None) -> IQListItem:
  action = IQToggleAction(initial_state=initial_state, enabled=enabled, callback=callback, param=param)
  return IQListItem(title=title, description=description, action_item=action, icon=icon, callback=callback)


def multiple_button_item_iq(title: str | Callable[[], str], description: str | Callable[[], str], buttons: list[str | Callable[[], str]],
                            selected_index: int = 0, button_width: int = style.BUTTON_ACTION_WIDTH, callback: Callable | None = None,
                            icon: str = "", param: str | None = None, inline: bool = False) -> IQListItem:
  action = IQMultipleButtonAction(buttons, button_width, selected_index, callback=callback, param=param)
  return IQListItem(title=title, description=description, icon=icon, action_item=action, inline=inline)


def option_item_iq(title: str | Callable[[], str], param: str,
                   min_value: int, max_value: int, description: str | Callable[[], str] | None = None,
                   value_change_step: int = 1, on_value_changed: Callable[[int], None] | None = None,
                   enabled: bool | Callable[[], bool] = True,
                   icon: str = "", label_width: int = LABEL_WIDTH, value_map: dict[int, int] | None = None,
                   use_float_scaling: bool = False, label_callback: Callable[[int], str] | None = None, inline: bool = False) -> IQListItem:
  action = IQOptionControl(
    param, min_value, max_value, value_change_step,
    enabled, on_value_changed, value_map, label_width, use_float_scaling, label_callback
  )
  return IQListItem(title=title, description=description, action_item=action, icon=icon, inline=inline)


def button_item_iq(title: str | Callable[[], str], button_text: str | Callable[[], str], description: str | Callable[[], str] | None = None,
                   callback: Callable | None = None, enabled: bool | Callable[[], bool] = True) -> IQListItem:
  action = IQButtonAction(text=button_text, enabled=enabled)
  return IQListItem(title=title, description=description, action_item=action, callback=callback)


def dual_button_item_iq(left_text: str | Callable[[], str], right_text: str | Callable[[], str], left_callback: Callable | None = None,
                        right_callback: Callable | None = None, description: str | Callable[[], str] | None = None,
                        enabled: bool | Callable[[], bool] = True, border_radius: int = 40) -> IQListItem:
  action = IQDualButtonAction(left_text, right_text, left_callback, right_callback, enabled, border_radius)
  return IQListItem(title="", description=description, action_item=action)


# Preferred IQ helper names.
simple_button_item = simple_button_item_iq
toggle_item = toggle_item_iq
multiple_button_item = multiple_button_item_iq
option_item = option_item_iq
button_item = button_item_iq
dual_button_item = dual_button_item_iq


class IQLineSeparator(LineSeparator):
  def __init__(self, height: int = 1):
    super().__init__()
    self._rect = rl.Rectangle(0, 0, 0, height)

  def _render(self, _):
    line_y = int(self._rect.y + self._rect.height // 2)
    rl.draw_line(int(self._rect.x) + LINE_PADDING, line_y,
                 int(self._rect.x + self._rect.width) - LINE_PADDING, line_y,
                 LINE_COLOR)
