
import json
from functools import partial
from hotbox_designer.vendor.Qt import QtWidgets, QtCore, QtGui
from hotbox_designer.reader import HotboxReader

from hotbox_designer.align import align_shapes, arrange_shapes, arrange_radial
from hotbox_designer.templates import SQUARE_BUTTON, TEXT, BACKGROUND
from hotbox_designer.interactive import Shape
from hotbox_designer.geometry import get_combined_rects
from hotbox_designer.qtutils import icon, set_shortcut
from hotbox_designer.theme import apply_dark_theme
from hotbox_designer.data import copy_hotbox_data
from hotbox_designer.arrayutils import (
    move_elements_to_array_end, move_elements_to_array_begin,
    move_up_array_elements, move_down_array_elements)

from .editarea import ShapeEditArea
from .menu import MenuWidget
from .attributes import AttributeEditor


# marqueur du presse-papier système : permet le copier-coller de shapes
# entre deux éditeurs (même entre deux sessions de l'application)
SHAPES_CLIPBOARD_KEY = 'hotbox_designer_shapes'
STYLE_CLIPBOARD_KEY = 'hotbox_designer_style'

# groupes proposés au collage de style : (libellé, clés, coché par défaut)
STYLE_GROUPS = [
    ('Shape (square/round)', ['shape'], True),
    ('Size', ['shape.width', 'shape.height'], False),
    ('Colors & border', [
        'border', 'borderwidth.normal', 'borderwidth.hovered',
        'borderwidth.clicked', 'bordercolor.normal', 'bordercolor.hovered',
        'bordercolor.clicked', 'bordercolor.transparency', 'bgcolor.normal',
        'bgcolor.hovered', 'bgcolor.clicked', 'bgcolor.transparency'], True),
    ('Text style', [
        'text.size', 'text.bold', 'text.italic', 'text.color',
        'text.valign', 'text.halign'], True),
    ('Text content', ['text.content'], False),
    ('Image', ['image.path', 'image.fit', 'image.width', 'image.height'],
     False),
    ('Commands (actions)', [
        'action.left', 'action.left.close', 'action.left.language',
        'action.left.command', 'action.right', 'action.right.close',
        'action.right.language', 'action.right.command'], False),
]


class HotboxEditor(QtWidgets.QWidget):
    hotboxDataModified = QtCore.Signal(object)

    def __init__(self, hotbox_data, application, parent=None):
        super(HotboxEditor, self).__init__(parent, QtCore.Qt.Window)
        title = hotbox_data['general'].get('name') or ''
        self.setWindowTitle(
            'Hotbox editor' + (' - ' + title if title else ''))
        self.options = hotbox_data['general']
        self.application = application
        self.undo_manager = UndoManager(hotbox_data)
        apply_dark_theme(self)

        self.shape_editor = ShapeEditArea(self.options)
        self.set_hotbox_data(hotbox_data)
        self.shape_editor.selectedShapesChanged.connect(self.selection_changed)
        self.shape_editor.centerMoved.connect(self.move_center)
        method = self.set_data_modified
        self.shape_editor.increaseUndoStackRequested.connect(method)
        self.shape_editor.contextMenuRequested.connect(self.show_context_menu)
        self.shape_editor.editTextRequested.connect(self.edit_shape_text)
        self.shape_editor.placeImageEscaped.connect(
            lambda: self.attribute_editor.image.place.setChecked(False))
        self._text_editor = None

        self.menu = MenuWidget()
        self.menu.copyRequested.connect(self.copy)
        self.menu.pasteRequested.connect(self.paste)
        self.menu.copyStyleRequested.connect(self.copy_style)
        self.menu.pasteStyleRequested.connect(self.paste_style)
        self.menu.libraryRequested.connect(self.open_button_library)
        self.menu.saveToLibraryRequested.connect(
            self.save_selection_to_library)
        self.menu.deleteRequested.connect(self.delete_selection)
        self.menu.sizeChanged.connect(self.editor_size_changed)
        self.menu.fitZoneRequested.connect(self.fit_zone_to_shapes)
        self.menu.editCenterToggled.connect(self.edit_center_mode_changed)
        self.menu.useSnapToggled.connect(self.use_snap)
        self.menu.snapValuesChanged.connect(self.snap_value_changed)
        self.menu.centerValuesChanged.connect(self.move_center)
        width, height = self.options['width'], self.options['height']
        # emit=False : à l'ouverture, rien n'a été modifié (sinon un
        # état fantôme entrait dans la pile d'undo)
        self.menu.set_size_values(width, height, emit=False)
        x, y = self.options['centerx'], self.options['centery']
        self.menu.set_center_values(x, y)
        self.menu.undoRequested.connect(self.undo)
        self.menu.redoRequested.connect(self.redo)
        method = partial(self.create_shape, SQUARE_BUTTON)
        self.menu.addButtonRequested.connect(method)
        method = partial(self.create_shape, TEXT)
        self.menu.addTextRequested.connect(method)
        method = partial(self.create_shape, BACKGROUND, before=True)
        self.menu.addBackgroundRequested.connect(method)
        method = self.set_selection_move_down
        self.menu.moveDownRequested.connect(method)
        method = self.set_selection_move_up
        self.menu.moveUpRequested.connect(method)
        method = self.set_selection_on_top
        self.menu.onTopRequested.connect(method)
        method = self.set_selection_on_bottom
        self.menu.onBottomRequested.connect(method)
        self.menu.alignRequested.connect(self.align_selection)
        self.menu.arrangeRequested.connect(self.arrange_selection)
        self.menu.testRequested.connect(self.test_hotbox)
        self.menu.radialRequested.connect(self.arrange_selection_radial)
        self.test_reader = None

        set_shortcut("Ctrl+Z", self.shape_editor, self.undo)
        set_shortcut("Ctrl+Y", self.shape_editor, self.redo)
        set_shortcut("Ctrl+C", self.shape_editor, self.copy)
        set_shortcut("Ctrl+V", self.shape_editor, self.paste)
        set_shortcut("Ctrl+Shift+C", self.shape_editor, self.copy_style)
        set_shortcut("Ctrl+Shift+V", self.shape_editor, self.paste_style)
        set_shortcut("Ctrl+H", self.shape_editor, self.open_search_replace)
        set_shortcut("del", self.shape_editor, self.delete_selection)
        set_shortcut("Ctrl+D", self.shape_editor, self.deselect_all)
        set_shortcut("Ctrl+A", self.shape_editor, self.select_all)
        set_shortcut("Ctrl+I", self.shape_editor, self.invert_selection)

        self.attribute_editor = AttributeEditor(self.application)
        self.attribute_editor.optionSet.connect(self.option_set)
        self.attribute_editor.rectModified.connect(self.rect_modified)
        self.attribute_editor.imageModified.connect(self.image_modified)
        self.attribute_editor.placeImageToggled.connect(self.place_image_mode)
        self.attribute_editor.centerImageRequested.connect(self.center_image)

        # librairie intégrée en bas, façon shelf Maya
        from hotbox_designer.buttonlibrary import LibraryShelf
        self.library_shelf = LibraryShelf(self.application)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.addWidget(self.shape_editor, stretch=1)
        self.hlayout.addWidget(self.attribute_editor)

        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.vlayout.addWidget(self.menu)
        self.vlayout.addLayout(self.hlayout, stretch=1)
        self.vlayout.addWidget(self.library_shelf)

    def copy(self):
        shapes = [dict(s.options) for s in self.shape_editor.selection]
        if not shapes:
            return
        text = json.dumps({SHAPES_CLIPBOARD_KEY: shapes})
        QtWidgets.QApplication.clipboard().setText(text)

    @staticmethod
    def clipboard_shapes():
        """Shapes portées par le presse-papier système, sinon []."""
        text = QtWidgets.QApplication.clipboard().text()
        try:
            shapes = json.loads(text)[SHAPES_CLIPBOARD_KEY]
            return [dict(shape) for shape in shapes]
        except (ValueError, TypeError, KeyError):
            return []

    def edit_shape_text(self, shape):
        """Champ d'édition posé sur le bouton (double-clic) : Entrée
        valide, Échap annule."""
        editor = self.shape_editor
        vp_rect = editor.viewport_mapper.to_viewport_rect(shape.rect)
        line = QtWidgets.QLineEdit(shape.options.get('text.content', ''), editor)
        line.setGeometry(vp_rect.toRect())
        line.setAlignment(QtCore.Qt.AlignCenter)
        line.selectAll()
        line.show()
        line.setFocus()
        self._text_editor = line

        def commit():
            if self._text_editor is None:
                return
            value = line.text()
            self._text_editor = None
            line.deleteLater()
            if value != shape.options.get('text.content', ''):
                shape.options['text.content'] = value
                editor.repaint()
                self.selection_changed()
                self.set_data_modified()

        def cancel():
            if self._text_editor is None:
                return
            self._text_editor = None
            line.deleteLater()

        line.returnPressed.connect(commit)
        line.editingFinished.connect(commit)  # perte de focus = valider
        # Échap annule (intercepté avant editingFinished)
        line.installEventFilter(self)
        line._cancel = cancel

    def eventFilter(self, obj, event):
        if (self._text_editor is not None and obj is self._text_editor
                and event.type() == QtCore.QEvent.KeyPress
                and event.key() == QtCore.Qt.Key_Escape):
            self._text_editor._cancel()
            return True
        return super(HotboxEditor, self).eventFilter(obj, event)

    def show_context_menu(self, global_pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction(icon('copy.png'), 'Copy\tCtrl+C', self.copy)
        menu.addAction(icon('paste.png'), 'Paste\tCtrl+V', self.paste)
        menu.addAction(
            icon('copy_settings.png'), 'Copy style\tCtrl+Shift+C',
            self.copy_style)
        menu.addAction(
            icon('paste_settings.png'), 'Paste style...\tCtrl+Shift+V',
            self.paste_style)
        menu.addSeparator()
        menu.addAction(
            icon('delete.png'), 'Delete\tDel', self.delete_selection)
        menu.addSeparator()
        menu.addAction(icon('ontop.png'), 'On top', self.set_selection_on_top)
        menu.addAction(
            icon('moveup.png'), 'Move up', self.set_selection_move_up)
        menu.addAction(
            icon('movedown.png'), 'Move down', self.set_selection_move_down)
        menu.addAction(
            icon('onbottom.png'), 'On bottom', self.set_selection_on_bottom)
        menu.addSeparator()
        menu.addAction(
            icon('picker.png'), 'Button library...', self.open_button_library)
        menu.addAction(
            icon('save.png'), 'Save selection to library...',
            self.save_selection_to_library)
        menu.addSeparator()
        menu.addAction(
            'Search and replace...\tCtrl+H', self.open_search_replace)
        menu.addSeparator()
        lock = menu.addAction('Lock selection', self.lock_selection)
        lock.setEnabled(bool(self.shape_editor.selection.shapes))
        locked_count = sum(
            1 for s in self.shape_editor.shapes if s.options.get('lock'))
        unlock = menu.addAction(
            'Unlock all (%d)' % locked_count, self.unlock_all)
        unlock.setEnabled(bool(locked_count))
        magnet = menu.addAction('Magnet snapping')
        magnet.setCheckable(True)
        magnet.setChecked(self.shape_editor.magnet_enabled)
        magnet.toggled.connect(self.set_magnet_enabled)
        menu.addSeparator()
        menu.addAction(
            icon('fit_zone.png'), 'Fit zone to shapes',
            self.fit_zone_to_shapes)
        menu.addAction('Frame view\tF', self.shape_editor.focus_view)
        menu.exec_(global_pos)

    def open_button_library(self):
        """Bouton librairie de la barre d'outils : affiche/masque la
        shelf du bas."""
        self.library_shelf.setVisible(not self.library_shelf.isVisible())

    def save_selection_to_library(self):
        """Range les boutons sélectionnés dans la shelf (nom +
        catégorie), pour les glisser-déposer dans d'autres hotboxes."""
        from hotbox_designer.buttonlibrary import SaveToLibraryDialog
        from hotbox_designer.dialog import warning
        shapes = list(self.shape_editor.selection)
        if not shapes:
            return warning('Button library', 'No shape selected')
        default = shapes[0].options.get('text.content') or 'button'
        dialog = SaveToLibraryDialog(
            self.library_shelf.categories(), default, self)
        dialog.category.setCurrentText(self.library_shelf.current_category())
        if dialog.exec_() == QtWidgets.QDialog.Rejected:
            return
        name = dialog.name.text() or 'button'
        category = dialog.category.currentText() or 'General'
        entries = []
        for index, shape in enumerate(shapes):
            entry_name = name if index == 0 else '%s %d' % (name, index + 1)
            entries.append({
                'name': entry_name,
                'category': category,
                'options': dict(shape.options)})
        self.library_shelf.add_entries(entries)
        self.library_shelf.show()

    def open_search_replace(self):
        from hotbox_designer.dialog import SearchReplaceDialog
        SearchReplaceDialog(self.replace_in_shapes, self).exec_()

    def replace_in_shapes(
            self, search, replace, in_left, in_right, in_labels):
        """Remplace dans les commandes/labels ; porte sur la sélection
        si elle existe, sinon sur toutes les shapes. Retourne le nombre
        de remplacements."""
        keys = []
        if in_left:
            keys.append('action.left.command')
        if in_right:
            keys.append('action.right.command')
        if in_labels:
            keys.append('text.content')
        shapes = (list(self.shape_editor.selection)
                  or list(self.shape_editor.shapes))
        count = 0
        for shape in shapes:
            for key in keys:
                value = shape.options.get(key) or ''
                occurrences = value.count(search)
                if occurrences:
                    shape.options[key] = value.replace(search, replace)
                    count += occurrences
        if count:
            self.shape_editor.repaint()
            self.selection_changed()
            self.set_data_modified()
        return count

    def lock_selection(self):
        """Verrouille la sélection : plus sélectionnable ni déplaçable
        (idéal pour un background) — déverrouillage par « Unlock all »."""
        for shape in self.shape_editor.selection:
            shape.options['lock'] = True
        self.shape_editor.selection.clear()
        self.shape_editor.update_selection()
        self.shape_editor.repaint()
        self.set_data_modified()

    def unlock_all(self):
        for shape in self.shape_editor.shapes:
            shape.options.pop('lock', None)
        self.shape_editor.repaint()
        self.set_data_modified()

    def set_magnet_enabled(self, state):
        self.shape_editor.magnet_enabled = state

    def copy_style(self):
        """Copie les options de la shape sélectionnée (une seule)."""
        shapes = list(self.shape_editor.selection)
        if len(shapes) != 1:
            from hotbox_designer.dialog import warning
            return warning(
                'Copy style', 'Select exactly one shape to copy its style')
        text = json.dumps({STYLE_CLIPBOARD_KEY: dict(shapes[0].options)})
        QtWidgets.QApplication.clipboard().setText(text)

    @staticmethod
    def clipboard_style():
        text = QtWidgets.QApplication.clipboard().text()
        try:
            return dict(json.loads(text)[STYLE_CLIPBOARD_KEY])
        except (ValueError, TypeError, KeyError):
            return None

    def paste_style(self):
        """Colle des groupes d'options choisis sur la sélection."""
        from hotbox_designer.dialog import PasteStyleDialog, warning
        style = self.clipboard_style()
        if style is None:
            return warning('Paste style', 'No style in clipboard')
        if not self.shape_editor.selection.shapes:
            return warning('Paste style', 'No shape selected')
        dialog = PasteStyleDialog(STYLE_GROUPS, self)
        if dialog.exec_() == QtWidgets.QDialog.Rejected:
            return
        self.apply_style(style, dialog.selected_keys())

    def apply_style(self, style, keys):
        keys = [k for k in keys if k in style]
        if not keys:
            return
        for shape in self.shape_editor.selection:
            for key in keys:
                shape.options[key] = style[key]
            if 'shape.width' in keys:
                shape.rect.setWidth(style['shape.width'])
            if 'shape.height' in keys:
                shape.rect.setHeight(style['shape.height'])
            shape.synchronize_rect()
            shape.synchronize_image()
        self.shape_editor.update_selection()
        self.selection_changed()
        self.shape_editor.repaint()
        self.set_data_modified()

    def paste(self):
        pasted = self.clipboard_shapes()
        if not pasted:
            return
        shape_datas = self.hotbox_data()['shapes'][:] + pasted
        hotbox_data = {
            'general': self.options,
            'shapes': shape_datas}
        self.set_hotbox_data(hotbox_data)
        self.undo_manager.set_data_modified(hotbox_data)
        self.hotboxDataModified.emit(hotbox_data)
        # select new shapes
        shapes = self.shape_editor.shapes[-len(pasted):]
        self.shape_editor.selection.replace(shapes)
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def undo(self):
        result = self.undo_manager.undo()
        if result is False:
            return
        data = self.undo_manager.data
        self.set_hotbox_data(data)
        self.hotboxDataModified.emit(self.hotbox_data())

    def redo(self):
        self.undo_manager.redo()
        data = self.undo_manager.data
        self.set_hotbox_data(data)
        self.hotboxDataModified.emit(self.hotbox_data())

    def deselect_all(self):
        self.shape_editor.selection.clear()
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def select_all(self):
        self.shape_editor.selection.add(self.shape_editor.shapes)
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def invert_selection(self):
        self.shape_editor.selection.invert(self.shape_editor.shapes)
        self.shape_editor.update_selection()
        self.shape_editor.repaint()

    def set_data_modified(self):
        self.undo_manager.set_data_modified(self.hotbox_data())
        self.hotboxDataModified.emit(self.hotbox_data())

    def use_snap(self, state):
        snap = self.menu.snap_values() if state else None
        self.shape_editor.transform.snap = snap
        self.shape_editor.repaint()

    def snap_value_changed(self):
        self.shape_editor.transform.snap = self.menu.snap_values()
        self.set_data_modified()
        self.shape_editor.repaint()

    def edit_center_mode_changed(self, state):
        self.shape_editor.edit_center_mode = state
        self.shape_editor.repaint()

    def option_set(self, option, value):
        for shape in self.shape_editor.selection:
            shape.options[option] = value
        self.shape_editor.repaint()
        self.set_data_modified()

    def editor_size_changed(self):
        size = self.menu.get_size()
        self.options['width'] = size.width()
        self.options['height'] = size.height()
        self.shape_editor.repaint()
        self.set_data_modified()

    FIT_ZONE_MARGIN = 10

    def fit_zone_to_shapes(self):
        """Recadre le plan de travail sur les shapes (façon dwpicker :
        on pose ses boutons librement, la zone s'ajuste autour)."""
        shapes = self.shape_editor.shapes
        if not shapes:
            return
        margin = self.FIT_ZONE_MARGIN
        bounds = get_combined_rects([shape.rect for shape in shapes])
        dx, dy = margin - bounds.left(), margin - bounds.top()
        for shape in shapes:
            shape.rect.moveLeft(shape.rect.left() + dx)
            shape.rect.moveTop(shape.rect.top() + dy)
            shape.synchronize_rect()
            shape.synchronize_image()
        width = int(round(bounds.width())) + 2 * margin
        height = int(round(bounds.height())) + 2 * margin
        self.options['width'] = width
        self.options['height'] = height
        self.options['centerx'] = int(round(self.options['centerx'] + dx))
        self.options['centery'] = int(round(self.options['centery'] + dy))
        self.menu.set_size_values(width, height, emit=False)
        self.menu.set_center_values(
            self.options['centerx'], self.options['centery'])
        if self.shape_editor.selection.shapes:
            self.shape_editor.update_selection()
        self.shape_editor.focus_view()
        self.set_data_modified()

    def move_center(self, x, y):
        self.options['centerx'] = x
        self.options['centery'] = y
        self.menu.set_center_values(x, y)
        self.shape_editor.repaint()
        self.set_data_modified()

    def rect_modified(self, option, value):
        shapes = self.shape_editor.selection
        for shape in shapes:
            shape.options[option] = value
            if option == 'shape.height':
                shape.rect.setHeight(value)
                continue
            elif option == 'shape.width':
                shape.rect.setWidth(value)
                continue

            width = shape.rect.width()
            height = shape.rect.height()
            if option == 'shape.left':
                shape.rect.setLeft(value)
            else:
                shape.rect.setTop(value)
            shape.rect.setWidth(width)
            shape.rect.setHeight(height)

        rects = [shape.rect for shape in self.shape_editor.selection]
        rect = get_combined_rects(rects)
        self.shape_editor.manipulator.set_rect(rect)
        self.shape_editor.repaint()

    def selection_changed(self):
        shapes = self.shape_editor.selection
        options = [shape.options for shape in shapes]
        self.attribute_editor.set_options(options)

    def create_shape(self, template, before=False):
        options = template.copy()
        shape = Shape(options)
        shape.rect.moveCenter(self.shape_editor.hotbox_rect().center())
        shape.synchronize_rect()
        if before is True:
            self.shape_editor.shapes.insert(0, shape)
        else:
            self.shape_editor.shapes.append(shape)
        self.shape_editor.repaint()
        self.set_data_modified()

    def image_modified(self):
        for shape in self.shape_editor.selection:
            shape.synchronize_image()
        self.shape_editor.repaint()

    def _selected_image_shape(self):
        shapes = list(self.shape_editor.selection)
        return shapes[0] if len(shapes) == 1 else None

    def place_image_mode(self, active):
        shape = self._selected_image_shape()
        if active and shape is not None:
            self.shape_editor.start_place_image(shape)
        else:
            self.shape_editor.stop_place_image()

    def center_image(self):
        shape = self._selected_image_shape()
        if shape is not None:
            self.shape_editor.center_image(shape)

    def set_selection_move_down(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        move_down_array_elements(array, elements)
        self.shape_editor.repaint()
        self.set_data_modified()

    def set_selection_move_up(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        move_up_array_elements(array, elements)
        self.shape_editor.repaint()
        self.set_data_modified()

    def set_selection_on_top(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        self.shape_editor.shapes = move_elements_to_array_end(array, elements)
        self.shape_editor.repaint()
        self.set_data_modified()

    def set_selection_on_bottom(self):
        array = self.shape_editor.shapes
        elements = self.shape_editor.selection
        shapes = move_elements_to_array_begin(array, elements)
        self.shape_editor.shapes = shapes
        self.shape_editor.repaint()
        self.set_data_modified()

    def align_selection(self, direction):
        if not align_shapes(self.shape_editor.selection, direction):
            return
        self.shape_editor.update_selection()
        self.shape_editor.repaint()
        self.set_data_modified()

    def arrange_selection(self, direction):
        if not arrange_shapes(self.shape_editor.selection, direction):
            return
        self.shape_editor.update_selection()
        self.shape_editor.repaint()
        self.set_data_modified()

    def arrange_selection_radial(self):
        """Dispose les boutons sélectionnés en cercle autour du centre
        de la hotbox (façon marking menu)."""
        from hotbox_designer.dialog import warning
        shapes = list(self.shape_editor.selection)
        if len(shapes) < 2:
            return warning(
                'Radial layout', 'Select at least 2 buttons to arrange')
        center = QtCore.QPointF(
            self.options['centerx'], self.options['centery'])
        if not arrange_radial(shapes, center=center):
            return
        self.shape_editor.update_selection()
        self.shape_editor.repaint()
        self.set_data_modified()

    def test_hotbox(self):
        """Ouvre la hotbox comme en production (reader), CENTRÉE sur
        l'éditeur, pour tester survol / clics / états. Se ferme avec
        Échap ou un clic en dehors."""
        from copy import deepcopy
        if self.test_reader is not None:
            self.test_reader.close()
        data = deepcopy(self.hotbox_data())
        self.test_reader = _TestReader(data, anchor=self)
        self.test_reader.show_centered()

    def closeEvent(self, event):
        if self.test_reader is not None:
            self.test_reader.close()
            self.test_reader = None
        super(HotboxEditor, self).closeEvent(event)

    def delete_selection(self):
        for shape in reversed(self.shape_editor.selection.shapes):
            self.shape_editor.shapes.remove(shape)
            self.shape_editor.selection.remove(shape)
        rects = [shape.rect for shape in self.shape_editor.selection]
        rect = get_combined_rects(rects)
        self.shape_editor.manipulator.set_rect(rect)
        self.shape_editor.repaint()
        self.set_data_modified()

    def hotbox_data(self):
        return {
            'general': self.options,
            'shapes': [shape.options for shape in self.shape_editor.shapes]}

    def set_hotbox_data(self, hotbox_data, reset_stacks=False):
        self.options = hotbox_data['general']
        self.shape_editor.options = self.options
        shapes = [Shape(options) for options in hotbox_data['shapes']]
        self.shape_editor.shapes = shapes
        self.shape_editor.manipulator.rect = None
        self.shape_editor.repaint()
        if reset_stacks is True:
            self.undo_manager.reset_stacks()


class _TestReader(HotboxReader):
    """Reader du mode test : centré sur l'éditeur (pas sous le curseur,
    qui est sur le bouton play), et refermable au clic en dehors."""

    def __init__(self, hotbox_data, anchor=None):
        super(_TestReader, self).__init__(hotbox_data, parent=None)
        self._anchor = anchor

    def show_centered(self):
        QtWidgets.QWidget.show(self)
        if self._anchor is not None:
            geo = self._anchor.geometry()
            global_center = self._anchor.mapToGlobal(
                QtCore.QPoint(geo.width() // 2, geo.height() // 2))
        else:
            global_center = QtGui.QCursor.pos()
        self.move(
            global_center.x() - self.width() // 2,
            global_center.y() - self.height() // 2)
        self.set_hovered_shapes()
        self.activateWindow()
        self.setFocus()

    def focusOutEvent(self, event):
        # un clic en dehors (ou Alt-Tab) referme le test
        self.close()
        super(_TestReader, self).focusOutEvent(event)


class UndoManager():
    def __init__(self, data):
        # copie profonde : l'état initial était stocké par référence et
        # se retrouvait corrompu par la première modification in place
        self._current_state = copy_hotbox_data(data)
        self._modified = False
        self._undo_stack = []
        self._redo_stack = []

    @property
    def data(self):
        return copy_hotbox_data(self._current_state)

    def undo(self):
        if not self._undo_stack:
            print ('no undostack')
            return False
        self._redo_stack.append(copy_hotbox_data(self._current_state))
        self._current_state = copy_hotbox_data(self._undo_stack[-1])
        del self._undo_stack[-1]
        return True

    def redo(self):
        if not self._redo_stack:
            return False

        self._undo_stack.append(copy_hotbox_data(self._current_state))
        self._current_state = copy_hotbox_data(self._redo_stack[-1])
        del self._redo_stack[-1]
        return True

    def set_data_modified(self, data):
        self._redo_stack = []
        self._undo_stack.append(copy_hotbox_data(self._current_state))
        self._current_state = copy_hotbox_data(data)
        self._modified = True

    def set_data_saved(self):
        self._modified = False

    @property
    def data_saved(self):
        return not self._modified

    def reset_stacks(self):
        self._undo_stack = []
        self._redo_stack = []
