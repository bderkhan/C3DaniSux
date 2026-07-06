"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
import pyray as rl

from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr, tr_noop
from openpilot.system.ui.iqpilot.widgets.list_view import toggle_item, multiple_button_item, IQListItem, IQLineSeparator
from openpilot.system.ui.widgets.scroller_tici import Scroller
from openpilot.system.ui.widgets import Widget
from .display import DisplayLayout

CHEVRON_INFO_DESCRIPTION = {
  "enabled": tr_noop("Display useful metrics below the chevron that tracks the lead car " +
                     "only applicable to cars with IQ.Pilot longitudinal control."),
  "disabled": tr_noop("This feature requires IQ.Pilot longitudinal control to be available.")
}


class VisualsLayout(Widget):
  def __init__(self):
    super().__init__()

    self._params = Params()
    self._display_layout = DisplayLayout()
    items = self._initialize_items()
    self._scroller = Scroller(items, line_separator=True, spacing=0)

  def _initialize_items(self):
    self._toggle_defs = {
      "BlindSpot": (
        lambda: tr("Show Blind Spot Warnings"),
        tr("Enabling this will display warnings when a vehicle is detected in your " +
           "blind spot as long as your car has BSM supported."),
        None,
      ),
      "IQExpandedStatus": (
        lambda: tr("Expanded Status Bar"),
        tr("Show temperature, vehicle, and Konn3kt status as expanded indicators on the offroad home screen, like the classic UI."),
        None,
      ),
      "TorqueBar": (
        lambda: tr("Steering Arc"),
        tr("Display steering arc on the driving screen when lateral control is enabled."),
        None,
      ),
      "RoadNameToggle": (
        lambda: tr("Display Road Name"),
        tr("Displays the name of the road the car is traveling on." +
           "<br>The OpenStreetMap database for the location must already be installed."),
        None,
      ),
      "ShowTurnSignals": (
        lambda: tr("Display Turn Signals"),
        tr("When enabled, visual turn indicators are drawn on the HUD."),
        None,
      ),
      "RocketFuel": (
        lambda: tr("Real-time Acceleration Bar"),
        tr("Show an indicator on the left side of the screen to display real-time vehicle acceleration and deceleration. " +
           "This displays what the car is currently doing, not what the planner is requesting."),
        None,
      ),
    }
    self._toggles = {}
    for param, (title, desc, callback) in self._toggle_defs.items():
      toggle = toggle_item(
        title=title,
        description=desc,
        param=param,
        initial_state=ui_state.params.get_bool(param),
        callback=callback,
      )
      self._toggles[param] = toggle

    self._chevron_info = multiple_button_item(
      title=lambda: tr("Display Metrics Below Chevron"),
      description="",
      buttons=[lambda: tr("Off"), lambda: tr("Distance"), lambda: tr("Speed"), lambda: tr("Time"), lambda: tr("All")],
      param="ChevronInfo",
      inline=False
    )
    self._dev_ui_info = toggle_item(
      title=lambda: tr("Onroad Developer UI"),
      description=lambda: tr("Display real-time parameters and metrics from various sources."),
      initial_state=bool(int(ui_state.params.get("DevUIInfo", return_default=True))),
      callback=self._set_dev_ui_info,
    )

    # Display items from DisplayLayout (index 0 is Force Mici UI — not moved here)
    display_items = self._display_layout._scroller._items[1:]

    items = [
      IQListItem(title=lambda: tr("Display"), description="", action_item=None, inline=True,
                 title_color=rl.Color(16, 185, 169, 255)),
      IQLineSeparator(20),
      *display_items,
      IQLineSeparator(60),
    ] + list(self._toggles.values()) + [
      self._chevron_info,
      self._dev_ui_info,
    ]
    return items

  def _update_state(self):
    super()._update_state()

    for param in self._toggle_defs:
      self._toggles[param].action_item.set_state(self._params.get_bool(param))

    self._dev_ui_info.action_item.set_state(bool(int(ui_state.params.get("DevUIInfo", return_default=True))))

    if ui_state.has_longitudinal_control:
      self._chevron_info.set_description(tr(CHEVRON_INFO_DESCRIPTION["enabled"]))
      self._chevron_info.action_item.set_selected_button(ui_state.params.get("ChevronInfo", return_default=True))
      self._chevron_info.action_item.set_enabled(True)
    else:
      self._chevron_info.set_description(tr(CHEVRON_INFO_DESCRIPTION["disabled"]))
      self._chevron_info.action_item.set_enabled(False)
      ui_state.params.put("ChevronInfo", 0)

  def _render(self, rect):
    self._scroller.render(rect)

  def _set_dev_ui_info(self, enabled: bool):
    ui_state.params.put("DevUIInfo", 3 if enabled else 0)

  def show_event(self):
    self._display_layout.show_event()
    self._scroller.show_event()
    if not ui_state.has_longitudinal_control:
      self._chevron_info.set_description(tr(CHEVRON_INFO_DESCRIPTION["disabled"]))
      self._chevron_info.show_description(True)
