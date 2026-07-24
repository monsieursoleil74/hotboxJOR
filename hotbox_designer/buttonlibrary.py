"""Librairie de boutons pré-configurés.

On sauvegarde n'importe quel bouton (avec ses commandes, couleurs,
texte…) dans une librairie rangée par catégories, puis on le glisse-
dépose dans n'importe quelle hotbox. Le fichier
``button_library.json`` vit dans le dossier de données de
l'application (préférences Maya, ~/.hotboxjor en standalone) — il peut
se partager entre artistes en le copiant.
"""
import json
import os

from hotbox_designer.vendor.Qt import QtWidgets, QtCore, QtGui
from hotbox_designer.interactive import Shape
from hotbox_designer.painting import draw_shape
from hotbox_designer.theme import apply_dark_theme

LIBRARY_FILENAME = 'button_library.json'
BUTTONS_MIME = 'application/x-hotbox-designer-buttons'
DEFAULT_CATEGORY = 'General'
THUMB_SIZE = 24


def library_path(application):
    return os.path.join(application.get_data_folder(), LIBRARY_FILENAME)


def load_library(path):
    """Retourne la liste d'entrées [{'name', 'category', 'options'}]."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            entries = json.load(f)
    except (ValueError, OSError):
        return []
    return [e for e in entries if isinstance(e, dict) and 'options' in e]


def save_library(path, entries):
    with open(path, 'w') as f:
        json.dump(entries, f, indent=2)


def button_thumbnail(options):
    """Dessine le bouton lui-même en guise d'icône."""
    shape = Shape(dict(options))
    rect = shape.rect
    pixmap = QtGui.QPixmap(THUMB_SIZE * 2, THUMB_SIZE)
    pixmap.fill(QtGui.QColor('#2b2b2b'))
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    width = rect.width() or 1.0
    height = rect.height() or 1.0
    scale = min((THUMB_SIZE * 2 - 4) / width, (THUMB_SIZE - 4) / height)
    painter.translate(
        (THUMB_SIZE * 2 - width * scale) / 2 - rect.left() * scale,
        (THUMB_SIZE - height * scale) / 2 - rect.top() * scale)
    painter.scale(scale, scale)
    draw_shape(painter, shape)
    painter.end()
    return QtGui.QIcon(pixmap)


class SaveToLibraryDialog(QtWidgets.QDialog):
    """Nom + catégorie pour ranger un bouton dans la librairie."""

    def __init__(self, categories, default_name='', parent=None):
        super(SaveToLibraryDialog, self).__init__(parent)
        self.setWindowTitle('Save button to library')
        self.name = QtWidgets.QLineEdit(default_name)
        self.category = QtWidgets.QComboBox()
        self.category.setEditable(True)
        self.category.addItems(sorted(categories) or [DEFAULT_CATEGORY])
        layout = QtWidgets.QFormLayout(self)
        layout.addRow('Name:', self.name)
        layout.addRow('Category:', self.category)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class ButtonLibraryTree(QtWidgets.QTreeWidget):
    """Arbre catégories → boutons, source du drag & drop."""

    def __init__(self, parent=None):
        super(ButtonLibraryTree, self).__init__(parent)
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setIconSize(QtCore.QSize(THUMB_SIZE * 2, THUMB_SIZE))

    def selected_options(self):
        options = []
        for item in self.selectedItems():
            entry = item.data(0, QtCore.Qt.UserRole)
            if entry is not None:
                options.append(entry['options'])
        return options

    def startDrag(self, actions):
        options = self.selected_options()
        if not options:
            return
        mime = QtCore.QMimeData()
        payload = json.dumps(options).encode('utf-8')
        mime.setData(BUTTONS_MIME, QtCore.QByteArray(payload))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        item = self.selectedItems()[0]
        pixmap = item.icon(0).pixmap(THUMB_SIZE * 2, THUMB_SIZE)
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
        drag.exec_(QtCore.Qt.CopyAction)


class ButtonLibraryWindow(QtWidgets.QWidget):
    """Fenêtre de librairie, partagée par tous les éditeurs."""

    def __init__(self, application, parent=None):
        super(ButtonLibraryWindow, self).__init__(parent, QtCore.Qt.Window)
        self.setWindowTitle('Button library')
        self.resize(280, 420)
        apply_dark_theme(self)
        self.path = library_path(application)

        self.tree = ButtonLibraryTree()
        self.hint = QtWidgets.QLabel(
            'Drag & drop buttons into a hotbox editor.')
        self.hint.setWordWrap(True)
        delete_button = QtWidgets.QPushButton('Delete selected')
        delete_button.released.connect(self.delete_selected)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addWidget(self.hint)
        layout.addWidget(delete_button)
        self.refresh()

    def entries(self):
        return load_library(self.path)

    def categories(self):
        return sorted({
            entry.get('category') or DEFAULT_CATEGORY
            for entry in self.entries()})

    def refresh(self):
        self.tree.clear()
        by_category = {}
        for entry in self.entries():
            category = entry.get('category') or DEFAULT_CATEGORY
            by_category.setdefault(category, []).append(entry)
        for category in sorted(by_category):
            top = QtWidgets.QTreeWidgetItem([category])
            top.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(top)
            for entry in sorted(
                    by_category[category], key=lambda e: e.get('name') or ''):
                item = QtWidgets.QTreeWidgetItem(
                    [entry.get('name') or 'button'])
                item.setIcon(0, button_thumbnail(entry['options']))
                item.setData(0, QtCore.Qt.UserRole, entry)
                flags = (
                    QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable |
                    QtCore.Qt.ItemIsDragEnabled)
                item.setFlags(flags)
                top.addChild(item)
            top.setExpanded(True)

    def add_entries(self, new_entries):
        entries = self.entries()
        entries.extend(new_entries)
        save_library(self.path, entries)
        self.refresh()

    def delete_selected(self):
        selected = [
            item.data(0, QtCore.Qt.UserRole)
            for item in self.tree.selectedItems()]
        selected = [entry for entry in selected if entry]
        if not selected:
            return
        entries = [e for e in self.entries() if e not in selected]
        save_library(self.path, entries)
        self.refresh()


class ShelfList(QtWidgets.QListWidget):
    """Rangée de boutons d'une catégorie, source du drag & drop."""

    def __init__(self, parent=None):
        super(ShelfList, self).__init__(parent)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setWrapping(False)
        self.setIconSize(QtCore.QSize(THUMB_SIZE * 2, THUMB_SIZE))
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(4)

    def selected_entries(self):
        return [
            item.data(QtCore.Qt.UserRole)
            for item in self.selectedItems()
            if item.data(QtCore.Qt.UserRole)]

    def startDrag(self, actions):
        entries = self.selected_entries()
        if not entries:
            return
        mime = QtCore.QMimeData()
        payload = json.dumps(
            [entry['options'] for entry in entries]).encode('utf-8')
        mime.setData(BUTTONS_MIME, QtCore.QByteArray(payload))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        pixmap = self.selectedItems()[0].icon().pixmap(
            THUMB_SIZE * 2, THUMB_SIZE)
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
        drag.exec_(QtCore.Qt.CopyAction)


class LibraryShelf(QtWidgets.QWidget):
    """Librairie intégrée en bas de l'éditeur, façon shelf Maya :
    un onglet par catégorie, les boutons se glissent-déposent vers la
    hotbox juste au-dessus. Clic droit sur un bouton : supprimer."""

    def __init__(self, application, parent=None):
        super(LibraryShelf, self).__init__(parent)
        self.path = library_path(application)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
        self.setFixedHeight(THUMB_SIZE + 74)
        register_shelf(self)
        self.refresh()

    def categories(self):
        return sorted({
            entry.get('category') or DEFAULT_CATEGORY
            for entry in load_library(self.path)})

    def refresh(self):
        current = self.tabs.tabText(self.tabs.currentIndex())
        self.tabs.clear()
        by_category = {}
        for entry in load_library(self.path):
            category = entry.get('category') or DEFAULT_CATEGORY
            by_category.setdefault(category, []).append(entry)
        if not by_category:
            empty = ShelfList()
            empty.setToolTip(
                'Save buttons here: select shapes then use the save '
                'button of the toolbar')
            self.tabs.addTab(empty, DEFAULT_CATEGORY)
            return
        for category in sorted(by_category):
            shelf_list = ShelfList()
            shelf_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            shelf_list.customContextMenuRequested.connect(
                lambda pos, lst=shelf_list: self._menu(lst, pos))
            for entry in sorted(
                    by_category[category], key=lambda e: e.get('name') or ''):
                item = QtWidgets.QListWidgetItem(entry.get('name') or 'button')
                item.setIcon(button_thumbnail(entry['options']))
                item.setData(QtCore.Qt.UserRole, entry)
                item.setToolTip(
                    '%s — drag & drop into the hotbox' % (
                        entry.get('name') or 'button'))
                shelf_list.addItem(item)
            index = self.tabs.addTab(shelf_list, category)
            if category == current:
                self.tabs.setCurrentIndex(index)

    def current_category(self):
        text = self.tabs.tabText(self.tabs.currentIndex())
        return text or DEFAULT_CATEGORY

    def _menu(self, shelf_list, position):
        entries = shelf_list.selected_entries()
        if not entries:
            return
        menu = QtWidgets.QMenu(self)
        label = ('Delete "%s"' % entries[0]['name']
                 if len(entries) == 1 else 'Delete %d buttons' % len(entries))
        menu.addAction(label, lambda: self._delete(entries))
        menu.exec_(shelf_list.mapToGlobal(position))

    def _delete(self, entries):
        remaining = [e for e in load_library(self.path) if e not in entries]
        save_library(self.path, remaining)
        refresh_shelves()

    def add_entries(self, new_entries):
        entries = load_library(self.path)
        entries.extend(new_entries)
        save_library(self.path, entries)
        refresh_shelves()


_shelves = []


def register_shelf(shelf):
    _shelves.append(shelf)
    shelf.destroyed.connect(
        lambda *_: _shelves.remove(shelf) if shelf in _shelves else None)


def refresh_shelves():
    """Toutes les shelves ouvertes (un éditeur chacune) se resynchronisent."""
    for shelf in list(_shelves):
        try:
            shelf.refresh()
        except RuntimeError:  # widget C++ détruit
            _shelves.remove(shelf)


_library_windows = {}


def show_button_library(application, parent=None):
    """Une seule fenêtre de librairie par dossier de données."""
    key = library_path(application)
    window = _library_windows.get(key)
    if window is None:
        window = ButtonLibraryWindow(application, parent)
        _library_windows[key] = window
    window.refresh()
    window.show()
    window.raise_()
    window.activateWindow()
    return window
