"""Alignement et distribution des shapes sélectionnées.

Adapté de dwpicker (DreamWall Animation, licence MIT), ramené au Shape
de hotbox_designer : le rect est la seule géométrie, on resynchronise
options et image après chaque déplacement.
"""
import math

from hotbox_designer.vendor.Qt import QtCore
from hotbox_designer.geometry import split_line


def align_shapes(shapes, direction):
    shapes = list(shapes)
    if len(shapes) < 2:
        return False
    _direction_matches[direction](shapes)
    _synchronize(shapes)
    return True


def arrange_shapes(shapes, direction):
    shapes = list(shapes)
    if len(shapes) < 3:
        return False
    if direction == 'horizontal':
        arrange_horizontal(shapes)
    else:
        arrange_vertical(shapes)
    _synchronize(shapes)
    return True


def _synchronize(shapes):
    for shape in shapes:
        shape.synchronize_rect()
        shape.synchronize_image()


def arrange_radial(shapes, center=None, radius=None, start_angle=-90.0):
    """Répartit les centres des shapes en cercle autour d'un point,
    façon marking menu. center = QPointF (sinon barycentre) ; radius en
    unités (sinon déduit de l'étalement). start_angle en degrés,
    -90 = premier bouton en haut ; sens horaire."""
    shapes = list(shapes)
    if len(shapes) < 2:
        return False
    if center is None:
        cx = sum(s.rect.center().x() for s in shapes) / len(shapes)
        cy = sum(s.rect.center().y() for s in shapes) / len(shapes)
        center = QtCore.QPointF(cx, cy)
    if radius is None:
        # rayon = de quoi ne pas chevaucher, basé sur la plus grosse
        # shape et le nombre de boutons
        max_dim = max(
            max(s.rect.width(), s.rect.height()) for s in shapes)
        radius = max(max_dim * 1.2, max_dim * len(shapes) / (2 * math.pi))
    for index, shape in enumerate(shapes):
        angle = math.radians(start_angle + 360.0 * index / len(shapes))
        point = QtCore.QPointF(
            center.x() + radius * math.cos(angle),
            center.y() + radius * math.sin(angle))
        shape.rect.moveCenter(point)
    _synchronize(shapes)
    return True


def align_left(shapes):
    left = min(shape.rect.left() for shape in shapes)
    for shape in shapes:
        shape.rect.moveLeft(left)


def align_h_center(shapes):
    x = sum(shape.rect.center().x() for shape in shapes) / len(shapes)
    for shape in shapes:
        shape.rect.moveCenter(
            QtCore.QPointF(x, shape.rect.center().y()))


def align_right(shapes):
    right = max(shape.rect.right() for shape in shapes)
    for shape in shapes:
        shape.rect.moveRight(right)


def align_top(shapes):
    top = min(shape.rect.top() for shape in shapes)
    for shape in shapes:
        shape.rect.moveTop(top)


def align_v_center(shapes):
    y = sum(shape.rect.center().y() for shape in shapes) / len(shapes)
    for shape in shapes:
        shape.rect.moveCenter(
            QtCore.QPointF(shape.rect.center().x(), y))


def align_bottom(shapes):
    bottom = max(shape.rect.bottom() for shape in shapes)
    for shape in shapes:
        shape.rect.moveBottom(bottom)


def arrange_horizontal(shapes):
    """Répartit les centres régulièrement entre la shape la plus à
    gauche et la plus à droite."""
    shapes = sorted(shapes, key=lambda s: s.rect.center().x())
    centers = split_line(
        point1=shapes[0].rect.center(),
        point2=shapes[-1].rect.center(),
        step_number=len(shapes))
    for shape, center in zip(shapes, centers):
        shape.rect.moveCenter(
            QtCore.QPointF(center.x(), shape.rect.center().y()))


def arrange_vertical(shapes):
    shapes = sorted(shapes, key=lambda s: s.rect.center().y())
    centers = split_line(
        point1=shapes[0].rect.center(),
        point2=shapes[-1].rect.center(),
        step_number=len(shapes))
    for shape, center in zip(shapes, centers):
        shape.rect.moveCenter(
            QtCore.QPointF(shape.rect.center().x(), center.y()))


_direction_matches = {
    'left': align_left,
    'h_center': align_h_center,
    'right': align_right,
    'top': align_top,
    'v_center': align_v_center,
    'bottom': align_bottom,
}
