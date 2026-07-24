import os
import json
from hotbox_designer.vendor.Qt import QtWidgets
from hotbox_designer.data import (
    get_new_hotbox, get_valid_name, copy_hotbox_data, load_templates,
    ensure_old_data_compatible)
from hotbox_designer.widgets import TouchEdit, BoolCombo


def warning(title, message, parent=None):
    return QtWidgets.QMessageBox.warning(
        parent,
        title,
        message,
        QtWidgets.QMessageBox.Ok,
        QtWidgets.QMessageBox.Ok)


def import_hotbox():
    filenames = QtWidgets.QFileDialog.getOpenFileName(
        None, 'Import hotbox (or dwpicker file)', os.path.expanduser("~"),
        filter='*.json')
    if not filenames[0]:
        return
    with open(filenames[0], 'r') as f:
        data = json.load(f)
    # un picker dwpicker est reconnu et converti à la volée
    from hotbox_designer.dwpickerimport import (
        is_dwpicker_data, convert_dwpicker_to_hotbox)
    if is_dwpicker_data(data):
        return convert_dwpicker_to_hotbox(data)
    return ensure_old_data_compatible(data)


def import_hotbox_link():
    filenames = QtWidgets.QFileDialog.getOpenFileName(
        None, 'Import hotbox', os.path.expanduser("~"),
        filter='*.json')
    if filenames:
        return filenames[0]
    return None


def export_hotbox(hotbox):
    filenames = QtWidgets.QFileDialog.getSaveFileName(
        None, 'Export hotbox', os.path.expanduser("~"),
        '*.json')
    filename = filenames[0]
    if not filename:
        return
    if not filename.lower().endswith('.json'):
        filename += '.json'
    with open(filename, 'w') as f:
        json.dump(hotbox, f, indent=2)


class CreateHotboxDialog(QtWidgets.QDialog):
    """Création d'une hotbox : nom + source (vide par défaut, dupliquer
    une existante, ou partir d'un template). Les menus ne sont actifs
    que quand leur option est cochée."""

    def __init__(self, hotboxes, parent=None):
        super(CreateHotboxDialog, self).__init__(parent)
        self.setWindowTitle("Create new hotbox")
        self.setMinimumWidth(340)
        self.hotboxes = hotboxes

        self.name_edit = QtWidgets.QLineEdit(get_valid_name(hotboxes))
        self.name_edit.selectAll()

        self.new = QtWidgets.QRadioButton("Empty hotbox")
        self.duplicate = QtWidgets.QRadioButton("Duplicate existing hotbox")
        self.duplicate.setEnabled(bool(self.hotboxes))
        self.template = QtWidgets.QRadioButton("From template")
        self.groupbutton = QtWidgets.QButtonGroup()
        self.groupbutton.addButton(self.new, 0)
        self.groupbutton.addButton(self.duplicate, 1)
        self.groupbutton.addButton(self.template, 2)
        self.new.setChecked(True)

        self.existing = QtWidgets.QComboBox()
        self.existing.addItems([hb['general']['name'] for hb in self.hotboxes])
        self.template_combo = QtWidgets.QComboBox()
        items = [
            hb['general']['name'] or 'template'
            for hb in load_templates()]
        self.template_combo.addItems(items)

        # les combos ne s'activent qu'avec leur option
        self.existing.setEnabled(False)
        self.template_combo.setEnabled(False)
        self.duplicate.toggled.connect(self.existing.setEnabled)
        self.template.toggled.connect(self.template_combo.setEnabled)

        form = QtWidgets.QFormLayout()
        form.addRow('Name:', self.name_edit)

        self.up_layout = QtWidgets.QGridLayout()
        self.up_layout.setContentsMargins(0, 0, 0, 0)
        self.up_layout.setSpacing(6)
        self.up_layout.addWidget(self.new, 0, 0)
        self.up_layout.addWidget(self.duplicate, 1, 0)
        self.up_layout.addWidget(self.existing, 1, 1)
        self.up_layout.addWidget(self.template, 2, 0)
        self.up_layout.addWidget(self.template_combo, 2, 1)

        self.ok = QtWidgets.QPushButton('Create')
        self.ok.setDefault(True)
        self.ok.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton('Cancel')
        self.cancel.released.connect(self.reject)

        self.down_layout = QtWidgets.QHBoxLayout()
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        self.down_layout.addStretch(1)
        self.down_layout.addWidget(self.ok)
        self.down_layout.addWidget(self.cancel)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.addLayout(form)
        self.layout.addLayout(self.up_layout)
        self.layout.addLayout(self.down_layout)

    def hotbox(self):
        checked = self.groupbutton.checkedId()
        hotbox = None
        if checked == 1:
            name = self.existing.currentText()
            sources = [
                hb for hb in self.hotboxes
                if hb['general']['name'] == name]
            if sources:
                hotbox = copy_hotbox_data(sources[0])
        elif checked == 2:
            index = self.template_combo.currentIndex()
            templates = load_templates()
            if 0 <= index < len(templates):
                hotbox = copy_hotbox_data(templates[index])
        if hotbox is None:  # hotbox vide (ou source introuvable)
            hotbox = get_new_hotbox(self.hotboxes)
        # le nom saisi, validé contre les hotboxes EXISTANTES (l'ancien
        # code validait contre les templates : noms en double garantis)
        wanted = self.name_edit.text().strip() or hotbox['general']['name']
        hotbox['general']['name'] = get_valid_name(self.hotboxes, wanted)
        return hotbox


class CommandDisplayDialog(QtWidgets.QDialog):
    def __init__(self, command, parent=None):
        super(CommandDisplayDialog, self).__init__(parent)
        self.setWindowTitle("Command")
        self.text = QtWidgets.QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(command)
        self.ok = QtWidgets.QPushButton('ok')
        self.ok.released.connect(self.accept)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addLayout(self.button_layout)


class HotkeySetter(QtWidgets.QDialog):
    def __init__(self, modes, parent=None):
        super(HotkeySetter, self).__init__(parent)
        self.setWindowTitle("Set hotkey")
        self.ctrl = BoolCombo(False)
        self.alt = BoolCombo(False)
        self.shift = BoolCombo(False)
        self.touch = TouchEdit()
        self.hotkeytype = QtWidgets.QComboBox()
        self.hotkeytype.addItems(modes)

        self.options_layout = QtWidgets.QFormLayout()
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setVerticalSpacing(0)
        self.options_layout.addRow("Ctrl", self.ctrl)
        self.options_layout.addRow("Alt", self.alt)
        self.options_layout.addRow("Shift", self.shift)
        self.options_layout.addRow("Touch", self.touch)
        self.options_layout.addRow("Hotkey event", self.hotkeytype)

        self.ok = QtWidgets.QPushButton("ok")
        self.ok.released.connect(self.accept)
        self.cancel = QtWidgets.QPushButton("cancel")
        self.cancel.released.connect(self.reject)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.ok)
        self.button_layout.addWidget(self.cancel)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.options_layout)
        self.layout.addLayout(self.button_layout)

    def get_key_sequence(self):
        sequence = ''
        if self.ctrl.state() is True:
            sequence += "Ctrl+"
        if self.alt.state() is True:
            sequence += "Alt+"
        if self.shift.state() is True:
            sequence += "Shift+"
        sequence += self.touch.text()
        return sequence

    def mode(self):
        return self.hotkeytype.currentText()


class PasteStyleDialog(QtWidgets.QDialog):
    """Choix des groupes d'options à coller sur les shapes
    sélectionnées (copier/coller de style façon dwpicker)."""

    def __init__(self, groups, parent=None):
        super(PasteStyleDialog, self).__init__(parent)
        self.setWindowTitle('Paste style')
        self.checkboxes = []
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel('Options to paste:'))
        for label, keys, checked in groups:
            checkbox = QtWidgets.QCheckBox(label)
            checkbox.setChecked(checked)
            checkbox.keys = keys
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_keys(self):
        keys = []
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                keys.extend(checkbox.keys)
        return keys


class SearchReplaceDialog(QtWidgets.QDialog):
    """Recherche/remplacement dans les commandes et labels des shapes
    (sélection si elle existe, sinon toute la hotbox)."""

    def __init__(self, replace_callback, parent=None):
        super(SearchReplaceDialog, self).__init__(parent)
        self.setWindowTitle('Search and replace')
        self.setMinimumWidth(340)
        self.replace_callback = replace_callback

        self.search = QtWidgets.QLineEdit()
        self.replace = QtWidgets.QLineEdit()
        self.in_left = QtWidgets.QCheckBox('Left click commands')
        self.in_left.setChecked(True)
        self.in_right = QtWidgets.QCheckBox('Right click commands')
        self.in_right.setChecked(True)
        self.in_labels = QtWidgets.QCheckBox('Button labels (text)')
        self.result = QtWidgets.QLabel('')

        form = QtWidgets.QFormLayout()
        form.addRow('Search:', self.search)
        form.addRow('Replace by:', self.replace)

        apply_button = QtWidgets.QPushButton('Replace all')
        apply_button.released.connect(self._apply)
        close_button = QtWidgets.QPushButton('Close')
        close_button.released.connect(self.close)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(apply_button)
        buttons.addWidget(close_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.in_left)
        layout.addWidget(self.in_right)
        layout.addWidget(self.in_labels)
        layout.addWidget(self.result)
        layout.addLayout(buttons)

    def _apply(self):
        if not self.search.text():
            self.result.setText('Nothing to search')
            return
        count = self.replace_callback(
            self.search.text(), self.replace.text(),
            self.in_left.isChecked(), self.in_right.isChecked(),
            self.in_labels.isChecked())
        self.result.setText('%d replacement(s) done' % count)
