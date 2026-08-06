"""Librairie de boutons pré-configurés.

Deux niveaux, façon pipeline studio :

- **Perso** : ``button_library.json`` dans le dossier de données
  (préférences Maya ; ``~/.hotboxjor`` en standalone). Modifiable par
  l'artiste.
- **Studio** (optionnel, LECTURE SEULE) : une librairie partagée sur le
  réseau, désignée par la variable d'environnement
  ``HOTBOX_STUDIO_LIBRARY`` (un fichier .json OU un dossier contenant
  ``button_library.json``). À défaut de variable, on cherche le dossier
  ``DEFAULT_STUDIO_DIR`` ci-dessous. Les onglets studio portent le
  **logo du studio** en icône (``studio_logo.png``/``logo.png`` posé à
  côté de la librairie, ou variable ``HOTBOX_STUDIO_LOGO`` ; sinon un
  logo par défaut) et ne sont pas modifiables — seul le lead maintient
  ce fichier.

Un même bouton se glisse-dépose depuis n'importe quel onglet vers une
hotbox.
"""
import json
import os
import subprocess
import sys

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

# librairie studio partagée
STUDIO_ENV_VARIABLE = 'HOTBOX_STUDIO_LIBRARY'
STUDIO_LOGO_ENV_VARIABLE = 'HOTBOX_STUDIO_LOGO'
DEFAULT_STUDIO_DIR = r'C:\Users\ortzj\Desktop\JOR\hotbox'
STUDIO_PREFIX = '\u2605 '  # « ★ » : repli si aucun logo trouvé
STUDIO_LOGO_NAMES = ('studio_logo.png', 'logo.png')

# mode « admin studio » : choisi AU LANCEMENT —
# launch_manager('maya', studio_admin=True) pour le lead, lancement
# normal pour les animateurs. Seul l'admin peut modifier la librairie
# officielle (catégories, envoi/renommage/rangement de boutons) ; en
# mode normal elle est une référence en lecture seule, chacun gardant
# sa librairie perso modifiable.
_STUDIO_ADMIN = False


def set_studio_admin(enabled):
    global _STUDIO_ADMIN
    _STUDIO_ADMIN = bool(enabled)


def is_studio_admin():
    return _STUDIO_ADMIN


def library_path(application):
    return os.path.join(application.get_data_folder(), LIBRARY_FILENAME)


def studio_location():
    location = os.environ.get(STUDIO_ENV_VARIABLE) or DEFAULT_STUDIO_DIR
    if not location:
        return None
    return os.path.expandvars(os.path.expanduser(location))


def studio_library_path():
    """Chemin du fichier de librairie studio, ou None. On accepte un
    fichier .json direct ou un dossier contenant button_library.json."""
    location = studio_location()
    if not location:
        return None
    if location.lower().endswith('.json'):
        return location if os.path.exists(location) else None
    candidate = os.path.join(location, LIBRARY_FILENAME)
    return candidate if os.path.exists(candidate) else None


def studio_logo_path():
    """Logo du studio pour les onglets partagés :
    variable HOTBOX_STUDIO_LOGO, sinon studio_logo.png/logo.png à côté
    de la librairie studio, sinon le logo par défaut embarqué."""
    env = os.environ.get(STUDIO_LOGO_ENV_VARIABLE)
    if env:
        env = os.path.expandvars(os.path.expanduser(env))
        if os.path.exists(env):
            return env
    location = studio_location()
    if location:
        folder = location if os.path.isdir(location) else os.path.dirname(
            location)
        for name in STUDIO_LOGO_NAMES:
            candidate = os.path.join(folder, name)
            if os.path.exists(candidate):
                return candidate
    default = os.path.join(
        os.path.dirname(__file__), 'resources', 'icons', 'studio_logo.png')
    return default if os.path.exists(default) else None


def load_studio_library():
    """Boutons de la librairie studio (liste possiblement vide)."""
    path = studio_library_path()
    return load_library(path) if path else []


def studio_write_path():
    """Chemin où ÉCRIRE la librairie studio (crée le dossier au besoin).
    Retourne None si aucun emplacement studio n'est configuré."""
    location = studio_location()
    if not location:
        return None
    if location.lower().endswith('.json'):
        path = location
    else:
        path = os.path.join(location, LIBRARY_FILENAME)
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except OSError:
            return None
    return path


def export_to_studio(entries):
    """Ajoute des boutons à la librairie studio (dédupliqués). Retourne
    le nombre réellement ajouté, ou -1 si le studio n'est pas
    accessible en écriture."""
    path = studio_write_path()
    if not path:
        return -1
    existing = load_library_raw(path)
    already = [e for e in existing if 'options' in e]
    added = 0
    for entry in entries:
        if entry not in already:
            existing.append(entry)
            already.append(entry)
            added += 1
    if added:
        try:
            save_library(path, existing)
        except OSError:
            return -1
    return added


def load_library_raw(path):
    """Toutes les entrées du fichier : boutons ET marqueurs de
    catégories vides."""
    if not path or not os.path.exists(path):
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


def categories_in(path):
    """Toutes les catégories d'un fichier de librairie (boutons +
    catégories vides marquées), triées."""
    categories = {
        e.get('category') or DEFAULT_CATEGORY for e in load_library(path)}
    categories.update(load_extra_categories(path))
    return sorted(categories)


def add_category_to(path, name):
    """Crée une catégorie vide (marqueur) dans `path`. Retourne False si
    elle existe déjà ou si le nom est vide."""
    name = (name or '').strip()
    if not name or name in categories_in(path):
        return False
    raw = load_library_raw(path)
    raw.append({CATEGORY_KEY: name})
    save_library(path, raw)
    return True


def rename_category_in(path, old, new):
    """Renomme une catégorie : ré-étiquette tous ses boutons ET son
    marqueur de catégorie vide. Retourne False si rien à faire."""
    new = (new or '').strip()
    if not new or new == old or old not in categories_in(path):
        return False
    raw = load_library_raw(path)
    for entry in raw:
        if 'options' in entry:
            if (entry.get('category') or DEFAULT_CATEGORY) == old:
                entry['category'] = new
        elif entry.get(CATEGORY_KEY) == old:
            entry[CATEGORY_KEY] = new
    save_library(path, raw)
    return True


def delete_empty_category_in(path, name):
    """Supprime une catégorie VIDE (aucun bouton). Retourne False si elle
    contient encore des boutons."""
    has_buttons = any(
        (e.get('category') or DEFAULT_CATEGORY) == name
        for e in load_library(path))
    if has_buttons:
        return False
    raw = [e for e in load_library_raw(path) if e.get(CATEGORY_KEY) != name]
    save_library(path, raw)
    return True


def set_entries_category_in(path, entries, category):
    """Range des boutons EXISTANTS dans une autre catégorie (déplacement).
    Retourne le nombre de boutons effectivement déplacés."""
    category = (category or '').strip() or DEFAULT_CATEGORY
    raw = load_library_raw(path)
    changed = 0
    for entry in raw:
        if 'options' not in entry or entry not in entries:
            continue
        if (entry.get('category') or DEFAULT_CATEGORY) != category:
            entry['category'] = category
            changed += 1
    if changed:
        save_library(path, raw)
    return changed


def rename_entry_in(path, entry, new_name):
    """Renomme un bouton EXISTANT de la librairie. Retourne True si un
    bouton a été renommé."""
    new_name = (new_name or '').strip()
    if not new_name:
        return False
    raw = load_library_raw(path)
    renamed = False
    for candidate in raw:
        if 'options' in candidate and candidate == entry:
            candidate['name'] = new_name
            renamed = True
    if renamed:
        save_library(path, raw)
    return renamed


def open_folder(path):
    """Ouvre le dossier contenant `path` dans l'explorateur de fichiers
    du système (Windows/mac/Linux). Retourne False si impossible."""
    if not path:
        return False
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    if not folder or not os.path.exists(folder):
        return False
    try:
        if sys.platform.startswith('win'):
            os.startfile(folder)  # noqa: seulement sous Windows
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', folder])
        else:
            subprocess.Popen(['xdg-open', folder])
        return True
    except OSError:
        return False


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
    """Icône du bouton pour la librairie (mise en cache).

    - bouton AVEC image : on affiche l'image seule, ajustée, sur fond
      transparent (icône propre, pas de rectangle sombre derrière) ;
    - bouton SANS image : on dessine le bouton (forme + couleurs), fond
      transparent."""
    thumb_width, thumb_height = size or (THUMB_SIZE * 2, THUMB_SIZE)
    key = _thumb_cache_key(options, (thumb_width, thumb_height))
    cached = _THUMB_CACHE.get(key)
    if cached is not None:
        return cached
    pixmap = QtGui.QPixmap(thumb_width, thumb_height)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    from hotbox_designer.images import resolve_image_path
    image_path = resolve_image_path(options.get('image.path') or '')
    image = QtGui.QPixmap(image_path) if image_path else QtGui.QPixmap()
    if not image.isNull():
        # image seule, centrée et ajustée en gardant les proportions
        scaled = image.scaled(
            thumb_width - 4, thumb_height - 4,
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        painter.drawPixmap(
            (thumb_width - scaled.width()) // 2,
            (thumb_height - scaled.height()) // 2, scaled)
    else:
        shape = Shape(dict(options))
        rect = shape.rect
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
    """Nom + destination (perso ou studio) + catégorie pour ranger un
    bouton dans la librairie. La destination studio n'est proposée que si
    un emplacement studio est configuré et accessible en écriture — on
    peut donc envoyer un bouton directement dans une shelf TAT, sans
    passer par General puis « Move to »."""

    def __init__(self, perso_categories, studio_categories=None,
                 studio_available=False, default_name='', parent=None):
        super(SaveToLibraryDialog, self).__init__(parent)
        self.setWindowTitle('Save button to library')
        self._perso_categories = sorted(perso_categories) or [DEFAULT_CATEGORY]
        self._studio_categories = (
            sorted(studio_categories or []) or [DEFAULT_CATEGORY])
        self.name = QtWidgets.QLineEdit(default_name)

        self.destination = QtWidgets.QComboBox()
        self.destination.addItem('Perso', 'perso')
        if studio_available:
            self.destination.addItem('Studio (TAT)', 'studio')
        self.destination.currentIndexChanged.connect(self._update_categories)

        self.category = QtWidgets.QComboBox()
        self.category.setEditable(True)

        layout = QtWidgets.QFormLayout(self)
        layout.addRow('Name:', self.name)
        # inutile d'afficher le choix s'il n'y a que « Perso »
        if studio_available:
            layout.addRow('Library:', self.destination)
        layout.addRow('Category:', self.category)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self._update_categories()

    def is_studio(self):
        return self.destination.currentData() == 'studio'

    def _update_categories(self):
        keep = self.category.currentText()
        self.category.clear()
        categories = (self._studio_categories if self.is_studio()
                      else self._perso_categories)
        self.category.addItems(categories)
        if keep:
            self.category.setCurrentText(keep)


class ShelfList(QtWidgets.QListWidget):
    """Rangée de boutons d'une catégorie, source du drag & drop."""

    def __init__(self, parent=None):
        super(ShelfList, self).__init__(parent)
        self.readonly = False  # True pour les onglets studio
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
        logo = studio_logo_path()
        self.studio_icon = QtGui.QIcon(logo) if logo else QtGui.QIcon()
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setIconSize(QtCore.QSize(20, 16))
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('＋')
        self.add_button.setToolTip('Create a category')
        self.add_button.released.connect(self._prompt_category)
        # badge visible seulement quand le manager est lancé en mode
        # admin studio : on sait d'un coup d'œil qu'on édite l'officiel
        self.admin_badge = QtWidgets.QLabel(' ★ STUDIO ADMIN ')
        self.admin_badge.setToolTip(
            'Studio admin mode — you are editing the OFFICIAL library')
        from hotbox_designer.theme import ACCENT
        self.admin_badge.setStyleSheet(
            'QLabel {color: white; background: %s; border-radius: 3px;'
            'font-weight: bold; font-size: 10px; padding: 1px 4px;}' % ACCENT)
        self.admin_badge.setVisible(is_studio_admin())
        corner = QtWidgets.QWidget()
        corner_layout = QtWidgets.QHBoxLayout(corner)
        corner_layout.setContentsMargins(0, 0, 4, 0)
        corner_layout.setSpacing(6)
        corner_layout.addWidget(self.admin_badge)
        corner_layout.addWidget(self.add_button)
        self.tabs.setCornerWidget(corner, QtCore.Qt.TopRightCorner)
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

    def studio_categories(self):
        """Catégories de la librairie studio (avec les vides)."""
        path = studio_library_path()
        return categories_in(path) if path else []

    def save_entries(self, entries, studio=False):
        """Range des boutons dans la librairie perso (défaut) ou
        directement dans la librairie studio. Retourne le nombre ajouté
        (ou -1 si le studio n'est pas accessible en écriture)."""
        if studio:
            added = export_to_studio(entries)
            if added < 0:
                self._warn_no_studio()
            else:
                refresh_shelves()
            return added
        return self.add_entries(entries)

    def refresh(self):
        current = self._current_key()
        self.tabs.clear()

        # 1) onglets studio (partagés) EN PREMIER — on affiche AUSSI les
        # catégories studio vides (marqueurs), sinon une catégorie créée
        # mais pas encore remplie resterait invisible
        studio = {}
        studio_src = studio_library_path()
        if studio_src:
            for category in load_extra_categories(studio_src):
                studio.setdefault(category, [])
        for entry in load_studio_library():
            category = entry.get('category') or DEFAULT_CATEGORY
            studio.setdefault(category, []).append(entry)
        for category in sorted(studio):
            self._add_tab(category, studio[category], current, readonly=True)

        # 2) onglets perso (modifiables)
        by_category = {
            category: [] for category in load_extra_categories(self.path)}
        for entry in load_library(self.path):
            category = entry.get('category') or DEFAULT_CATEGORY
            by_category.setdefault(category, []).append(entry)
        if not by_category and not studio:
            by_category = {DEFAULT_CATEGORY: []}
        for category in sorted(by_category):
            self._add_tab(category, by_category[category], current)

    def _current_key(self):
        """(readonly, catégorie) de l'onglet courant, pour le restaurer
        après un refresh (studio et perso peuvent avoir le même nom)."""
        widget = self.tabs.currentWidget()
        if widget is None:
            return None
        text = self.tabs.tabText(self.tabs.currentIndex())
        if text.startswith(STUDIO_PREFIX):
            text = text[len(STUDIO_PREFIX):]
        return (getattr(widget, 'readonly', False), text)

    def _add_tab(self, category, entries, current, readonly=False):
        shelf_list = ShelfList()
        shelf_list.readonly = readonly
        # menu contextuel sur toutes les listes (l'ouverture de dossier
        # marche aussi pour le studio ; suppression/envoi = perso seul)
        shelf_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        shelf_list.customContextMenuRequested.connect(
            lambda pos, lst=shelf_list: self._menu(lst, pos))
        if not readonly:
            if not entries:
                shelf_list.setToolTip(
                    'Empty category — select shapes and use the save '
                    'button of the toolbar to fill it')
        suffix = ''
        if readonly:
            suffix = (' (studio, admin)' if is_studio_admin()
                      else ' (studio, read-only)')
        for entry in sorted(entries, key=lambda e: e.get('name') or ''):
            item = QtWidgets.QListWidgetItem(entry.get('name') or 'button')
            item.setIcon(button_thumbnail(
                entry['options'], (SHELF_THUMB_WIDTH, SHELF_THUMB_HEIGHT)))
            item.setData(QtCore.Qt.UserRole, entry)
            item.setToolTip(
                '%s — drag & drop into the hotbox%s' % (
                    entry.get('name') or 'button', suffix))
            shelf_list.addItem(item)
        # onglet studio : logo du studio en icône (repli ★ si pas de logo)
        if readonly and not self.studio_icon.isNull():
            index = self.tabs.addTab(shelf_list, self.studio_icon, category)
            self.tabs.setTabToolTip(
                index, 'Studio library — admin mode (editable)'
                if is_studio_admin() else 'Studio library (read-only)')
        elif readonly:
            index = self.tabs.addTab(shelf_list, STUDIO_PREFIX + category)
        else:
            index = self.tabs.addTab(shelf_list, category)
        if (readonly, category) == current:
            self.tabs.setCurrentIndex(index)

    def _prompt_category(self, studio=False):
        title = 'New studio category' if studio else 'New category'
        name, accepted = QtWidgets.QInputDialog.getText(
            self, title, 'Category name:')
        if not accepted or not name.strip():
            return
        if studio:
            self.add_studio_category(name.strip())
        else:
            self.add_category(name.strip())

    def add_studio_category(self, name):
        path = studio_write_path()
        if path is None:
            return self._warn_no_studio()
        if add_category_to(path, name):
            refresh_shelves()

    def _prompt_rename(self, path, old):
        if path is None:
            return self._warn_no_studio()
        new, accepted = QtWidgets.QInputDialog.getText(
            self, 'Rename category', 'New name:', text=old)
        if not accepted:
            return
        if rename_category_in(path, old, new.strip()):
            refresh_shelves()

    def _delete_category(self, path, name):
        if path is None:
            return self._warn_no_studio()
        if delete_empty_category_in(path, name):
            refresh_shelves()

    def _prompt_rename_entry(self, path, entry):
        if path is None:
            return self._warn_no_studio()
        new, accepted = QtWidgets.QInputDialog.getText(
            self, 'Rename button', 'New name:', text=entry.get('name') or '')
        if not accepted:
            return
        if rename_entry_in(path, entry, new.strip()):
            refresh_shelves()

    def _prompt_move(self, path, entries):
        if path is None:
            return self._warn_no_studio()
        existing = categories_in(path) or [DEFAULT_CATEGORY]
        category, accepted = QtWidgets.QInputDialog.getItem(
            self, 'Move to category', 'Category:', existing, 0, True)
        if not accepted or not category.strip():
            return
        if set_entries_category_in(path, entries, category.strip()):
            refresh_shelves()

    def _warn_no_studio(self):
        QtWidgets.QMessageBox.warning(
            self, 'Studio library',
            'Studio library is not configured or not writable.\n'
            'Set the HOTBOX_STUDIO_LIBRARY location first.')

    def add_category(self, name):
        if not add_category_to(self.path, name):
            return
        refresh_shelves()
        names = [self.tabs.tabText(i) for i in range(self.tabs.count())]
        if name in names:
            self.tabs.setCurrentIndex(names.index(name))

    def delete_category(self, name):
        """Supprime une catégorie VIDE (marqueur seulement)."""
        deleted = delete_empty_category_in(self.path, name)
        if deleted:
            refresh_shelves()
        return deleted

    def _tab_name(self, index):
        """Nom de catégorie de l'onglet (préfixe ★ studio retiré)."""
        text = self.tabs.tabText(index)
        if text.startswith(STUDIO_PREFIX):
            text = text[len(STUDIO_PREFIX):]
        return text

    def _category_target(self, readonly):
        """Fichier de librairie à modifier selon l'onglet (studio/perso)."""
        return studio_write_path() if readonly else self.path

    def _can_edit(self, readonly):
        """Les onglets perso sont toujours modifiables ; les onglets
        studio uniquement quand le manager a été lancé en mode admin.
        C'est ce qui garde la librairie officielle intouchable pour les
        animateurs."""
        return (not readonly) or is_studio_admin()

    def _tab_menu(self, position):
        tab_bar = self.tabs.tabBar()
        index = tab_bar.tabAt(position)
        if index < 0:
            return
        widget = self.tabs.widget(index)
        readonly = getattr(widget, 'readonly', False)
        name = self._tab_name(index)
        target = self._category_target(readonly)
        menu = QtWidgets.QMenu(self)

        if self._can_edit(readonly):
            new_label = ('New studio category…' if readonly
                         else 'New category…')
            new = menu.addAction(
                new_label, lambda: self._prompt_category(readonly))
            new.setEnabled(target is not None)

            rename = menu.addAction(
                'Rename category…', lambda: self._prompt_rename(target, name))
            rename.setEnabled(target is not None)

            delete = menu.addAction(
                'Delete category "%s"' % name,
                lambda: self._delete_category(target, name))
            empty = widget is not None and widget.count() == 0
            delete.setEnabled(target is not None and empty)
            if not empty:
                delete.setToolTip('Only empty categories can be deleted')
            menu.addSeparator()

        menu.addAction(
            'Open library folder',
            lambda: self._open_library_folder(readonly))
        menu.exec_(tab_bar.mapToGlobal(position))

    def _open_library_folder(self, readonly):
        if readonly:
            target = studio_library_path() or studio_location()
        else:
            target = self.path
        if not open_folder(target):
            QtWidgets.QMessageBox.warning(
                self, 'Library folder',
                'Could not open the folder (not found or not configured).')

    def current_selected_entries(self):
        """Boutons sélectionnés dans l'onglet courant de la shelf (pour
        « Replace with library button » dans l'éditeur)."""
        widget = self.tabs.currentWidget()
        if widget is None:
            return []
        return widget.selected_entries()

    def current_category(self):
        # une sauvegarde va toujours dans la librairie PERSO : si
        # l'onglet courant est studio (lecture seule), on retombe sur
        # General
        widget = self.tabs.currentWidget()
        if widget is None or getattr(widget, 'readonly', False):
            return DEFAULT_CATEGORY
        return self.tabs.tabText(self.tabs.currentIndex()) or DEFAULT_CATEGORY

    def _menu(self, shelf_list, position):
        menu = QtWidgets.QMenu(self)
        entries = shelf_list.selected_entries()
        # renommer / ranger : perso toujours, studio seulement en admin
        if entries and self._can_edit(shelf_list.readonly):
            target = self._category_target(shelf_list.readonly)
            if len(entries) == 1:
                rename = menu.addAction(
                    'Rename…',
                    lambda: self._prompt_rename_entry(target, entries[0]))
                rename.setEnabled(target is not None)
            move = menu.addAction(
                'Move to category…',
                lambda: self._prompt_move(target, entries))
            move.setEnabled(target is not None)
            menu.addSeparator()
        # actions sur les boutons perso sélectionnés
        if entries and not shelf_list.readonly:
            count = len(entries)
            # publier vers la librairie officielle : admin seulement
            if is_studio_admin() and studio_write_path() is not None:
                send_label = (
                    'Send "%s" to studio library' % entries[0]['name']
                    if count == 1
                    else 'Send %d buttons to studio library' % count)
                menu.addAction(
                    self.studio_icon, send_label,
                    lambda: self._send_to_studio(entries))
            del_label = ('Delete "%s"' % entries[0]['name']
                         if count == 1 else 'Delete %d buttons' % count)
            menu.addAction(del_label, lambda: self._delete(entries))
            menu.addSeparator()
        # toujours disponible : ouvrir le dossier de la librairie
        menu.addAction(
            'Open library folder',
            lambda: self._open_library_folder(shelf_list.readonly))
        menu.exec_(shelf_list.mapToGlobal(position))

    def _send_to_studio(self, entries):
        added = export_to_studio(entries)
        if added < 0:
            QtWidgets.QMessageBox.warning(
                self, 'Studio library',
                'Studio library is not configured or not writable.\n'
                'Set the HOTBOX_STUDIO_LIBRARY location first.')
            return
        refresh_shelves()
        QtWidgets.QMessageBox.information(
            self, 'Studio library',
            '%d button(s) sent to the studio library.' % added
            if added else 'These buttons are already in the studio library.')

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
