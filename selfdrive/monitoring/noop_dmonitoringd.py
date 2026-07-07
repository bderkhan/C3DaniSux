#!/usr/bin/env python3
from cereal import messaging
from openpilot.common.params import Params
from openpilot.common.realtime import Ratekeeper
from openpilot.common.swaglog import cloudlog


def main() -> None:
  cloudlog.warning("stock dmonitoringd disabled; publishing noop driverMonitoringState")
  params = Params()
  pm = messaging.PubMaster(["driverMonitoringState"])
  rk = Ratekeeper(20, print_delay_threshold=None)

  while True:
    msg = messaging.new_message("driverMonitoringState", valid=True)
    dm = msg.driverMonitoringState
    dm.events = []
    dm.faceDetected = False
    dm.isDistracted = False
    dm.distractedType = 0
    dm.awarenessStatus = 1.0
    dm.posePitchOffset = 0.0
    dm.posePitchValidCount = 0
    dm.poseYawOffset = 0.0
    dm.poseYawValidCount = 0
    dm.stepChange = 0.0
    dm.awarenessActive = 1.0
    dm.awarenessPassive = 1.0
    dm.isLowStd = False
    dm.hiStdCount = 0
    dm.isActiveMode = False
    dm.isRHD = params.get_bool("IsRhdDetected")
    dm.uncertainCount = 0
    dm.phoneProbOffset = 0.0
    dm.phoneProbValidCount = 0

    pm.send("driverMonitoringState", msg)
    rk.keep_time()


if __name__ == "__main__":
  main()
