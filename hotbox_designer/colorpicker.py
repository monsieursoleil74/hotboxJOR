"""Sélecteur de couleurs moderne, façon Miro.

Un carré saturation/valeur, une barre de teinte, un champ hexa et une
rangée de couleurs prédéfinies — dans le thème sombre. Remplace le
QColorDialog natif, jugé vieillot.

Usage :
    color = ColorPickerDialog.get_color('#3388ff', parent)  # -> '#rrggbb' ou None
"""
from hotbox_designer.vendor.Qt import QtWidgets, QtCore, QtGui


PRESETS = [
    '#f24d4d', '#f2994a', '#f2c94c', '#6fcf50', '#27ae60',
    '#56ccf2', '#2f80ed', '#9b51e0', '#eb5eb0', '#ffffff',
    '#e0e0e0', '#9e9e9e', '#5c5c5c', '#333333', '#000000',
]
MARKER = QtGui.QColor('#ffffff')
MARKER_EDGE = QtGui.QColor('#000000')


class _SVSquare(QtWidgets.QWidget):
    """Carré saturation (X) / valeur (Y) pour la teinte courante."""
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(_SVSquare, self).__init__(parent)
        self.setMinimumSize(220, 160)
        self.setCursor(QtCore.Qt.CrossCursor)
        self._hue = 0.0
        self._sat = 0.0
        self._val = 1.0

    def set_hsv(self, h, s, v):
        self._hue, self._sat, self._val = h, s, v
        self.update()

    def sat(self):
        return self._sat

    def val(self):
        return self._val

    def set_hue(self, hue):
        self._hue = hue
        self.update()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        # dégradé horizontal : blanc -> teinte pure
        hue_color = QtGui.QColor.fromHsvF(self._hue, 1.0, 1.0)
        grad = QtGui.QLinearGradient(rect.topLeft(), rect.topRight())
        grad.setColorAt(0.0, QtGui.QColor('#ffffff'))
        grad.setColorAt(1.0, hue_color)
        painter.fillRect(rect, grad)
        # dégradé vertical : transparent -> noir
        dark = QtGui.QLinearGradient(rect.topLeft(), rect.bottomLeft())
        dark.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        dark.setColorAt(1.0, QtGui.QColor(0, 0, 0, 255))
        painter.fillRect(rect, dark)
        # marqueur
        x = self._sat * rect.width()
        y = (1.0 - self._val) * rect.height()
        painter.setPen(QtGui.QPen(MARKER_EDGE, 3))
        painter.drawEllipse(QtCore.QPointF(x, y), 6, 6)
        painter.setPen(QtGui.QPen(MARKER, 1.5))
        painter.drawEllipse(QtCore.QPointF(x, y), 6, 6)

    def _apply(self, pos):
        w = max(1, self.width())
        h = max(1, self.height())
        self._sat = min(1.0, max(0.0, pos.x() / float(w)))
        self._val = 1.0 - min(1.0, max(0.0, pos.y() / float(h)))
        self.update()
        self.changed.emit()

    def mousePressEvent(self, event):
        self._apply(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self._apply(event.pos())


class _HueBar(QtWidgets.QWidget):
    """Barre verticale de teinte."""
    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super(_HueBar, self).__init__(parent)
        self.setFixedWidth(18)
        self.setMinimumHeight(160)
        self.setCursor(QtCore.Qt.SizeVerCursor)
        self._hue = 0.0

    def hue(self):
        return self._hue

    def set_hue(self, hue):
        self._hue = hue
        self.update()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        grad = QtGui.QLinearGradient(rect.topLeft(), rect.bottomLeft())
        for i in range(7):
            grad.setColorAt(i / 6.0, QtGui.QColor.fromHsvF(i / 6.0, 1.0, 1.0))
        painter.fillRect(rect, grad)
        y = self._hue * rect.height()
        painter.setPen(QtGui.QPen(QtGui.QColor('#000000'), 3))
        painter.drawLine(0, int(y), rect.width(), int(y))
        painter.setPen(QtGui.QPen(QtGui.QColor('#ffffff'), 1.5))
        painter.drawLine(0, int(y), rect.width(), int(y))

    def _apply(self, pos):
        h = max(1, self.height())
        self._hue = min(1.0, max(0.0, pos.y() / float(h)))
        self.update()
        self.changed.emit()

    def mousePressEvent(self, event):
        self._apply(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self._apply(event.pos())


class _Swatch(QtWidgets.QPushButton):
    picked = QtCore.Signal(str)

    def __init__(self, color, parent=None):
        super(_Swatch, self).__init__(parent)
        self._color = color
        self.setFixedSize(20, 20)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet(
            'QPushButton {background: %s; border: 1px solid #222;'
            'border-radius: 3px;} QPushButton:hover {border: 1px solid #fff;}'
            % color)
        self.released.connect(lambda: self.picked.emit(self._color))


class ColorPickerDialog(QtWidgets.QDialog):
    def __init__(self, initial='#888888', parent=None):
        super(ColorPickerDialog, self).__init__(parent)
        self.setWindowTitle('Color')
        self._color = QtGui.QColor(initial if initial else '#888888')
        if not self._color.isValid():
            self._color = QtGui.QColor('#888888')

        self.square = _SVSquare()
        self.hue_bar = _HueBar()
        self.preview = QtWidgets.QFrame()
        self.preview.setFixedHeight(26)
        self.hexedit = QtWidgets.QLineEdit()
        self.hexedit.setMaxLength(7)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(self.square, stretch=1)
        top.addWidget(self.hue_bar)

        # rangée de couleurs prédéfinies
        presets = QtWidgets.QGridLayout()
        presets.setSpacing(4)
        for i, color in enumerate(PRESETS):
            swatch = _Swatch(color)
            swatch.picked.connect(self._set_hex)
            presets.addWidget(swatch, i // 8, i % 8)

        hexrow = QtWidgets.QHBoxLayout()
        hexrow.setSpacing(8)
        hexrow.addWidget(self.preview, stretch=1)
        hexrow.addWidget(QtWidgets.QLabel('Hex'))
        hexrow.addWidget(self.hexedit)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addLayout(top)
        layout.addLayout(presets)
        layout.addLayout(hexrow)
        layout.addWidget(buttons)
        self.setMinimumWidth(300)

        self.square.changed.connect(self._sv_changed)
        self.hue_bar.changed.connect(self._hue_changed)
        self.hexedit.editingFinished.connect(self._hex_edited)
        self._push_to_widgets()

    # --- synchronisation ---
    def _push_to_widgets(self):
        h, s, v, _ = self._color.getHsvF()
        h = max(0.0, h)  # -1 pour les gris -> 0
        self.square.set_hsv(h, s, v)
        self.hue_bar.set_hue(h)
        self._update_preview()

    def _update_preview(self):
        name = self._color.name()
        self.preview.setStyleSheet(
            'background: %s; border: 1px solid #222; border-radius: 3px;'
            % name)
        if self.hexedit.text().lower() != name.lower():
            self.hexedit.setText(name)

    def _sv_changed(self):
        self._color = QtGui.QColor.fromHsvF(
            self.hue_bar.hue(), self.square.sat(), self.square.val())
        self._update_preview()

    def _hue_changed(self):
        hue = self.hue_bar.hue()
        self.square.set_hue(hue)
        self._color = QtGui.QColor.fromHsvF(
            hue, self.square.sat(), self.square.val())
        self._update_preview()

    def _hex_edited(self):
        text = self.hexedit.text().strip()
        if not text.startswith('#'):
            text = '#' + text
        color = QtGui.QColor(text)
        if color.isValid():
            self._color = color
            self._push_to_widgets()

    def _set_hex(self, color):
        self._color = QtGui.QColor(color)
        self._push_to_widgets()

    def color_name(self):
        return self._color.name()

    @staticmethod
    def get_color(initial='#888888', parent=None):
        dialog = ColorPickerDialog(initial, parent)
        from hotbox_designer.theme import apply_dark_theme
        apply_dark_theme(dialog)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            return dialog.color_name()
        return None
