#!/usr/bin/env python3
import os

import cereal.messaging as messaging
from openpilot.common.params import Params
from openpilot.common.realtime import config_realtime_process, Ratekeeper, DT_DMON
from openpilot.selfdrive.monitoring.helpers import DriverMonitoring


def dm_disabled(params: Params) -> bool:
  return os.getenv("DISABLE_DRIVER_MONITORING") == "1" or params.get_bool("DisableDriverMonitoring")


def build_stub_dm_state(params: Params | None = None):
  """Return a safe driverMonitoringState that never triggers alerts."""
  rhd = False
  if params is not None:
    try:
      rhd = params.get_bool("IsRhdDetected")
    except Exception:
      rhd = False

  dat = messaging.new_message('driverMonitoringState', valid=True)
  dat.driverMonitoringState = {
    "events": [],
    "faceDetected": False,
    "isDistracted": False,
    "distractedType": 0,
    "awarenessStatus": 1.0,
    "posePitchOffset": 0.0,
    "posePitchValidCount": 0,
    "poseYawOffset": 0.0,
    "poseYawValidCount": 0,
    "stepChange": 0.0,
    "awarenessActive": 1.0,
    "awarenessPassive": 1.0,
    "isLowStd": True,
    "hiStdCount": 0,
    "isActiveMode": True,
    "isRHD": rhd,
  }
  return dat


def dmonitoringd_thread():
  config_realtime_process([0, 1, 2, 3], 5)

  params = Params()
  pm = messaging.PubMaster(['driverMonitoringState'])
  sm = messaging.SubMaster(['driverStateV2', 'liveCalibration', 'carState', 'selfdriveState', 'modelV2',
                            'carControl'], poll='driverStateV2')

  DM = DriverMonitoring(rhd_saved=params.get_bool("IsRhdDetected"), always_on=params.get_bool("AlwaysOnDM"))

  # 20Hz <- dmonitoringmodeld
  while True:
    sm.update()

    if dm_disabled(params):
      pm.send('driverMonitoringState', build_stub_dm_state(params))
      continue

    if not sm.updated['driverStateV2']:
      # iterate when model has new output
      continue

    valid = sm.all_checks()
    if valid:
      DM.run_step(sm)

    # publish
    dat = DM.get_state_packet(valid=valid)
    pm.send('driverMonitoringState', dat)

    # load live always-on toggle
    if sm['driverStateV2'].frameId % 40 == 1:
      DM.always_on = params.get_bool("AlwaysOnDM")

    # save rhd virtual toggle every 5 mins
    if (sm['driverStateV2'].frameId % 6000 == 0 and
     DM.wheelpos_learner.filtered_stat.n > DM.settings._WHEELPOS_FILTER_MIN_COUNT and
     DM.wheel_on_right == (DM.wheelpos_learner.filtered_stat.M > DM.settings._WHEELPOS_THRESHOLD)):
      params.put_bool_nonblocking("IsRhdDetected", DM.wheel_on_right)

def main():
  dmonitoringd_thread()


if __name__ == '__main__':
  main()
