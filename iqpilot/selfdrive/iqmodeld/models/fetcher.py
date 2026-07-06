#!/usr/bin/env python3
"""
Copyright (c) IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
from cereal import custom
from openpilot.iqpilot._proprietary_loader import ProprietaryModuleMissing, load_private_module

try:
  load_private_module(__name__, "iqpilot_private.models.fetcher")
except ProprietaryModuleMissing:
  from iqpilot.models_private_src.fetcher import *  # noqa: F403


_ModelParser = globals().get("ModelParser")
if _ModelParser is not None and hasattr(_ModelParser, "_parse_bundle"):
  _ORIGINAL_PARSE_BUNDLE = _ModelParser._parse_bundle

  def _parse_bundle(bundle):
    model_bundle = _ORIGINAL_PARSE_BUNDLE(bundle)
    if not bundle.get("runner"):
      model_bundle.runner = custom.IQModelManager.Runner.tinygrad
    return model_bundle

  _ModelParser._parse_bundle = staticmethod(_parse_bundle)
