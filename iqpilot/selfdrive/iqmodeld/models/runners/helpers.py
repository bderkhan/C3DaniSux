from openpilot.iqpilot.selfdrive.iqmodeld.models.helpers import get_active_bundle
from openpilot.iqpilot.selfdrive.iqmodeld.models.combined_artifact import has_combined_split_artifact
from openpilot.iqpilot.selfdrive.iqmodeld.models.runners.model_runner import ModelRunner
from openpilot.iqpilot.selfdrive.iqmodeld.models.runners.tinygrad.tinygrad_runner import TinygradRunner, TinygradSplitRunner
from openpilot.iqpilot.selfdrive.iqmodeld.models.runners.constants import ModelType


def _is_fused_bundle(bundle) -> bool:
  return len(bundle.models) == 1 and bundle.models[0].artifact.fileName.startswith("driving_fused_")


def _is_supercombo_bundle(bundle) -> bool:
  return len(bundle.models) == 1 and bundle.models[0].artifact.fileName.startswith("driving_supercombo_")


def _is_split_bundle(bundle) -> bool:
  model_types = {m.type.raw for m in bundle.models}
  split_types = {ModelType.vision, ModelType.policy, ModelType.offPolicy, ModelType.onPolicy}
  return bool(model_types & split_types)


def get_model_runner() -> ModelRunner:
  """
  Factory function to create and return the appropriate ModelRunner instance.

  Selects TinygradRunner, choosing TinygradSplitRunner if separate vision/policy
  models are detected in the active bundle.

  :return: An instance of a ModelRunner subclass (ONNXRunner, TinygradRunner, or TinygradSplitRunner).
  """
  bundle = get_active_bundle()
  if bundle and bundle.models:
    if _is_supercombo_bundle(bundle):
      # lazy import so a runner issue can't break other bundles at import
      from openpilot.iqpilot.selfdrive.iqmodeld.models.runners.tinygrad.supercombo_runner import TinygradSupercomboRunner
      return TinygradSupercomboRunner()

    if _is_fused_bundle(bundle):
      # lazy import so a fused-runner issue can't break non-fused bundles at import
      from openpilot.iqpilot.selfdrive.iqmodeld.models.runners.tinygrad.fused_runner import TinygradFusedRunner
      return TinygradFusedRunner()

    if _is_split_bundle(bundle) and has_combined_split_artifact(bundle):
      from openpilot.iqpilot.selfdrive.iqmodeld.models.runners.tinygrad.combined_split_runner import TinygradCombinedSplitRunner
      return TinygradCombinedSplitRunner()

    if _is_split_bundle(bundle):
      return TinygradSplitRunner()
    if bundle.models:
      return TinygradRunner(bundle.models[0].type.raw)

  return TinygradRunner(ModelType.supercombo)
