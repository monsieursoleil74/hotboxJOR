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

from hotbox_designer.vendor.Qt import QtWidgets, QtCore

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


if __name__ == '__main__':
    test_reader_and_roundtrip()
    test_interactions()
    test_align_and_handles()
    test_cross_hotbox_copy_paste()
    print('TOUT EST VERT')
