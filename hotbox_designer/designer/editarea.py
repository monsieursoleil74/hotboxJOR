
from hotbox_designer.vendor.Qt import QtCore, QtGui, QtWidgets

from hotbox_designer.interactive import Manipulator, SelectionSquare
from hotbox_designer.geometry import (
    Transform, ViewportMapper, snap, get_combined_rects)
from hotbox_designer.painting import draw_editor, draw_editor_center
from hotbox_designer.qtutils import get_cursor


class ShapeEditArea(QtWidgets.QWidget):
    selectedShapesChanged = QtCore.Signal()
    increaseUndoStackRequested = QtCore.Signal()
    centerMoved = QtCore.Signal(int, int)

    def __init__(self, options, parent=None):
        super(ShapeEditArea, self).__init__(parent)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.options = options

        self.viewport_mapper = ViewportMapper()
        self.focused_once = False
        self.panning = False
        self.pan_reference = None

        self.selection = Selection()
        self.selection_square = SelectionSquare()
        self.manipulator = Manipulator()
        self.transform = Transform()

        self.shapes = []
        self.clicked_shape = None
        self.clicked = False
        self.handeling = False
        self.manipulator_moved = False
        self.edit_center_mode = False
        self.increase_undo_on_release = False

        self.ctrl_pressed = False
        self.shit_pressed = False

    def hotbox_rect(self):
        """Le « plan de travail » : la zone de la hotbox en unités."""
        return QtCore.QRectF(
            0, 0, self.options['width'], self.options['height'])

    def units_cursor(self):
        """Position du curseur convertie en unités de la hotbox."""
        return self.viewport_mapper.to_units_coords(get_cursor(self))

    def focus_view(self):
        """F : cadre la sélection si elle existe, sinon la hotbox."""
        rect = self.manipulator.rect if self.selection.shapes else None
        self.viewport_mapper.viewsize = self.size()
        self.viewport_mapper.focus(rect or self.hotbox_rect())
        self.sync_zoom()
        self.repaint()

    def sync_zoom(self):
        """Garde poignées et traits à taille constante à l'écran."""
        self.manipulator.zoom_factor = self.viewport_mapper.zoom
        if self.manipulator.rect is not None:
            self.manipulator.update_geometries()

    def resizeEvent(self, event):
        self.viewport_mapper.viewsize = self.size()
        if not self.focused_once and self.width() > 0:
            self.focused_once = True
            self.viewport_mapper.focus(self.hotbox_rect())
        self.sync_zoom()
        self.repaint()

    def wheelEvent(self, event):
        # zoom vers le curseur, façon dwpicker
        delta = event.angleDelta().y()
        if not delta:
            return
        factor = 1.15 if delta > 0 else 1 / 1.15
        self.viewport_mapper.zoom_towards(get_cursor(self), factor)
        self.sync_zoom()
        self.repaint()

    def mouseMoveEvent(self, event):
        if self.panning:
            position = get_cursor(self)
            offset = position - self.pan_reference
            self.pan_reference = position
            self.viewport_mapper.origin -= offset
            self.repaint()
            return
        cursor = self.units_cursor()
        if self.edit_center_mode is True:
            if self.clicked is False:
                return
            if self.transform.snap:
                x, y = snap(cursor.x(), cursor.y(), self.transform.snap)
            else:
                x, y = cursor.x(), cursor.y()
            self.centerMoved.emit(int(round(x)), int(round(y)))
            self.increase_undo_on_release = True
            self.repaint()
            return

        for shape in self.shapes:
            shape.set_hovered(cursor)

        if self.selection_square.handeling:
            self.selection_square.handle(cursor)

        if self.handeling is False:
            return self.repaint()

        self.manipulator_moved = True
        rect = self.manipulator.rect
        if self.transform.direction:
            self.transform.resize([s.rect for s in self.selection], cursor)
            self.manipulator.update_geometries()
        elif rect is not None and rect.contains(cursor):
            self.transform.move([s.rect for s in self.selection], cursor)
            self.manipulator.update_geometries()
        for shape in self.shapes:
            shape.synchronize_rect()
            shape.synchronize_image()
        self.increase_undo_on_release = True
        self.selectedShapesChanged.emit()
        self.repaint()

    def mousePressEvent(self, event):
        self.setFocus(QtCore.Qt.MouseFocusReason)
        if event.button() == QtCore.Qt.MiddleButton:
            self.panning = True
            self.pan_reference = get_cursor(self)
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            return
        if event.button() != QtCore.Qt.LeftButton:
            return
        cursor = self.units_cursor()
        direction = self.manipulator.get_direction(cursor)
        self.clicked = True
        self.transform.direction = direction

        self.manipulator_moved = False
        rect = self.manipulator.rect
        # Alt + glisser la sélection = la dupliquer et déplacer la copie
        alt = bool(event.modifiers() & QtCore.Qt.AltModifier)
        if (alt and not direction and self.selection.shapes
                and rect is not None and rect.contains(cursor)):
            self.duplicate_selection()
            rect = self.manipulator.rect
        if rect is not None:
            self.transform.set_rect(rect)
            self.transform.reference_rect = QtCore.QRectF(rect)

        self.clicked_shape = None
        for shape in reversed(self.shapes):
            if shape.rect.contains(cursor):
                self.clicked_shape = shape
                break

        if rect and rect.contains(cursor):
            self.transform.set_reference_point(cursor)
        handeling = bool(direction or rect.contains(cursor) if rect else False)

        self.handeling = handeling
        if not self.handeling:
            self.selection_square.clicked(cursor)

        self.repaint()

    def mouseReleaseEvent(self, event):
        if self.panning and event.button() == QtCore.Qt.MiddleButton:
            self.panning = False
            self.pan_reference = None
            self.unsetCursor()
            return
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self.edit_center_mode is True:
            self.clicked = False
            return

        shape = self.clicked_shape
        selection_update_conditions = (
            self.handeling is False
            or shape not in self.selection
            and self.manipulator_moved is False)
        if selection_update_conditions:
            self.selection.set([shape] if shape else None)
            self.update_selection()

        if self.selection_square.handeling:
            shapes = [
                s for s in self.shapes
                if s.rect.intersects(self.selection_square.rect)]
            if shapes:
                self.selection.set(shapes)
                rects = [shape.rect for shape in self.selection]
                self.manipulator.set_rect(get_combined_rects(rects))
                self.selectedShapesChanged.emit()
        self.selection_square.release()

        if self.increase_undo_on_release:
            self.increaseUndoStackRequested.emit()
            self.increase_undo_on_release = False

        self.clicked = False
        self.handeling = False
        self.repaint()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
            return self.focus_view()

        if event.key() == QtCore.Qt.Key_Shift:
            self.transform.square = True
            self.shit_pressed = True

        if event.key() == QtCore.Qt.Key_Control:
            self.ctrl_pressed = True

        self.selection.mode = get_selection_mode(
            shift=self.shit_pressed,
            ctrl=self.ctrl_pressed)

        self.repaint()

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Shift:
            self.transform.square = False
            self.shit_pressed = False

        if event.key() == QtCore.Qt.Key_Control:
            self.ctrl_pressed = False

        self.selection.mode = get_selection_mode(
            shift=self.shit_pressed,
            ctrl=self.ctrl_pressed)

        self.repaint()

    def update_selection(self):
        rects = [shape.rect for shape in self.selection]
        self.manipulator.set_rect(get_combined_rects(rects))
        self.selectedShapesChanged.emit()

    def duplicate_selection(self):
        from copy import deepcopy
        from hotbox_designer.interactive import Shape
        duplicates = [Shape(deepcopy(s.options)) for s in self.selection]
        self.shapes.extend(duplicates)
        self.selection.replace(duplicates)
        self.update_selection()
        self.increase_undo_on_release = True

    def paintEvent(self, _):
        painter = QtGui.QPainter()
        painter.begin(self)
        self.paint(painter)
        painter.end()

    def paint(self, painter):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # fond hors plan de travail
        painter.fillRect(self.rect(), QtGui.QColor('#333333'))
        # tout le reste est dessiné dans l'espace de la hotbox
        painter.save()
        painter.setTransform(self.viewport_mapper.to_viewport_transform())
        draw_editor(painter, self.hotbox_rect(), snap=self.transform.snap)
        for shape in self.shapes:
            shape.draw(painter)
        self.manipulator.draw(painter, self.units_cursor())
        self.selection_square.draw(painter, self.viewport_mapper.zoom)
        if self.edit_center_mode is True:
            point = self.options['centerx'], self.options['centery']
            draw_editor_center(painter, self.hotbox_rect(), point)
        painter.restore()


class Selection():
    def __init__(self):
        self.shapes = []
        self.mode = 'replace'

    def set(self, shapes):
        if self.mode == 'add':
            if shapes is None:
                return
            return self.add(shapes)
        elif self.mode == 'replace':
            if shapes is None:
                return self.clear()
            return self.replace(shapes)
        elif self.mode == 'invert':
            if shapes is None:
                return
            return self.invert(shapes)
        elif self.mode == 'remove':
            if shapes is None:
                return
            for shape in shapes:
                if shape in self.shapes:
                    self.remove(shape)

    def replace(self, shapes):
        self.shapes = shapes

    def add(self, shapes):
        self.shapes.extend([s for s in shapes if s not in self])

    def remove(self, shape):
        self.shapes.remove(shape)

    def invert(self, shapes):
        for shape in shapes:
            if shape not in self.shapes:
                self.add([shape])
            else:
                self.remove(shape)

    def clear(self):
        self.shapes = []

    def __iter__(self):
        return self.shapes.__iter__()


def get_selection_mode(ctrl, shift):
    if not ctrl and not shift:
        return 'replace'
    elif ctrl and shift:
        return 'invert'
    elif shift and not ctrl:
        return 'add'
    elif ctrl and not shift:
        return 'remove'
