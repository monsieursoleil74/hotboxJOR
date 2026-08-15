"""Librairie de boutons pré-configurés.

Deux niveaux, façon pipeline studio :

- **Perso** : ``button_library.json`` dans le dossier de données
  (préférences Maya ; ``~/.hotboxjor`` en standalone). Modifiable par
  l'artiste.
- **Studio** (optionnel, LECTURE SEULE hors mode admin) : une librairie
  partagée, choisie via l'UI (badge/bouton dossier de la shelf, choix
  persisté) ou désignée par la variable d'environnement
  ``HOTBOX_STUDIO_LIBRARY`` (un fichier .json OU un dossier contenant
  ``button_library.json``). AUCUNE librairie par défaut : au premier
  lancement il n'y en a pas, on en crée/ouvre une explicitement. Les
  onglets studio portent le **logo du studio** en icône
  (``studio_logo.png``/``logo.png`` posé à côté de la librairie, ou
  variable ``HOTBOX_STUDIO_LOGO`` ; sinon un logo par défaut).

Un même bouton se glisse-dépose depuis n'importe quel onglet vers une
hotbox.
"""
import json
import os
import shutil
import subprocess
import sys

from hotbox_designer.vendor.Qt import QtWidgets, QtCore, QtGui
from hotbox_designer.interactive import Shape
from hotbox_designer.painting import draw_shape
from hotbox_designer.qtutils import icon

LIBRARY_FILENAME = 'button_library.json'
BUTTONS_MIME = 'application/x-hotbox-designer-buttons'
# payload complet d'un drag de shelf (déplacement/réordonnancement) :
# {'entries': [...], 'readonly': bool, 'category': str}
SHELF_ENTRIES_MIME = 'application/x-hotbox-designer-shelf-entries'
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


# emplacement de librairie studio choisi via l'UI (menu du bouton TAT
# de la shelf, mode admin) : prioritaire sur la variable d'environnement
# — permet de SWITCHER de librairie selon le projet, sans redémarrer.
# Persisté dans studio_settings.json du dossier du fork.
_STUDIO_OVERRIDE = None
STUDIO_SETTINGS_FILENAME = 'studio_settings.json'


def set_studio_location(path):
    """Fixe (ou efface avec None) l'emplacement de librairie studio de
    la session ; prend le pas sur HOTBOX_STUDIO_LIBRARY."""
    global _STUDIO_OVERRIDE
    _STUDIO_OVERRIDE = path or None


def get_studio_override():
    return _STUDIO_OVERRIDE


def studio_settings_path(application):
    return os.path.join(
        application.get_fork_folder(), STUDIO_SETTINGS_FILENAME)


def load_studio_settings(application):
    """{'current': chemin ou None, 'recent': [chemins]} — vide sinon."""
    path = studio_settings_path(application)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except (ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_studio_settings(application, settings):
    from hotbox_designer.data import atomic_write_json
    try:
        atomic_write_json(studio_settings_path(application), settings)
    except OSError:
        pass


def library_path(application):
    """Librairie perso : dans le dossier du fork (`prefs/hotboxJOR/`
    sous Maya). Un fichier resté à la racine des prefs (versions
    antérieures) est déplacé une fois pour toutes."""
    from hotbox_designer.applications import migrate_legacy_file
    path = os.path.join(application.get_fork_folder(), LIBRARY_FILENAME)
    migrate_legacy_file(
        os.path.join(application.get_data_folder(), LIBRARY_FILENAME), path)
    return path


def studio_location():
    # AUCUN défaut : sans choix via l'UI ni variable d'environnement,
    # il n'y a tout simplement pas de librairie studio
    location = _STUDIO_OVERRIDE or os.environ.get(STUDIO_ENV_VARIABLE)
    if not location:
        return None
    return os.path.expandvars(os.path.expanduser(location))


def library_location_exists(path):
    """Vrai si cet emplacement de librairie pointe encore sur un fichier
    réel (.json direct, ou dossier contenant button_library.json)."""
    if not path:
        return False
    if path.lower().endswith('.json'):
        return os.path.exists(path)
    return os.path.exists(os.path.join(path, LIBRARY_FILENAME))


def studio_library_label():
    """Nom de la librairie courante pour le badge de la shelf —
    sans l'extension (« ringo », pas « ringo.json »)."""
    location = studio_location()
    if not location:
        return '(no library)'
    if location.lower().endswith('.json'):
        return os.path.splitext(os.path.basename(location))[0]
    return os.path.splitext(LIBRARY_FILENAME)[0]


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
    # librairie perso ou OFFICIELLE (partagée réseau) : écriture
    # atomique + 3 backups tournants (.bak/.bak2/.bak3 à côté du json)
    from hotbox_designer.data import atomic_write_json
    atomic_write_json(path, entries, backups=3)


# --- ordre du fichier = ordre affiché -----------------------------------
# L'ordre des catégories (onglets) et des boutons dans une catégorie est
# celui du fichier — plus d'alphabétique imposé. Les fonctions ci-dessous
# reconstruisent le fichier sous forme canonique : pour chaque catégorie,
# son marqueur puis ses boutons, dans l'ordre voulu.

def parse_library_structure(path):
    """(ordre_des_categories, {categorie: [boutons]}) — ordre de
    première apparition dans le fichier (marqueur ou bouton)."""
    order, by_category = [], {}
    for entry in load_library_raw(path):
        if CATEGORY_KEY in entry:
            category = entry[CATEGORY_KEY]
            if category not in by_category:
                order.append(category)
                by_category[category] = []
        elif 'options' in entry:
            category = entry.get('category') or DEFAULT_CATEGORY
            if category not in by_category:
                order.append(category)
                by_category[category] = []
            by_category[category].append(entry)
    return order, by_category


def save_library_structure(path, order, by_category):
    raw = []
    for category in order:
        raw.append({CATEGORY_KEY: category})
        raw.extend(by_category.get(category) or [])
    save_library(path, raw)


def set_category_order(path, ordered_names):
    """Réordonne les catégories (drag des onglets). Les noms inconnus
    sont ignorés, les catégories omises gardent leur place à la fin."""
    order, by_category = parse_library_structure(path)
    known = [c for c in ordered_names if c in by_category]
    rest = [c for c in order if c not in known]
    save_library_structure(path, known + rest, by_category)


def move_entries_to_category(path, entries, category, index=None):
    """Déplace (et/ou réordonne) des boutons vers `category`, insérés à
    la position `index` parmi les boutons restants (None = à la fin).
    Sert au drag & drop entre catégories ET au réordonnancement dans une
    même catégorie. Retourne le nombre de boutons déplacés."""
    order, by_category = parse_library_structure(path)
    moved = []
    for name in list(by_category):
        kept = []
        for entry in by_category[name]:
            (moved if entry in entries else kept).append(entry)
        by_category[name] = kept
    if not moved:
        return 0
    if category not in by_category:
        by_category[category] = []
        order.append(category)
    updated = []
    for entry in moved:
        entry = dict(entry)
        entry['category'] = category
        updated.append(entry)
    target = by_category[category]
    if index is None or index > len(target):
        index = len(target)
    by_category[category] = target[:index] + updated + target[index:]
    save_library_structure(path, order, by_category)
    return len(updated)


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
    # même pixmap à l'état sélectionné : sans ça Qt teinte l'icône en
    # bleu système, moche sur le cadre accent de la sélection
    icon.addPixmap(pixmap, QtGui.QIcon.Selected)
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

        # la destination est FIXÉE par le mode : admin → la librairie
        # studio courante, uniquement ; sinon → perso, uniquement.
        # (Pas de choix à faire — la ligne Library sert de repère.)
        self.destination = QtWidgets.QComboBox()
        if studio_available:
            logo = studio_logo_path()
            label = studio_library_label()
            if logo:
                self.destination.addItem(
                    QtGui.QIcon(logo), label, 'studio')
            else:
                self.destination.addItem(label, 'studio')
        else:
            self.destination.addItem('Perso', 'perso')
        self.destination.currentIndexChanged.connect(self._update_categories)

        self.category = QtWidgets.QComboBox()
        self.category.setEditable(True)

        # assez large pour lire les noms de catégories en entier et
        # repérer le menu déroulant (avant : « ANIMATION » → « ATION »)
        self.setMinimumWidth(340)
        self.name.setMinimumWidth(220)
        self.destination.setMinimumWidth(220)
        self.category.setMinimumWidth(220)

        layout = QtWidgets.QFormLayout(self)
        layout.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
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
        # on ne garde le texte courant que s'il existe dans la NOUVELLE
        # liste — sinon on montre sa première catégorie (avant, basculer
        # sur Studio laissait « General » de la perso dans le champ)
        if keep and keep in categories:
            self.category.setCurrentText(keep)
        else:
            self.category.setCurrentIndex(0)


class ShelfList(QtWidgets.QListWidget):
    """Rangée de boutons d'une catégorie, source du drag & drop."""

    def __init__(self, parent=None):
        super(ShelfList, self).__init__(parent)
        self.readonly = False  # True pour les onglets studio
        self.shelf = None      # LibraryShelf propriétaire
        self.category = None   # catégorie de l'onglet
        self.setAcceptDrops(True)
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
        # états visuels francs : cadre accent + fond teinté sur TOUTE la
        # vignette (icône comprise) — le simple surlignage du texte ne se
        # voyait pas
        from hotbox_designer.theme import ACCENT
        color = QtGui.QColor(ACCENT)
        r, g, b = color.red(), color.green(), color.blue()
        # le style peint aussi un voile « Highlight » (bleu système) sur
        # l'icône sélectionnée : on aligne la palette sur l'accent
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Highlight, color)
        palette.setColor(
            QtGui.QPalette.HighlightedText, QtGui.QColor('white'))
        self.setPalette(palette)
        self.setStyleSheet("""
            QListWidget::item {
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 2px;
            }
            QListWidget::item:hover {
                background: rgba(%(r)d, %(g)d, %(b)d, 50);
                border: 2px solid rgba(%(r)d, %(g)d, %(b)d, 120);
            }
            QListWidget::item:selected {
                background: rgba(%(r)d, %(g)d, %(b)d, 110);
                border: 2px solid %(accent)s;
                color: white;
            }
        """ % {'r': r, 'g': g, 'b': b, 'accent': ACCENT})

    def selected_entries(self):
        return [
            item.data(QtCore.Qt.UserRole)
            for item in self.selectedItems()
            if item.data(QtCore.Qt.UserRole)]

    def _drop_payload(self, event):
        """Payload d'un drag de shelf accepté ici : même librairie
        (perso↔perso, studio↔studio) et cible modifiable."""
        data = event.mimeData().data(SHELF_ENTRIES_MIME)
        if not data or self.shelf is None:
            return None
        try:
            payload = json.loads(bytes(data).decode('utf-8'))
        except ValueError:
            return None
        if payload.get('readonly') != self.readonly:
            return None
        if not self.shelf._can_edit(self.readonly):
            return None
        return payload

    def dragEnterEvent(self, event):
        if self._drop_payload(event) is not None:
            return event.acceptProposedAction()
        super(ShelfList, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self._drop_payload(event) is not None:
            return event.acceptProposedAction()
        super(ShelfList, self).dragMoveEvent(event)

    def dropEvent(self, event):
        payload = self._drop_payload(event)
        if payload is None:
            return super(ShelfList, self).dropEvent(event)
        position = getattr(event, 'position', None)
        point = (position().toPoint() if position
                 else event.pos())
        row = self.indexAt(point).row()
        entries = payload['entries']
        if row < 0:
            index = None  # à la fin
        else:
            # position parmi les boutons NON déplacés (les déplacés
            # sont d'abord retirés par move_entries_to_category)
            index = 0
            for i in range(row):
                item = self.item(i)
                if item.data(QtCore.Qt.UserRole) not in entries:
                    index += 1
        path = self.shelf._category_target(self.readonly)
        if path and move_entries_to_category(
                path, entries, self.category, index):
            refresh_shelves()
        event.acceptProposedAction()

    def startDrag(self, actions):
        entries = self.selected_entries()
        if not entries:
            return
        mime = QtCore.QMimeData()
        payload = json.dumps(
            [entry['options'] for entry in entries]).encode('utf-8')
        mime.setData(BUTTONS_MIME, QtCore.QByteArray(payload))
        # payload complet : permet le dépôt sur un onglet (changement de
        # catégorie) ou dans une liste (réordonnancement)
        full = json.dumps({
            'entries': entries, 'readonly': self.readonly,
            'category': self.category}).encode('utf-8')
        mime.setData(SHELF_ENTRIES_MIME, QtCore.QByteArray(full))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        pixmap = self.selectedItems()[0].icon().pixmap(
            SHELF_THUMB_WIDTH, SHELF_THUMB_HEIGHT)
        if not pixmap.isNull():
            drag.setPixmap(pixmap)
        drag.exec_(QtCore.Qt.CopyAction)


class CategoryPalette(QtWidgets.QWidget):
    """Palette flottante d'une catégorie (double-clic sur son onglet) :
    grille de boutons avec retour à la ligne, TOUJOURS AU-DESSUS, qui
    reste ouverte tant qu'on ne la ferme pas — pratique pour piocher
    dans une grosse catégorie sans scroller la shelf. Les drags (vers
    une hotbox, un onglet, une liste) marchent comme depuis la shelf."""

    def __init__(self, shelf, category, readonly):
        super(CategoryPalette, self).__init__(
            shelf.window(),
            QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint)
        from hotbox_designer.theme import apply_dark_theme
        apply_dark_theme(self)
        self.shelf = shelf
        self.category = category
        self.readonly = readonly
        self.setWindowTitle(category)
        self.list = ShelfList()
        shelf._configure_list(self.list, category, readonly)
        # grille multi-lignes (la shelf, elle, reste une rangée)
        self.list.setWrapping(True)
        self.list.setResizeMode(QtWidgets.QListView.Adjust)
        self.list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.list.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.list)
        self.resize(4 * (SHELF_THUMB_WIDTH + 22) + 20, 320)

    def closeEvent(self, event):
        if self in self.shelf._palettes:
            self.shelf._palettes.remove(self)
        super(CategoryPalette, self).closeEvent(event)


class _ShelfTabBar(QtWidgets.QTabBar):
    """Barre d'onglets de la shelf : accepte le dépôt d'un bouton sur un
    onglet (= le ranger dans cette catégorie), sélectionne l'onglet
    survolé pendant le drag."""

    def __init__(self, tabs):
        super(_ShelfTabBar, self).__init__(tabs)
        self._tabs = tabs
        self.setAcceptDrops(True)

    def _payload(self, event, index):
        if index < 0:
            return None
        shelf = self._tabs.shelf
        widget = self._tabs.widget(index)
        if shelf is None or widget is None:
            return None
        data = event.mimeData().data(SHELF_ENTRIES_MIME)
        if not data:
            return None
        try:
            payload = json.loads(bytes(data).decode('utf-8'))
        except ValueError:
            return None
        readonly = getattr(widget, 'readonly', False)
        if payload.get('readonly') != readonly:
            return None
        if not shelf._can_edit(readonly):
            return None
        return payload

    def mouseDoubleClickEvent(self, event):
        position = getattr(event, 'position', None)
        point = position().toPoint() if position else event.pos()
        index = self.tabAt(point)
        if index >= 0 and self._tabs.shelf is not None:
            return self._tabs.shelf.open_category_palette(index)
        super(_ShelfTabBar, self).mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(SHELF_ENTRIES_MIME):
            return event.acceptProposedAction()
        super(_ShelfTabBar, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        position = getattr(event, 'position', None)
        point = position().toPoint() if position else event.pos()
        index = self.tabAt(point)
        if index >= 0:
            self._tabs.setCurrentIndex(index)  # survol = on voit où on va
        if event.mimeData().hasFormat(SHELF_ENTRIES_MIME):
            return event.acceptProposedAction()
        super(_ShelfTabBar, self).dragMoveEvent(event)

    def dropEvent(self, event):
        position = getattr(event, 'position', None)
        point = position().toPoint() if position else event.pos()
        index = self.tabAt(point)
        payload = self._payload(event, index)
        if payload is None:
            return super(_ShelfTabBar, self).dropEvent(event)
        shelf = self._tabs.shelf
        widget = self._tabs.widget(index)
        category = shelf._tab_name(index)
        path = shelf._category_target(getattr(widget, 'readonly', False))
        if path and category != payload.get('category'):
            if move_entries_to_category(path, payload['entries'], category):
                refresh_shelves()
        event.acceptProposedAction()


class _ShelfTabs(QtWidgets.QTabWidget):
    """QTabWidget de la shelf avec sa barre d'onglets à drops."""

    def __init__(self, shelf):
        super(_ShelfTabs, self).__init__()
        self.shelf = shelf
        self.setTabBar(_ShelfTabBar(self))


class LibraryShelf(QtWidgets.QWidget):
    """Librairie intégrée en bas de l'éditeur, façon shelf Maya :
    un onglet par catégorie, les boutons se glissent-déposent vers la
    hotbox juste au-dessus. Clic droit sur un bouton : supprimer.
    « ＋ » : créer une catégorie ; clic droit sur un onglet vide : la
    supprimer."""

    def __init__(self, application, parent=None):
        super(LibraryShelf, self).__init__(parent)
        self.application = application
        self.path = library_path(application)
        # librairie studio mémorisée (choisie via le bouton TAT) :
        # appliquée avant le premier refresh
        current = load_studio_settings(application).get('current')
        if current:
            set_studio_location(current)
        logo = studio_logo_path()
        self.studio_icon = QtGui.QIcon(logo) if logo else QtGui.QIcon()
        self.tabs = _ShelfTabs(self)
        self.tabs.setDocumentMode(True)
        self.tabs.setIconSize(QtCore.QSize(20, 16))
        # réordonner les onglets au drag (admin) — persisté au lâcher
        self._rebuilding_tabs = False
        self.tabs.tabBar().tabMoved.connect(self._on_tab_moved)
        # palettes flottantes ouvertes (double-clic sur un onglet)
        self._palettes = []
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('＋')
        # ＋ suit le mode : admin → catégorie DANS la librairie studio
        # courante (onglet logo TAT) ; animateur — ou admin SANS
        # librairie chargée — → catégorie perso, façon shelf Maya
        self.add_button.released.connect(lambda: self._prompt_category(
            is_studio_admin() and studio_location() is not None))
        # deux boutons bien distincts : CRÉER une librairie (admin
        # seulement) et OUVRIR/charger une librairie existante
        self.create_library_button = QtWidgets.QToolButton()
        self.create_library_button.setIcon(icon('new.png'))
        self.create_library_button.setToolTip(
            'Create a new studio library (.json)')
        self.create_library_button.released.connect(
            self._create_studio_library)
        self.create_library_button.setVisible(is_studio_admin())
        self.open_library_button = QtWidgets.QToolButton()
        self.open_library_button.setIcon(icon('open.png'))
        self.open_library_button.setToolTip(
            'Open an existing studio library')
        self.open_library_button.released.connect(
            self._open_studio_library)
        # le badge-BOUTON : le nom du json courant EST le sélecteur —
        # on voit son environnement, on clique dessus pour switcher
        # (vert = mode admin, gris = lecture seule)
        self.library_badge = QtWidgets.QPushButton()
        self.library_badge.setCursor(QtCore.Qt.PointingHandCursor)
        self.library_badge.setFlat(True)
        self.library_badge.released.connect(self._studio_library_menu)
        corner = QtWidgets.QWidget()
        corner_layout = QtWidgets.QHBoxLayout(corner)
        corner_layout.setContentsMargins(0, 0, 4, 0)
        corner_layout.setSpacing(6)
        corner_layout.addWidget(self.library_badge)
        corner_layout.addWidget(self.create_library_button)
        corner_layout.addWidget(self.open_library_button)
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

    def _update_library_badge(self):
        """Badge-bouton = nom du json courant, toujours vert : c'est le
        repère d'environnement (la librairie), pas un indicateur de
        rôle. Clic = menu de switch. Infobulle = chemin complet + rôle."""
        from hotbox_designer.theme import ACCENT
        location = studio_location()
        self.library_badge.setVisible(bool(location))
        self.library_badge.setText(studio_library_label())
        self.library_badge.setStyleSheet(
            'QPushButton {color: white; background: %s; border: none;'
            'border-radius: 3px; font-weight: bold; font-size: 10px;'
            'padding: 2px 8px;}'
            'QPushButton:hover {background: #86a878;}' % ACCENT)
        self.library_badge.setToolTip(
            '%s — %s\nClick to switch library' % (
                location or 'no library',
                'admin (editable)' if is_studio_admin() else 'read-only'))

    def refresh(self):
        self._rebuilding_tabs = True
        try:
            self._refresh()
        finally:
            self._rebuilding_tabs = False

    def _refresh(self):
        current = self._current_key()
        # le mode admin et la librairie peuvent changer EN COURS DE
        # SESSION : badge, boutons et logo suivent (le logo peut
        # différer par projet)
        self._update_library_badge()
        self.create_library_button.setVisible(is_studio_admin())
        if is_studio_admin() and studio_location():
            self.add_button.setToolTip(
                'Create a category in %s' % studio_library_label())
        else:
            self.add_button.setToolTip('Create a personal category')
        logo = studio_logo_path()
        self.studio_icon = QtGui.QIcon(logo) if logo else QtGui.QIcon()
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
        self.tabs.tabBar().setMovable(is_studio_admin())
        for category in studio:  # ordre du FICHIER, plus d'alphabétique
            self._add_tab(category, studio[category], current, readonly=True)
        # librairie toute neuve (aucune catégorie) en admin : un onglet
        # « General » vide garde la shelf vivante — sans AUCUN onglet,
        # Qt cache aussi le coin (badge / dossier / ＋) et tout semble
        # avoir disparu
        if is_studio_admin() and not studio and studio_location():
            self._add_tab(DEFAULT_CATEGORY, [], current, readonly=True)

        # 2) onglets perso (modifiables) — CACHÉS en mode admin : on y
        # gère l'OFFICIEL, le perso appartient au mode animateur (c'est
        # lui qui faisait apparaître un « General » sans logo)
        if not is_studio_admin():
            by_category = {
                category: []
                for category in load_extra_categories(self.path)}
            for entry in load_library(self.path):
                category = entry.get('category') or DEFAULT_CATEGORY
                by_category.setdefault(category, []).append(entry)
            if not by_category and not studio:
                by_category = {DEFAULT_CATEGORY: []}
            for category in by_category:  # ordre du fichier
                self._add_tab(category, by_category[category], current)
        # les palettes flottantes ouvertes suivent le contenu
        self._sync_palettes()
        # surveiller le json courant : publication du lead → les
        # shelves des animateurs se rafraîchissent toutes seules
        watch_studio_library()

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

    def _configure_list(self, shelf_list, category, readonly):
        """Câblage commun aux listes (onglets ET palettes) : gating,
        menu contextuel, drag & drop."""
        shelf_list.readonly = readonly
        shelf_list.shelf = self
        shelf_list.category = category
        shelf_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        shelf_list.customContextMenuRequested.connect(
            lambda pos, lst=shelf_list: self._menu(lst, pos))

    def _fill_list(self, shelf_list, entries):
        """(Re)remplit une liste avec les boutons, dans l'ordre du
        fichier."""
        shelf_list.clear()
        suffix = ''
        if shelf_list.readonly:
            suffix = (' (studio, admin)' if is_studio_admin()
                      else ' (studio, read-only)')
        for entry in entries:  # ordre du fichier (réordonnable au drag)
            item = QtWidgets.QListWidgetItem(entry.get('name') or 'button')
            item.setIcon(button_thumbnail(
                entry['options'], (SHELF_THUMB_WIDTH, SHELF_THUMB_HEIGHT)))
            item.setData(QtCore.Qt.UserRole, entry)
            item.setToolTip(
                '%s — drag & drop into the hotbox%s' % (
                    entry.get('name') or 'button', suffix))
            shelf_list.addItem(item)

    def _add_tab(self, category, entries, current, readonly=False):
        shelf_list = ShelfList()
        self._configure_list(shelf_list, category, readonly)
        if not readonly and not entries:
            shelf_list.setToolTip(
                'Empty category — select shapes and use the save '
                'button of the toolbar to fill it')
        self._fill_list(shelf_list, entries)
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

    # --- choix de la librairie studio ---------------------------------
    def _studio_library_menu(self):
        """Bouton TAT : UNIQUEMENT la liste des librairies (récentes +
        courante), la cochée est celle en cours. Rien d'autre."""
        menu = QtWidgets.QMenu(self)
        location = studio_location()
        normalized = os.path.normpath(location) if location else ''
        entries = list(
            load_studio_settings(self.application).get('recent') or [])
        # l'emplacement courant (ex. défaut/variable d'env) est toujours
        # proposé, même s'il n'a jamais été choisi via l'UI
        if location and all(
                os.path.normpath(p) != normalized for p in entries):
            entries.insert(0, location)
        if not entries:
            empty = menu.addAction('No library — use the folder button')
            empty.setEnabled(False)

        def display(path):
            name = os.path.basename(path.rstrip('\\/'))
            if name.lower().endswith('.json'):
                name = os.path.splitext(name)[0]
            return name

        for path in entries:
            exists = library_location_exists(path)
            is_current = os.path.normpath(path) == normalized
            label = display(path)
            if not exists:
                label += '  (missing)'
            action = menu.addAction(
                label, lambda p=path: self._switch_studio_library(p))
            action.setToolTip(path)
            action.setCheckable(True)
            action.setChecked(is_current)
            action.setEnabled(exists and not is_current)
        # faire le ménage : oublier une librairie obsolète (la courante
        # n'est pas proposée — on est dessus)
        others = [
            p for p in entries if os.path.normpath(p) != normalized]
        if others:
            menu.addSeparator()
            remove_menu = menu.addMenu('Remove from list')
            for path in others:
                remove_menu.addAction(
                    display(path),
                    lambda p=path: self._forget_studio_library(p))
        menu.exec_(QtGui.QCursor.pos())

    def _forget_studio_library(self, path):
        """Retire une librairie de la liste des récents (le fichier
        lui-même n'est évidemment pas touché)."""
        settings = load_studio_settings(self.application)
        normalized = os.path.normpath(path)
        settings['recent'] = [
            p for p in settings.get('recent') or []
            if os.path.normpath(p) != normalized]
        save_studio_settings(self.application, settings)

    def _library_dialog_start(self):
        start = studio_location() or ''
        if start.lower().endswith('.json'):
            start = os.path.dirname(start)
        return start

    def _create_studio_library(self):
        """Bouton « new » (admin) : créer une librairie — dialogue
        Enregistrer sous, nom du .json libre. Choisir un fichier
        existant l'ouvre simplement (jamais écrasé)."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Create a studio library',
            os.path.join(self._library_dialog_start(), LIBRARY_FILENAME),
            'Library (*.json)',
            options=QtWidgets.QFileDialog.DontConfirmOverwrite)
        if path:
            self._open_studio_json(path)

    def _open_studio_library(self):
        """Bouton dossier : charger une librairie EXISTANTE."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open a studio library',
            self._library_dialog_start(), 'Library (*.json)')
        if path:
            self._open_studio_json(path)

    def _open_studio_json(self, path):
        """Bascule sur ce fichier de librairie ; s'il n'existe pas,
        l'admin le crée (et le logo courant est COPIÉ à côté, pour ne
        pas perdre l'identité TAT), l'animateur est prévenu. Retourne
        True si la bascule a eu lieu."""
        if not path.lower().endswith('.json'):
            path += '.json'
        if not os.path.exists(path):
            if not is_studio_admin():
                QtWidgets.QMessageBox.warning(
                    self, 'Studio library',
                    'This library does not exist:\n%s' % path)
                return False
            current_logo = studio_logo_path()
            try:
                save_library(path, [])
            except OSError:
                QtWidgets.QMessageBox.warning(
                    self, 'Studio library',
                    'Could not create %s (folder not writable).' % path)
                return False
            # la nouvelle librairie hérite du logo courant
            if current_logo:
                destination = os.path.join(
                    os.path.dirname(path) or '.', STUDIO_LOGO_NAMES[0])
                if not os.path.exists(destination):
                    try:
                        shutil.copy(current_logo, destination)
                    except OSError:
                        pass
        self._switch_studio_library(path)
        return True

    def _switch_studio_library(self, folder):
        """Bascule la session sur cette librairie et mémorise le choix.
        La librairie QUITTÉE entre aussi dans les récents — sinon la
        toute première (venue du défaut/variable d'env, jamais choisie
        via l'UI) disparaissait de la liste après un switch."""
        previous = studio_location()
        set_studio_location(folder)
        settings = load_studio_settings(self.application)
        settings['current'] = folder
        recent, seen = [], set()
        for candidate in [folder, previous] + (settings.get('recent') or []):
            if not candidate:
                continue
            normalized = os.path.normpath(candidate)
            if normalized in seen:
                continue
            seen.add(normalized)
            recent.append(candidate)
        settings['recent'] = recent[:8]
        save_studio_settings(self.application, settings)
        refresh_shelves()

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

    def open_category_palette(self, index):
        """Double-clic sur un onglet : ouvre (ou ramène devant) la
        palette flottante de cette catégorie."""
        widget = self.tabs.widget(index)
        if widget is None:
            return
        category = self._tab_name(index)
        readonly = getattr(widget, 'readonly', False)
        for palette in self._palettes:
            if (palette.category == category
                    and palette.readonly == readonly):
                palette.show()
                palette.raise_()
                return palette
        palette = CategoryPalette(self, category, readonly)
        entries = [widget.item(i).data(QtCore.Qt.UserRole)
                   for i in range(widget.count())]
        self._fill_list(palette.list, entries)
        self._palettes.append(palette)
        palette.show()
        return palette

    def _sync_palettes(self):
        """Après un refresh : recharge les palettes ouvertes ; ferme
        celles dont la catégorie a disparu (ou librairie switchée)."""
        for palette in list(self._palettes):
            match = None
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                if (self._tab_name(i) == palette.category
                        and getattr(widget, 'readonly', False)
                        == palette.readonly):
                    match = widget
                    break
            if match is None:
                palette.close()
                continue
            entries = [match.item(i).data(QtCore.Qt.UserRole)
                       for i in range(match.count())]
            self._fill_list(palette.list, entries)

    def _on_tab_moved(self, *_):
        """Drag d'un onglet (admin) : persiste le nouvel ordre des
        catégories dans le json de la librairie courante."""
        if self._rebuilding_tabs or not is_studio_admin():
            return
        path = studio_write_path()
        if not path:
            return
        names = [self._tab_name(i) for i in range(self.tabs.count())]
        set_category_order(path, names)
        # les autres shelves se resynchronisent ; pas la nôtre (le drag
        # est en cours, la reconstruire casserait le geste)
        for shelf in list(_shelves):
            if shelf is not self:
                try:
                    shelf.refresh()
                except RuntimeError:
                    pass

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

        # ouvrir le dossier : perso toujours ; studio en mode admin
        # seulement (le fichier du lead ne regarde pas l'animateur)
        if self._can_edit(readonly):
            menu.addAction(
                'Open library folder',
                lambda: self._open_library_folder(readonly))
        if not menu.isEmpty():
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
        """Catégorie proposée par défaut à la sauvegarde : l'ONGLET
        COURANT, s'il correspond à la destination du mode (studio en
        admin, perso sinon) — on enregistre là où on est, sans
        re-choisir à chaque fois."""
        widget = self.tabs.currentWidget()
        if widget is None:
            return DEFAULT_CATEGORY
        readonly = getattr(widget, 'readonly', False)
        if readonly == is_studio_admin():
            return self._tab_name(
                self.tabs.currentIndex()) or DEFAULT_CATEGORY
        return DEFAULT_CATEGORY

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
        # ouvrir le dossier : perso toujours ; studio en mode admin
        # seulement
        if self._can_edit(shelf_list.readonly):
            menu.addAction(
                'Open library folder',
                lambda: self._open_library_folder(shelf_list.readonly))
        if not menu.isEmpty():
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


# --- rafraîchissement AUTOMATIQUE de la librairie studio ----------------
# Le lead publie un bouton → les shelves des animateurs se mettent à
# jour toutes seules : un QFileSystemWatcher surveille le json studio
# courant. Débouncé (les éditeurs/os.replace émettent plusieurs
# événements), et re-armé après chaque événement car un remplacement
# atomique fait souvent « perdre » le fichier au watcher.

_watcher = None
_watch_timer = None


def watch_studio_library():
    """(Re)pointe la surveillance sur le fichier de librairie courant
    (ou plus rien s'il n'y a pas de librairie)."""
    global _watcher
    if QtWidgets.QApplication.instance() is None:
        return
    if _watcher is None:
        _watcher = QtCore.QFileSystemWatcher()
        _watcher.fileChanged.connect(_on_library_file_changed)
    files = _watcher.files()
    if files:
        _watcher.removePaths(files)
    path = studio_library_path()
    if path:
        _watcher.addPath(path)


def _on_library_file_changed(_):
    global _watch_timer
    if _watch_timer is None:
        _watch_timer = QtCore.QTimer()
        _watch_timer.setSingleShot(True)
        _watch_timer.setInterval(300)
        _watch_timer.timeout.connect(_reload_after_change)
    _watch_timer.start()  # débounce : repart à chaque événement


def _reload_after_change():
    watch_studio_library()  # re-armer (os.replace décroche le watcher)
    refresh_shelves()
