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

LIBRARY_FILENAME = 'button_library.json'
BUTTONS_MIME = 'application/x-hotbox-designer-buttons'
DEFAULT_CATEGORY = 'General'
THUMB_SIZE = 24
# vignettes de la shelf (plus grandes que celles de la fenêtre legacy)
SHELF_THUMB_WIDTH = 72
SHELF_THUMB_HEIGHT = 36
# une catégorie vide est persistée par une entrée marqueur
CATEGORY_KEY = '__category__'


def library_path(application):
    return os.path.join(application.get_data_folder(), LIBRARY_FILENAME)


def load_library_raw(path):
    """Toutes les entrées du fichier : boutons ET marqueurs de
    catégories vides."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            entries = json.load(f)
    except (ValueError, OSError):
        return []
    return [e for e in entries if isinstance(e, dict)]


def load_library(path):
    """Retourne la liste des boutons [{'name', 'category', 'options'}]."""
    return [e for e in load_library_raw(path) if 'options' in e]


def load_extra_categories(path):
    """Catégories créées à la main, même sans bouton dedans."""
    return [
        e[CATEGORY_KEY] for e in load_library_raw(path) if CATEGORY_KEY in e]


def save_library(path, entries):
    with open(path, 'w') as f:
        json.dump(entries, f, indent=2)


# cache des vignettes : les rendus sont coûteux et la shelf se
# rafraîchit souvent (ajout/suppression) — on ré-dessine seulement
# quand l'apparence d'un bouton change réellement
_THUMB_CACHE = {}
_THUMB_KEYS = (
    'shape', 'shape.cornersx', 'shape.cornersy', 'border',
    'borderwidth.normal', 'bordercolor.normal', 'bordercolor.transparency',
    'bgcolor.normal', 'bgcolor.transparency', 'text.content', 'text.size',
    'text.bold', 'text.italic', 'text.color', 'text.valign', 'text.halign',
    'image.path', 'image.fit')


def _thumb_cache_key(options, size):
    return (size,) + tuple(options.get(k) for k in _THUMB_KEYS)


def button_thumbnail(options, size=None):
    """Dessine le bouton lui-même en guise d'icône (mis en cache)."""
    thumb_width, thumb_height = size or (THUMB_SIZE * 2, THUMB_SIZE)
    key = _thumb_cache_key(options, (thumb_width, thumb_height))
    cached = _THUMB_CACHE.get(key)
    if cached is not None:
        return cached
    shape = Shape(dict(options))
    rect = shape.rect
    pixmap = QtGui.QPixmap(thumb_width, thumb_height)
    pixmap.fill(QtGui.QColor('#2b2b2b'))
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    width = rect.width() or 1.0
    height = rect.height() or 1.0
    scale = min((thumb_width - 4) / width, (thumb_height - 4) / height)
    painter.translate(
        (thumb_width - width * scale) / 2 - rect.left() * scale,
        (thumb_height - height * scale) / 2 - rect.top() * scale)
    painter.scale(scale, scale)
    draw_shape(painter, shape)
    painter.end()
    icon = QtGui.QIcon(pixmap)
    if len(_THUMB_CACHE) > 512:  # garde-fou mémoire
        _THUMB_CACHE.clear()
    _THUMB_CACHE[key] = icon
    return icon


def hotbox_thumbnail(hotbox_data, width=190, height=120):
    """Mini-rendu d'une hotbox complète, pour l'aperçu du manager."""
    general = hotbox_data.get('general', {})
    hb_w = general.get('width') or 1
    hb_h = general.get('height') or 1
    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtGui.QColor('#2b2b2b'))
    shapes = hotbox_data.get('shapes') or []
    if not shapes:
        return pixmap
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    margin = 6
    scale = min(
        (width - 2 * margin) / float(hb_w),
        (height - 2 * margin) / float(hb_h))
    painter.translate(
        (width - hb_w * scale) / 2, (height - hb_h * scale) / 2)
    painter.scale(scale, scale)
    for options in shapes:
        Shape(dict(options)).draw(painter)
    painter.end()
    return pixmap


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


class ShelfList(QtWidgets.QListWidget):
    """Rangée de boutons d'une catégorie, source du drag & drop."""

    def __init__(self, parent=None):
        super(ShelfList, self).__init__(parent)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setWrapping(False)
        self.setIconSize(
            QtCore.QSize(SHELF_THUMB_WIDTH, SHELF_THUMB_HEIGHT))
        self.setDragEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSpacing(6)

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
            SHELF_THUMB_WIDTH, SHELF_THUMB_HEIGHT)
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
        drag.exec_(QtCore.Qt.CopyAction)


class LibraryShelf(QtWidgets.QWidget):
    """Librairie intégrée en bas de l'éditeur, façon shelf Maya :
    un onglet par catégorie, les boutons se glissent-déposent vers la
    hotbox juste au-dessus. Clic droit sur un bouton : supprimer.
    « ＋ » : créer une catégorie ; clic droit sur un onglet vide : la
    supprimer."""

    def __init__(self, application, parent=None):
        super(LibraryShelf, self).__init__(parent)
        self.path = library_path(application)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('＋')
        self.add_button.setToolTip('Create a category')
        self.add_button.released.connect(self._prompt_category)
        self.tabs.setCornerWidget(
            self.add_button, QtCore.Qt.TopRightCorner)
        tab_bar = self.tabs.tabBar()
        tab_bar.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tab_bar.customContextMenuRequested.connect(self._tab_menu)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
        self.setFixedHeight(SHELF_THUMB_HEIGHT + 96)
        register_shelf(self)
        self.refresh()

    def categories(self):
        categories = {
            entry.get('category') or DEFAULT_CATEGORY
            for entry in load_library(self.path)}
        categories.update(load_extra_categories(self.path))
        return sorted(categories)

    def refresh(self):
        current = self.tabs.tabText(self.tabs.currentIndex())
        self.tabs.clear()
        by_category = {
            category: [] for category in load_extra_categories(self.path)}
        for entry in load_library(self.path):
            category = entry.get('category') or DEFAULT_CATEGORY
            by_category.setdefault(category, []).append(entry)
        if not by_category:
            by_category = {DEFAULT_CATEGORY: []}
        for category in sorted(by_category):
            shelf_list = ShelfList()
            shelf_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            shelf_list.customContextMenuRequested.connect(
                lambda pos, lst=shelf_list: self._menu(lst, pos))
            if not by_category[category]:
                shelf_list.setToolTip(
                    'Empty category — select shapes and use the save '
                    'button of the toolbar to fill it')
            for entry in sorted(
                    by_category[category], key=lambda e: e.get('name') or ''):
                item = QtWidgets.QListWidgetItem(entry.get('name') or 'button')
                item.setIcon(button_thumbnail(
                    entry['options'],
                    (SHELF_THUMB_WIDTH, SHELF_THUMB_HEIGHT)))
                item.setData(QtCore.Qt.UserRole, entry)
                item.setToolTip(
                    '%s — drag & drop into the hotbox' % (
                        entry.get('name') or 'button'))
                shelf_list.addItem(item)
            index = self.tabs.addTab(shelf_list, category)
            if category == current:
                self.tabs.setCurrentIndex(index)

    def _prompt_category(self):
        name, accepted = QtWidgets.QInputDialog.getText(
            self, 'New category', 'Category name:')
        if not accepted or not name.strip():
            return
        self.add_category(name.strip())

    def add_category(self, name):
        if name in self.categories():
            return
        raw = load_library_raw(self.path)
        raw.append({CATEGORY_KEY: name})
        save_library(self.path, raw)
        refresh_shelves()
        index = [
            self.tabs.tabText(i) for i in range(self.tabs.count())
        ].index(name)
        self.tabs.setCurrentIndex(index)

    def delete_category(self, name):
        """Supprime une catégorie VIDE (marqueur seulement)."""
        buttons = [
            e for e in load_library(self.path)
            if (e.get('category') or DEFAULT_CATEGORY) == name]
        if buttons:
            return False
        raw = [
            e for e in load_library_raw(self.path)
            if e.get(CATEGORY_KEY) != name]
        save_library(self.path, raw)
        refresh_shelves()
        return True

    def _tab_menu(self, position):
        tab_bar = self.tabs.tabBar()
        index = tab_bar.tabAt(position)
        if index < 0:
            return
        name = self.tabs.tabText(index)
        widget = self.tabs.widget(index)
        menu = QtWidgets.QMenu(self)
        action = menu.addAction(
            'Delete category "%s"' % name,
            lambda: self.delete_category(name))
        action.setEnabled(widget is not None and widget.count() == 0)
        if not action.isEnabled():
            action.setToolTip('Only empty categories can be deleted')
        menu.exec_(tab_bar.mapToGlobal(position))

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
        remaining = [
            e for e in load_library_raw(self.path) if e not in entries]
        save_library(self.path, remaining)
        refresh_shelves()

    def add_entries(self, new_entries):
        entries = load_library_raw(self.path)
        # anti-doublon : on ne stocke pas deux fois un bouton identique
        # (même nom, catégorie ET options)
        existing = [e for e in entries if 'options' in e]
        added = 0
        for entry in new_entries:
            if entry not in existing:
                entries.append(entry)
                existing.append(entry)
                added += 1
        if added:
            save_library(self.path, entries)
            refresh_shelves()
        return added


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
