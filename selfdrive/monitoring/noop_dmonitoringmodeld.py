#!/usr/bin/env python3
from cereal import messaging
from openpilot.common.realtime import Ratekeeper
from openpilot.common.swaglog import cloudlog


def _fill_driver_data(driver_data) -> None:
  driver_data.faceOrientation = [0.0, 0.0, 0.0]
  driver_data.faceOrientationStd = [1.0, 1.0, 1.0]
  driver_data.facePosition = [0.0, 0.0]
  driver_data.facePositionStd = [1.0, 1.0]
  driver_data.faceProb = 0.0
  driver_data.leftEyeProb = 0.0
  driver_data.rightEyeProb = 0.0
  driver_data.leftBlinkProb = 0.0
  driver_data.rightBlinkProb = 0.0
  driver_data.sunglassesProb = 0.0
  driver_data.phoneProb = 0.0


def main() -> None:
  cloudlog.warning("stock dmonitoringmodeld disabled; publishing noop driverStateV2")
  pm = messaging.PubMaster(["driverStateV2"])
  rk = Ratekeeper(20, print_delay_threshold=None)
  frame_id = 0

  while True:
    msg = messaging.new_message("driverStateV2", valid=True)
    ds = msg.driverStateV2
    ds.frameId = frame_id
    ds.modelExecutionTime = 0.0
    ds.gpuExecutionTime = 0.0
    ds.rawPredictions = b""
    ds.wheelOnRightProb = 0.0
    _fill_driver_data(ds.leftDriverData)
    _fill_driver_data(ds.rightDriverData)

    pm.send("driverStateV2", msg)
    frame_id += 1
    rk.keep_time()


if __name__ == "__main__":
  main()
