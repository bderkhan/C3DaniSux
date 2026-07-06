import pytest
from parameterized import parameterized_class

from cereal import car
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.selfdrive.car.cruise import V_CRUISE_INITIAL
from openpilot.selfdrive.car.tests.test_cruise_speed import TestVCruiseHelper

ButtonEvent = car.CarState.ButtonEvent
ButtonType = car.CarState.ButtonEvent.Type


# TODO: test pcmCruise and pcmCruiseSpeed
@parameterized_class(('pcm_cruise', 'pcm_cruise_speed'), [(False, True)])
class TestLongIncrements(TestVCruiseHelper):
  def setup_method(self):
    TestVCruiseHelper.setup_method(self)
    self.params = Params()
    self.reset_long_increment_params()

  def reset_long_increment_params(self) -> None:
    """Reset to default long-increment parameters"""
    self.params.put_bool("LongIncrementsEnabled", False)
    self.params.put("LongIncrementTapStep", 1)
    self.params.put("LongIncrementHoldStep", 5)
    self.v_cruise_helper.read_custom_set_speed_params()

  def press_button_short(self, button_type: car.CarState.ButtonEvent.Type) -> None:
    """Simulate a short button press (press + release)"""
    CS = car.CarState(cruiseState={"available": True})
    CS.buttonEvents = [ButtonEvent(type=button_type, pressed=True)]
    self.v_cruise_helper.update_v_cruise(CS, enabled=True, is_metric=True)

    CS.buttonEvents = [ButtonEvent(type=button_type, pressed=False)]
    self.v_cruise_helper.update_v_cruise(CS, enabled=True, is_metric=True)

  def press_button_long(self, button_type: car.CarState.ButtonEvent.Type) -> None:
    """Simulate a long button press (50+ frames)"""
    CS = car.CarState(cruiseState={"available": True})
    CS.buttonEvents = [ButtonEvent(type=button_type, pressed=True)]
    self.v_cruise_helper.update_v_cruise(CS, enabled=True, is_metric=True)

    # Hold for 50 frames to trigger long press
    CS.buttonEvents = []
    for _ in range(50):
      self.v_cruise_helper.update_v_cruise(CS, enabled=True, is_metric=True)

    CS.buttonEvents = [ButtonEvent(type=button_type, pressed=False)]
    self.v_cruise_helper.update_v_cruise(CS, enabled=True, is_metric=True)

  def set_long_increments(self, enabled: bool, tap_step: int, hold_step: int) -> None:
    """Set long-increment parameters"""
    self.params.put_bool("LongIncrementsEnabled", enabled)
    self.params.put("LongIncrementTapStep", tap_step)
    self.params.put("LongIncrementHoldStep", hold_step)
    self.v_cruise_helper.read_custom_set_speed_params()

  def test_default_behavior_when_disabled(self):
    """Test that default increments are used when the feature is disabled"""
    self.set_long_increments(enabled=False, tap_step=5, hold_step=10)
    self.enable(V_CRUISE_INITIAL * CV.KPH_TO_MS, False, False)

    initial_speed = self.v_cruise_helper.v_cruise_kph

    # Short press should increment by 1 (default)
    self.press_button_short(ButtonType.accelCruise)
    assert self.v_cruise_helper.v_cruise_kph == initial_speed + 1

  @pytest.mark.parametrize("step", (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
  def test_custom_tap_steps(self, step):
    """Test custom tap-press steps (1-10)"""
    self.set_long_increments(enabled=True, tap_step=step, hold_step=5)
    self.enable(50 * CV.KPH_TO_MS, False, False)

    initial_speed = self.v_cruise_helper.v_cruise_kph
    self.press_button_short(ButtonType.accelCruise)

    if step >= 5:
      # Should snap to the nearest multiple of the step
      expected_speed = ((initial_speed // step) + 1) * step
    else:
      expected_speed = initial_speed + step

    assert self.v_cruise_helper.v_cruise_kph == expected_speed

  @pytest.mark.parametrize("step", (1, 5, 10))
  def test_custom_hold_steps(self, step):
    """Test custom held-press steps (1, 5, 10)"""
    self.set_long_increments(enabled=True, tap_step=1, hold_step=step)
    self.enable(50 * CV.KPH_TO_MS, False, False)

    initial_speed = self.v_cruise_helper.v_cruise_kph
    self.press_button_long(ButtonType.accelCruise)

    if step >= 5:
      # Should snap to the nearest multiple of the step
      expected_speed = ((initial_speed // step) + 1) * step
    else:
      expected_speed = initial_speed + step

    assert self.v_cruise_helper.v_cruise_kph == expected_speed

  @pytest.mark.parametrize("button_type", [ButtonType.accelCruise, ButtonType.decelCruise])
  def test_accel_decel_symmetry(self, button_type):
    """Test that acceleration and deceleration work symmetrically"""
    self.set_long_increments(enabled=True, tap_step=3, hold_step=5)
    self.enable(50 * CV.KPH_TO_MS, False, False)

    initial_speed = self.v_cruise_helper.v_cruise_kph
    self.press_button_short(button_type)

    expected_change = 3 if button_type == ButtonType.accelCruise else -3
    assert self.v_cruise_helper.v_cruise_kph == initial_speed + expected_change

  def test_snap_to_grid_behavior(self):
    """Test snap-to-grid behavior for steps of 5 and 10"""
    test_cases = [
      (47, 5, 50),   # 47 -> 50 (round up to next 5)
      (45, 5, 50),   # 45 -> 50 (already at 5, increment by 5)
      (43, 10, 50),  # 43 -> 50 (round up to next 10)
      (40, 10, 50),  # 40 -> 50 (already at 10, increment by 10)
    ]

    for initial, step, expected in test_cases:
      self.set_long_increments(enabled=True, tap_step=step, hold_step=step)
      self.reset_cruise_speed_state()
      self.enable(initial * CV.KPH_TO_MS, False, False)

      self.press_button_short(ButtonType.accelCruise)
      assert self.v_cruise_helper.v_cruise_kph == expected

  def test_invalid_values_fallback(self):
    """Test that out-of-range step values fall back to safe defaults"""
    # Test invalid tap step
    self.set_long_increments(enabled=True, tap_step=-1, hold_step=5)
    self.enable(50 * CV.KPH_TO_MS, False, False)

    initial_speed = self.v_cruise_helper.v_cruise_kph
    self.press_button_short(ButtonType.accelCruise)
    assert self.v_cruise_helper.v_cruise_kph == initial_speed + 1  # Should fallback to 1

    # Test invalid hold step
    self.reset_cruise_speed_state()
    self.set_long_increments(enabled=True, tap_step=1, hold_step=99)
    self.enable(50 * CV.KPH_TO_MS, False, False)

    initial_speed = self.v_cruise_helper.v_cruise_kph
    self.press_button_long(ButtonType.accelCruise)
    assert self.v_cruise_helper.v_cruise_kph == initial_speed + 10  # Should fallback to 10
