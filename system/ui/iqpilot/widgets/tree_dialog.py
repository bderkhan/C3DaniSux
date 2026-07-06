"""
Copyright © IQ.Lvbs, apart of Project Teal Lvbs, All Rights Reserved, licensed under https://konn3kt.com/tos
"""
from dataclasses import dataclass, field

import pyray as rl
from openpilot.common.params import Params
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets import DialogResult
from openpilot.system.ui.widgets.button import Button, ButtonStyle, BUTTON_PRESSED_BACKGROUND_COLORS
from openpilot.system.ui.widgets.label import gui_label
from openpilot.system.ui.widgets.option_dialog import MultiOptionDialog

from openpilot.system.ui.iqpilot.lib.styles import style
from openpilot.system.ui.iqpilot.widgets.helpers.fuzzy_search import search_from_list
from openpilot.system.ui.iqpilot.widgets.helpers.star_icon import draw_star
from openpilot.system.ui.iqpilot.widgets.input_dialog import IQInputDialog

TREE_TEAL = rl.Color(16, 185, 169, 255)
TREE_FOLDER_COLOR = rl.Color(48, 51, 58, 255)        # brand header rows (lighter)
TREE_SEARCH_FILL = rl.Color(42, 45, 52, 255)
TREE_SEARCH_PRESSED = rl.Color(58, 62, 70, 255)
TREE_SEARCH_BORDER = rl.Color(255, 255, 255, 38)


@dataclass
class TreeNode:
  ref: str
  data: dict = field(default_factory=dict)


@dataclass
class TreeFolder:
  folder: str
  nodes: list


class TreeItemWidget(Button):
  def __init__(self, text, ref, is_folder=False, indent_level=0, click_callback=None, favorite_callback=None, is_favorite=False, is_expanded=False):
    super().__init__(text, click_callback, button_style=ButtonStyle.NORMAL, text_alignment=rl.GuiTextAlignment.TEXT_ALIGN_LEFT,
                     text_padding=20 + indent_level * 30, elide_right=True)
    self.text = text
    self.ref = ref
    self.is_folder = is_folder
    self.indent_level = indent_level
    self.is_favorite = is_favorite
    self.selected = False
    self._favorite_callback = favorite_callback
    self.text_padding = 20 + indent_level * 30
    self.border_radius = 10
    self.is_expanded = is_expanded

  def _render(self, rect):
    indent = 60 * self.indent_level
    self._rect = rl.Rectangle(rect.x + indent, rect.y, rect.width - indent, rect.height)
    if self.is_pressed:
      color = BUTTON_PRESSED_BACKGROUND_COLORS[self._button_style]
    elif self.selected and self.ref != "search_bar":
      color = TREE_TEAL
    elif self.is_folder:
      color = TREE_FOLDER_COLOR
    else:
      color = style.BUTTON_DISABLED_BG_COLOR
    roundness = self.border_radius / (min(self._rect.width, self._rect.height) / 2)
    rl.draw_rectangle_rounded(self._rect, roundness, 10, color)

    cy = self._rect.y + self._rect.height / 2
    text_offset = self.text_padding + 20

    if self.is_folder:
      # chevron: down when expanded, right when collapsed
      chev = gui_app.texture("icons/iq/chevron_down.png" if self.is_expanded else "icons/iq/chevron_right.png",
                             40, 40, keep_aspect_ratio=True)
      rl.draw_texture(chev, int(self._rect.x + self.text_padding + 6), int(cy - chev.height / 2), rl.Color(205, 205, 210, 255))
      text_offset = self.text_padding + 6 + 40 + 22
    elif self.indent_level > 0 and not self.selected:
      # teal accent marking a model under the expanded brand
      rl.draw_rectangle_rounded(rl.Rectangle(self._rect.x + 16, cy - 24, 6, 48), 1.0, 4, TREE_TEAL)

    text_rect = rl.Rectangle(self._rect.x + text_offset, self._rect.y, self._rect.width - text_offset - 90, self._rect.height)
    self._label.render(text_rect)

    if not self.is_folder and self._favorite_callback:
      draw_star(self._rect.x + self._rect.width - 90, self._rect.y + self._rect.height / 2, 40, self.is_favorite,
                style.ON_BG_COLOR if self.is_favorite else rl.GRAY)

  def _handle_mouse_release(self, mouse_pos):
    star_rect = rl.Rectangle(self._rect.x + self._rect.width - 90 - 40, self._rect.y + self._rect.height / 2 - 40, 80, 80)
    if not self.is_folder and self._favorite_callback and rl.check_collision_point_rec(mouse_pos, star_rect):
      self._favorite_callback()
      return True
    return super()._handle_mouse_release(mouse_pos)


class TreeOptionDialog(MultiOptionDialog):
  def __init__(self, title, folders, current_ref="", fav_param="", option_font_weight=FontWeight.MEDIUM, search_prompt=None,
               get_folders_fn=None, on_exit=None, display_func=None, search_funcs=None, search_title=None, search_subtitle=None):
    super().__init__(title, [], current_ref, option_font_weight)
    self.folders = folders
    self.selection_ref = current_ref
    self.fav_param = fav_param
    self.expanded = set()
    self.params = Params()
    val = self.params.get(fav_param) if fav_param else None
    self.favorites = set(val.split(';')) if val else set()
    self.query = ""
    self.search_prompt = search_prompt or tr("Search")
    self.get_folders_fn = get_folders_fn
    self.on_exit = on_exit
    self.display_func = display_func or (lambda node: node.data.get('display_name', node.ref))
    self.search_funcs = search_funcs or [lambda node: node.data.get('display_name', ''), lambda node: node.data.get('short_name', '')]
    self._search_rect = None
    self._search_width = 0.475

    # Default title & overridable subtitle for IQInputDialog
    self.search_title = search_title or tr("Enter search query")
    self.search_subtitle = search_subtitle
    self.search_dialog = None
    self._search_pressed = False

    self.selection_node = None
    # Try to match by ref, by display text, or fall back to "Default" when no ref is set
    for folder in self.folders:
      for node in folder.nodes:
        display = self.display_func(node)
        if (
          node.ref == current_ref or
          display == current_ref or
          (not current_ref and node.ref == "Default")
        ):
          self.selection = display
          self.current = display
          self.selection_node = node
          break
      if self.selection_node is not None:
        break

    self._build_visible_items()

  def _on_search_confirm(self, result, text):
    if result == DialogResult.CONFIRM:
      self.query = text
      self._build_visible_items()
    gui_app.set_modal_overlay(self, callback=self.on_exit)

  def _on_search_clicked(self):
    self.search_dialog = IQInputDialog(
      self.search_title,
      self.search_subtitle,
      current_text=self.query,
      callback=self._on_search_confirm,
    )
    self.search_dialog.show()

  def _toggle_folder(self, folder):
    if folder.folder:
      if folder.folder in self.expanded:
        self.expanded.remove(folder.folder)
      else:
        self.expanded.add(folder.folder)
      if folder == self.folders[-1] and folder.folder in self.expanded:
        self.scroller.scroll_panel.set_offset(self.scroller.scroll_panel.offset - 200)
      self._build_visible_items(reset_scroll=False)

  def _select_node(self, node):
    self.selection = self.display_func(node)
    self.selection_ref = node.ref

  def _toggle_favorite(self, node):
    self.favorites.remove(node.ref) if node.ref in self.favorites else self.favorites.add(node.ref)
    if self.fav_param:
      self.params.put(self.fav_param, ';'.join(self.favorites))
    if self.get_folders_fn:
      self.folders = self.get_folders_fn(self.favorites)
    self._build_visible_items(reset_scroll=False)

  def _build_visible_items(self, reset_scroll=True):
    self.visible_items = []

    # Pinned selected item at the very top (if any)
    if getattr(self, "selection_node", None) is not None:
      node = self.selection_node
      display = self.display_func(node)
      self.selection = self.current = display
      favorite_cb = (lambda node_ref=node: self._toggle_favorite(node_ref)) if self.fav_param and node.ref != "Default" else None
      self.visible_items.append(TreeItemWidget(self.display_func(node), node.ref, False, 0,
                                               lambda node_ref=node: self._select_node(node_ref),
                                               favorite_cb, node.ref in self.favorites, is_expanded=True))

    for folder in self.folders:
      nodes = [node for node in folder.nodes if not self.query or search_from_list(self.query, [search_func(node) for search_func in self.search_funcs])]
      if not nodes and self.query:
        continue
      expanded = folder.folder in self.expanded or not folder.folder or bool(self.query)
      if folder.folder:
        self.visible_items.append(TreeItemWidget(folder.folder, "", True, 0,
                                                 lambda folder_ref=folder: self._toggle_folder(folder_ref),
                                                 is_expanded=expanded))
      if expanded:
        for node in nodes:
          # Skip duplicate root-level item for the selected node
          if self.selection_node is not None and node.ref == self.selection_node.ref and not folder.folder:
            continue

          favorite_cb = (lambda node_ref=node: self._toggle_favorite(node_ref)) if self.fav_param and node.ref != "Default" else None
          self.visible_items.append(TreeItemWidget(self.display_func(node), node.ref, False, 1 if folder.folder else 0,
                                                   lambda node_ref=node: self._select_node(node_ref),
                                                   favorite_cb, node.ref in self.favorites, is_expanded=expanded))

    self.option_buttons = self.visible_items
    self.options = [item.text for item in self.visible_items]
    self.scroller._items = self.visible_items
    if reset_scroll:
      self.scroller.scroll_panel.set_offset(0)

  def _render(self, rect):
    dialog_content_rect = rl.Rectangle(rect.x + 50, rect.y + 50, rect.width - 100, rect.height - 100)
    rl.draw_rectangle_rounded(dialog_content_rect, 0.02, 20, rl.BLACK)

    # Title on the left
    title_rect = rl.Rectangle(dialog_content_rect.x + 50, dialog_content_rect.y + 50, dialog_content_rect.width * 0.5, 70)
    gui_label(title_rect, self.title, 70, font_weight=FontWeight.BOLD)

    # Search bar — full-width filled field beneath the title
    search_x = dialog_content_rect.x + 50
    search_width = dialog_content_rect.width - 100
    search_y = title_rect.y + title_rect.height + 36
    search_height = 100
    self._search_rect = rl.Rectangle(search_x, search_y, search_width, search_height)

    fill_color = TREE_SEARCH_PRESSED if self._search_pressed else TREE_SEARCH_FILL
    rl.draw_rectangle_rounded(self._search_rect, 0.4, 16, fill_color)
    rl.draw_rectangle_rounded_lines_ex(self._search_rect, 0.4, 16, 2, TREE_SEARCH_BORDER)

    # Magnifying glass icon
    icon_color = rl.Color(190, 190, 195, 255)
    cx = self._search_rect.x + 54
    cy = self._search_rect.y + self._search_rect.height / 2 - 2
    radius = 24
    for i in range(4):
      rl.draw_circle_lines(int(cx), int(cy), radius - i, icon_color)
    rl.draw_line_ex(rl.Vector2(cx + radius * 0.65, cy + radius * 0.65),
                    rl.Vector2(cx + radius * 1.4, cy + radius * 1.4), 5, icon_color)

    # Query text, or muted placeholder
    text_x = cx + radius * 1.4 + 34
    text_rect = rl.Rectangle(text_x, self._search_rect.y, self._search_rect.x + self._search_rect.width - text_x - 24, self._search_rect.height)
    if self.query:
      gui_label(text_rect, self.query, 56, font_weight=FontWeight.MEDIUM)
    else:
      gui_label(text_rect, self.search_prompt, 56, color=rl.Color(150, 150, 155, 255), font_weight=FontWeight.NORMAL)

    options_top = self._search_rect.y + self._search_rect.height + 36
    options_area_rect = rl.Rectangle(dialog_content_rect.x + 50, options_top, dialog_content_rect.width - 100,
                                     dialog_content_rect.height - (options_top - dialog_content_rect.y) - 210)

    for index, option_text in enumerate(self.options):
      self.option_buttons[index].selected = (option_text == self.selection)
      self.option_buttons[index].set_button_style(ButtonStyle.PRIMARY if option_text == self.selection else ButtonStyle.NORMAL)
      self.option_buttons[index].set_rect(rl.Rectangle(0, 0, options_area_rect.width, 120))
    self.scroller.render(options_area_rect)

    button_width = (dialog_content_rect.width - 150) / 2
    button_y_position = dialog_content_rect.y + dialog_content_rect.height - 160

    self.cancel_button._border_radius = self.select_button._border_radius = 44
    cancel_rect = rl.Rectangle(dialog_content_rect.x + 50, button_y_position, button_width, 160)
    self.cancel_button.render(cancel_rect)

    select_rect = rl.Rectangle(dialog_content_rect.x + 100 + button_width, button_y_position, button_width, 160)
    select_enabled = self.selection != self.current
    self.select_button.set_enabled(select_enabled)
    if select_enabled:
      sel_round = 44 / (min(select_rect.width, select_rect.height) / 2)
      rl.draw_rectangle_rounded(select_rect, sel_round, 10, TREE_TEAL)
      self.select_button.set_button_style(ButtonStyle.TRANSPARENT_WHITE_TEXT)
    else:
      self.select_button.set_button_style(ButtonStyle.NORMAL)
    self.select_button.render(select_rect)

    return self._result

  def _handle_mouse_press(self, mouse_pos):
    if self._search_rect and rl.check_collision_point_rec(mouse_pos, self._search_rect):
      self._search_pressed = True
      return True
    return super()._handle_mouse_press(mouse_pos)

  def _handle_mouse_release(self, mouse_pos):
    clicked_search = False
    if self._search_rect and rl.check_collision_point_rec(mouse_pos, self._search_rect):
      clicked_search = self._search_pressed

    self._search_pressed = False

    if clicked_search:
      self._on_search_clicked()
      return True

    return super()._handle_mouse_release(mouse_pos)
