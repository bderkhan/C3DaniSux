#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# On comma three, use the C3-specific IQ launcher/AGNOS manifest.
trap 'exec ./launch_chffrplus.sh' ERR
IQ_C3_LAUNCH_SH="./iqpilot/system/hardware/c3/launch_chffrplus.sh"

MODEL="$(tr -d '\0' < "/sys/firmware/devicetree/base/model")"
export MODEL

if [ "$MODEL" = "comma tici" ] || [ "$MODEL" = "comma three" ]; then
  [ -x "$IQ_C3_LAUNCH_SH" ] || false
  exec "$IQ_C3_LAUNCH_SH"
fi

exec ./launch_chffrplus.sh
