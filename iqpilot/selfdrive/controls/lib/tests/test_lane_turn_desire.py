"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos/
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from cereal import custom, log

from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL
from openpilot.iqpilot.selfdrive.controls.lib.helpers.lane_change import AutoLaneChangeMode
from openpilot.iqpilot.selfdrive.controls.lib.helpers.lane_turn import LANE_CHANGE_SPEED_MIN, LaneTurnController
from openpilot.selfdrive.controls.lib.desire_helper import DesireHelper, TURN_DESIRE_STOP_HOLD_TIME, TURN_DESIRE_STOP_GAP_TIME

TurnDirection = custom.IQTurnSignalDirection


def _fresh_controller() -> LaneTurnController:
  hub = DesireHelper()
  controller = LaneTurnController(hub)
  controller.enabled = True
  controller.lane_turn_value = LANE_CHANGE_SPEED_MIN
  controller.turn_direction = TurnDirection.none
  return controller


@dataclass
class _ControllerCase:
  left_blinker: bool
  right_blinker: bool
  speed_mps: float
  blindspot_left: bool
  blindspot_right: bool
  expected: int


@pytest.mark.parametrize("case", [
  _ControllerCase(True, False, 5, False, False, TurnDirection.turnLeft),
  _ControllerCase(False, True, 6, False, False, TurnDirection.turnRight),
  _ControllerCase(True, False, 9, False, False, TurnDirection.none),
  _ControllerCase(True, False, 7, True, False, TurnDirection.none),
  _ControllerCase(False, True, 6, False, True, TurnDirection.none),
  _ControllerCase(False, False, 5, False, False, TurnDirection.none),
  _ControllerCase(True, True, 5, False, False, TurnDirection.none),
])
def test_lane_turn_controller_gate(case: _ControllerCase):
  controller = _fresh_controller()
  controller.update_lane_turn(case.blindspot_left,
                              case.blindspot_right,
                              case.left_blinker,
                              case.right_blinker,
                              case.speed_mps)
  assert controller.get_turn_direction() == case.expected


def test_lane_turn_controller_respects_disable():
  controller = _fresh_controller()
  controller.enabled = False
  controller.update_lane_turn(False, False, True, False, 7)
  assert controller.get_turn_direction() == TurnDirection.none


def test_lane_turn_controller_reacts_to_signal_swaps():
  controller = _fresh_controller()
  controller.update_lane_turn(False, False, True, False, 5)
  assert controller.get_turn_direction() == TurnDirection.turnLeft
  controller.update_lane_turn(False, False, False, True, 6)
  assert controller.get_turn_direction() == TurnDirection.turnRight
  controller.update_lane_turn(False, False, False, False, 7)
  assert controller.get_turn_direction() == TurnDirection.none


@pytest.mark.parametrize(("speed_mps", "expected"), [
  (8.93, TurnDirection.turnLeft),
  (8.96, TurnDirection.none),
  (8.95, TurnDirection.none),
])
def test_lane_turn_threshold(speed_mps: float, expected: int):
  controller = _fresh_controller()
  controller.update_lane_turn(False, True, True, False, speed_mps)
  assert controller.get_turn_direction() == expected


@dataclass
class _FakeCarState:
  vEgo: float = 0.0
  standstill: bool = False
  leftBlinker: bool = False
  rightBlinker: bool = False
  leftBlindspot: bool = False
  rightBlindspot: bool = False
  steeringPressed: bool = False
  steeringTorque: float = 0.0
  brakePressed: bool = False


@dataclass
class _FakeNavState:
  active: bool = False
  maneuverPhase: int = custom.IQNavState.ManeuverPhase.none
  shouldSendTurnDesire: bool = False
  turnDesireDirection: int = TurnDirection.none


@pytest.fixture
def lane_turn_params():
  params = Params()
  params.put("LaneTurnDesire", True)
  params.put("LaneTurnValue", 20.0)


@pytest.mark.parametrize(("carstate", "lateral_active", "lane_change_prob", "expected_desire"), [
  (_FakeCarState(vEgo=5, leftBlinker=True), True, 1.0, log.Desire.turnLeft),
  (_FakeCarState(vEgo=7, rightBlinker=True), True, 1.0, log.Desire.turnRight),
  (_FakeCarState(vEgo=9, leftBlinker=True, steeringPressed=True, steeringTorque=1), True, 1.0, log.Desire.laneChangeLeft),
  (_FakeCarState(vEgo=9, rightBlinker=True, steeringPressed=True, steeringTorque=-1), True, 1.0, log.Desire.laneChangeRight),
  (_FakeCarState(vEgo=9), False, 1.0, log.Desire.none),
  (_FakeCarState(vEgo=4), True, 1.0, log.Desire.none),
])
def test_desire_helper_lane_turn_priority(carstate: _FakeCarState,
                                          lateral_active: bool,
                                          lane_change_prob: float,
                                          expected_desire,
                                          lane_turn_params):
  desire_logic = DesireHelper()
  desire_logic.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGE
  for _ in range(10):
    desire_logic.update(carstate, lateral_active, lane_change_prob)
  assert desire_logic.desire == expected_desire


def test_stopped_turn_desire_cycles_after_hold(lane_turn_params):
  desire_logic = DesireHelper()
  desire_logic.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGE
  carstate = _FakeCarState(vEgo=0.0, standstill=True, leftBlinker=True)

  hold_frames = int(TURN_DESIRE_STOP_HOLD_TIME / DT_MDL)
  gap_frames = int(TURN_DESIRE_STOP_GAP_TIME / DT_MDL)

  seen = []
  for _ in range(hold_frames + gap_frames + 4):
    desire_logic.update(carstate, True, 1.0)
    seen.append(desire_logic.desire)

  assert all(desire == log.Desire.turnLeft for desire in seen[:hold_frames])
  assert all(desire == log.Desire.none for desire in seen[hold_frames:hold_frames + gap_frames])
  assert all(desire == log.Desire.turnLeft for desire in seen[hold_frames + gap_frames:])


def test_turn_desire_cycle_resets_after_vehicle_moves(lane_turn_params):
  desire_logic = DesireHelper()
  desire_logic.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGE
  stopped = _FakeCarState(vEgo=0.0, standstill=True, leftBlinker=True)
  moving = _FakeCarState(vEgo=3.0, standstill=False, leftBlinker=True)

  hold_frames = int(TURN_DESIRE_STOP_HOLD_TIME / DT_MDL)

  for _ in range(hold_frames + 2):
    desire_logic.update(stopped, True, 1.0)
  assert desire_logic.desire == log.Desire.none

  desire_logic.update(moving, True, 1.0)
  assert desire_logic.desire == log.Desire.turnLeft

  desire_logic.update(stopped, True, 1.0)
  assert desire_logic.desire == log.Desire.turnLeft


def test_nav_turn_direction_stays_active_during_model_pulse_gap():
  desire_logic = DesireHelper()
  nav_state = _FakeNavState(
    active=True,
    maneuverPhase=custom.IQNavState.ManeuverPhase.turnActive,
    shouldSendTurnDesire=True,
    turnDesireDirection=TurnDirection.turnRight,
  )
  carstate = _FakeCarState(vEgo=0.0, standstill=True)

  hold_frames = int(TURN_DESIRE_STOP_HOLD_TIME / DT_MDL)
  for _ in range(hold_frames + 1):
    desire_logic.update(carstate, True, 1.0, nav_state=nav_state)

  assert desire_logic.nav_turn_direction == TurnDirection.turnRight
  assert desire_logic.desire == log.Desire.none
