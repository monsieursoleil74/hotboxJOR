from functools import partial
from hotbox_designer.vendor.Qt import QtCore, QtWidgets, QtGui

from hotbox_designer.colorwheel import ColorDialog
from hotbox_designer.qtutils import icon, VALIGNS, HALIGNS
from hotbox_designer.widgets import (
    Title, BoolCombo, WidgetToggler, FloatEdit, BrowseEdit, ColorEdit,
    ColorButton, OpacitySlider, BoolCheckBox)
from hotbox_designer.designer.highlighter import get_highlighter


LEFT_CELL_WIDTH = 80
SHAPE_TYPES = 'square', 'round'


class AttributeEditor(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)
    rectModified = QtCore.Signal(str, float)
    imageModified = QtCore.Signal()

    def __init__(self, application, parent=None):
        super(AttributeEditor, self).__init__(parent)
        self.application = application
        self.widget = QtWidgets.QWidget()

        self.shape = ShapeSettings()
        self.shape.optionSet.connect(self.optionSet.emit)
        self.shape.rectModified.connect(self.rectModified.emit)
        self.shape_toggler = WidgetToggler('Shape', self.shape)

        self.image = ImageSettings()
        self.image.optionSet.connect(self.image_modified)
        self.image_toggler = WidgetToggler('Image', self.image)

        self.appearence = AppearenceSettings()
        self.appearence.optionSet.connect(self.optionSet.emit)
        self.appearence_toggler = WidgetToggler('Appearence', self.appearence)

        self.text = TextSettings()
        self.text.optionSet.connect(self.optionSet.emit)
        self.text_toggler = WidgetToggler('Text', self.text)

        self.action = ActionSettings()
        self.action.set_languages(self.application.available_languages)
        self.action.optionSet.connect(self.optionSet.emit)
        self.action_toggler = WidgetToggler('Action', self.action)

        self.layout = QtWidgets.QVBoxLayout(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.shape_toggler)
        self.layout.addWidget(self.shape)
        self.layout.addWidget(self.image_toggler)
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.appearence_toggler)
        self.layout.addWidget(self.appearence)
        self.layout.addWidget(self.text_toggler)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.action_toggler)
        self.layout.addWidget(self.action)
        self.layout.addStretch(1)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(self.widget)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.scroll_area)

        # largeur fixe (la largeur auto gonflait avec les nouveaux
        # widgets — on garde le gabarit d'origine)
        self.setFixedWidth(290)
        self.scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

    def set_options(self, options):
        self.blockSignals(True)
        self.shape.set_options(options)
        self.image.set_options(options)
        self.appearence.set_options(options)
        self.text.set_options(options)
        self.action.set_options(options)
        self.blockSignals(False)

    def image_modified(self, option, value):
        self.optionSet.emit(option, value)
        self.imageModified.emit()


class ShapeSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)
    rectModified = QtCore.Signal(str, float)

    def __init__(self, parent=None):
        super(ShapeSettings, self).__init__(parent)
        # les dimensions/positions se manipulent au viewport : la
        # section « Dimensions » (dont le champ top écrivait dans
        # shape.right !) a été retirée
        self.shape = QtWidgets.QComboBox()
        self.shape.addItems(SHAPE_TYPES)
        self.shape.currentIndexChanged.connect(self.shape_changed)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('Shape', self.shape)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def shape_changed(self, _):
        self.optionSet.emit('shape', self.shape.currentText())

    def set_options(self, options):
        values = list({option['shape'] for option in options})
        value = values[0] if len(values) == 1 else '...'
        self.shape.setCurrentText(value)


class ImageSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(ImageSettings, self).__init__(parent)
        self.path = BrowseEdit()
        self.path.valueSet.connect(partial(self.optionSet.emit, 'image.path'))

        self.fit = BoolCombo(True)
        self.fit.valueSet.connect(partial(self.optionSet.emit, 'image.fit'))

        self.width = FloatEdit()
        method = partial(self.optionSet.emit, 'image.width')
        self.width.valueSet.connect(method)

        self.height = FloatEdit()
        method = partial(self.optionSet.emit, 'image.height')
        self.height.valueSet.connect(method)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('Path', self.path)
        self.layout.addRow('Fit to shape', self.fit)
        self.layout.addRow('Width', self.width)
        self.layout.addRow('Height', self.height)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def set_options(self, options):
        values = list({option['image.path'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.path.set_value(value)

        values = list({option['image.fit'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.fit.setCurrentText(value)

        values = list({option['image.width'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.width.setText(value)

        values = list({option['image.height'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.height.setText(value)


class AppearenceSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    COLOR_KEYS = (
        'bgcolor.normal', 'bgcolor.hovered', 'bgcolor.clicked',
        'bordercolor.normal', 'bordercolor.hovered', 'bordercolor.clicked')
    WIDTH_KEYS = (
        'borderwidth.normal', 'borderwidth.hovered', 'borderwidth.clicked')

    def __init__(self, parent=None):
        super(AppearenceSettings, self).__init__(parent)
        # pastilles de couleur façon Photoshop : un clic = le sélecteur
        # natif ; l'opacité est un curseur 0-100 % (stockée en
        # transparence 0-255 inversée, conversion dans OpacitySlider)
        self.color_buttons = {}
        for key in self.COLOR_KEYS:
            button = ColorButton()
            button.valueSet.connect(partial(self.optionSet.emit, key))
            self.color_buttons[key] = button

        self.bg_opacity = OpacitySlider()
        method = partial(self.optionSet.emit, 'bgcolor.transparency')
        self.bg_opacity.valueSet.connect(method)

        self.border = BoolCheckBox(True)
        method = partial(self.optionSet.emit, 'border')
        self.border.valueSet.connect(method)

        self.border_opacity = OpacitySlider()
        method = partial(self.optionSet.emit, 'bordercolor.transparency')
        self.border_opacity.valueSet.connect(method)

        self.width_edits = {}
        widths = QtWidgets.QHBoxLayout()
        widths.setContentsMargins(0, 0, 0, 0)
        widths.setSpacing(4)
        for key, label in zip(self.WIDTH_KEYS, ('N', 'H', 'C')):
            edit = FloatEdit(minimum=0.0)
            edit.setFixedWidth(42)
            edit.valueSet.connect(partial(self.optionSet.emit, key))
            edit.setToolTip(
                {'N': 'Normal', 'H': 'Hovered', 'C': 'Clicked'}[label])
            self.width_edits[key] = edit
            widths.addWidget(QtWidgets.QLabel(label))
            widths.addWidget(edit)
        widths.addStretch(1)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow(Title('Background'))
        self.layout.addRow('normal', self.color_buttons['bgcolor.normal'])
        self.layout.addRow('hovered', self.color_buttons['bgcolor.hovered'])
        self.layout.addRow('clicked', self.color_buttons['bgcolor.clicked'])
        self.layout.addRow('opacity', self.bg_opacity)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Border'))
        self.layout.addRow('visible', self.border)
        self.layout.addRow(
            'normal', self.color_buttons['bordercolor.normal'])
        self.layout.addRow(
            'hovered', self.color_buttons['bordercolor.hovered'])
        self.layout.addRow(
            'clicked', self.color_buttons['bordercolor.clicked'])
        self.layout.addRow('opacity', self.border_opacity)
        self.layout.addRow('width', widths)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title) and label.text() not in 'NHC':
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def set_options(self, options):
        for key, button in self.color_buttons.items():
            values = list({option[key] for option in options})
            button.set_color(values[0] if len(values) == 1 else None)

        for key, edit in self.width_edits.items():
            values = list({option[key] for option in options})
            edit.setText(str(values[0]) if len(values) == 1 else None)

        values = list({option['border'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.border.setCurrentText(value)

        values = list({option['bgcolor.transparency'] for option in options})
        self.bg_opacity.set_transparency(
            values[0] if len(values) == 1 else None)

        values = list(
            {option['bordercolor.transparency'] for option in options})
        self.border_opacity.set_transparency(
            values[0] if len(values) == 1 else None)


class ActionSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(ActionSettings, self).__init__(parent)
        self._lactive = BoolCombo(False)
        method = partial(self.optionSet.emit, 'action.left')
        self._lactive.valueSet.connect(method)
        self._lactive.valueSet.connect(self.set_left_enabled)

        self._lclose = BoolCombo(False)
        method = partial(self.optionSet.emit, 'action.left.close')
        self._lclose.valueSet.connect(method)

        self._llanguage = QtWidgets.QComboBox()
        method = partial(self.language_changed, 'left')
        self._llanguage.currentIndexChanged.connect(method)
        self._lcommand = QtWidgets.QPlainTextEdit()
        self._lcommand.setFixedHeight(100)
        self._lsave = QtWidgets.QPushButton('save command')
        self._lsave.released.connect(partial(self.save_command, 'left'))

        self._ractive = BoolCombo(False)
        method = partial(self.optionSet.emit, 'action.right')
        self._ractive.valueSet.connect(method)
        self._ractive.valueSet.connect(self.set_right_enabled)

        self._rclose = BoolCombo(False)
        method = partial(self.optionSet.emit, 'action.right.close')
        self._rclose.valueSet.connect(method)

        self._rlanguage = QtWidgets.QComboBox()
        method = partial(self.language_changed, 'right')
        self._rlanguage.currentIndexChanged.connect(method)
        self._rcommand = QtWidgets.QPlainTextEdit()
        self._rcommand.setFixedHeight(100)
        self._rsave = QtWidgets.QPushButton('save command')
        self._rsave.released.connect(partial(self.save_command, 'right'))

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow(Title('Left click'))
        self.layout.addRow('Has command', self._lactive)
        self.layout.addRow('Close Hotbox', self._lclose)
        self.layout.addRow('Language', self._llanguage)
        self.layout.addRow(self._lcommand)
        self.layout.addRow(self._lsave)
        self.layout.addRow(Title('Right click'))
        self.layout.addRow('Has command', self._ractive)
        self.layout.addRow('Close Hotbox', self._rclose)
        self.layout.addRow('Language', self._rlanguage)
        self.layout.addRow(self._rcommand)
        self.layout.addRow(self._rsave)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def set_languages(self, languages):
        self.blockSignals(True)
        self._llanguage.addItems(languages)
        self._rlanguage.addItems(languages)
        self.blockSignals(False)

    def language_changed(self, side, *_):
        option = 'action.' + side + '.language'
        combo = self._llanguage if side == 'left' else self._rlanguage
        text_edit = self._lcommand if side == 'left' else self._rcommand
        language = combo.currentText()
        highlighter = get_highlighter(language)
        highlighter(text_edit.document())
        self.optionSet.emit(option, language)

    def save_command(self, side):
        text_edit = self._lcommand if side == 'left' else self._rcommand
        option = 'action.' + side + '.command'
        self.optionSet.emit(option, text_edit.toPlainText())

    def set_options(self, options):
        values = list({option['action.left'] for option in options})
        value = values[0] if len(values) == 1 else None
        self._lactive.setCurrentText(str(value))
        self.set_left_enabled(bool(value))

        values = list({option['action.left.close'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self._lclose.setCurrentText(value)

        values = list({option['action.left.language'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self._llanguage.setCurrentText(value)

        if not options or len(options) > 1 or not options[0]['action.left']:
            self._lcommand.setPlainText('')
            self._lcommand.setEnabled(False)
            self._lsave.setEnabled(False)
        else:
            self._lcommand.setPlainText(options[0]['action.left.command'])
            self._lcommand.setEnabled(True)
            self._lsave.setEnabled(True)

        values = list({option['action.right'] for option in options})
        value = values[0] if len(values) == 1 else None
        self._ractive.setCurrentText(str(value))
        self.set_right_enabled(bool(value))

        values = list({option['action.right.close'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self._rclose.setCurrentText(value)

        values = list({option['action.right.language'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self._rlanguage.setCurrentText(value)

        if not options or len(options) > 1 or not options[0]['action.right']:
            self._rcommand.setPlainText('')
            self._rcommand.setEnabled(False)
            self._rsave.setEnabled(False)
        else:
            self._rcommand.setPlainText(options[0]['action.right.command'])
            self._rcommand.setEnabled(True)
            self._rsave.setEnabled(True)

    def set_left_enabled(self, state):
        self._lclose.setEnabled(state)
        self._llanguage.setEnabled(state)
        self._lcommand.setEnabled(state)
        self._lsave.setEnabled(state)

    def set_right_enabled(self, state):
        self._rclose.setEnabled(state)
        self._rlanguage.setEnabled(state)
        self._rcommand.setEnabled(state)
        self._rsave.setEnabled(state)


class TextSettings(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super(TextSettings, self).__init__(parent)
        self.text = QtWidgets.QLineEdit()
        self.text.returnPressed.connect(self.text_changed)

        self.size = FloatEdit(minimum=0.0)
        self.size.valueSet.connect(partial(self.optionSet.emit, 'text.size'))

        self.bold = BoolCheckBox()
        self.bold.valueSet.connect(partial(self.optionSet.emit, 'text.bold'))

        self.italic = BoolCheckBox()
        method = partial(self.optionSet.emit, 'text.italic')
        self.italic.valueSet.connect(method)

        self.color = ColorButton()
        self.color.valueSet.connect(partial(self.optionSet.emit, 'text.color'))

        self.halignement = QtWidgets.QComboBox()
        self.halignement.addItems(list(HALIGNS.keys()))
        self.halignement.currentIndexChanged.connect(self.halign_changed)
        self.valignement = QtWidgets.QComboBox()
        self.valignement.addItems(list(VALIGNS.keys()))
        self.valignement.currentIndexChanged.connect(self.valign_changed)

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow('Content', self.text)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Options'))
        self.layout.addRow('Size', self.size)
        self.layout.addRow('Bold', self.bold)
        self.layout.addRow('Italic', self.italic)
        self.layout.addRow('Color', self.color)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Alignement'))
        self.layout.addRow('Horizontal', self.halignement)
        self.layout.addRow('Vertical', self.valignement)
        for label in self.findChildren(QtWidgets.QLabel):
            if not isinstance(label, Title):
                label.setFixedWidth(LEFT_CELL_WIDTH)

    def text_changed(self):
        self.optionSet.emit('text.content', self.text.text())

    def valign_changed(self):
        self.optionSet.emit('text.valign', self.valignement.currentText())

    def halign_changed(self):
        self.optionSet.emit('text.halign', self.halignement.currentText())

    def set_options(self, options):
        values = list({option['text.content'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.text.setText(value)

        values = list({option['text.size'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.size.setText(value)

        values = list({option['text.bold'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.bold.setCurrentText(value)

        values = list({option['text.italic'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.italic.setCurrentText(value)

        values = list({option['text.color'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.color.set_color(value)

        values = list({option['text.halign'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.halignement.setCurrentText(value)

        values = list({option['text.valign'] for option in options})
        value = str(values[0]) if len(values) == 1 else None
        self.valignement.setCurrentText(value)
