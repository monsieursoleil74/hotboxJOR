from hotbox_designer.vendor.Qt import QtCore, QtGui

from hotbox_designer.geometry import (
    DIRECTIONS, get_topleft_rect, get_bottomleft_rect, get_topright_rect,
    get_bottomright_rect, get_left_side_rect, get_right_side_rect,
    get_top_side_rect, get_bottom_side_rect, proportional_rect)
from hotbox_designer.painting import (
    draw_selection_square, draw_manipulator, get_hovered_path, draw_shape)
from hotbox_designer.languages import execute_code


class SelectionSquare():
    def __init__(self):
        self.rect = None
        self.handeling = False

    def clicked(self, cursor):
        self.handeling = True
        self.rect = QtCore.QRectF(cursor, cursor)

    def handle(self, cursor):
        self.rect.setBottomRight(cursor)

    def release(self):
        self.handeling = False
        self.rect = None

    def draw(self, painter, zoom=1.0):
        if self.rect is None:
            return
        draw_selection_square(painter, self.rect, zoom)


class Manipulator():
    def __init__(self):
        self.rect = None
        self._is_hovered = False
        # zoom courant du viewport : les poignées gardent une taille
        # constante à l'écran (leurs rects unités sont divisés par lui)
        self.zoom_factor = 1.0

        self._tl_corner_rect = None
        self._bl_corner_rect = None
        self._tr_corner_rect = None
        self._br_corner_rect = None
        self._l_side_rect = None
        self._r_side_rect = None
        self._t_side_rect = None
        self._b_side_rect = None

        self.hovered_path = None

    def handler_rects(self):
        return [
            self._tl_corner_rect, self._bl_corner_rect, self._tr_corner_rect,
            self._br_corner_rect, self._l_side_rect, self._r_side_rect,
            self._t_side_rect, self._b_side_rect]

    # zone de saisie autour des bords du rectangle de sélection, en
    # pixels ÉCRAN (convertie en unités selon le zoom)
    GRAB_TOLERANCE_PX = 8

    def get_direction(self, cursor):
        if self.rect is None:
            return None
        for i, rect in enumerate(self.handler_rects()):
            if rect.contains(cursor):
                return DIRECTIONS[i]
        # TOUT le bord du rectangle est saisissable, pas seulement les 8
        # petites poignées : viser un trait est bien plus rapide qu'un
        # point (coins prioritaires sur les côtés)
        tolerance = self.GRAB_TOLERANCE_PX / max(self.zoom_factor, 0.001)
        rect = self.rect
        outer = rect.adjusted(-tolerance, -tolerance, tolerance, tolerance)
        if not outer.contains(cursor):
            return None
        near_left = abs(cursor.x() - rect.left()) <= tolerance
        near_right = abs(cursor.x() - rect.right()) <= tolerance
        near_top = abs(cursor.y() - rect.top()) <= tolerance
        near_bottom = abs(cursor.y() - rect.bottom()) <= tolerance
        if near_top and near_left:
            return 'top_left'
        if near_bottom and near_left:
            return 'bottom_left'
        if near_top and near_right:
            return 'top_right'
        if near_bottom and near_right:
            return 'bottom_right'
        if near_left:
            return 'left'
        if near_right:
            return 'right'
        if near_top:
            return 'top'
        if near_bottom:
            return 'bottom'
        return None

    def hovered_rects(self, cursor):
        rects = []
        for rect in self.handler_rects() + [self.rect]:
            if not rect:
                continue
            if rect.contains(cursor):
                rects.append(rect)
        return rects

    def set_rect(self, rect):
        self.rect = rect
        self.update_geometries()

    def update_geometries(self):
        rect, zoom = self.rect, self.zoom_factor
        self._tl_corner_rect = get_topleft_rect(rect, zoom) if rect else None
        self._bl_corner_rect = get_bottomleft_rect(rect, zoom) if rect else None
        self._tr_corner_rect = get_topright_rect(rect, zoom) if rect else None
        self._br_corner_rect = get_bottomright_rect(rect, zoom) if rect else None
        self._l_side_rect = get_left_side_rect(rect, zoom) if rect else None
        self._r_side_rect = get_right_side_rect(rect, zoom) if rect else None
        self._t_side_rect = get_top_side_rect(rect, zoom) if rect else None
        self._b_side_rect = get_bottom_side_rect(rect, zoom) if rect else None
        self.hovered_path = get_hovered_path(rect, zoom) if rect else None

    def draw(self, painter, cursor):
        if self.rect is not None and all(self.handler_rects()):
            draw_manipulator(painter, self, cursor, self.zoom_factor)


def get_shape_rect_from_options(options):
    return QtCore.QRectF(
        options['shape.left'],
        options['shape.top'],
        options['shape.width'],
        options['shape.height'])


class Shape():
    def __init__(self, options):
        self.hovered = False
        self.clicked = False
        self.options = options
        self.rect = get_shape_rect_from_options(options)
        self.pixmap = None
        self.image_rect = None
        self.synchronize_image()

    def set_hovered(self, cursor):
        self.hovered = self.rect.contains(cursor)

    def set_clicked(self, cursor):
        self.clicked = self.rect.contains(cursor)

    def release(self, cursor):
        self.clicked = False
        self.hovered = self.rect.contains(cursor)

    def draw(self, painter):
        draw_shape(painter, self)

    def synchronize_rect(self):
        self.options['shape.left'] = self.rect.left()
        self.options['shape.top'] = self.rect.top()
        self.options['shape.width'] = self.rect.width()
        self.options['shape.height'] = self.rect.height()

    def content_rect(self):
        if self.options['shape'] == 'round':
            return proportional_rect(self.rect.toRect(), 70)
        return self.rect.toRect()

    def execute(self, left=False, right=False):
        side = 'left' if left else 'right' if right else None
        if not side or not self.options['action.' + side]:
            return
        code = self.options['action.{}.command'.format(side)]
        language = self.options['action.{}.language'.format(side)]
        execute_code(language, code)

    def is_interactive(self):
        return any([self.options['action.right'], self.options['action.left']])

    def autoclose(self, left=False, right=False):
        if left is True and right is False:
            return self.options['action.left.close']
        elif left is False and right is True:
            return self.options['action.right.close']
        elif left is True and right is True:
            r_close = self.options['action.right.close']
            l_close = self.options['action.left.close']
            return  r_close or l_close
        return False

    def synchronize_image(self):
        from hotbox_designer.images import resolve_image_path
        self.pixmap = QtGui.QPixmap(
            resolve_image_path(self.options['image.path']))
        if self.options['image.fit'] is True:
            self.image_rect = None
            return
        self.image_rect = QtCore.QRect(
            int(self.rect.left()),
            int(self.rect.top()),
            int(self.options['image.width']),
            int(self.options['image.height']))
        self.image_rect.moveCenter(self.rect.center().toPoint())
        # décalage manuel dans le bouton (mode « placer l'image »)
        self.image_rect.translate(
            int(self.options.get('image.offsetx', 0)),
            int(self.options.get('image.offsety', 0)))
