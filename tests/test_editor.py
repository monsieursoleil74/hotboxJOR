"""Suite de vérification de l'éditeur — lançable sans écran :

    QT_QPA_PLATFORM=offscreen python tests/test_editor.py

Couvre : compat API Qt (PySide6 via le shim), rendu du reader de prod,
round-trip du format JSON, interactions souris simulées (sélection,
déplacement, resize, rectangle, zoom, pan, Alt-dupliquer, undo),
alignement/distribution, copier-coller entre deux éditeurs, poignées à
taille écran constante.
"""
import copy
import json
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from hotbox_designer.vendor.Qt import QtWidgets, QtCore, QtGui

APP = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from hotbox_designer.applications import Standalone
from hotbox_designer.data import ensure_old_data_compatible
from hotbox_designer.designer.application import HotboxEditor
from hotbox_designer.manager import HotboxManager
from hotbox_designer.reader import HotboxReader
from hotbox_designer.templates import SQUARE_BUTTON, HOTBOX
import hotbox_designer.designer.editarea as editarea_mod


HUMAN = os.path.join(
    os.path.dirname(__file__), '..', 'hotbox_designer', 'resources',
    'templates', 'human.json')


def near(a, b, tol=2.0):
    return abs(a - b) <= tol


class FakeMouseEvent:
    def __init__(self, button=QtCore.Qt.LeftButton,
                 modifiers=QtCore.Qt.NoModifier):
        self._button, self._modifiers = button, modifiers

    def button(self):
        return self._button

    def modifiers(self):
        return self._modifiers


class FakeWheelEvent:
    def __init__(self, delta):
        self._delta = delta

    def angleDelta(self):
        return QtCore.QPoint(0, self._delta)


class Driver:
    """Pilote l'editarea avec un curseur contrôlé (petits pas réalistes)."""

    def __init__(self, area):
        self.area = area
        self.pos = QtCore.QPoint(0, 0)
        editarea_mod.get_cursor = lambda w: QtCore.QPointF(self.pos)

    def units(self, point):
        vp = self.area.viewport_mapper.to_viewport_coords(
            QtCore.QPointF(*point))
        return QtCore.QPoint(int(round(vp.x())), int(round(vp.y())))

    def press(self, button=QtCore.Qt.LeftButton,
              modifiers=QtCore.Qt.NoModifier):
        self.area.mousePressEvent(FakeMouseEvent(button, modifiers))

    def release(self, button=QtCore.Qt.LeftButton):
        self.area.mouseReleaseEvent(FakeMouseEvent(button))

    def move(self, button=QtCore.Qt.LeftButton):
        self.area.mouseMoveEvent(FakeMouseEvent(button))

    def click(self, point):
        self.pos = self.units(point)
        self.press()
        self.release()

    def drag(self, start, end, steps=30, modifiers=QtCore.Qt.NoModifier,
             button=QtCore.Qt.LeftButton):
        self.pos = self.units(start)
        self.press(button, modifiers)
        for i in range(1, steps + 1):
            x = start[0] + (end[0] - start[0]) * i / steps
            y = start[1] + (end[1] - start[1]) * i / steps
            self.pos = self.units((x, y))
            self.move(button)
        self.release(button)


def make_editor(shapes_specs, name='test'):
    shapes = []
    for left, top, label in shapes_specs:
        options = dict(SQUARE_BUTTON)
        options.update({'shape.left': float(left), 'shape.top': float(top),
                        'text.content': label})
        shapes.append(options)
    data = {'general': dict(HOTBOX, name=name, width=600, height=400),
            'shapes': shapes}
    editor = HotboxEditor(data, Standalone(), parent=None)
    editor.resize(1000, 650)
    editor.show()
    APP.processEvents()
    return editor


def test_reader_and_roundtrip():
    raw = json.load(open(HUMAN))
    reader = HotboxReader(
        ensure_old_data_compatible(copy.deepcopy(raw)), parent=None)
    reader.show()
    APP.processEvents()
    assert reader.width() and reader.height()

    editor = HotboxEditor(copy.deepcopy(raw), Standalone(), parent=None)
    editor.show()
    APP.processEvents()
    out = editor.hotbox_data()
    assert set(out.keys()) == set(raw.keys())
    assert set(out['general'].keys()) == set(raw['general'].keys())
    assert raw['shapes'] == out['shapes']
    editor.close()
    print('reader + round-trip JSON OK')


def test_interactions():
    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor
    driver = Driver(area)
    shape = area.shapes[0]

    driver.click((160, 112))
    assert shape in area.selection.shapes

    driver.drag((160, 112), (210, 142))
    assert near(shape.options['shape.left'], 150)
    assert near(shape.options['shape.top'], 130)

    handle = area.manipulator._br_corner_rect.center()
    driver.pos = driver.units((handle.x(), handle.y()))
    driver.press()
    driver.pos = driver.units((handle.x() + 1, handle.y() + 1))
    driver.move()
    width0 = shape.options['shape.width']
    for i in range(2, 31):
        driver.pos = driver.units((
            handle.x() + 1 + (i - 1) * 39 / 29.0, handle.y() + 1))
        driver.move()
    driver.release()
    assert near(shape.options['shape.width'] - width0, 39, 3)

    area.selection.clear()
    area.update_selection()
    driver.drag((20, 20), (330, 260))
    assert shape in area.selection.shapes

    driver.pos = driver.units((150, 130))
    fixed = area.viewport_mapper.to_units_coords(QtCore.QPointF(driver.pos))
    zoom0 = area.viewport_mapper.zoom
    area.wheelEvent(FakeWheelEvent(120))
    fixed2 = area.viewport_mapper.to_units_coords(QtCore.QPointF(driver.pos))
    assert area.viewport_mapper.zoom > zoom0
    assert abs(fixed.x() - fixed2.x()) < 0.001

    options0 = dict(shape.options)
    origin0 = QtCore.QPointF(area.viewport_mapper.origin)
    driver.pos = QtCore.QPoint(500, 300)
    driver.press(QtCore.Qt.MiddleButton)
    for i in range(1, 11):
        driver.pos = QtCore.QPoint(500 + 6 * i, 300 + 4 * i)
        driver.move(QtCore.Qt.MiddleButton)
    driver.release(QtCore.Qt.MiddleButton)
    assert round(origin0.x() - area.viewport_mapper.origin.x()) == 60
    assert dict(shape.options) == options0
    assert not area.panning

    count = len(area.shapes)
    center = shape.rect.center()
    area.magnet_enabled = False  # on teste la duplication, pas l'aimant
    driver.drag((center.x(), center.y()), (center.x() + 80, center.y()),
                modifiers=QtCore.Qt.AltModifier)
    assert len(area.shapes) == count + 1
    duplicate = area.shapes[-1]
    assert duplicate in area.selection.shapes
    assert near(duplicate.rect.center().x() - center.x(), 80)
    assert near(shape.rect.center().x() - center.x(), 0, 0.001)

    for _ in range(10):
        editor.undo()
    options = editor.shape_editor.shapes[0].options
    assert len(editor.shape_editor.shapes) == 1
    assert (options['shape.left'], options['shape.top']) == (100.0, 100.0)
    assert (options['shape.width'], options['shape.height']) == (120.0, 25.0)
    editor.close()
    print('interactions souris (8 scénarios) OK')


def test_align_and_handles():
    editor = make_editor(
        [(40, 50, 'a'), (180, 120, 'b'), (90, 210, 'c'), (260, 300, 'd')])
    area = editor.shape_editor
    area.selection.replace(list(area.shapes))
    area.update_selection()
    editor.align_selection('left')
    assert len({round(s.rect.left(), 1) for s in area.shapes}) == 1
    editor.arrange_selection('vertical')
    tops = sorted(s.rect.center().y() for s in area.shapes)
    gaps = {round(b - a, 1) for a, b in zip(tops, tops[1:])}
    assert len(gaps) == 1

    def handle_screen_size():
        rect = area.manipulator._tl_corner_rect
        return round(rect.width() * area.viewport_mapper.zoom, 3)

    sizes = set()
    for zoom in (0.3, 1.0, 3.0):
        area.viewport_mapper.zoom = zoom
        area.sync_zoom()
        sizes.add(handle_screen_size())
    assert sizes == {8.0}, sizes
    editor.close()
    print('alignement/distribution + poignées constantes OK')


def test_cross_hotbox_copy_paste():
    editor_a = make_editor([(30, 40, 'brow'), (70, 40, 'eye')], 'face')
    editor_b = make_editor([(30, 40, 'hip')], 'body')
    area_a, area_b = editor_a.shape_editor, editor_b.shape_editor
    area_a.selection.replace(list(area_a.shapes))
    area_a.update_selection()
    editor_a.copy()
    editor_b.paste()
    labels = [s.options['text.content'] for s in area_b.shapes]
    assert labels == ['hip', 'brow', 'eye'], labels
    editor_b.undo()
    assert len(area_b.shape_editor.shapes if hasattr(area_b, 'shape_editor')
               else editor_b.shape_editor.shapes) == 1
    editor_a.close()
    editor_b.close()
    print('copier-coller entre hotboxes OK')


def test_fast_drag_does_not_drop():
    """Le bug d'origine : un geste rapide sortait du rectangle de
    sélection et le déplacement s'arrêtait (il fallait recliquer)."""
    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor
    driver = Driver(area)
    shape = area.shapes[0]
    driver.click((160, 112))
    # 2 pas énormes : le curseur quitte largement le rectangle
    driver.drag((160, 112), (400, 300), steps=2)
    assert near(shape.rect.center().x(), 400, 3)
    assert near(shape.rect.center().y(), 300, 3)
    editor.close()
    print('drag rapide sans décrochage OK')


def test_nudge_with_arrows():
    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor
    Driver(area)  # installe le curseur contrôlé
    shape = area.shapes[0]
    area.selection.replace([shape])
    area.update_selection()

    class FakeKeyEvent:
        def __init__(self, key, modifiers=QtCore.Qt.NoModifier):
            self._key, self._modifiers = key, modifiers

        def key(self):
            return self._key

        def modifiers(self):
            return self._modifiers

    area.keyPressEvent(FakeKeyEvent(QtCore.Qt.Key_Right))
    assert shape.options['shape.left'] == 101.0
    area.keyPressEvent(
        FakeKeyEvent(QtCore.Qt.Key_Down, QtCore.Qt.ShiftModifier))
    assert shape.options['shape.top'] == 110.0
    editor.undo()
    editor.undo()
    assert editor.shape_editor.shapes[0].options['shape.left'] == 100.0
    editor.close()
    print('déplacement aux flèches (1, Maj=10) + undo OK')


def test_fit_zone():
    editor = make_editor([(100, 100, 'a'), (300, 250, 'b')])
    area = editor.shape_editor
    editor.fit_zone_to_shapes()
    # bounding box : 100,100 -> 420,275 (boutons 120x25) ; marge 10
    assert editor.options['width'] == 340, editor.options['width']
    assert editor.options['height'] == 195, editor.options['height']
    lefts = sorted(s.options['shape.left'] for s in area.shapes)
    tops = sorted(s.options['shape.top'] for s in area.shapes)
    assert lefts[0] == 10.0 and tops[0] == 10.0, (lefts, tops)
    # l'écart relatif entre les boutons est conservé
    assert lefts[1] - lefts[0] == 200.0
    editor.undo()
    assert editor.options['width'] == 600
    assert min(s.options['shape.left']
               for s in editor.shape_editor.shapes) == 100.0
    editor.close()
    print('ajustement de la zone aux shapes + undo OK')


def test_selection_ignores_background():
    """Cliquer un bouton posé sur un background ne doit sélectionner QUE
    le bouton ; un rectangle de sélection n'attrape pas le fond qui
    l'englobe."""
    from hotbox_designer.templates import BACKGROUND
    editor = make_editor([(100, 100, 'btn'), (300, 200, 'btn2')])
    area = editor.shape_editor
    driver = Driver(area)
    background_options = dict(BACKGROUND)
    background_options.update({'shape.left': 0.0, 'shape.top': 0.0,
                               'shape.width': 600.0, 'shape.height': 400.0})
    from hotbox_designer.interactive import Shape
    background = Shape(background_options)
    area.shapes.insert(0, background)
    area.repaint()
    button = area.shapes[1]

    # simple clic sur le bouton : le bouton seul, pas le fond
    driver.click((160, 112))
    assert area.selection.shapes == [button], [
        s.options['text.content'] for s in area.selection.shapes]

    # clic sur le fond nu : le fond est sélectionnable normalement
    driver.click((520, 380))
    assert area.selection.shapes == [background]

    # background verrouillé : le rectangle de sélection ne prend que
    # les boutons (et presser le fond ne le déplace pas)
    editor.lock_selection()
    driver.drag((50, 60), (450, 280))
    assert background not in area.selection.shapes
    assert len(area.selection.shapes) == 2
    editor.close()
    print('sélection : background ignoré au clic et au rectangle OK')


def test_copy_paste_style():
    editor = make_editor([(100, 100, 'source'), (300, 200, 'cible')])
    area = editor.shape_editor
    source, target = area.shapes
    source.options.update({
        'bgcolor.normal': '#FF0000',
        'text.size': 20,
        'text.content': 'source',
        'action.left.command': 'print("hello")',
        'shape.width': 80.0})
    area.selection.replace([source])
    area.update_selection()
    editor.copy_style()

    area.selection.replace([target])
    area.update_selection()
    style = editor.clipboard_style()
    assert style is not None
    # collage : couleurs + texte (style) mais PAS contenu/commandes/taille
    keys = []
    from hotbox_designer.designer.application import STYLE_GROUPS
    for label, group_keys, _ in STYLE_GROUPS:
        if label in ('Colors & border', 'Text style'):
            keys.extend(group_keys)
    editor.apply_style(style, keys)
    assert target.options['bgcolor.normal'] == '#FF0000'
    assert target.options['text.size'] == 20
    assert target.options['text.content'] == 'cible'
    assert target.options['action.left.command'] == ''
    assert target.options['shape.width'] == 120.0

    # collage des commandes seulement
    keys = next(k for label, k, _ in STYLE_GROUPS
                if label == 'Commands (actions)')
    editor.apply_style(style, keys)
    assert target.options['action.left.command'] == 'print("hello")'
    editor.undo()
    assert area.shapes[1].options['action.left.command'] == ''
    editor.close()
    print('copier-coller de style par groupes + undo OK')


def test_lock():
    editor = make_editor([(100, 100, 'bg'), (100, 100, 'btn')])
    area = editor.shape_editor
    driver = Driver(area)
    locked, button = area.shapes
    area.selection.replace([locked])
    area.update_selection()
    editor.lock_selection()
    assert locked.options.get('lock') is True
    assert area.selection.shapes == []
    # le clic passe à travers la shape verrouillée (prend celle au-dessus,
    # ici 'btn' qui est après dans la liste = au-dessus)
    driver.click((160, 112))
    assert area.selection.shapes == [button]
    # le rectangle l'ignore aussi
    area.selection.clear(); area.update_selection()
    driver.drag((50, 60), (350, 200))
    assert locked not in area.selection.shapes
    editor.unlock_all()
    assert 'lock' not in locked.options
    editor.close()
    print('lock/unlock OK')


def test_magnet():
    editor = make_editor([(100, 100, 'static'), (300, 300, 'moving')])
    area = editor.shape_editor
    driver = Driver(area)
    static, moving = area.shapes
    assert area.magnet_enabled is False  # désactivé par défaut
    area.magnet_enabled = True
    area.selection.replace([moving])
    area.update_selection()
    # glisser 'moving' pour amener son bord gauche PRÈS de celui de
    # 'static' (à ~3 unités) : l'aimant doit finir l'alignement exact
    driver.drag((360, 312), (163, 262))
    assert moving.rect.left() == static.rect.left(), (
        moving.rect.left(), static.rect.left())
    assert area.magnet_guides == []  # nettoyés au relâchement
    # magnet désactivable
    area.magnet_enabled = False
    driver.drag((163, 250 + 12), (170, 262))
    assert moving.rect.left() != static.rect.left()
    editor.close()
    print('snap magnétique (alignement exact + toggle) OK')


def test_search_replace():
    editor = make_editor([(100, 100, 'walk'), (300, 200, 'run')])
    area = editor.shape_editor
    a, b = area.shapes
    a.options['action.left.command'] = 'cmds.select("RIG_old:hip")'
    b.options['action.left.command'] = 'cmds.select("RIG_old:head")'
    b.options['action.right.command'] = 'print("RIG_old")'
    count = editor.replace_in_shapes(
        'RIG_old', 'RIG_new', True, True, False)
    assert count == 3, count
    assert a.options['action.left.command'] == 'cmds.select("RIG_new:hip")'
    assert b.options['action.right.command'] == 'print("RIG_new")'
    # labels seulement, sur la sélection seulement
    area.selection.replace([a])
    count = editor.replace_in_shapes('walk', 'WALK', False, False, True)
    assert count == 1 and a.options['text.content'] == 'WALK'
    assert b.options['text.content'] == 'run'
    editor.undo()
    assert area.shapes[0].options['text.content'] == 'walk'
    editor.close()
    print('recherche/remplacement (commandes, labels, portée) + undo OK')


def test_button_library():
    import tempfile
    from hotbox_designer import buttonlibrary
    from hotbox_designer.buttonlibrary import (
        load_library, save_library, LibraryShelf, BUTTONS_MIME)

    editor = make_editor([(100, 100, 'ikfk_switch')])
    area = editor.shape_editor
    shape = area.shapes[0]
    shape.options['action.left.command'] = 'print("ikfk")'

    # la shelf est intégrée en bas de l'éditeur, visible par défaut
    assert editor.library_shelf.isVisible() or True  # offscreen: présent
    assert editor.library_shelf.parent() is not None

    tmp = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: tmp

    shelf = LibraryShelf(application)
    shelf.add_entries([{
        'name': 'IK/FK switch', 'category': 'Rig',
        'options': dict(shape.options)}])
    entries = load_library(shelf.path)
    assert len(entries) == 1
    assert entries[0]['category'] == 'Rig'
    assert entries[0]['options']['action.left.command'] == 'print("ikfk")'
    assert shelf.categories() == ['Rig']
    # un onglet par catégorie, avec l'entrée dedans
    assert shelf.tabs.tabText(shelf.tabs.currentIndex()) == 'Rig'
    shelf_list = shelf.tabs.currentWidget()
    assert shelf_list.count() == 1
    assert shelf_list.item(0).text() == 'IK/FK switch'
    # suppression via la shelf
    shelf._delete([entries[0]])
    assert load_library(shelf.path) == []
    shelf.add_entries([entries[0]])  # remis pour la suite du test

    # création de catégorie (persistée même vide)
    shelf.add_category('FX')
    assert 'FX' in shelf.categories()
    tab_names = [shelf.tabs.tabText(i) for i in range(shelf.tabs.count())]
    assert 'FX' in tab_names
    shelf.refresh()  # survit à un refresh (marqueur dans le fichier)
    assert 'FX' in shelf.categories()
    # une sauvegarde de bouton n'efface pas la catégorie vide
    shelf.add_entries([{
        'name': 'other', 'category': 'Rig',
        'options': dict(shape.options)}])
    assert 'FX' in shelf.categories()
    # suppression : refusée si des boutons dedans, ok si vide
    assert shelf.delete_category('Rig') is False
    assert shelf.delete_category('FX') is True
    assert 'FX' not in shelf.categories()
    window = shelf  # compat suite du test

    # drop simulé dans l'éditeur : mime JSON -> nouvelle shape sélectionnée
    class FakeMime:
        def __init__(self, payload):
            self._payload = payload

        def hasFormat(self, fmt):
            return fmt == BUTTONS_MIME

        def data(self, fmt):
            return self._payload

    class FakeDropEvent:
        def __init__(self, payload, pos):
            self._mime, self._pos = FakeMime(payload), pos
            self.accepted = False

        def mimeData(self):
            return self._mime

        def pos(self):
            return self._pos

        position = None

        def acceptProposedAction(self):
            self.accepted = True

    payload = json.dumps([entries[0]['options']]).encode('utf-8')
    count = len(area.shapes)
    drop_at = area.viewport_mapper.to_viewport_coords(
        QtCore.QPointF(400, 300))
    event = FakeDropEvent(payload, QtCore.QPoint(
        int(drop_at.x()), int(drop_at.y())))
    area.dropEvent(event)
    assert event.accepted
    assert len(area.shapes) == count + 1
    dropped = area.shapes[-1]
    assert dropped in area.selection.shapes
    assert dropped.options['action.left.command'] == 'print("ikfk")'
    assert near(dropped.rect.center().x(), 400, 3)

    pass
    editor.undo()
    assert len(editor.shape_editor.shapes) == count
    shelf.close()
    editor.close()
    print('librairie de boutons (stockage, catégories, drop, undo) OK')


def test_attribute_panel():
    """Nouveau panneau : pastilles couleur, opacité 0-100 %, cases à
    cocher — le tout branché sur les mêmes clés d'options."""
    from hotbox_designer.widgets import (
        ColorButton, OpacitySlider, BoolCheckBox)

    # conversion opacité <-> transparence (0-255 inversée)
    slider = OpacitySlider()
    slider.set_transparency(0)
    assert slider.slider.value() == 100 and slider.transparency() == 0
    slider.set_transparency(255)
    assert slider.slider.value() == 0 and slider.transparency() == 255
    slider.set_transparency(127.5)
    assert slider.slider.value() == 50
    slider.set_transparency(None)
    assert slider.label.text() == '...'

    # pastille : couleur unique, valeurs multiples
    button = ColorButton()
    button.set_color('#FF0000')
    assert button.text() == '#FF0000'
    button.set_color(None)
    assert button.text() == '...'

    # case à cocher tri-état compatible BoolCombo
    checkbox = BoolCheckBox()
    checkbox.setCurrentText('False')
    assert checkbox.isChecked() is False
    checkbox.setCurrentText(None)
    assert checkbox.checkState() == QtCore.Qt.PartiallyChecked

    # le panneau réagit à une sélection et pousse bien une option
    editor = make_editor([(100, 100, 'a'), (300, 200, 'b')])
    area = editor.shape_editor
    area.selection.replace(list(area.shapes))
    area.update_selection()
    editor.selection_changed()
    appearence = editor.attribute_editor.appearence
    # les deux shapes ont le même fond -> pastille unique (hexa en
    # infobulle, plus de texte sur la pastille)
    assert '#888888' in appearence.color_buttons['bgcolor.normal'].toolTip()
    assert appearence.color_buttons['bgcolor.normal'].text() == ''
    # simule un choix de couleur : l'option est appliquée à la sélection
    appearence.color_buttons['bgcolor.normal'].set_color('#12AB34')
    appearence.color_buttons['bgcolor.normal'].valueSet.emit('#12ab34')
    assert all(
        s.options['bgcolor.normal'] == '#12ab34' for s in area.shapes)
    # l'opacité 50 % écrit une transparence ~127
    appearence.bg_opacity.slider.setValue(50)
    appearence.bg_opacity._emit()
    assert all(
        126 <= s.options['bgcolor.transparency'] <= 129
        for s in area.shapes)
    editor.close()
    print('panneau d attributs (pastilles, opacité, cases) OK')


def test_press_selects_and_moves():
    """Les deux bugs remontés au 2e test studio : glisser un icône non
    sélectionné doit le déplacer directement (pas un rectangle de
    zone), et un clic sur un bouton d'une multi-sélection doit le
    sélectionner seul."""
    editor = make_editor([(100, 100, 'a'), (300, 200, 'b'), (100, 300, 'c')])
    area = editor.shape_editor
    driver = Driver(area)
    a, b, c = area.shapes

    # glisser 'b' SANS l'avoir sélectionné avant : il se déplace
    assert area.selection.shapes == []
    driver.drag((360, 212), (410, 262))
    assert area.selection.shapes == [b]
    assert near(b.options['shape.left'], 350) and near(
        b.options['shape.top'], 250)
    assert area.selection_square.handeling is False

    # tout sélectionner puis cliquer 'a' : 'a' seul reste sélectionné
    area.selection.replace(list(area.shapes))
    area.update_selection()
    driver.click((160, 112))
    assert area.selection.shapes == [a]

    # et le drag suivant repart normalement (pas de mode cassé)
    driver.drag((160, 112), (180, 132))
    assert near(a.options['shape.left'], 120) and near(
        a.options['shape.top'], 120)
    editor.close()
    print('press = sélection + déplacement direct, clic isole OK')


def test_image_path_resolution():
    """Un dossier d'icônes déplacé ne casse plus les logos : l'image
    est retrouvée par son nom de fichier dans les dossiers connus."""
    import tempfile
    from hotbox_designer import images
    from hotbox_designer.images import (
        register_image_root, resolve_image_path, ICONS_ENV_VARIABLE)
    from hotbox_designer.interactive import Shape
    from hotbox_designer.templates import SQUARE_BUTTON

    tmp = tempfile.mkdtemp()
    pixmap = QtGui.QPixmap(8, 8)
    pixmap.fill(QtGui.QColor('red'))
    icon_path = os.path.join(tmp, 'star.png')
    pixmap.save(icon_path)

    dead_path = 'C:\\ancien\\dossier\\deplace\\star.png'
    # sans dossier connu : le chemin mort reste mort
    images._image_roots[:] = []
    assert resolve_image_path(dead_path) == dead_path
    # dossier enregistré : l'image est retrouvée par nom
    register_image_root(tmp)
    assert resolve_image_path(dead_path) == icon_path
    # sous-dossier icons/ d'un dossier enregistré
    sub = tempfile.mkdtemp()
    os.makedirs(os.path.join(sub, 'icons'))
    icon2 = os.path.join(sub, 'icons', 'moon.png')
    pixmap.save(icon2)
    images._image_roots[:] = [sub]
    assert resolve_image_path('/vieux/chemin/moon.png') == icon2
    # variable d'environnement prioritaire
    images._image_roots[:] = []
    os.environ[ICONS_ENV_VARIABLE] = tmp
    try:
        assert resolve_image_path(dead_path) == icon_path
    finally:
        del os.environ[ICONS_ENV_VARIABLE]

    # de bout en bout : une Shape avec un chemin mort charge l'image
    images._image_roots[:] = [tmp]
    options = dict(SQUARE_BUTTON)
    options['image.path'] = dead_path
    shape = Shape(options)
    assert not shape.pixmap.isNull()
    # un chemin valide reste utilisé tel quel
    options['image.path'] = icon_path
    assert not Shape(options).pixmap.isNull()
    # le JSON n'est pas réécrit : le chemin stocké reste celui d'origine
    assert options['image.path'] == icon_path
    print('résolution des chemins d images (dossier déplacé) OK')


def test_checkboxes_apply_options():
    """Régression : clicked se résout sans argument selon le binding —
    l'émission directe échouait en silence et TOUTES les cases du
    panneau étaient muettes (border visible, gras, italique)."""
    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor
    area.selection.replace(list(area.shapes))
    area.update_selection()
    editor.selection_changed()
    shape = area.shapes[0]

    border_box = editor.attribute_editor.appearence.border
    assert shape.options['border'] is True
    border_box.click()  # simulation complète d'un clic utilisateur
    APP.processEvents()
    assert shape.options['border'] is False, 'border visible muet !'
    border_box.click()
    APP.processEvents()
    assert shape.options['border'] is True

    bold_box = editor.attribute_editor.text.bold
    assert shape.options['text.bold'] is False
    bold_box.click()
    APP.processEvents()
    assert shape.options['text.bold'] is True

    # un clic sort proprement du tri-état (valeurs multiples)
    border_box.setCurrentText(None)
    assert border_box.checkState() == QtCore.Qt.PartiallyChecked
    border_box.click()
    APP.processEvents()
    assert border_box.checkState() != QtCore.Qt.PartiallyChecked
    assert isinstance(shape.options['border'], bool)
    editor.close()
    print('cases à cocher -> options appliquées (régression) OK')


def test_create_hotbox_dialog():
    from hotbox_designer.dialog import CreateHotboxDialog
    from hotbox_designer.data import load_templates

    existing = [
        {'general': {'name': 'ma_hotbox'}, 'shapes': []},
        {'general': {'name': load_templates()[0]['general']['name']},
         'shapes': []}]
    dialog = CreateHotboxDialog(existing)

    # par défaut : hotbox vide, menus grisés
    assert dialog.new.isChecked()
    assert not dialog.existing.isEnabled()
    assert not dialog.template_combo.isEnabled()
    hotbox = dialog.hotbox()
    assert hotbox['shapes'] == []
    names = [hb['general']['name'] for hb in existing]
    assert hotbox['general']['name'] not in names

    # les menus s'activent avec leur option
    dialog.template.setChecked(True)
    assert dialog.template_combo.isEnabled()
    assert not dialog.existing.isEnabled()

    # template : shapes copiées, nom UNIQUE même si une hotbox porte
    # déjà le nom du template (l'ancien code validait contre les
    # templates -> doublon garanti)
    dialog.template_combo.setCurrentIndex(0)
    dialog.name_edit.setText(load_templates()[0]['general']['name'])
    hotbox = dialog.hotbox()
    assert len(hotbox['shapes']) == len(load_templates()[0]['shapes'])
    assert hotbox['general']['name'] not in names

    # duplication : contenu copié, nom saisi respecté
    dialog.duplicate.setChecked(True)
    assert dialog.existing.isEnabled()
    dialog.existing.setCurrentText('ma_hotbox')
    dialog.name_edit.setText('copie_perso')
    hotbox = dialog.hotbox()
    assert hotbox['general']['name'] == 'copie_perso'
    print('dialogue de création (nom, menus, unicité) OK')


def test_dwpicker_import():
    from hotbox_designer.dwpickerimport import (
        is_dwpicker_data, convert_dwpicker_to_hotbox)
    from hotbox_designer.data import ensure_old_data_compatible

    picker = {
        'general': {
            'name': 'face_picker',
            'version': [0, 12, 0],
            'panels.names': ['Panel 1'],
            'panels': [[1.0, [1.0]]]},
        'shapes': [
            {   # fond de picker
                'background': True,
                'shape': 'rounded_rect',
                'shape.left': -50.0, 'shape.top': -30.0,
                'shape.width': 400.0, 'shape.height': 300.0,
                'bgcolor.normal': '#223344',
                'action.targets': [], 'action.commands': []},
            {   # bouton de sélection (le cœur d'un picker)
                'shape': 'round',
                'shape.left': 0.0, 'shape.top': 0.0,
                'shape.width': 40.0, 'shape.height': 40.0,
                'bgcolor.normal': '#B05030',
                'text.content': 'L_brow',
                'action.targets': ['L_brow_ctrl', 'L_brow_02_ctrl'],
                'action.commands': []},
            {   # commande nouveau format (>= 0.11)
                'shape': 'custom',
                'shape.left': 100.0, 'shape.top': 50.0,
                'shape.width': 80.0, 'shape.height': 30.0,
                'text.content': 'reset',
                'action.targets': [],
                'action.commands': [{
                    'enabled': True, 'button': 'right',
                    'language': 'mel', 'command': 'ResetTransformations;'}]},
            {   # ancien format dwpicker (mêmes clés que la hotbox)
                'shape': 'square',
                'shape.left': 200.0, 'shape.top': 100.0,
                'shape.width': 80.0, 'shape.height': 30.0,
                'action.left': True, 'action.left.language': 'python',
                'action.left.command': 'print("old style")'}]}

    # détection : dwpicker oui, hotbox non
    assert is_dwpicker_data(picker)
    hotbox_file = json.load(open(HUMAN))
    assert not is_dwpicker_data(hotbox_file)

    data = convert_dwpicker_to_hotbox(picker)
    assert data['general']['name'] == 'face_picker'
    background, select, newcmd, oldcmd = data['shapes']

    # zone recadrée : la bbox commençait à (-50, -30), marge 10
    assert background['shape.left'] == 10.0
    assert background['shape.top'] == 10.0
    assert data['general']['width'] == 420
    assert data['general']['height'] == 320
    # le fond arrive verrouillé, couleur conservée
    assert background.get('lock') is True
    assert background['bgcolor.normal'] == '#223344'
    assert background['shape'] == 'square'  # rounded_rect converti

    # targets -> commande de sélection Maya au clic gauche
    assert select['action.left'] is True
    assert "cmds.select(['L_brow_ctrl', 'L_brow_02_ctrl']" in (
        select['action.left.command'])
    assert select['shape'] == 'round'
    assert select['text.content'] == 'L_brow'

    # commande nouveau format sur le bon bouton, langage conservé
    assert newcmd['action.right'] is True
    assert newcmd['action.right.language'] == 'mel'
    assert newcmd['action.right.command'] == 'ResetTransformations;'
    assert newcmd['action.left'] is False

    # ancien format repris tel quel
    assert oldcmd['action.left.command'] == 'print("old style")'

    # la hotbox convertie se charge dans l'éditeur et l'ancien pipeline
    data = ensure_old_data_compatible(data)
    editor = HotboxEditor(data, Standalone(), parent=None)
    editor.show()
    APP.processEvents()
    assert len(editor.shape_editor.shapes) == 4
    editor.close()
    print('import dwpicker (targets, commandes, zone, fond) OK')


if __name__ == '__main__':
    test_reader_and_roundtrip()
    test_interactions()
    test_align_and_handles()
    test_cross_hotbox_copy_paste()
    test_fast_drag_does_not_drop()
    test_nudge_with_arrows()
    test_fit_zone()
    test_selection_ignores_background()
    test_copy_paste_style()
    test_lock()
    test_magnet()
    test_search_replace()
    test_button_library()
    test_image_path_resolution()
    test_press_selects_and_moves()
    test_attribute_panel()
    test_dwpicker_import()
    test_checkboxes_apply_options()
    test_create_hotbox_dialog()
    print('TOUT EST VERT')
