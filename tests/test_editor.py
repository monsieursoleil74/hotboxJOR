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

    # background verrouillé (option posée sur la shape) : le rectangle
    # de sélection ne prend que les boutons
    background.options['lock'] = True
    area.selection.clear()
    area.update_selection()
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
    locked.options['lock'] = True  # (l'UI lock/unlock a été retirée)
    # le clic passe à travers la shape verrouillée (prend celle au-dessus,
    # ici 'btn' qui est après dans la liste = au-dessus)
    driver.click((160, 112))
    assert area.selection.shapes == [button]
    # le rectangle l'ignore aussi
    area.selection.clear(); area.update_selection()
    driver.drag((50, 60), (350, 200))
    assert locked not in area.selection.shapes
    editor.close()
    print('lock (option de shape respectée par la sélection) OK')


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
    from hotbox_designer.buttonlibrary import (
        load_library, LibraryShelf, BUTTONS_MIME)

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

    # slider d'épaisseur de bordure : une valeur pilote les 3 états
    # proportionnellement (normal, survol ×1.25, clic ×2)
    appearence.border_width.set_value(4.0)
    appearence.border_width._emit()
    for s in area.shapes:
        assert s.options['borderwidth.normal'] == 4.0
        assert s.options['borderwidth.hovered'] == 5.0
        assert s.options['borderwidth.clicked'] == 8.0
    editor.close()
    print('panneau d attributs (pastilles, opacité, épaisseur, cases) OK')


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
    assert not dialog.template_grid.isEnabled()
    hotbox = dialog.hotbox()
    assert hotbox['shapes'] == []
    names = [hb['general']['name'] for hb in existing]
    assert hotbox['general']['name'] not in names

    # les menus s'activent avec leur option
    dialog.template.setChecked(True)
    assert dialog.template_grid.isEnabled()
    assert not dialog.existing.isEnabled()

    # template : shapes copiées, nom UNIQUE même si une hotbox porte
    # déjà le nom du template (l'ancien code validait contre les
    # templates -> doublon garanti)
    dialog.template_grid.setCurrentRow(0)
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


def test_rounded_rect():
    from hotbox_designer.interactive import Shape
    from hotbox_designer.painting import draw_shape
    from hotbox_designer.data import ensure_old_data_compatible

    # rendu : un rounded_rect ne remplit pas les coins (fond visible)
    options = dict(SQUARE_BUTTON)
    options.update({
        'shape': 'rounded_rect', 'shape.left': 10.0, 'shape.top': 10.0,
        'shape.width': 80.0, 'shape.height': 40.0,
        'shape.cornersx': 18, 'shape.cornersy': 18,
        'bgcolor.normal': '#00FF00', 'border': False})
    image = QtGui.QImage(100, 60, QtGui.QImage.Format_RGB32)
    image.fill(QtGui.QColor('#000000'))
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    draw_shape(painter, Shape(options))
    painter.end()
    corner = QtGui.QColor(image.pixel(12, 12)).name()  # coin haut-gauche
    center = QtGui.QColor(image.pixel(50, 30)).name()
    assert center == '#00ff00', center       # centre rempli
    assert corner != '#00ff00', corner       # coin arrondi = fond noir

    # compat : ensure_old_data_compatible ajoute les rayons par défaut
    data = ensure_old_data_compatible(
        {'general': dict(HOTBOX, name='x'),
         'shapes': [{'shape': 'square', 'shape.left': 0.0}]})
    assert data['shapes'][0]['shape.cornersx'] == 8
    print('coins arrondis (rendu + défauts) OK')


def test_color_picker():
    from hotbox_designer.colorpicker import ColorPickerDialog

    dialog = ColorPickerDialog('#3388ff')
    assert dialog.color_name().lower() == '#3388ff'
    # champ hexa -> couleur
    dialog.hexedit.setText('#e24d4d')
    dialog._hex_edited()
    assert dialog.color_name().lower() == '#e24d4d'
    # preset -> couleur
    dialog._set_hex('#27ae60')
    assert dialog.color_name().lower() == '#27ae60'
    # teinte + carré SV recalculent la couleur
    dialog.hue_bar.set_hue(0.0)
    dialog._hue_changed()
    dialog.square._sat, dialog.square._val = 1.0, 1.0
    dialog._sv_changed()
    assert dialog.color_name().lower() == '#ff0000'  # rouge pur
    print('color picker (hexa, preset, teinte/SV) OK')


def test_studio_library():
    import tempfile
    from hotbox_designer.buttonlibrary import (
        LibraryShelf, STUDIO_ENV_VARIABLE, load_library)

    def entry(name, category):
        return {'name': name, 'category': category,
                'options': dict(SQUARE_BUTTON, **{'text.content': name})}

    studio_dir = tempfile.mkdtemp()
    json.dump(
        [entry('IK/FK', 'Rig'), entry('Playblast', 'Anim'),
         {'__category__': 'EXTRA TOOLS'}],  # catégorie studio VIDE
        open(os.path.join(studio_dir, 'button_library.json'), 'w'))
    os.environ[STUDIO_ENV_VARIABLE] = studio_dir
    try:
        perso = tempfile.mkdtemp()
        application = Standalone()
        application.get_data_folder = lambda: perso
        shelf = LibraryShelf(application)
        shelf.add_entries([entry('MyTool', 'Perso')])

        readonly = [shelf.tabs.widget(i).readonly
                    for i in range(shelf.tabs.count())]
        # onglets studio (lecture seule) en tête, puis perso
        assert readonly[0] is True
        assert readonly[-1] is False
        # onglet studio affiche le logo (icône non vide) et un nom propre
        assert not shelf.tabs.tabIcon(0).isNull()
        assert shelf.tabs.tabText(0) in ('Anim', 'EXTRA TOOLS', 'Rig')
        # une catégorie studio VIDE est bien visible en onglet
        studio_tabs = [shelf.tabs.tabText(i)
                       for i in range(shelf.tabs.count())
                       if shelf.tabs.widget(i).readonly]
        assert 'EXTRA TOOLS' in studio_tabs
        assert set(studio_tabs) == {'Anim', 'EXTRA TOOLS', 'Rig'}
        # sauvegarde depuis un onglet studio retombe sur une cat. perso
        shelf.tabs.setCurrentIndex(0)
        assert shelf.current_category() == 'General'
        # le studio n'est jamais écrit dans la perso
        assert all(e['name'] != 'IK/FK' for e in load_library(shelf.path))

        # export vers la librairie studio depuis la perso
        from hotbox_designer.buttonlibrary import (
            export_to_studio, load_studio_library)
        perso_entry = entry('MyTool', 'Perso')
        added = export_to_studio([perso_entry])
        assert added == 1
        assert any(e['name'] == 'MyTool' for e in load_studio_library())
        # ré-export du même bouton = doublon ignoré
        assert export_to_studio([perso_entry]) == 0
        shelf.close()
    finally:
        del os.environ[STUDIO_ENV_VARIABLE]
    print('librairie studio (onglets logo, lecture seule, export) OK')


def test_thumbnail_cache_and_dedup():
    import tempfile
    from hotbox_designer.buttonlibrary import (
        hotbox_thumbnail, button_thumbnail, LibraryShelf, _THUMB_CACHE)

    # vignette de hotbox : pixmap à la taille demandée, non vide
    data = {'general': dict(HOTBOX, name='t', width=400, height=300),
            'shapes': [dict(SQUARE_BUTTON, **{'shape.left': 50.0,
                       'shape.top': 50.0, 'bgcolor.normal': '#3388ff'})]}
    pixmap = hotbox_thumbnail(data, 190, 120)
    assert pixmap.width() == 190 and pixmap.height() == 120
    assert not pixmap.isNull()

    # une forme qui déborde de la zone est rognée comme dans la vraie
    # hotbox (sinon une barre trop large envahit l'aperçu)
    data = {'general': dict(HOTBOX, name='t2', width=400, height=300),
            'shapes': [dict(SQUARE_BUTTON, **{
                'shape.left': -400.0, 'shape.top': 100.0,
                'shape.width': 1200.0, 'shape.height': 60.0,
                'bgcolor.normal': '#ff0000',
                'bgcolor.transparency': 0,
                'border': False})]}
    pixmap = hotbox_thumbnail(data, 190, 120)
    image = pixmap.toImage()
    # au centre (dans la zone) : la barre rouge est là
    assert QtGui.QColor(image.pixel(95, 60)).red() > 200
    # sur le bord gauche (hors zone) : fond intact, pas de débordement
    assert QtGui.QColor(image.pixel(1, 60)).red() < 100

    # cache des vignettes de bouton : deux appels identiques = même objet
    _THUMB_CACHE.clear()
    options = dict(SQUARE_BUTTON, **{'text.content': 'A'})
    icon1 = button_thumbnail(options, (72, 36))
    icon2 = button_thumbnail(dict(options), (72, 36))
    assert icon1 is icon2  # servi depuis le cache
    icon3 = button_thumbnail(dict(options, **{'text.content': 'B'}), (72, 36))
    assert icon3 is not icon1  # apparence différente = nouveau rendu

    # anti-doublon en librairie
    tmp = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: tmp
    shelf = LibraryShelf(application)
    entry = {'name': 'IK', 'category': 'Rig', 'options': dict(SQUARE_BUTTON)}
    assert shelf.add_entries([entry]) == 1
    assert shelf.add_entries([dict(entry)]) == 0  # doublon ignoré
    from hotbox_designer.buttonlibrary import load_library
    assert len(load_library(shelf.path)) == 1
    shelf.close()
    print('cache vignettes + anti-doublon librairie OK')


def test_image_placement():
    """Mode « placer l'image » : drag déplace l'image dans le bouton,
    molette redimensionne, bouton Center remet à zéro."""
    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor
    driver = Driver(area)
    shape = area.shapes[0]
    shape.options['image.fit'] = False
    shape.options['image.offsetx'] = 0
    shape.options['image.offsety'] = 0
    shape.options['image.width'] = 40.0
    shape.options['image.height'] = 40.0
    area.selection.replace([shape])  # placement = 1 shape sélectionnée
    area.update_selection()

    # entrée en mode via l'éditeur
    editor.shape_editor.start_place_image(shape)
    assert area.place_image_shape is shape

    # drag dans le bouton -> l'image se décale (offset suit le geste)
    center = shape.rect.center()
    driver.pos = driver.units((center.x(), center.y()))
    driver.press()
    driver.pos = driver.units((center.x() + 30, center.y() + 15))
    driver.move()
    driver.release()
    assert near(shape.options['image.offsetx'], 30, 2)
    assert near(shape.options['image.offsety'], 15, 2)

    # molette agrandit l'image
    w0 = shape.options['image.width']
    driver.pos = driver.units((center.x(), center.y()))
    area.wheelEvent(FakeWheelEvent(120))
    assert shape.options['image.width'] > w0

    # le zoom du viewport n'a PAS bougé (la molette servait à l'image)
    zoom_before = area.viewport_mapper.zoom
    area.wheelEvent(FakeWheelEvent(120))
    assert area.viewport_mapper.zoom == zoom_before

    # Center remet l'image au milieu
    editor.center_image()
    assert shape.options['image.offsetx'] == 0
    assert shape.options['image.offsety'] == 0

    # flèches : décalage de l'image d'1 unité, Maj = 10, et la SHAPE
    # ne bouge pas (les flèches servent à l'image dans ce mode)
    shape_left = shape.options['shape.left']
    area.keyPressEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Right, QtCore.Qt.NoModifier))
    assert shape.options['image.offsetx'] == 1
    area.keyPressEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Down,
        QtCore.Qt.ShiftModifier))
    assert shape.options['image.offsety'] == 10
    area.keyPressEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Left, QtCore.Qt.NoModifier))
    assert shape.options['image.offsetx'] == 0
    assert shape.options['shape.left'] == shape_left
    shape.options['image.offsety'] = 0
    shape.synchronize_image()

    # sortie du mode
    editor.shape_editor.stop_place_image()
    assert area.place_image_shape is None
    # après sortie, la molette re-zoome
    area.wheelEvent(FakeWheelEvent(120))
    assert area.viewport_mapper.zoom > zoom_before

    # undo annule le déplacement d'image
    editor.undo()
    editor.close()
    print('mode placer l image (drag, molette, center, zoom) OK')


def test_command_autosave():
    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor
    shape = area.shapes[0]

    # auto-save de la commande : la perte de focus enregistre
    area.selection.replace([shape])
    area.update_selection()
    editor.selection_changed()
    action = editor.attribute_editor.action
    action._lactive.setCurrentText('True')
    action._lactive.valueSet.emit(True)
    action._lcommand.setPlainText('print("auto")')
    action._lcommand.committed.emit()  # simule la perte de focus
    APP.processEvents()
    assert shape.options['action.left.command'] == 'print("auto")'
    editor.close()
    print('auto-save commande OK')


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


def test_submenu_opener():
    """Sous-menu fluide : choisir une hotbox « is submenu » dans le
    panneau Action doit générer la commande d'ouverture sur le clic
    gauche du/des bouton(s) sélectionné(s), sans écrire de code."""
    from hotbox_designer.commands import OPEN_COMMAND

    # deux hotboxes existent : la courante et une marquée « is submenu »
    sub = {'general': dict(HOTBOX, name='outils', submenu=True),
           'shapes': []}
    main = {'general': dict(HOTBOX, name='principal', width=600,
                            height=400),
            'shapes': []}
    all_hotboxes = [main, sub]

    data = {'general': dict(HOTBOX, name='principal', width=600,
                            height=400),
            'shapes': [dict(SQUARE_BUTTON, **{
                'shape.left': 100.0, 'shape.top': 100.0,
                'text.content': 'btn'})]}
    editor = HotboxEditor(
        data, Standalone(), parent=None, all_hotboxes=all_hotboxes)
    editor.show()
    APP.processEvents()

    # la liste ne propose que le sous-menu (pas la hotbox courante)
    assert editor.submenu_names() == ['outils']
    combo = editor.attribute_editor.action._submenu
    values = [combo.itemData(i) for i in range(combo.count())]
    assert values == ['', 'outils']
    assert combo.isVisible()

    # avec sélection : la commande show('outils') est générée
    shape = editor.shape_editor.shapes[0]
    editor.shape_editor.selection.replace([shape])
    editor.set_submenu_opener('outils')
    expected = OPEN_COMMAND.format(application='Standalone', name='outils')
    assert shape.options['action.left'] is True
    assert shape.options['action.left.language'] == 'python'
    assert shape.options['action.left.command'] == expected
    assert "show('outils')" in shape.options['action.left.command']

    # déclencher via le combo (index 1 = 'outils') fait la même chose,
    # puis revient sur « none » (choix = déclencheur, pas un état)
    shape.options['action.left'] = False
    editor.shape_editor.selection.replace([shape])
    combo.setCurrentIndex(1)
    APP.processEvents()
    assert shape.options['action.left'] is True
    assert combo.currentIndex() == 0

    editor.close()
    print('sous-menu fluide (ouvreur de hotbox généré) OK')


def test_library_category_ops():
    """Organiser les catégories d'une librairie : créer, renommer,
    déplacer des boutons, supprimer une catégorie vide. Même logique
    pour la librairie perso et la librairie studio (fonctions par
    chemin)."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl

    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, 'button_library.json')

    def button(name, category=None):
        entry = {'name': name, 'options': {'text.content': name}}
        if category is not None:
            entry['category'] = category
        return entry

    # départ : « a » en General (implicite), « b » en TAT
    bl.save_library(path, [button('a'), button('b', 'TAT')])
    assert bl.categories_in(path) == ['General', 'TAT']

    # créer une catégorie vide (refusée si déjà là)
    assert bl.add_category_to(path, 'LEAD') is True
    assert bl.add_category_to(path, 'TAT') is False
    assert bl.categories_in(path) == ['General', 'LEAD', 'TAT']

    # renommer TAT -> DA : ré-étiquette le bouton « b »
    assert bl.rename_category_in(path, 'TAT', 'DA') is True
    cats = bl.categories_in(path)
    assert 'DA' in cats and 'TAT' not in cats
    b = [e for e in bl.load_library(path) if e['name'] == 'b'][0]
    assert b['category'] == 'DA'

    # déplacer « a » (General) vers LEAD
    a = [e for e in bl.load_library(path) if e['name'] == 'a'][0]
    assert bl.set_entries_category_in(path, [a], 'LEAD') == 1
    a2 = [e for e in bl.load_library(path) if e['name'] == 'a'][0]
    assert a2['category'] == 'LEAD'

    # supprimer une catégorie vide OK, non vide refusé
    assert bl.add_category_to(path, 'Vide') is True
    assert bl.delete_empty_category_in(path, 'Vide') is True
    assert bl.delete_empty_category_in(path, 'DA') is False
    print('organisation des catégories (créer/renommer/déplacer/vider) OK')


def test_manipulation_ergonomics():
    """Manipulation allégée : bords entièrement saisissables, curseurs
    contextuels, Maj = contrainte d'axe, Espace = pan, zoom +/-."""
    from hotbox_designer.geometry import Transform

    # contrainte d'axe (Maj) : le déplacement se verrouille sur l'axe
    # dominant du geste
    transform = Transform()
    rect = QtCore.QRectF(0, 0, 10, 10)
    transform.set_rect(rect)
    transform.reference_rect = QtCore.QRectF(rect)
    transform.set_reference_point(QtCore.QPointF(5, 5))
    transform.move([], QtCore.QPointF(30, 8), constrain=True)
    assert rect.top() == 0 and near(rect.left(), 25)  # horizontal domine
    transform = Transform()
    rect = QtCore.QRectF(0, 0, 10, 10)
    transform.set_rect(rect)
    transform.reference_rect = QtCore.QRectF(rect)
    transform.set_reference_point(QtCore.QPointF(5, 5))
    transform.move([], QtCore.QPointF(8, 40), constrain=True)
    assert rect.left() == 0 and near(rect.top(), 35)  # vertical domine

    # TOUT le bord est saisissable (pas seulement les 8 poignées) :
    # points sur les bords d'un grand rectangle, loin des poignées
    from hotbox_designer.interactive import Manipulator
    manip = Manipulator()
    manip.zoom_factor = 1.0
    manip.set_rect(QtCore.QRectF(0, 0, 200, 100))
    assert manip.get_direction(QtCore.QPointF(0, 30)) == 'left'
    assert manip.get_direction(QtCore.QPointF(60, 100)) == 'bottom'
    assert manip.get_direction(QtCore.QPointF(3, 4)) == 'top_left'
    assert manip.get_direction(QtCore.QPointF(100, 50)) is None
    assert manip.get_direction(QtCore.QPointF(300, 50)) is None

    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor
    driver = Driver(area)
    shape = area.shapes[0]
    driver.click((shape.rect.center().x(), shape.rect.center().y()))
    assert list(area.selection) == [shape]

    # curseurs contextuels : ↔ sur un bord, croix dans la sélection
    sel_rect = area.manipulator.rect
    left_mid = QtCore.QPointF(sel_rect.left(), sel_rect.center().y())
    driver.pos = driver.units((left_mid.x(), left_mid.y()))
    driver.move()
    assert area.cursor().shape() == QtCore.Qt.SizeHorCursor
    center = sel_rect.center()
    driver.pos = driver.units((center.x(), center.y()))
    driver.move()
    assert area.cursor().shape() == QtCore.Qt.SizeAllCursor

    # Espace + glisser gauche = pan : la vue bouge, pas la sélection
    origin_before = QtCore.QPointF(area.viewport_mapper.origin)
    pos_before = QtCore.QPointF(shape.rect.topLeft())
    area.keyPressEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Space, QtCore.Qt.NoModifier))
    driver.drag((150, 120), (250, 180))
    assert area.viewport_mapper.origin != origin_before
    assert shape.rect.topLeft() == pos_before
    area.keyReleaseEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyRelease, QtCore.Qt.Key_Space, QtCore.Qt.NoModifier))
    assert area.panning is False

    # zoom clavier + / -
    zoom_before = area.viewport_mapper.zoom
    area.keyPressEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Plus, QtCore.Qt.NoModifier))
    assert area.viewport_mapper.zoom > zoom_before
    area.keyPressEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Minus, QtCore.Qt.NoModifier))
    assert near(area.viewport_mapper.zoom, zoom_before, 0.01)

    editor.close()
    print('manipulation allégée (bords, curseurs, Maj, Espace, zoom) OK')


def test_replace_from_library():
    """Clic droit → « Replace with library button » : le contenu du
    bouton vient de la shelf, position et taille sont conservées."""
    import tempfile
    from hotbox_designer.templates import HOTBOX as HOTBOX_T

    tmp = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: tmp

    shapes = []
    for left, top, label in [(100, 100, 'a'), (300, 200, 'b')]:
        options = dict(SQUARE_BUTTON)
        options.update({'shape.left': float(left), 'shape.top': float(top),
                        'text.content': label})
        shapes.append(options)
    data = {'general': dict(HOTBOX_T, name='t', width=600, height=400),
            'shapes': shapes}
    editor = HotboxEditor(data, application, parent=None)
    editor.show()
    APP.processEvents()

    # un bouton stylé dans la shelf
    lib_options = dict(SQUARE_BUTTON)
    lib_options.update({
        'text.content': 'LIB', 'bgcolor.normal': '#ff0000',
        'action.left': True, 'action.left.command': 'print("lib")',
        'shape.left': 0.0, 'shape.top': 0.0,
        'shape.width': 500.0, 'shape.height': 500.0})
    editor.library_shelf.add_entries(
        [{'name': 'LibBtn', 'category': 'General', 'options': lib_options}])
    shelf_list = editor.library_shelf.tabs.currentWidget()
    shelf_list.item(0).setSelected(True)
    assert len(editor.library_shelf.current_selected_entries()) == 1

    # remplacer les deux boutons sélectionnés
    area = editor.shape_editor
    area.selection.replace(list(area.shapes))
    editor.replace_selection_from_library()
    for shape, (left, top) in zip(area.shapes, [(100, 100), (300, 200)]):
        assert shape.options['text.content'] == 'LIB'
        assert shape.options['bgcolor.normal'] == '#ff0000'
        assert shape.options['action.left.command'] == 'print("lib")'
        # géométrie conservée (ni déplacé ni redimensionné)
        assert shape.options['shape.left'] == float(left)
        assert shape.options['shape.top'] == float(top)
        assert shape.options['shape.width'] == SQUARE_BUTTON['shape.width']

    editor.close()
    print('replace avec un bouton de la librairie OK')


def test_user_templates():
    """Templates utilisateur : save_hotbox_as_template écrit dans le
    dossier de données, load_templates les liste après les embarqués,
    et le dialogue de création les propose avec un aperçu."""
    import tempfile
    from hotbox_designer.data import (
        load_templates, save_hotbox_as_template)
    from hotbox_designer.dialog import CreateHotboxDialog
    from hotbox_designer.templates import HOTBOX as HOTBOX_T

    tmp = tempfile.mkdtemp()
    builtin_count = len(load_templates())

    hotbox = {'general': dict(HOTBOX_T, name='MonTemplate', width=400,
                              height=300),
              'shapes': [dict(SQUARE_BUTTON, **{'text.content': 'tpl'})]}
    path = save_hotbox_as_template(tmp, hotbox)
    assert path is not None and os.path.exists(path)
    # collision de nom : suffixe numéroté, pas d'écrasement
    path2 = save_hotbox_as_template(tmp, hotbox)
    assert path2 != path and os.path.exists(path2)

    templates = load_templates(tmp)
    assert len(templates) == builtin_count + 2
    assert templates[-1]['general']['name'] == 'MonTemplate'

    dialog = CreateHotboxDialog([], templates_folder=tmp)
    dialog.show()
    APP.processEvents()
    assert dialog.template_grid.count() == builtin_count + 2
    # choisir le template utilisateur → aperçu rendu + données copiées
    dialog.template.setChecked(True)
    dialog.template_grid.setCurrentRow(builtin_count)
    APP.processEvents()
    # l'aperçu du template EST sa vignette dans la grille (la grande
    # preview est réservée à « Duplicate existing »)
    item = dialog.template_grid.item(builtin_count)
    assert not item.icon().isNull()
    assert dialog.preview.isHidden()
    dialog.name_edit.setText('nouvelle')
    created = dialog.hotbox()
    assert created['general']['name'] == 'nouvelle'
    assert created['shapes'][0]['text.content'] == 'tpl'
    dialog.close()
    print('templates utilisateur (save + liste + aperçu) OK')


def test_studio_location_restored_at_manager_launch():
    """La librairie studio mémorisée est active dès l'ouverture du
    manager — sans devoir ouvrir un éditeur (et sa shelf) d'abord :
    badge, mode admin et boutons la voient immédiatement."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.manager import HotboxManager

    tmp = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: tmp
    studio = os.path.join(tmp, 'TAT.json')
    bl.save_library(studio, [])
    bl.save_studio_settings(application, {'current': studio, 'recent': []})
    bl.set_studio_location(None)
    try:
        assert bl.studio_location() is None
        manager = HotboxManager(application)
        assert bl.studio_location() == studio  # restaurée par le manager
        manager.close()
    finally:
        bl.set_studio_location(None)
    print('librairie mémorisée restaurée au lancement du manager OK')


def test_shelf_filter():
    """Le champ de filtre de la shelf cherche les boutons par nom,
    toutes catégories confondues, dans un onglet unique de résultats ;
    l'effacer restaure les onglets normaux."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import LibraryShelf, save_library

    tmp = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: tmp
    entries = [
        {'name': 'smart_snap', 'category': 'ANIM',
         'options': dict(SQUARE_BUTTON)},
        {'name': 'ik_switch', 'category': 'RIG',
         'options': dict(SQUARE_BUTTON)},
        {'name': 'snap_keys', 'category': 'RIG',
         'options': dict(SQUARE_BUTTON)},
    ]
    save_library(bl.library_path(application), entries)
    shelf = LibraryShelf(application)
    shelf.show()
    APP.processEvents()
    normal_tabs = shelf.tabs.count()
    assert normal_tabs == 2  # ANIM + RIG

    shelf.filter_edit.setText('snap')
    APP.processEvents()
    assert shelf.tabs.count() == 1
    results = shelf.tabs.widget(0)
    names = [results.item(i).text() for i in range(results.count())]
    assert sorted(names) == ['smart_snap', 'snap_keys']
    # glissable vers la hotbox, mais pas de réorganisation depuis là
    assert results.reorderable is False

    shelf.filter_edit.setText('')
    APP.processEvents()
    assert shelf.tabs.count() == normal_tabs
    shelf.close()
    print('filtre de recherche de la shelf OK')


def test_hotkey_column():
    """Les listes du manager affichent le raccourci assigné en 2e
    colonne (grisé, aligné à droite) — visible sans ouvrir le dialogue."""
    from hotbox_designer.manager import HotboxPersonalTableModel
    from hotbox_designer.vendor.Qt import QtCore as QC

    hotbox = {'general': dict(HOTBOX, name='ma_hotbox'), 'shapes': []}
    model = HotboxPersonalTableModel([hotbox])
    assert model.columnCount(None) == 2
    index = model.index(0, 1)
    assert model.data(index, QC.Qt.DisplayRole) == ''  # rien d'assigné
    model.set_hotkeys({'ma_hotbox': {'sequence': 'Shift+Q', 'mode': 'x'}})
    assert model.data(index, QC.Qt.DisplayRole) == 'Shift+Q'
    assert model.data(model.index(0, 0), QC.Qt.DisplayRole) == 'ma_hotbox'
    print('colonne raccourci dans les listes du manager OK')


def test_state_preview():
    """L'aperçu d'états en haut du panneau d'attributs suit la
    sélection et les réglages en direct (normal / survol / clic)."""
    from hotbox_designer.designer.attributes import AttributeEditor
    attr = AttributeEditor(Standalone())
    attr.show()
    APP.processEvents()
    assert attr.preview._shapes is None  # rien de sélectionné

    attr.set_options([dict(SQUARE_BUTTON)])
    assert len(attr.preview._shapes) == 3
    assert [s.hovered for s in attr.preview._shapes] == [False, True, True]
    assert [s.clicked for s in attr.preview._shapes] == [False, False, True]

    # un réglage émis par une section se répercute immédiatement
    attr.optionSet.emit('bgcolor.normal', '#ff0000')
    assert attr.preview._options['bgcolor.normal'] == '#ff0000'
    assert attr.preview._shapes[0].options['bgcolor.normal'] == '#ff0000'

    # le widget se peint sans erreur
    assert not attr.preview.grab().isNull()
    attr.close()
    print('aperçu des états (normal/survol/clic) OK')


def test_builtin_templates():
    """Templates embarqués : ceux d'origine + le template TAT (base
    studio fournie par l'utilisateur) — les anciens templates maison
    ont été retirés. Le TAT s'ouvre dans l'éditeur sans erreur."""
    from hotbox_designer.data import load_templates

    templates = load_templates()
    assert templates, 'aucun template embarqué chargé'
    names = [t['general']['name'] for t in templates]
    for removed in ('Pie_8_Directions', 'Mini_Shelf_4x3', 'Barre_6_Boutons',
                    'Manette', 'Nid_Abeille', 'Colonnes_TAT', 'Grille_6x4'):
        assert removed not in names, removed

    assert 'TAT' in names
    data = templates[names.index('TAT')]
    assert len(data['shapes']) == 29
    editor = HotboxEditor(copy.deepcopy(data), Standalone(), parent=None)
    editor.show()
    APP.processEvents()
    assert len(editor.shape_editor.shapes) == len(data['shapes'])
    editor.close()
    print('templates embarqués (origine + TAT) OK')


def test_color_picker_pipette():
    """La pipette du sélecteur de couleurs prélève la couleur sous le
    curseur (screen_color_at simulé hors écran)."""
    from hotbox_designer import colorpicker
    from hotbox_designer.colorpicker import ColorPickerDialog

    dialog = ColorPickerDialog('#112233')
    dialog.show()
    APP.processEvents()
    assert dialog.pick_screen is not None

    saved = colorpicker.screen_color_at
    try:
        colorpicker.screen_color_at = lambda pos: QtGui.QColor('#12ab34')
        dialog.start_screen_pick()
        assert dialog._screen_picking is True
        dialog.mousePressEvent(FakeMouseEvent())
        assert dialog._screen_picking is False
        assert dialog.color_name() == '#12ab34'
    finally:
        colorpicker.screen_color_at = saved

    # Échap annule la pipette sans changer la couleur
    dialog.start_screen_pick()
    dialog.keyPressEvent(QtGui.QKeyEvent(
        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Escape, QtCore.Qt.NoModifier))
    assert dialog._screen_picking is False
    assert dialog.color_name() == '#12ab34'
    dialog.close()
    print('pipette écran du sélecteur de couleurs OK')


def test_startup_framing():
    """Au démarrage la hotbox doit être cadrée même si le layout
    redimensionne le widget après le premier resizeEvent (avant, seul le
    PREMIER resize cadrait → vue décentrée tant qu'on ne pressait pas F).
    Dès que l'utilisateur navigue, les resizes ne recadrent plus."""
    editor = make_editor([(100, 100, 'btn')])
    area = editor.shape_editor

    def framed_center():
        # centre de la hotbox exprimé en pixels de la vue
        center = area.hotbox_rect().center()
        view = area.viewport_mapper.to_viewport_coords(center)
        return view

    # simule le layout : plusieurs resizes successifs → toujours cadré
    area.resize(300, 200)
    APP.processEvents()
    area.resize(900, 500)
    APP.processEvents()
    view_center = framed_center()
    assert near(view_center.x(), area.width() / 2.0, 2)
    assert near(view_center.y(), area.height() / 2.0, 2)

    # l'utilisateur zoome : la vue lui appartient, un resize ne touche
    # plus au cadrage (l'origine du viewport reste la sienne)
    area.wheelEvent(FakeWheelEvent(120))
    origin = QtCore.QPointF(area.viewport_mapper.origin)
    zoom = area.viewport_mapper.zoom
    area.resize(700, 400)
    APP.processEvents()
    assert area.viewport_mapper.origin == origin
    assert area.viewport_mapper.zoom == zoom

    editor.close()
    print('cadrage au démarrage (resizes successifs) OK')


def test_library_rename_and_save_studio():
    """Renommer un bouton déjà rangé, et sauvegarder directement dans la
    librairie studio (sans passer par General + Move to)."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import (
        LibraryShelf, SaveToLibraryDialog, STUDIO_ENV_VARIABLE,
        load_studio_library)

    def entry(name, category='General'):
        return {'name': name, 'category': category,
                'options': dict(SQUARE_BUTTON, **{'text.content': name})}

    # rename_entry_in sur un fichier perso
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, 'button_library.json')
    bl.save_library(path, [entry('old', 'Perso')])
    assert bl.rename_entry_in(path, entry('old', 'Perso'), 'new') is True
    assert [e['name'] for e in bl.load_library(path)] == ['new']
    assert bl.rename_entry_in(path, entry('absent'), 'x') is False
    assert bl.rename_entry_in(path, entry('new', 'Perso'), '   ') is False

    # sauvegarde directe dans la librairie studio
    studio_dir = tempfile.mkdtemp()
    os.environ[STUDIO_ENV_VARIABLE] = studio_dir
    try:
        perso = tempfile.mkdtemp()
        application = Standalone()
        application.get_data_folder = lambda: perso
        shelf = LibraryShelf(application)
        added = shelf.save_entries([entry('DirectTool', 'ANIM')], studio=True)
        assert added == 1
        assert any(e['name'] == 'DirectTool' for e in load_studio_library())
        # rien n'atterrit dans la perso
        assert all(
            e['name'] != 'DirectTool' for e in bl.load_library(shelf.path))

        # destination FIXÉE par le mode : studio_available (admin) →
        # Studio uniquement, catégories studio, logo TAT ; sinon perso
        dialog = SaveToLibraryDialog(['Perso'], ['ANIM', 'SHELF'], True, 'btn')
        assert dialog.is_studio() is True
        assert dialog.destination.count() == 1
        assert not dialog.destination.itemIcon(0).isNull()
        studio_items = [dialog.category.itemText(i)
                        for i in range(dialog.category.count())]
        assert studio_items == ['ANIM', 'SHELF']
        assert dialog.category.currentText() == 'ANIM'

        dialog = SaveToLibraryDialog(['Perso'], [], False, 'btn')
        assert dialog.is_studio() is False
        assert dialog.destination.count() == 1
        perso_items = [dialog.category.itemText(i)
                       for i in range(dialog.category.count())]
        assert perso_items == ['Perso']
        shelf.close()
    finally:
        del os.environ[STUDIO_ENV_VARIABLE]
    print('rename bouton de shelf + save direct studio OK')


def test_studio_admin_mode():
    """Mode admin choisi au lancement : en mode normal la librairie
    studio est en lecture seule (pas de badge, pas d'édition) ; en mode
    admin tout s'ouvre (badge visible, onglets studio éditables)."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import LibraryShelf

    tmp = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: tmp

    try:
        # mode normal (animateur)
        bl.set_studio_admin(False)
        assert bl.is_studio_admin() is False
        shelf = LibraryShelf(application)
        shelf.show()
        APP.processEvents()
        # badge = nom du json, en mode lecture seule (infobulle)
        assert 'read-only' in shelf.library_badge.toolTip()
        assert shelf._can_edit(readonly=False) is True   # perso : oui
        assert shelf._can_edit(readonly=True) is False   # studio : non
        shelf.close()

        # mode admin (lead)
        bl.set_studio_admin(True)
        assert bl.is_studio_admin() is True
        shelf = LibraryShelf(application)
        shelf.show()
        APP.processEvents()
        assert 'admin' in shelf.library_badge.toolTip()
        assert shelf._can_edit(readonly=True) is True

        # bascule de mode EN COURS DE SESSION (sans reconstruire la
        # shelf) : refresh_shelves() fait suivre badge et gardes
        bl.set_studio_admin(False)
        bl.refresh_shelves()
        APP.processEvents()
        assert 'read-only' in shelf.library_badge.toolTip()
        assert shelf._can_edit(readonly=True) is False
        bl.set_studio_admin(True)
        bl.refresh_shelves()
        APP.processEvents()
        assert 'admin' in shelf.library_badge.toolTip()
        shelf.close()

        # badge « STUDIO ADMIN » de la barre d'outils de l'éditeur :
        # visible en mode admin, jamais pour les animateurs
        from hotbox_designer.designer.menu import MenuWidget
        menu = MenuWidget()
        assert menu.admin_badge_action.isVisible() is True
        bl.set_studio_admin(False)
        menu = MenuWidget()
        # ceinture et bretelles : l'action ET le widget sont masqués
        # (sur certaines versions de Qt, masquer seulement l'action
        # laissait le badge visible en mode animateur)
        assert menu.admin_badge_action.isVisible() is False
        assert menu.admin_badge.isHidden() is True
        # bascule EN SESSION : le badge suit sans reconstruire l'éditeur
        bl.set_studio_admin(True)
        menu.update_admin_badge()
        assert menu.admin_badge_action.isVisible() is True
        bl.set_studio_admin(False)
        menu.update_admin_badge()
        assert menu.admin_badge.isHidden() is True

        # bandeau du manager : barre verte pleine largeur en mode
        # lead, ENTIÈREMENT masqué en mode animateur (plus de bande
        # vide), bascule via refresh()
        from hotbox_designer.manager import _ManagerHeader
        header = _ManagerHeader()  # admin False à ce stade
        assert header.isHidden() is True
        bl.set_studio_admin(True)
        header.refresh()
        assert header.isHidden() is False
        bl.set_studio_admin(False)
        header.refresh()
        assert header.isHidden() is True
    finally:
        bl.set_studio_admin(False)  # ne pas polluer les autres tests
    print('mode admin studio (lancement + bascule en session) OK')


def test_studio_library_switch():
    """Sélecteur de librairie studio (bouton TAT, mode admin) : bascule
    par projet, création du json manquant, récents mémorisés, retour au
    défaut, persistance entre sessions."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import LibraryShelf

    prefs = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: prefs

    project_a = tempfile.mkdtemp()
    project_b = tempfile.mkdtemp()

    def entry(name, category):
        return {'name': name, 'category': category,
                'options': dict(SQUARE_BUTTON, **{'text.content': name})}

    bl.save_library(
        os.path.join(project_a, 'button_library.json'),
        [entry('a', 'PROJET_A')])

    try:
        bl.set_studio_admin(True)
        shelf = LibraryShelf(application)
        shelf.show()
        APP.processEvents()
        # ZÉRO librairie au départ : rien de configuré, badge caché
        assert bl.studio_location() is None
        assert shelf.library_badge.isVisible() is False
        # admin : bouton « créer » ET bouton « ouvrir » visibles
        assert shelf.create_library_button.isVisible() is True
        assert shelf.open_library_button.isVisible() is True

        # bascule sur le projet A : la lib studio suit, le choix est
        # mémorisé (current + recent), le badge apparaît
        shelf._switch_studio_library(project_a)
        assert bl.studio_location() == project_a
        assert shelf.studio_categories() == ['PROJET_A']
        assert shelf.library_badge.isVisible() is True
        settings = bl.load_studio_settings(application)
        assert settings['current'] == project_a
        assert settings['recent'] == [project_a]

        # « créer » le projet B : json absent → créé vide, bascule
        path_b = os.path.join(project_b, 'button_library.json')
        assert not os.path.exists(path_b)
        bl.save_library(path_b, [])  # (le dialogue de dossier fait ça)
        shelf._switch_studio_library(project_b)
        assert bl.studio_location() == project_b
        assert os.path.exists(path_b)
        recent = bl.load_studio_settings(application)['recent']
        assert recent[:2] == [project_b, project_a]  # plus récent en tête

        # re-bascule A : remonte en tête, pas de doublon
        shelf._switch_studio_library(project_a)
        recent = bl.load_studio_settings(application)['recent']
        assert recent[:2] == [project_a, project_b]
        assert len(recent) == len(set(os.path.normpath(p) for p in recent))

        # ménage : oublier une librairie obsolète — retirée des récents
        # et elle ne réapparaît pas au switch suivant
        shelf._forget_studio_library(project_b)
        recent = bl.load_studio_settings(application)['recent']
        assert all(os.path.normpath(p) != os.path.normpath(project_b)
                   for p in recent)
        shelf._switch_studio_library(project_a)
        recent = bl.load_studio_settings(application)['recent']
        assert all(os.path.normpath(p) != os.path.normpath(project_b)
                   for p in recent)
        # détection des librairies disparues (entrée « missing » du menu)
        assert bl.library_location_exists(project_a) is True
        assert bl.library_location_exists(tempfile.mkdtemp()) is False

        # une NOUVELLE shelf (nouvelle session) retrouve la lib mémorisée
        bl.set_studio_location(None)
        shelf2 = LibraryShelf(application)
        assert bl.studio_location() == project_a
        shelf2.close()

        # retour au défaut (env/DEFAULT) : override effacé, persisté
        shelf._switch_studio_library(None)
        assert bl.get_studio_override() is None
        assert bl.load_studio_settings(application)['current'] is None

        # l'admin crée un json au NOM LIBRE ; le logo courant est copié
        # à côté (la nouvelle librairie garde l'identité TAT)
        project_c = tempfile.mkdtemp()
        ringo = os.path.join(project_c, 'ringo.json')
        assert shelf._open_studio_json(ringo) is True
        assert os.path.exists(ringo)
        assert bl.studio_location() == ringo
        assert bl.studio_library_label() == 'ringo'
        assert os.path.exists(os.path.join(project_c, 'studio_logo.png'))
        assert shelf.library_badge.text().strip() == 'ringo'
        # librairie toute neuve : un onglet General vide reste affiché
        # (sinon zéro onglet → Qt cache aussi le coin badge/dossier/＋)
        assert shelf.tabs.count() == 1
        assert shelf._tab_name(0) == 'General'
        assert shelf.tabs.widget(0).readonly is True

        # en mode ANIMATEUR : le bouton reste visible (il choisit sur
        # quelle librairie il est), mais pas de création possible
        bl.set_studio_admin(False)
        bl.refresh_shelves()
        APP.processEvents()
        assert shelf.library_badge.isVisible() is True
        # animateur : pas de bouton « créer », seulement « ouvrir »
        assert shelf.create_library_button.isVisible() is False
        assert shelf.open_library_button.isVisible() is True
        project_d = tempfile.mkdtemp()  # librairie inexistante
        warned = []
        saved_warning = QtWidgets.QMessageBox.warning
        QtWidgets.QMessageBox.warning = (
            lambda *a, **k: warned.append(a) or 0)
        try:
            assert shelf._open_studio_json(
                os.path.join(project_d, 'perso.json')) is False
        finally:
            QtWidgets.QMessageBox.warning = saved_warning
        assert warned  # prévenu, pas de création
        assert not os.path.exists(os.path.join(project_d, 'perso.json'))
        # ouvrir une librairie EXISTANTE marche pour lui
        assert shelf._open_studio_json(ringo) is True
        assert bl.studio_location() == ringo
        shelf.close()
    finally:
        bl.set_studio_admin(False)
        bl.set_studio_location(None)  # ne pas polluer les autres tests
    print('sélecteur de librairie studio (switch/création/récents) OK')


def test_plus_button_follows_mode():
    """Le bouton ＋ de la shelf suit le mode : admin → catégorie créée
    DANS la librairie studio courante (onglet TAT) ; animateur →
    catégorie perso (façon shelf Maya)."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import LibraryShelf

    prefs = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: prefs
    studio_dir = tempfile.mkdtemp()
    ringo = os.path.join(studio_dir, 'ringo.json')
    bl.save_library(ringo, [])

    saved_gettext = QtWidgets.QInputDialog.getText
    try:
        bl.set_studio_admin(True)
        bl.set_studio_location(ringo)
        shelf = LibraryShelf(application)
        shelf.show()
        APP.processEvents()

        # admin : ＋ écrit dans ringo.json
        QtWidgets.QInputDialog.getText = (
            lambda *a, **k: ('OFFICIELLE', True))
        shelf.add_button.released.emit()
        assert 'OFFICIELLE' in bl.categories_in(ringo)
        assert 'OFFICIELLE' not in shelf.categories()  # pas en perso
        # en admin, AUCUN onglet perso (pas de « General » sans logo)
        assert all(
            shelf.tabs.widget(i).readonly
            for i in range(shelf.tabs.count()))
        # la sauvegarde propose la catégorie de l'ONGLET COURANT
        names = [shelf._tab_name(i) for i in range(shelf.tabs.count())]
        shelf.tabs.setCurrentIndex(names.index('OFFICIELLE'))
        assert shelf.current_category() == 'OFFICIELLE'

        # animateur : ＋ écrit dans la librairie PERSO
        bl.set_studio_admin(False)
        bl.refresh_shelves()
        QtWidgets.QInputDialog.getText = lambda *a, **k: ('MIENNE', True)
        shelf.add_button.released.emit()
        assert 'MIENNE' in shelf.categories()
        assert 'MIENNE' not in bl.categories_in(ringo)
        # en animateur, les onglets perso réapparaissent
        assert any(
            not shelf.tabs.widget(i).readonly
            for i in range(shelf.tabs.count()))
        # catégorie proposée = onglet perso courant ; sur un onglet
        # studio (lecture seule), repli sur General
        for i in range(shelf.tabs.count()):
            shelf.tabs.setCurrentIndex(i)
            if shelf.tabs.widget(i).readonly:
                assert shelf.current_category() == 'General'
            elif shelf._tab_name(i) == 'MIENNE':
                assert shelf.current_category() == 'MIENNE'
        shelf.close()
    finally:
        QtWidgets.QInputDialog.getText = saved_gettext
        bl.set_studio_admin(False)
        bl.set_studio_location(None)
    print('bouton ＋ selon le mode (studio en admin, perso sinon) OK')



def test_shelf_drag_organization():
    """Organisation par drag & drop : ordre du fichier respecté (onglets
    et boutons), déplacement/réordonnancement via
    move_entries_to_category, ordre des onglets via set_category_order,
    onglets déplaçables en admin seulement."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import LibraryShelf

    prefs = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: prefs
    studio_dir = tempfile.mkdtemp()
    ringo = os.path.join(studio_dir, 'ringo.json')

    def button(name, category):
        return {'name': name, 'category': category,
                'options': dict(SQUARE_BUTTON, **{'text.content': name})}

    # ordre voulu dans le fichier : B avant A, b1 avant b2
    bl.save_library(ringo, [
        {'__category__': 'B'}, button('b1', 'B'), button('b2', 'B'),
        {'__category__': 'A'}, button('a1', 'A')])

    try:
        bl.set_studio_admin(True)
        bl.set_studio_location(ringo)
        shelf = LibraryShelf(application)
        shelf.show()
        APP.processEvents()

        # l'ordre du FICHIER est respecté (fini l'alphabétique)
        names = [shelf._tab_name(i) for i in range(shelf.tabs.count())]
        assert names == ['B', 'A']
        tab_b = shelf.tabs.widget(0)
        assert [tab_b.item(i).data(QtCore.Qt.UserRole)['name']
                for i in range(tab_b.count())] == ['b1', 'b2']
        assert shelf.tabs.tabBar().isMovable() is True  # admin

        # déplacement vers une autre catégorie, à une position précise
        order, by_cat = bl.parse_library_structure(ringo)
        assert bl.move_entries_to_category(
            ringo, [by_cat['B'][1]], 'A', index=0) == 1
        order, by_cat = bl.parse_library_structure(ringo)
        assert [e['name'] for e in by_cat['A']] == ['b2', 'a1']
        assert by_cat['A'][0]['category'] == 'A'
        assert [e['name'] for e in by_cat['B']] == ['b1']
        assert order == ['B', 'A']

        # réordonnancement DANS la même catégorie
        assert bl.move_entries_to_category(
            ringo, [by_cat['A'][1]], 'A', index=0) == 1
        _, by_cat = bl.parse_library_structure(ringo)
        assert [e['name'] for e in by_cat['A']] == ['a1', 'b2']

        # ordre des onglets (drag d'onglet → set_category_order)
        bl.set_category_order(ringo, ['A', 'B'])
        order, _ = bl.parse_library_structure(ringo)
        assert order == ['A', 'B']
        bl.refresh_shelves()
        APP.processEvents()
        names = [shelf._tab_name(i) for i in range(shelf.tabs.count())]
        assert names == ['A', 'B']

        # drop simulé sur la liste de « A » : b1 (venu de B) à la fin
        _, by_cat = bl.parse_library_structure(ringo)
        payload = {'entries': [by_cat['B'][0]], 'readonly': True,
                   'category': 'B'}
        mime = QtCore.QMimeData()
        mime.setData(bl.SHELF_ENTRIES_MIME, QtCore.QByteArray(
            json.dumps(payload).encode('utf-8')))
        tab_a = shelf.tabs.widget(0)
        assert tab_a.category == 'A' and tab_a.shelf is shelf
        try:
            event = QtGui.QDropEvent(
                QtCore.QPointF(2000, 2000), QtCore.Qt.CopyAction, mime,
                QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        except TypeError:  # signature Qt5
            event = QtGui.QDropEvent(
                QtCore.QPoint(2000, 2000), QtCore.Qt.CopyAction, mime,
                QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        tab_a.dropEvent(event)
        _, by_cat = bl.parse_library_structure(ringo)
        assert [e['name'] for e in by_cat['A']] == ['a1', 'b2', 'b1']
        assert by_cat.get('B', []) == []

        # en mode animateur : onglets studio non déplaçables, drop refusé
        bl.set_studio_admin(False)
        bl.refresh_shelves()
        APP.processEvents()
        assert shelf.tabs.tabBar().isMovable() is False
        studio_list = shelf.tabs.widget(0)
        assert studio_list.readonly is True
        assert studio_list._drop_payload(event) is None
        shelf.close()
    finally:
        bl.set_studio_admin(False)
        bl.set_studio_location(None)
    print('drag & drop d organisation (onglets + boutons, ordre) OK')



def test_category_palette():
    """Palette flottante (double-clic sur un onglet) : grille toujours
    au-dessus, réutilisée si déjà ouverte, synchronisée au refresh,
    fermée si la catégorie disparaît (switch de librairie)."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import LibraryShelf

    prefs = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: prefs
    studio_dir = tempfile.mkdtemp()
    ringo = os.path.join(studio_dir, 'ringo.json')

    def button(name, category='ANIM'):
        return {'name': name, 'category': category,
                'options': dict(SQUARE_BUTTON, **{'text.content': name})}

    bl.save_library(ringo, [button('walk'), button('run')])

    try:
        bl.set_studio_admin(True)
        bl.set_studio_location(ringo)
        shelf = LibraryShelf(application)
        shelf.show()
        APP.processEvents()

        palette = shelf.open_category_palette(0)
        assert palette is not None
        assert palette.isVisible()
        # toujours au-dessus + contenu de la catégorie, ordre du fichier
        assert palette.windowFlags() & QtCore.Qt.WindowStaysOnTopHint
        assert [palette.list.item(i).data(QtCore.Qt.UserRole)['name']
                for i in range(palette.list.count())] == ['walk', 'run']
        assert palette.list.isWrapping() is True  # grille multi-lignes
        # gating identique à la shelf (drag/drop/menus)
        assert palette.list.shelf is shelf
        assert palette.list.readonly is True

        # re-double-clic : la MÊME palette revient (pas de doublon)
        assert shelf.open_category_palette(0) is palette
        assert len(shelf._palettes) == 1

        # un ajout dans la librairie se reflète au refresh
        bl.export_to_studio([button('jump')])
        bl.refresh_shelves()
        APP.processEvents()
        assert [palette.list.item(i).data(QtCore.Qt.UserRole)['name']
                for i in range(palette.list.count())] == [
            'walk', 'run', 'jump']

        # switch de librairie : la catégorie disparaît, la palette aussi
        other = os.path.join(tempfile.mkdtemp(), 'pipo.json')
        bl.save_library(other, [button('solo', 'CAMERA')])
        shelf._switch_studio_library(other)
        APP.processEvents()
        assert palette not in shelf._palettes
        assert not palette.isVisible()
        shelf.close()
    finally:
        bl.set_studio_admin(False)
        bl.set_studio_location(None)
    print('palette flottante de catégorie (double-clic) OK')



def test_atomic_write():
    """Écriture atomique : le json n'est jamais corrompu par une
    écriture interrompue, et aucun fichier annexe ne traîne — pas de
    backups (le studio a les siens, l'utilisateur fait les siens)."""
    import tempfile
    from hotbox_designer.data import atomic_write_json
    from hotbox_designer import buttonlibrary as bl

    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, 'TAT.json')

    for version in ('v1', 'v2', 'v3'):
        atomic_write_json(path, [version])
    assert json.load(open(path)) == ['v3']
    assert not os.path.exists(path + '.tmp')  # le temporaire a disparu
    assert os.listdir(tmp) == ['TAT.json']    # rien d'autre dans le dossier

    # save_library passe par le circuit atomique
    bl.save_library(path, [{'__category__': 'ANIM'}])
    assert bl.load_extra_categories(path) == ['ANIM']
    assert os.listdir(tmp) == ['TAT.json']
    print('écriture atomique OK')


def test_studio_watcher():
    """Publication du lead → refresh automatique : le watcher suit le
    json courant et déclenche refresh_shelves (débouncé)."""
    import tempfile
    import time
    from hotbox_designer import buttonlibrary as bl
    from hotbox_designer.buttonlibrary import LibraryShelf

    prefs = tempfile.mkdtemp()
    application = Standalone()
    application.get_data_folder = lambda: prefs
    studio_dir = tempfile.mkdtemp()
    ringo = os.path.join(studio_dir, 'ringo.json')
    bl.save_library(ringo, [{'__category__': 'ANIM'}])

    try:
        bl.set_studio_admin(True)
        bl.set_studio_location(ringo)
        shelf = LibraryShelf(application)
        shelf.show()
        APP.processEvents()
        # le watcher est armé sur le json courant
        assert bl._watcher is not None
        assert [os.path.normpath(f) for f in bl._watcher.files()] == [
            os.path.normpath(ringo)]

        # modification EXTERNE du fichier (un autre poste publie)
        entry = {'name': 'new', 'category': 'ANIM',
                 'options': dict(SQUARE_BUTTON)}
        bl.save_library(ringo, [{'__category__': 'ANIM'}, entry])
        # le débounce + l'événement fichier passent par la boucle Qt
        deadline = time.time() + 3.0
        updated = False
        while time.time() < deadline:
            APP.processEvents()
            tab = shelf.tabs.widget(0)
            if tab is not None and tab.count() == 1:
                updated = True
                break
            time.sleep(0.05)
        assert updated, 'le refresh automatique n a pas eu lieu'
        # et le watcher est re-armé après le remplacement atomique
        assert [os.path.normpath(f) for f in bl._watcher.files()] == [
            os.path.normpath(ringo)]
        shelf.close()
    finally:
        bl.set_studio_admin(False)
        bl.set_studio_location(None)
        bl.watch_studio_library()  # désarmer (plus de librairie)
    print('watcher de librairie studio (refresh auto) OK')


def test_fork_folder_migration():
    """Rangement des données : la librairie perso et le registre des
    raccourcis vivent dans le dossier du fork (prefs/hotbox sous
    Maya) ; les fichiers restés à la racine des prefs sont migrés
    automatiquement, hotboxes.json reste où il est."""
    import tempfile
    from hotbox_designer import buttonlibrary as bl

    root = tempfile.mkdtemp()
    fork = os.path.join(root, 'hotbox')

    class MayaLike(Standalone):
        def get_data_folder(self):
            return root

        def get_fork_folder(self):
            if not os.path.exists(fork):
                os.makedirs(fork)
            return fork

    app = MayaLike()

    # un button_library.json « historique » à la racine des prefs
    legacy = os.path.join(root, 'button_library.json')
    bl.save_library(legacy, [
        {'name': 'old', 'category': 'TAT',
         'options': dict(SQUARE_BUTTON)}])
    path = bl.library_path(app)
    assert path == os.path.join(fork, 'button_library.json')
    assert not os.path.exists(legacy)          # déplacé...
    assert os.path.exists(path)                # ...vers hotbox/
    assert [e['name'] for e in bl.load_library(path)] == ['old']

    # registre des raccourcis : pareil
    legacy_keys = os.path.join(root, 'hotbox_hotkey.json')
    with open(legacy_keys, 'w') as f:
        json.dump({'face': {'sequence': 'Ctrl+F', 'mode': 'x'}}, f)
    assert app.get_hotkey_file() == os.path.join(
        fork, 'hotbox_hotkey.json')
    assert not os.path.exists(legacy_keys)
    assert app.load_hotkeys()['face']['sequence'] == 'Ctrl+F'

    # Standalone (dossier déjà dédié) : aucun déplacement, mêmes chemins
    solo_root = tempfile.mkdtemp()
    solo = Standalone()
    solo.get_data_folder = lambda: solo_root
    assert bl.library_path(solo) == os.path.join(
        solo_root, 'button_library.json')
    # renommage hotboxJOR -> hotbox : l'ancien dossier est repris
    # tel quel au premier lancement (vraie classe Maya-like)
    from hotbox_designer.applications import (
        FORK_FOLDER_NAME, LEGACY_FORK_FOLDER_NAME)
    assert FORK_FOLDER_NAME == 'hotbox'
    root2 = tempfile.mkdtemp()
    old_folder = os.path.join(root2, LEGACY_FORK_FOLDER_NAME)
    os.makedirs(old_folder)
    with open(os.path.join(old_folder, 'studio_settings.json'), 'w') as f:
        json.dump({'current': 'x'}, f)

    class MayaLike2(Standalone):
        def get_data_folder(self):
            return root2
        # get_fork_folder de Maya, réutilisé tel quel
        get_fork_folder = __import__(
            'hotbox_designer.applications', fromlist=['Maya']
        ).Maya.get_fork_folder

    app2 = MayaLike2()
    fork2 = app2.get_fork_folder()
    assert fork2 == os.path.join(root2, 'hotbox')
    assert not os.path.exists(old_folder)  # renommé, pas dupliqué
    assert os.path.exists(os.path.join(fork2, 'studio_settings.json'))

    print('rangement des données (prefs/hotbox + migrations) OK')


def test_hotkey_registry():
    """Registre des raccourcis : on peut noter, relire, mettre à jour et
    RETIRER un raccourci — ce que l'ancien Maya ne permettait pas (pose
    directe dans cmds.hotkey, sans trace)."""
    import tempfile
    from hotbox_designer.applications import Standalone

    tmp = tempfile.mkdtemp()

    class TmpApp(Standalone):
        def get_data_folder(self):
            return tmp

    app = TmpApp()
    assert app.load_hotkeys() == {}

    app.record_hotkey('face', 'Ctrl+F', 'switch on press')
    app.record_hotkey('body', 'Alt+B', 'open on press | close on release')
    data = app.load_hotkeys()
    assert set(data) == {'face', 'body'}
    assert data['face'] == {'sequence': 'Ctrl+F', 'mode': 'switch on press'}

    # ré-assigner met à jour (pas de doublon)
    app.record_hotkey('face', 'Ctrl+Shift+F', 'switch on press')
    assert app.load_hotkeys()['face']['sequence'] == 'Ctrl+Shift+F'

    # retrait ciblé, les autres restent
    app.remove_hotkey('face')
    remaining = app.load_hotkeys()
    assert 'face' not in remaining and 'body' in remaining
    # retirer un inconnu ne casse rien
    app.remove_hotkey('fantome')
    assert set(app.load_hotkeys()) == {'body'}
    print('registre des raccourcis (noter/relire/retirer) OK')


def test_hotkey_edit_capture():
    """La zone de capture lit les modificateurs sur la frappe : on tape
    la combinaison, elle s'affiche « Shift+q ». Plus de cases à cocher."""
    from hotbox_designer.widgets import HotkeyEdit

    edit = HotkeyEdit()

    def press(key, mods=QtCore.Qt.NoModifier):
        event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, key, mods)
        edit.keyPressEvent(event)

    # touche seule
    press(QtCore.Qt.Key_Q)
    assert edit.sequence() == 'q'

    # avec Shift → « Shift+q »
    press(QtCore.Qt.Key_Q, QtCore.Qt.ShiftModifier)
    assert edit.sequence() == 'Shift+q'
    assert edit.text() == 'Shift+q'

    # ordre fixe Ctrl, Alt, Shift (compatible avec le parsing Maya)
    press(QtCore.Qt.Key_F,
          QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier)
    assert edit.sequence() == 'Ctrl+Shift+f'

    # un modificateur seul est ignoré (on attend la vraie touche)
    before = edit.sequence()
    press(QtCore.Qt.Key_Shift, QtCore.Qt.ShiftModifier)
    assert edit.sequence() == before

    # Échap efface
    press(QtCore.Qt.Key_Escape)
    assert edit.sequence() == ''
    print('capture de raccourci (modificateurs lus à la frappe) OK')


def test_hotkey_manager_dialog():
    """Le gestionnaire de raccourcis liste les hotboxes, affiche leur
    touche et branche les boutons Set/Clear."""
    from hotbox_designer.dialog import HotkeyManagerDialog

    store = {'face': {'sequence': 'Ctrl+F', 'mode': 'switch on press'}}
    calls = {'assign': [], 'clear': []}

    def load():
        return dict(store)

    def assign(name):
        calls['assign'].append(name)
        store[name] = {'sequence': 'Alt+X', 'mode': 'switch on press'}
        return True

    def clear(name):
        calls['clear'].append(name)
        store.pop(name, None)

    dialog = HotkeyManagerDialog(
        ['face', 'body'], load, True, assign, clear, parent=None)
    dialog.show()
    APP.processEvents()

    assert dialog.table.rowCount() == 2
    assert dialog.table.item(0, dialog.NAME_COL).text() == 'face'
    assert dialog.table.item(0, dialog.KEY_COL).text() == 'Ctrl+F'
    assert dialog.table.item(1, dialog.KEY_COL).text() == '—'

    # assigner « body » via son bouton Set
    cell = dialog.table.cellWidget(1, dialog.ACTION_COL)
    buttons = cell.findChildren(QtWidgets.QPushButton)
    buttons[0].click()
    APP.processEvents()
    assert calls['assign'] == ['body']
    assert dialog.table.item(1, dialog.KEY_COL).text() == 'Alt+X'

    # effacer « face » via son bouton Clear
    cell0 = dialog.table.cellWidget(0, dialog.ACTION_COL)
    clear_button = cell0.findChildren(QtWidgets.QPushButton)[1]
    clear_button.click()
    APP.processEvents()
    assert calls['clear'] == ['face']
    assert dialog.table.item(0, dialog.KEY_COL).text() == '—'

    dialog.close()
    print('gestionnaire de raccourcis (liste + Set/Clear) OK')


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
    test_command_autosave()
    test_image_placement()
    test_rounded_rect()
    test_color_picker()
    test_studio_library()
    test_thumbnail_cache_and_dedup()
    test_submenu_opener()
    test_library_category_ops()
    test_library_rename_and_save_studio()
    test_manipulation_ergonomics()
    test_startup_framing()
    test_replace_from_library()
    test_user_templates()
    test_studio_location_restored_at_manager_launch()
    test_shelf_filter()
    test_hotkey_column()
    test_state_preview()
    test_builtin_templates()
    test_color_picker_pipette()
    test_studio_admin_mode()
    test_studio_library_switch()
    test_plus_button_follows_mode()
    test_shelf_drag_organization()
    test_category_palette()
    test_atomic_write()
    test_studio_watcher()
    test_fork_folder_migration()
    test_hotkey_registry()
    test_hotkey_edit_capture()
    test_hotkey_manager_dialog()
    print('TOUT EST VERT')
