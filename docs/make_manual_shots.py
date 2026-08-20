"""Captures d'écran du manuel — générateur reproductible.

Construit un faux projet (librairies perso + studio, hotboxes, logo),
ouvre chaque fenêtre de l'outil HORS ÉCRAN et l'enregistre en PNG, puis
**incruste les images dans `MANUEL.html`** sous forme de data URI : le
wiki reste UN SEUL FICHIER autonome, qu'on peut envoyer tel quel.

Usage (depuis la racine du dépôt) :

    QT_QPA_PLATFORM=offscreen python docs/make_manual_shots.py

À relancer quand l'interface change — les captures du manuel suivent.
Les PNG intermédiaires vont dans un dossier temporaire ; seul
`MANUEL.html` est modifié.
"""
import base64
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from hotbox_designer.vendor.Qt import QtWidgets, QtCore, QtGui  # noqa: E402

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from hotbox_designer import buttonlibrary as bl              # noqa: E402
from hotbox_designer.applications import Standalone          # noqa: E402
from hotbox_designer.designer.application import HotboxEditor  # noqa: E402
from hotbox_designer.templates import (                      # noqa: E402
    SQUARE_BUTTON, TEXT, HOTBOX)
from hotbox_designer.theme import ACCENT                     # noqa: E402

MANUAL = os.path.join(ROOT, 'MANUEL.html')
BEGIN = '/* == CAPTURES : bloc généré par docs/make_manual_shots.py == */'
END = '/* == /CAPTURES == */'

shots = {}  # nom -> (largeur, hauteur, png bytes)


# ---------------------------------------------------------------- outils

def flush():
    for _ in range(5):
        APP.processEvents()


def grab(widget, name, dark_background=False, keep_it=True):
    """Enregistre le rendu d'un widget. `dark_background` compose la
    capture sur un fond sombre (le reader est translucide) ;
    `keep_it=False` rend la capture SANS l'incruster (utile pour une
    image qui ne sert que de base à une version annotée)."""
    flush()
    pixmap = widget.grab()
    if dark_background:
        canvas = QtGui.QPixmap(pixmap.size())
        canvas.fill(QtGui.QColor('#232623'))
        painter = QtGui.QPainter(canvas)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        pixmap = canvas
    if keep_it:
        keep(pixmap, name)
    return pixmap


def keep(pixmap, name):
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QIODevice.WriteOnly)
    pixmap.save(buffer, 'PNG')
    shots[name] = (pixmap.width(), pixmap.height(),
                   bytes(buffer.data()))
    print('  %-18s %d×%d  %d ko' % (
        name, pixmap.width(), pixmap.height(), len(shots[name][2]) // 1024))


def annotate(pixmap, marks, name):
    """Repères numérotés (pastilles accent) posés sur une capture ;
    `marks` = [(x, y, '1'), …]. Les numéros renvoient à une légende du
    manuel."""
    out = QtGui.QPixmap(pixmap)
    painter = QtGui.QPainter(out)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    font = QtGui.QFont()
    font.setPixelSize(15)
    font.setBold(True)
    painter.setFont(font)
    radius = 14
    for x, y, label in marks:
        center = QtCore.QPointF(x, y)
        painter.setPen(QtGui.QPen(QtGui.QColor('white'), 2))
        painter.setBrush(QtGui.QColor(ACCENT))
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QtGui.QColor('white'))
        painter.drawText(
            QtCore.QRectF(x - radius, y - radius, radius * 2, radius * 2),
            QtCore.Qt.AlignCenter, label)
    painter.end()
    keep(out, name)


def button(left, top, width, height, label, color, text_size=12):
    """Un bouton crédible : les trois états déclinent la MÊME teinte
    (survol plus clair, clic plus clair encore) — sinon l'aperçu
    d'états et le reader montrent le gris par défaut du template."""
    base = QtGui.QColor(color)
    options = dict(SQUARE_BUTTON)
    options.update({
        'shape.left': float(left), 'shape.top': float(top),
        'shape.width': float(width), 'shape.height': float(height),
        'text.content': label, 'text.size': text_size,
        'bgcolor.normal': color,
        'bgcolor.hovered': base.lighter(125).name(),
        'bgcolor.clicked': base.lighter(155).name()})
    return options


def entry(name, category, options):
    return {'name': name, 'category': category, 'options': options}


def label(left, top, width, content, size=13):
    options = dict(TEXT)
    options.update({
        'shape.left': float(left), 'shape.top': float(top),
        'shape.width': float(width), 'shape.height': 20.0,
        'text.content': content, 'text.size': size,
        'text.color': '#8fb27c', 'text.bold': True,
        # transparency 255 = alpha 0 : pas de rectangle derrière le titre
        'bgcolor.transparency': 255, 'border': False})
    return options


def demo_hotbox(name='TAT_body'):
    """Une hotbox d'animation crédible : trois groupes de boutons
    colorés autour d'un bouton central — c'est elle qu'on montre dans
    le manuel (l'éditeur ET le reader)."""
    shapes = [label(20, 12, 140, 'IK / FK'),
              label(330, 12, 150, 'SÉLECTION')]
    for index, (text, color) in enumerate((
            ('bras L', BLUE), ('bras R', BLUE),
            ('jambe L', PURPLE), ('jambe R', PURPLE))):
        shapes.append(button(20, 40 + index * 38, 140, 30, text, color))
    for index, (text, color) in enumerate((
            ('tout', GREEN), ('corps', GREEN),
            ('visage', BROWN), ('props', BROWN))):
        shapes.append(button(330, 40 + index * 38, 150, 30, text, color))
    shapes.append(button(185, 78, 120, 120, 'MENU', '#4a5f3d', text_size=15))
    for index, (text, color) in enumerate((
            ('key all', RED), ('mirror', BLUE),
            ('reset', BROWN), ('playblast', PURPLE))):
        shapes.append(button(20 + index * 120, 210, 110, 30, text, color))
    return {'general': dict(HOTBOX, name=name, width=500, height=260,
                            centerx=250, centery=130),
            'shapes': shapes}


# ------------------------------------------------------- faux projet

tmp = tempfile.mkdtemp(prefix='lumen-manuel-')
application = Standalone()
application.get_data_folder = staticmethod(lambda: tmp)
application.local_file = os.path.join(tmp, 'hotboxes.json')
application.shared_file = os.path.join(tmp, 'shared_hotboxes.json')

# librairie perso : trois catégories bien remplies + un set
BLUE, PURPLE, GREEN, BROWN, RED = (
    '#5a7a96', '#7a5a96', '#5a967a', '#96755a', '#96605a')
perso = [
    {bl.CATEGORY_KEY: 'BODY'},
    entry('ik fk', 'BODY', button(0, 0, 60, 30, 'ik/fk', BLUE)),
    entry('mirror', 'BODY', button(0, 0, 60, 30, 'mirror', PURPLE)),
    entry('reset', 'BODY', button(0, 0, 60, 30, 'reset', BROWN)),
    entry('snap hand', 'BODY', button(0, 0, 60, 30, 'snap', GREEN)),
    {'name': 'Kit main IK', 'category': 'BODY', 'set': [
        button(0, 0, 60, 26, 'wrist', GREEN),
        button(66, 0, 60, 26, 'palm', BLUE),
        button(0, 30, 60, 26, 'fingers', BROWN),
        button(66, 30, 60, 26, 'thumb', PURPLE)]},
    {bl.CATEGORY_KEY: 'FACE'},
    entry('brows', 'FACE', button(0, 0, 60, 30, 'brows', PURPLE)),
    entry('jaw', 'FACE', button(0, 0, 60, 30, 'jaw', BLUE)),
    {bl.CATEGORY_KEY: 'TOOLS'},
    entry('key all', 'TOOLS', button(0, 0, 60, 30, 'key all', RED)),
    entry('playblast', 'TOOLS', button(0, 0, 70, 30, 'playblast', BROWN)),
]
bl.save_library(bl.library_path(application), perso)

# librairie studio « TAT.json » + son logo
studio_folder = os.path.join(tmp, 'studio')
os.makedirs(studio_folder)
studio_path = os.path.join(studio_folder, 'TAT.json')
bl.save_library(studio_path, [
    {bl.CATEGORY_KEY: 'ANIMATION'},
    entry('select all', 'ANIMATION', button(0, 0, 70, 30, 'select all', BLUE)),
    entry('bake', 'ANIMATION', button(0, 0, 60, 30, 'bake', GREEN)),
    entry('euler filter', 'ANIMATION',
          button(0, 0, 80, 30, 'euler', PURPLE)),
    {bl.CATEGORY_KEY: 'SELECTION'},
    entry('body ctrls', 'SELECTION', button(0, 0, 70, 30, 'body', BROWN)),
])
logo_source = os.path.join(
    ROOT, 'hotbox_designer', 'resources', 'icons', 'studio_logo.png')
if os.path.exists(logo_source):
    shutil.copy(logo_source, os.path.join(studio_folder, 'studio_logo.png'))
bl.set_studio_location(studio_path)
bl.save_studio_settings(
    application, {'current': studio_path, 'recent': [studio_path]})

# hotboxes de démonstration
demo = demo_hotbox('TAT_body')
others = [demo_hotbox('TAT_face'), demo_hotbox('tools')]
with open(application.local_file, 'w') as f:
    json.dump([demo] + others, f)
application.record_hotkey('TAT_body', 'Shift+Q', 'switch on press')
application.record_hotkey('TAT_face', 'Alt+F', 'open on press & close on release')


# --------------------------------------------------------- les captures

print('captures :')

# 1. le manager (mode animateur) ------------------------------------
from hotbox_designer.manager import HotboxManager               # noqa: E402

bl.set_studio_admin(False)
manager = HotboxManager(application)
manager.resize(880, 380)
manager.show()
flush()
manager.personnal_view.selectRow(0)
grab(manager, 'manager')

# 2. le manager en mode admin (bandeau vert) ------------------------
bl.set_studio_admin(True)
manager.header.refresh()
grab(manager, 'manager-admin')
manager.close()
bl.set_studio_admin(False)

# 3. l'éditeur complet ----------------------------------------------
editor = HotboxEditor(json.loads(json.dumps(demo)), application, parent=None)
editor.resize(1320, 800)
editor.show()
flush()
editor.library_shelf.show()
chosen = [s for s in editor.shape_editor.shapes
          if s.options.get('text.content') == 'bras L']
if chosen:
    editor.shape_editor.selection.replace(chosen)
    editor.selection_changed()
editor_pixmap = grab(editor, 'editor', keep_it=False)

# 3b. la même, avec des repères numérotés (légende dans le manuel) ---
width, height = editor_pixmap.width(), editor_pixmap.height()
# (repères posés sur des zones VIDES pour ne rien masquer)
annotate(editor_pixmap, [
    (width - 30, 21, '1'),                # barre d'outils
    (80, 145, '2'),                       # plan de travail
    (width - 170, 145, '3'),              # panneau d'attributs
    (660, height - 65, '4'),              # shelf librairie
], 'editor-reperes')

# 4. la barre d'outils seule ----------------------------------------
grab(editor.menu, 'toolbar')

# 5. le panneau d'attributs -----------------------------------------
panel = editor.attribute_editor
panel.setFixedWidth(330)
grab(panel, 'attributs')

# 6. la shelf (onglets studio + perso) -------------------------------
shelf = editor.library_shelf
shelf.setFixedWidth(940)
shelf.refresh()
grab(shelf, 'shelf')

# 6b. la shelf sur une catégorie PERSO : on y voit le set --------------
for index in range(shelf.tabs.count()):
    if shelf._tab_name(index) == 'BODY':
        shelf.tabs.setCurrentIndex(index)
        break
grab(shelf, 'shelf-set')

# 7. la shelf, filtre de recherche actif -----------------------------
shelf.filter_edit.setText('sn')
flush()
grab(shelf, 'shelf-recherche')
shelf.filter_edit.setText('')
flush()

# 8. le coin de la shelf : badge + créer + ouvrir + ＋ -----------------
corner = shelf.tabs.cornerWidget(QtCore.Qt.TopRightCorner)
bl.set_studio_admin(True)
shelf.refresh()
flush()
grab(corner, 'shelf-coin')
bl.set_studio_admin(False)
shelf.refresh()

# 9. la palette flottante d'une catégorie ----------------------------
palette = shelf.open_category_palette(0)
if palette is not None:
    palette.resize(430, 260)
    grab(palette, 'palette')
    palette.close()

# 10. le badge STUDIO ADMIN de l'éditeur ------------------------------
bl.set_studio_admin(True)
editor.menu.update_admin_badge()
editor.resize(1600, 800)
flush()
grab(editor.menu, 'badge-admin')
bl.set_studio_admin(False)
editor.menu.update_admin_badge()

# 11. le dialogue « enregistrer dans la librairie » (avec set) ---------
dialog = bl.SaveToLibraryDialog(
    ['BODY', 'FACE', 'TOOLS'], default_name='Kit main IK', count=4)
dialog.show()
grab(dialog, 'dialogue-librairie')
dialog.close()

# 12. le dialogue de création (grille de templates) --------------------
from hotbox_designer.dialog import (                             # noqa: E402
    CreateHotboxDialog, HotkeyManagerDialog)

create = CreateHotboxDialog([demo] + others)
create.show()
flush()
if create.template_grid.count():
    create.template_grid.setCurrentRow(0)
    create.template_grid.setFixedWidth(460)  # deux colonnes de vignettes
flush()
grab(create, 'dialogue-creation')
create.close()

# 13. le gestionnaire de raccourcis ------------------------------------
hotkeys = HotkeyManagerDialog(
    ['TAT_body', 'TAT_face', 'tools'], application.load_hotkeys, True,
    lambda name: True, lambda name: None, parent=None)
hotkeys.resize(520, 220)
hotkeys.show()
grab(hotkeys, 'raccourcis')
hotkeys.close()

# 14. le sélecteur de couleurs ------------------------------------------
from hotbox_designer.colorpicker import ColorPickerDialog        # noqa: E402

picker = ColorPickerDialog('#6d8c5e')
picker.show()
grab(picker, 'colorpicker')
picker.close()

# 15. la hotbox en production (reader) ----------------------------------
from hotbox_designer.reader import HotboxReader                  # noqa: E402

reader = HotboxReader(json.loads(json.dumps(demo)), parent=None)
reader.show()
flush()
grab(reader, 'reader', dark_background=True)
reader.close()

editor.close()


# ------------------------------------------- incrustation dans le wiki

def css_block():
    lines = [BEGIN]
    for name in sorted(shots):
        width, height, data = shots[name]
        encoded = base64.b64encode(data).decode('ascii')
        # max-width = largeur naturelle : une petite capture n'est
        # jamais agrandie (donc jamais floue) ; une grande se réduit
        lines.append(
            '.shot--%s {aspect-ratio: %d / %d; max-width: %dpx; '
            'background-image: url(data:image/png;base64,%s);}'
            % (name, width, height, width, encoded))
    lines.append(END)
    return '\n'.join(lines)


with open(MANUAL, 'r', encoding='utf-8') as f:
    html = f.read()

block = css_block()
if BEGIN in html and END in html:
    html = re.sub(
        re.escape(BEGIN) + '.*?' + re.escape(END), lambda _: block,
        html, flags=re.S)
else:  # première exécution : juste avant la fin de la feuille de style
    html = html.replace('</style>', block + '\n</style>', 1)

with open(MANUAL, 'w', encoding='utf-8') as f:
    f.write(html)

total = sum(len(data) for _, _, data in shots.values())
print('%d captures incrustées dans MANUEL.html (%d ko d\'images)'
      % (len(shots), total // 1024))
shutil.rmtree(tmp, ignore_errors=True)
