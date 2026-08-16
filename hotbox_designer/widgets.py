from hotbox_designer.vendor.Qt import QtGui, QtCore, QtWidgets


# en-tête de section repliable : capitales espacées + tiret d'accent à
# gauche, chevron discret — même vocabulaire que les titres du manager
TOGGLER_STYLESHEET = (
    'QPushButton {background: #333333; color: #cfcfcf; text-align: left;'
    'font-weight: bold; font-size: 11px; letter-spacing: 1px;'
    'padding: 6px 8px 6px 10px; border: none;'
    'border-top: 1px solid #242424; border-left: 3px solid #6d8c5e;}'
    'QPushButton:hover {background: #3a3a3a;}'
    'QPushButton:!checked {border-left-color: #4a4a4a; color: #9a9a9a;}')


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
        self._label = label.upper()
        self.widget = widget
        self.setCheckable(True)
        self.setChecked(True)
        self._update_text()
        self.toggled.connect(self._call_toggled)

    def _update_text(self):
        arrow = '▾' if self.isChecked() else '▸'  # ▾ / ▸
        self.setText('%s  %s' % (arrow, self._label))

    def _call_toggled(self, state):
        self.widget.setVisible(state)
        self._update_text()


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
        self.setFixedHeight(26)
        # petit intitulé neutre en capitales espacées, souligné d'un
        # filet discret qui structure la colonne (pas d'accent coloré :
        # réservé aux états actifs)
        self.setStyleSheet(
            'color: #909090; font-weight: bold; font-size: 10px;'
            'letter-spacing: 2px; background: transparent;'
            'padding-left: 2px; padding-top: 6px;'
            'border-bottom: 1px solid #484848;')
        self.setText(title.upper())


class HotkeyEdit(QtWidgets.QLineEdit):
    """Capture d'un raccourci complet : on tape la combinaison (ex.
    Maj+Q) et elle s'affiche telle quelle (« Shift+q »). Plus besoin de
    cocher Ctrl/Alt/Shift séparément — les modificateurs sont lus sur la
    frappe elle-même. Échap efface."""
    keySet = QtCore.Signal(str)

    _MODIFIER_KEYS = (
        QtCore.Qt.Key_Control, QtCore.Qt.Key_Shift, QtCore.Qt.Key_Alt,
        QtCore.Qt.Key_Meta, QtCore.Qt.Key_AltGr)

    def __init__(self, parent=None):
        super(HotkeyEdit, self).__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText('type a shortcut…')
        self._sequence = ''

    def sequence(self):
        return self._sequence

    def set_sequence(self, sequence):
        self._sequence = sequence or ''
        self.setText(self._sequence)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self._sequence = ''
            self.clear()
            self.keySet.emit(self._sequence)
            return
        # tant qu'on n'a qu'un modificateur enfoncé, on attend la vraie touche
        if key in self._MODIFIER_KEYS:
            return
        touch = QtGui.QKeySequence(key).toString().lower()
        if not touch:
            return
        modifiers = event.modifiers()
        parts = []
        if modifiers & QtCore.Qt.ControlModifier:
            parts.append('Ctrl')
        if modifiers & QtCore.Qt.AltModifier:
            parts.append('Alt')
        if modifiers & QtCore.Qt.ShiftModifier:
            parts.append('Shift')
        parts.append(touch)
        self._sequence = '+'.join(parts)
        self.setText(self._sequence)
        self.keySet.emit(self._sequence)


class CommandButton(QtWidgets.QWidget):
    """Bouton « switch » du manager : affiche la commande à coller sur
    un bouton de shelf Maya (le play de test a été retiré)."""
    released = QtCore.Signal()

    def __init__(self, label, parent=None):
        super(CommandButton, self).__init__(parent)
        self.mainbutton = QtWidgets.QPushButton(label)
        self.mainbutton.released.connect(self.released.emit)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.layout.addWidget(self.mainbutton)

class ColorButton(QtWidgets.QPushButton):
    """Pastille de couleur façon Photoshop : le bouton EST la couleur,
    le code hexa vit dans l'infobulle, un clic ouvre le sélecteur de
    couleurs. set_color(None) = valeurs multiples ('...').

    Le style est CIBLÉ sur la pastille (sélecteur #colorSwatch) : un
    sélecteur QPushButton générique ruisselait sur les enfants — le
    dialogue de couleurs, parenté à la pastille, voyait ses boutons
    OK/Cancel peints de la couleur choisie."""
    valueSet = QtCore.Signal(str)

    def __init__(self, parent=None, show_text=True, label=''):
        super(ColorButton, self).__init__(parent)
        self.setObjectName('colorSwatch')
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
                'QPushButton#colorSwatch {background: #4a4a4a;'
                'color: #bbbbbb; border: 1px solid #5a5a5a;'
                'border-radius: 3px;}')
            return
        # sobre : pas de texte teinté selon la couleur — le code hexa
        # est dans l'infobulle
        self.setText(self._color.upper() if self._show_text else '')
        tooltip = self._color.upper()
        if self._label:
            tooltip = '%s — %s' % (self._label, tooltip)
        self.setToolTip(tooltip)
        self.setStyleSheet(
            'QPushButton#colorSwatch {background: %s; color: #ffffff;'
            'border: 1px solid #222222; border-radius: 3px;}'
            'QPushButton#colorSwatch:hover {border-color: #ffffff;}'
            % self._color)

    def pick_color(self):
        from hotbox_designer.colorpicker import ColorPickerDialog
        name = ColorPickerDialog.get_color(self._color or '#888888', self)
        if name is None:
            return
        self.set_color(name)
        self.valueSet.emit(name)


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


class ValueSlider(QtWidgets.QWidget):
    """Curseur générique min..max avec valeur affichée à droite (même
    ergonomie que l'opacité). Émet un float au relâchement (pas à
    chaque tick, pour ne pas inonder l'undo). Le slider travaille en
    pas entiers ``STEPS`` par unité pour autoriser les décimales."""
    valueSet = QtCore.Signal(object)
    STEPS = 2  # 2 crans par unité -> pas de 0.5

    def __init__(self, minimum=0.0, maximum=10.0, suffix=' px', parent=None):
        super(ValueSlider, self).__init__(parent)
        self._min, self._max, self._suffix = minimum, maximum, suffix
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(
            int(minimum * self.STEPS), int(maximum * self.STEPS))
        self.label = QtWidgets.QLabel('')
        self.label.setFixedWidth(38)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.slider)
        layout.addWidget(self.label)
        self.slider.valueChanged.connect(self._update_label)
        self.slider.sliderReleased.connect(self._emit)
        self.slider.actionTriggered.connect(self._action_triggered)

    def _pretty(self, value):
        text = ('%.1f' % value).rstrip('0').rstrip('.')
        return text + self._suffix

    def _update_label(self, raw):
        self.label.setText(self._pretty(raw / float(self.STEPS)))

    def _action_triggered(self, action):
        if action != QtWidgets.QAbstractSlider.SliderMove:
            QtCore.QTimer.singleShot(0, self._emit)

    def _emit(self):
        self.valueSet.emit(self.value())

    def value(self):
        return self.slider.value() / float(self.STEPS)

    def set_value(self, value):
        self.slider.blockSignals(True)
        if value is None:
            self.slider.setValue(self.slider.minimum())
            self.label.setText('...')
        else:
            self.slider.setValue(int(round(float(value) * self.STEPS)))
            self.label.setText(self._pretty(self.value()))
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
