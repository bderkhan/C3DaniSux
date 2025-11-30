#!/usr/bin/env python3
import os

import cereal.messaging as messaging
from cereal import log
from openpilot.common.params import Params
from openpilot.common.realtime import config_realtime_process, Ratekeeper, DT_DMON
from openpilot.selfdrive.monitoring.helpers import DriverMonitoring
from openpilot.selfdrive.selfdrived.events import Events


def dm_disabled(params: Params) -> bool:
  return os.getenv("DISABLE_DRIVER_MONITORING") == "1" or params.get_bool("DisableDriverMonitoring")


EventName = log.OnroadEvent.EventName


def build_stub_dm_state(params: Params | None = None, *, face_detected: bool = False,
                        distracted: bool = False, events: list[EventName] | None = None):
  """Return a driverMonitoringState with optional one-off events and no disengage behavior."""
  rhd = False
  if params is not None:
    try:
      rhd = params.get_bool("IsRhdDetected")
    except Exception:
      rhd = False

  dat = messaging.new_message('driverMonitoringState', valid=True)
  dat.driverMonitoringState = {
    "events": Events().to_msg(),
    "faceDetected": face_detected,
    "isDistracted": distracted,
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

  if events:
    ev = Events()
    for e in events:
      ev.add(e)
    dat.driverMonitoringState.events = ev.to_msg()

  return dat


def dmonitoringd_thread():
  config_realtime_process([0, 1, 2, 3], 5)

  params = Params()
  pm = messaging.PubMaster(['driverMonitoringState'])
  gentle_reminder = params.get_bool("GentleDriverMonitoring")
  not_attentive_time = 0.0
  last_frame_id = None
  sm = messaging.SubMaster(['driverStateV2', 'liveCalibration', 'carState', 'selfdriveState', 'modelV2',
                            'carControl'], poll='driverStateV2')

  DM = DriverMonitoring(rhd_saved=params.get_bool("IsRhdDetected"), always_on=params.get_bool("AlwaysOnDM"))

  # 20Hz <- dmonitoringmodeld
  while True:
    sm.update()

    gentle_reminder = params.get_bool("GentleDriverMonitoring")

    if dm_disabled(params):
      pm.send('driverMonitoringState', build_stub_dm_state(params))
      continue

    if not sm.updated['driverStateV2']:
      # iterate when model has new output
      continue

    if gentle_reminder:
      ds = sm['driverStateV2']
      frame_id = ds.frameId
      if last_frame_id is None:
        last_frame_id = frame_id
      dt = max((frame_id - last_frame_id) * DT_DMON, DT_DMON)
      last_frame_id = frame_id

      wheel_on_right = ds.wheelOnRightProb > 0.5
      driver_data = ds.rightDriverData if wheel_on_right else ds.leftDriverData
      attentive = driver_data.faceProb > 0.5 and driver_data.occludedProb < 0.5

      alert = False
      if attentive:
        not_attentive_time = 0.0
      else:
        not_attentive_time += dt
        if not_attentive_time >= 180.0:
          alert = True
          not_attentive_time = 0.0

      events = [EventName.promptDriverDistracted] if alert else None
      pm.send('driverMonitoringState', build_stub_dm_state(params, face_detected=attentive,
                                                          distracted=not attentive, events=events))
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
