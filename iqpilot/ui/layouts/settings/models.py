"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
import os
import re
import time
import pyray as rl

from cereal import custom
from openpilot.selfdrive.ui.ui_state import device, ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets import DialogResult, Widget
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog
from openpilot.system.ui.widgets.scroller_tici import Scroller
from openpilot.system.ui.widgets.toggle import ON_COLOR

from openpilot.iqpilot.selfdrive.iqmodeld.models.helpers import select_stock_model
from openpilot.iqpilot.selfdrive.iqmodeld.models.runners.constants import CUSTOM_MODEL_PATH
from openpilot.system.ui.iqpilot.lib.utils import NoElideButtonAction
from openpilot.system.ui.iqpilot.widgets.list_view import IQListItem
from openpilot.system.ui.iqpilot.widgets.progress_bar import progress_item
from openpilot.system.ui.iqpilot.widgets.tree_dialog import TreeOptionDialog, TreeNode, TreeFolder

if gui_app.iqpilot_ui():
  from openpilot.system.ui.iqpilot.widgets.list_view import button_item as button_item

_ACTIVE_BUNDLE_KEY = "ModelManager_ActiveBundle"
_DOWNLOAD_INDEX_KEY = "ModelManager_DownloadIndex"
_RUNNER_CACHE_KEY = "ModelRunnerTypeCache"


class ModelsLayout(Widget):
  def __init__(self):
    super().__init__()
    self.model_manager = None
    self._refreshing = False
    self._refresh_start = 0.0
    self.download_status = None
    self.prev_download_status = None
    self.model_dialog = None
    self.last_cache_calc_time = 0

    self._initialize_items()

    self.clear_cache_item.action_item.set_value(f"{self._calculate_cache_size():.2f} MB")
    self._scroller = Scroller(self.items, line_separator=True, spacing=0)

  def _initialize_items(self):
    self.current_model_item = IQListItem(
      title=tr("Current Model"),
      description="",
      action_item=NoElideButtonAction(tr("SELECT")),
      callback=self._handle_current_model_clicked
    )

    self.supercombo_label = progress_item(tr("Driving Model"))
    self.vision_label = progress_item(tr("Vision Model"))
    self.policy_label = progress_item(tr("Policy Model"))

    self.refresh_item = button_item(tr("Refresh Model List"), tr("REFRESH"), "", self._on_refresh_models)

    self.clear_cache_item = IQListItem(
      title=tr("Clear Model Cache"),
      description="",
      action_item=NoElideButtonAction(tr("CLEAR")),
      callback=self._clear_cache
    )

    self.redownload_item = button_item(tr("Redownload Current Model"), tr("REDOWNLOAD"), "", self._redownload_model)
    self.cancel_download_item = button_item(tr("Cancel Download"), tr("Cancel"), "", self._cancel_model_request)

    self.items = [self.current_model_item, self.cancel_download_item, self.supercombo_label, self.vision_label,
                  self.policy_label, self.redownload_item, self.refresh_item, self.clear_cache_item]

  def _is_downloading(self):
    return (self.model_manager and self.model_manager.selectedBundle and
            self.model_manager.selectedBundle.status == custom.IQModelManager.DownloadStatus.downloading)

  @staticmethod
  def _has_download_request() -> bool:
    try:
      return int(ui_state.params.get(_DOWNLOAD_INDEX_KEY)) >= 0
    except (TypeError, ValueError):
      return False

  @staticmethod
  def _has_active_bundle_param() -> bool:
    return bool(ui_state.params.get(_ACTIVE_BUNDLE_KEY))

  def _has_model_request(self) -> bool:
    return self._has_download_request()

  @staticmethod
  def _calculate_cache_size():
    cache_size = 0.0
    if os.path.exists(CUSTOM_MODEL_PATH):
      cache_size = sum(os.path.getsize(os.path.join(CUSTOM_MODEL_PATH, file)) for file in os.listdir(CUSTOM_MODEL_PATH)) / (1024**2)
    return cache_size

  @staticmethod
  def _bundle_index(bundle) -> int | None:
    try:
      return int(getattr(bundle, "index", -1))
    except (TypeError, ValueError):
      return None

  @classmethod
  def _bundle_matches(cls, left, right) -> bool:
    if left is None or right is None:
      return False

    left_index = cls._bundle_index(left)
    right_index = cls._bundle_index(right)
    if left_index is not None and right_index is not None and left_index == right_index:
      return True

    for attr in ("ref", "internalName", "displayName"):
      left_value = getattr(left, attr, None)
      if left_value and left_value == getattr(right, attr, None):
        return True
    return False

  @staticmethod
  def _safe_model_path(filename: str) -> str | None:
    if not filename or os.path.basename(filename) != filename:
      return None

    root = os.path.realpath(CUSTOM_MODEL_PATH)
    path = os.path.realpath(os.path.join(root, filename))
    try:
      if os.path.commonpath([root, path]) != root:
        return None
    except ValueError:
      return None
    return path

  def _remove_bundle_files(self, bundle) -> None:
    for model in getattr(bundle, "models", []) or []:
      for artifact in (getattr(model, "metadata", None), getattr(model, "artifact", None)):
        filename = getattr(artifact, "fileName", "") if artifact is not None else ""
        path = self._safe_model_path(filename)
        if path is None:
          continue
        for candidate in (path, f"{path}.download"):
          try:
            if os.path.isfile(candidate):
              os.remove(candidate)
          except OSError:
            pass

  def _clear_cache(self):
    def _callback(response):
      if response == DialogResult.CONFIRM:
        ui_state.params.put_bool("ModelManager_ClearCache", True)
        self.clear_cache_item.action_item.set_value(f"{self._calculate_cache_size():.2f} MB")

    gui_app.set_modal_overlay(ConfirmDialog(tr("This will delete ALL downloaded models from the cache except the currently active model. Are you sure?"),
                                            tr("Clear Cache")), callback=_callback)

  def _redownload_target_bundle(self):
    if not self.model_manager:
      return None
    selected = self.model_manager.selectedBundle
    if selected and selected.status == custom.IQModelManager.DownloadStatus.failed:
      return selected
    active = self.model_manager.activeBundle
    if self._has_active_bundle_param() and active and active.ref:
      return active
    return None

  def _redownload_target_index(self) -> int | None:
    target = self._redownload_target_bundle()
    if not target:
      return None
    try:
      return int(target.index)
    except (TypeError, ValueError):
      pass

    for bundle in self.model_manager.availableBundles:
      if bundle.ref and bundle.ref == target.ref:
        return int(bundle.index)
      if bundle.internalName and bundle.internalName == target.internalName:
        return int(bundle.index)
    return None

  def _can_redownload(self) -> bool:
    return bool(ui_state.is_offroad() and not self._is_downloading() and not self._has_model_request() and self._redownload_target_index() is not None)

  def _cancel_model_request(self):
    ui_state.params.remove(_DOWNLOAD_INDEX_KEY)

  def _redownload_model(self):
    index = self._redownload_target_index()
    if index is None:
      return

    def _callback(response):
      if response == DialogResult.CONFIRM:
        target = self._redownload_target_bundle()
        if target is not None:
          self._remove_bundle_files(target)
          if self._bundle_matches(getattr(self.model_manager, "activeBundle", None), target):
            ui_state.params.remove(_ACTIVE_BUNDLE_KEY)
            ui_state.params.remove(_RUNNER_CACHE_KEY)
        ui_state.params.put(_DOWNLOAD_INDEX_KEY, index)

    gui_app.set_modal_overlay(ConfirmDialog(tr("Clear the selected model cache and download it again?"),
                                            tr("Redownload")), callback=_callback)

  def _handle_bundle_download_progress(self):
    labels = {custom.IQModelManager.Model.Type.supercombo: self.supercombo_label,
              custom.IQModelManager.Model.Type.vision: self.vision_label,
              custom.IQModelManager.Model.Type.policy: self.policy_label}
    for label in labels.values():
      label.set_visible(False)
    self.cancel_download_item.set_visible(False)

    if not self.model_manager or (not self.model_manager.selectedBundle and (not self._has_active_bundle_param() or not self.model_manager.activeBundle)):
      return

    bundle = self.model_manager.selectedBundle if self._is_downloading() or (
      self.model_manager.selectedBundle and self.model_manager.selectedBundle.status == custom.IQModelManager.DownloadStatus.failed
    ) else (self.model_manager.activeBundle if self._has_active_bundle_param() else None)
    if not bundle:
      return

    self.download_status = bundle.status
    status_changed = self.prev_download_status != self.download_status
    self.prev_download_status = self.download_status

    self.cancel_download_item.set_visible(bool(self.model_manager.selectedBundle) and self._has_download_request())

    if (current_time := time.monotonic()) - self.last_cache_calc_time > 0.5:
      self.last_cache_calc_time = current_time
      self.clear_cache_item.action_item.set_value(f"{self._calculate_cache_size():.2f} MB")

    if self.download_status == custom.IQModelManager.DownloadStatus.downloading:
      device._reset_interactive_timeout()

    for model in bundle.models:
      if label := labels.get(getattr(model.type, 'raw', model.type)):
        label.set_visible(True)
        p = model.artifact.downloadProgress
        text, show, color = f"pending - {bundle.displayName}", False, rl.GRAY
        if p.status == custom.IQModelManager.DownloadStatus.downloading:
          text, show = f"{int(p.progress)}% - {bundle.displayName}", True
        elif p.status in (custom.IQModelManager.DownloadStatus.downloaded, custom.IQModelManager.DownloadStatus.cached):
          status_text = tr("from cache" if p.status == custom.IQModelManager.DownloadStatus.cached else "downloaded")
          text, color = f"{bundle.displayName} - {status_text if status_changed else tr('ready')}", ON_COLOR
        elif p.status == custom.IQModelManager.DownloadStatus.failed:
          text, color = f"download failed - {bundle.displayName}", rl.RED
        label.action_item.update(p.progress, text, show, color)

  @staticmethod
  def _show_reset_params_dialog():
    def _callback(response):
      if response == DialogResult.CONFIRM:
        ui_state.params.remove("CalibrationParams")
        ui_state.params.remove("LiveTorqueParameters")
    msg = tr("The selected model changed. We suggest resetting calibration. Would you like to do that now?")
    gui_app.set_modal_overlay(ConfirmDialog(msg, tr("Reset Calibration")), callback=_callback)

  def _on_model_selected(self, result):
    if result != DialogResult.CONFIRM:
      return
    selected_ref = self.model_dialog.selection_ref
    if selected_ref == "Default":
      had_custom_model = bool(self.model_manager and self.model_manager.activeBundle and self.model_manager.activeBundle.ref)
      select_stock_model(ui_state.params)
      if had_custom_model:
        self._show_reset_params_dialog()
    elif selected_bundle := next((bundle for bundle in self.model_manager.availableBundles if bundle.ref == selected_ref), None):
      ui_state.params.put(_DOWNLOAD_INDEX_KEY, selected_bundle.index)
      if self.model_manager.activeBundle and selected_bundle.generation != self.model_manager.activeBundle.generation:
        self._show_reset_params_dialog()
    self.model_dialog = None

  @staticmethod
  def _bundle_to_node(bundle):
    return TreeNode(bundle.ref, {'display_name': bundle.displayName, 'short_name': bundle.internalName})

  def _get_folders(self, favorites):
    bundles = self.model_manager.availableBundles
    folders = {}
    for bundle in bundles:
      folders.setdefault(next((ov_ride.value for ov_ride in bundle.overrides if ov_ride.key == "folder"), ""), []).append(bundle)

    folders_list = [TreeFolder("", [TreeNode("Default", {'display_name': tr("Default Model"), 'short_name': "Default"})])]
    for folder, folder_bundles in sorted(folders.items(), key=lambda x: max((bundle.index for bundle in x[1]), default=-1), reverse=True):
      folder_bundles.sort(key=lambda bundle: bundle.index, reverse=True)
      name = folder + (f" - (Updated: {m.group(1)})" if folder_bundles and (m := re.search(r'\(([^)]*)\)[^(]*$', folder_bundles[0].displayName)) else "")
      folders_list.append(TreeFolder(name, [self._bundle_to_node(bundle) for bundle in folder_bundles]))

    if favorites and (fav_bundles := [bundle for bundle in bundles if bundle.ref in favorites]):
      folders_list.insert(1, TreeFolder("Favorites", [self._bundle_to_node(bundle) for bundle in fav_bundles]))
    return folders_list

  def _handle_current_model_clicked(self):
    favs = ui_state.params.get("ModelManager_Favs")
    favorites = set(favs.split(';')) if favs else set()
    folders_list = self._get_folders(favorites)

    active_ref = self.model_manager.activeBundle.ref if self._has_active_bundle_param() and self.model_manager.activeBundle else "Default"
    self.model_dialog = TreeOptionDialog(tr("Select a Model"), folders_list, active_ref, "ModelManager_Favs",
                                         get_folders_fn=self._get_folders, on_exit=self._on_model_selected)
    gui_app.set_modal_overlay(self.model_dialog, callback=self._on_model_selected)

  def _on_refresh_models(self):
    # Trigger a re-sync and show inline loading instead of a blocking dialog
    ui_state.params.put("ModelManager_LastSyncTime", 0)
    self._refreshing = True
    self._refresh_start = time.monotonic()
    self.refresh_item.action_item.set_enabled(False)

  def _update_refresh_state(self):
    if not self._refreshing:
      return
    try:
      last_sync = int(ui_state.params.get("ModelManager_LastSyncTime", return_default=True) or 0)
    except (TypeError, ValueError):
      last_sync = 0
    elapsed = time.monotonic() - self._refresh_start
    if (last_sync > 0 and elapsed > 1.0) or elapsed > 20.0:
      self._refreshing = False
      self.refresh_item.action_item.set_loading(False)
      self.refresh_item.action_item.set_enabled(True)
    else:
      self.refresh_item.action_item.set_loading(True)
      self.refresh_item.action_item.set_enabled(False)

  def _update_state(self):
    self._update_refresh_state()
    self.model_manager = ui_state.sm["iqModelManager"]
    self._handle_bundle_download_progress()
    active = self.model_manager.activeBundle if self.model_manager else None
    active_name = active.internalName if self._has_active_bundle_param() and active and active.ref else tr("Default Model")
    self.current_model_item.action_item.set_value(active_name)
    self.redownload_item.action_item.set_enabled(self._can_redownload())
    target = self._redownload_target_bundle()
    self.redownload_item.action_item.set_value(target.internalName if target else "")

    if not ui_state.is_offroad():
      self.current_model_item.action_item.set_enabled(False)
      self.current_model_item.set_description(tr("Only available when vehicle is off, or always offroad mode is on"))
    else:
      self.current_model_item.action_item.set_enabled(True)
      self.current_model_item.set_description("")

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
