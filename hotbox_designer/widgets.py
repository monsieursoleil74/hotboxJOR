from hotbox_designer.vendor.Qt import QtGui, QtCore, QtWidgets
from hotbox_designer.qtutils import icon


TOGGLER_STYLESHEET = (
    'QPushButton {background: #333333; color: #cfcfcf; text-align: left;'
    'font-weight: bold; padding: 5px 8px; border: none;'
    'border-top: 1px solid #444444;}'
    'QPushButton:hover {background: #3a3a3a;}')


class BoolCombo(QtWidgets.QComboBox):
    valueSet = QtCore.Signal(bool)

    def __init__(self, state=True, parent=None):
        super(BoolCombo, self).__init__(parent)
        self.addItem('True')
        self.addItem('False')
        self.setCurrentText(str(state))
        self.currentIndexChanged.connect(self.current_index_changed)

    def state(self):
        return self.currentText() == 'True'

    def current_index_changed(self):
        self.valueSet.emit(self.state())


class BrowseEdit(QtWidgets.QWidget):
    valueSet = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(BrowseEdit, self).__init__(parent)

        self.text = QtWidgets.QLineEdit()
        self.text.returnPressed.connect(self.apply)
        self.button = QtWidgets.QPushButton('B')
        self.button.setFixedSize(21, 21)
        self.button.released.connect(self.browse)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self._value = self.value()

    def browse(self):
        dialog = QtWidgets.QFileDialog.getOpenFileName(self, 'select image')
        self.text.setText(dialog[0])
        self.apply()

    def apply(self):
        self.valueSet.emit(self.text.text())

    def value(self):
        value = self.text.text()
        return value if value != '' else None

    def set_value(self, value):
        self.text.setText(value)


class WidgetToggler(QtWidgets.QPushButton):
    def __init__(self, label, widget, parent=None):
        super(WidgetToggler, self).__init__(parent)
        self.setStyleSheet(TOGGLER_STYLESHEET)
        self.setText(' v ' + label)
        self.widget = widget
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._call_toggled)

    def _call_toggled(self, state):
        if state is True:
            self.widget.show()
            self.setText(self.text().replace('>', 'v'))
        else:
            self.widget.hide()
            self.setText(self.text().replace('v', '>'))


class FloatEdit(QtWidgets.QLineEdit):
    valueSet = QtCore.Signal(float)

    def __init__(self, minimum=None, maximum=None, parent=None):
        super(FloatEdit, self).__init__(parent)
        self.validator = QtGui.QDoubleValidator()
        if minimum is not None:
            self.validator.setBottom(minimum)
        if maximum is not None:
            self.validator.setTop(maximum)
        self.setValidator(self.validator)
        self._value = self.value()
        self.returnPressed.connect(self.apply)

    def focusInEvent(self, event):
        self._value = self.value()
        return super(FloatEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.apply()
        return super(FloatEdit, self).focusOutEvent(event)

    def apply(self):
        if self._value != self.value():
            self.valueSet.emit(self.value())
        self._value = self.value()

    def value(self):
        if self.text() == '':
            return None
        return float(self.text().replace(',', '.'))


class Title(QtWidgets.QLabel):
    def __init__(self, title, parent=None):
        super(Title, self).__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet(
            'color: #8fb4e0; font-weight: bold; letter-spacing: 1px;'
            'background: transparent; padding-left: 2px;')
        self.setText(title.upper())


class TouchEdit(QtWidgets.QLineEdit):
    def keyPressEvent(self, event):
        self.setText(QtGui.QKeySequence(event.key()).toString().lower())
        self.textEdited.emit(self.text())


class CommandButton(QtWidgets.QWidget):
    released = QtCore.Signal()
    playReleased = QtCore.Signal()
    def __init__(self, label, parent=None):
        super(CommandButton, self).__init__(parent)
        self.mainbutton = QtWidgets.QPushButton(label)
        self.mainbutton.released.connect(self.released.emit)
        self.playbutton = QtWidgets.QPushButton(icon('play.png'), '')
        self.playbutton.released.connect(self.playReleased.emit)
        self.playbutton.setFixedSize(22, 22)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.layout.addWidget(self.mainbutton)
        self.layout.addWidget(self.playbutton)

class ColorButton(QtWidgets.QPushButton):
    """Pastille de couleur façon Photoshop : le bouton EST la couleur
    (code hexa affiché en contraste), un clic ouvre le sélecteur de
    couleurs natif. set_color(None) = valeurs multiples ('...')."""
    valueSet = QtCore.Signal(str)

    def __init__(self, parent=None, show_text=True, label=''):
        super(ColorButton, self).__init__(parent)
        self._color = '#888888'
        self._show_text = show_text
        self._label = label
        self.setFixedHeight(22)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.released.connect(self.pick_color)
        self._update_face()

    def color(self):
        return self._color

    def set_color(self, color):
        self._color = color
        self._update_face()

    def _update_face(self):
        if self._color is None:
            self.setText('...')
            self.setToolTip(self._label)
            self.setStyleSheet(
                'QPushButton {background: #4a4a4a; color: #bbbbbb;'
                'border: 1px solid #5a5a5a; border-radius: 3px;}')
            return
        qcolor = QtGui.QColor(self._color)
        # texte noir ou blanc selon la luminosité de la couleur
        luminance = (
            0.299 * qcolor.red() + 0.587 * qcolor.green() +
            0.114 * qcolor.blue())
        text_color = '#000000' if luminance > 130 else '#ffffff'
        self.setText(self._color.upper() if self._show_text else '')
        tooltip = self._color.upper()
        if self._label:
            tooltip = '%s — %s' % (self._label, tooltip)
        self.setToolTip(tooltip)
        self.setStyleSheet(
            'QPushButton {background: %s; color: %s;'
            'border: 1px solid #222222; border-radius: 3px;}'
            'QPushButton:hover {border-color: #3388ff;}'
            % (self._color, text_color))

    def pick_color(self):
        initial = QtGui.QColor(self._color or '#888888')
        color = QtWidgets.QColorDialog.getColor(
            initial, self, 'Choose color')
        if not color.isValid():
            return
        self.set_color(color.name())
        self.valueSet.emit(color.name())


class OpacitySlider(QtWidgets.QWidget):
    """Curseur d'opacité 0-100 % (stocké en transparence 0-255
    inversée dans les options — la conversion est faite ici)."""
    valueSet = QtCore.Signal(object)  # transparence 0-255

    def __init__(self, parent=None):
        super(OpacitySlider, self).__init__(parent)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(100)
        self.label = QtWidgets.QLabel('100%')
        self.label.setFixedWidth(38)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.slider)
        layout.addWidget(self.label)
        self.slider.valueChanged.connect(self._update_label)
        # émet au relâchement (pas à chaque tick : sinon l'undo déborde)
        self.slider.sliderReleased.connect(self._emit)
        self.slider.actionTriggered.connect(self._action_triggered)

    def _update_label(self, value):
        self.label.setText('%d%%' % value)

    def _action_triggered(self, action):
        # clic dans la gouttière / flèches clavier : pas de release
        if action != QtWidgets.QAbstractSlider.SliderMove:
            QtCore.QTimer.singleShot(0, self._emit)

    def _emit(self):
        self.valueSet.emit(self.transparency())

    def transparency(self):
        return int(round(255 - self.slider.value() * 255.0 / 100))

    def set_transparency(self, transparency):
        self.slider.blockSignals(True)
        if transparency is None:
            self.slider.setValue(100)
            self.label.setText('...')
        else:
            value = int(round((255 - float(transparency)) * 100.0 / 255))
            self.slider.setValue(value)
            self.label.setText('%d%%' % value)
        self.slider.blockSignals(False)


class BoolCheckBox(QtWidgets.QCheckBox):
    """Case à cocher compatible avec l'API des BoolCombo (setCurrentText
    'True'/'False'/None pour les valeurs multiples)."""
    valueSet = QtCore.Signal(bool)

    def __init__(self, state=True, parent=None):
        super(BoolCheckBox, self).__init__(parent)
        self.setChecked(state)
        # NE PAS connecter clicked directement à valueSet.emit : selon
        # le binding, clicked est résolu sans argument et l'émission
        # échouait silencieusement (cases muettes)
        self.clicked.connect(self._clicked)

    def _clicked(self, *_):
        # un clic sort aussi de l'état tri-état (valeurs multiples)
        self.setTristate(False)
        self.valueSet.emit(self.isChecked())

    def state(self):
        return self.isChecked()

    def setCurrentText(self, text):
        self.blockSignals(True)
        if text is None or text == '...':
            self.setTristate(True)
            self.setCheckState(QtCore.Qt.PartiallyChecked)
        else:
            self.setTristate(False)
            self.setChecked(text == 'True')
        self.blockSignals(False)


class CommandTextEdit(QtWidgets.QPlainTextEdit):
    """Éditeur de commande qui se sauvegarde tout seul à la perte de
    focus (fini le bouton « save command » et les commandes perdues)."""
    committed = QtCore.Signal()

    def focusOutEvent(self, event):
        self.committed.emit()
        super(CommandTextEdit, self).focusOutEvent(event)
