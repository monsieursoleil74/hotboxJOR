
import os
from functools import partial
from hotboxLibrary.vendor.Qt import QtWidgets, QtCore, QtGui

from hotboxLibrary.commands import OPEN_COMMAND, CLOSE_COMMAND, SWITCH_COMMAND
from hotboxLibrary.reader import HotboxReader
from hotboxLibrary.designer.application import HotboxEditor
from hotboxLibrary.applications import (
    Nuke, Maya, Houdini, Rumba, Standalone)
from hotboxLibrary.widgets import BoolCombo, Title, CommandButton
from hotboxLibrary.qtutils import icon
from hotboxLibrary.dialog import (
    import_hotbox, export_hotbox, import_hotbox_link, CreateHotboxDialog,
    CommandDisplayDialog, HotkeySetter, HotkeyManagerDialog, warning)
from hotboxLibrary.data import (
    get_valid_name, TRIGGERING_TYPES, save_datas, load_hotboxes_datas,
    hotbox_data_to_html, load_json, save_hotbox_as_template,
    read_hotbox_file, load_shared_hotbox, HotboxFileError)


hotboxes = {}          # hotboxes CONSTRUITES (fenêtres prêtes)
# hotboxes LUES mais pas encore construites : on ne construit une hotbox
# (et ne charge ses icônes, souvent sur le réseau) qu'au moment où on
# l'appelle. Avant, le tout premier appel de la session construisait
# TOUTES les hotboxes avec TOUTES leurs icônes : le freeze du 1er appel.
_pending = {}
_application = None   # celle du dernier chargement (pour recharger)
# préchauffage : après le 1er affichage, les ICÔNES des autres hotboxes
# sont chargées en tâche de fond, UNE par passage de la boucle Qt (une
# icône réseau = quelques ms, imperceptible) ; construire la fenêtre au
# moment de l'appel ne coûte alors presque rien
WARM_UP_DELAY_MS = 400
WARM_UP_STEP_MS = 15
_load_generation = [0]
_warm_up_scheduled = [False]
hotbox_manager = None
APPLICATIONS = {
    'maya': Maya,
    'nuke': Nuke,
    'houdini': Houdini,
    'rumba': Rumba,
    'standalone': Standalone}


def launch_manager(application, studio_admin=False):
    """Ouvre le manager. `studio_admin=True` = mode lead : la librairie
    studio devient éditable (catégories officielles, envoi de boutons).
    Sans le paramètre (les animateurs), elle est en lecture seule et
    chacun travaille dans sa librairie perso."""
    from hotboxLibrary.buttonlibrary import (
        set_studio_admin, refresh_shelves)
    global hotbox_manager
    set_studio_admin(studio_admin)
    if hotbox_manager is None:
        hotbox_manager = HotboxManager(APPLICATIONS[application]())
    # la fenêtre porte toujours le nom du tool ; le mode se lit sur le
    # badge vert STUDIO ADMIN du bandeau (et de l'éditeur)
    hotbox_manager.setWindowTitle('Hotbox Designer')
    hotbox_manager.header.refresh()
    # changement de mode SANS redémarrer Maya : les shelves déjà
    # ouvertes (badge, infobulles, menus) basculent immédiatement
    refresh_shelves()
    hotbox_manager.show()


def initialize(application):
    if hotboxes or _pending:
        return
    load_hotboxes(application)


def loaded_names():
    """Noms des hotboxes chargées, construites ou en attente."""
    return sorted(set(hotboxes) | set(_pending))


def load_hotboxes(application):
    global _application
    from hotboxLibrary.images import register_image_root
    _application = application
    hotboxes_datas = load_hotboxes_datas(application.local_file)
    file_ = application.shared_file
    links = load_json(file_, default=[])
    for link in links:
        # une hotbox partagée transporte souvent ses icônes à côté
        register_image_root(os.path.dirname(link))
        # lien mort (lecteur réseau absent, fichier déplacé) : on
        # l'ignore — avant, UN lien cassé empêchait TOUTES les hotboxes
        # de s'ouvrir (traceback sur le raccourci)
        shared = load_shared_hotbox(link)
        if shared is None:
            continue
        hotboxes_datas.append(shared)

    for hotboxes_data in hotboxes_datas:
        name = hotboxes_data['general']['name']
        _pending[name] = hotboxes_data


def _build(name):
    """Construit la hotbox `name` (fenêtre + icônes) si elle attend."""
    data = _pending.pop(name, None)
    if data is None:
        return hotboxes.get(name)
    reader = HotboxReader(data, parent=None)
    reader.hideSubmenusRequested.connect(hide_submenus)
    hotboxes[name] = reader
    return reader


def _pending_image_paths():
    """Icônes des hotboxes en attente, sans doublon, dans l'ordre."""
    paths = []
    for data in _pending.values():
        for shape in data.get('shapes', []):
            path = shape.get('image.path')
            if path and path not in paths:
                paths.append(path)
    return paths


def _schedule_warm_up():
    if _warm_up_scheduled[0] or not _pending:
        return
    _warm_up_scheduled[0] = True
    generation = _load_generation[0]
    queue = _pending_image_paths()
    QtCore.QTimer.singleShot(
        WARM_UP_DELAY_MS, lambda: _warm_up_step(generation, queue))


def _warm_up_step(generation, queue):
    """Charge UNE icône en cache puis rend la main à Maya ; se relance
    tant qu'il en reste. Abandonné si les hotboxes ont été rechargées
    entre-temps (édition dans le manager)."""
    from hotboxLibrary.images import image_pixmap
    if generation != _load_generation[0] or not queue:
        return
    try:
        image_pixmap(queue.pop(0))
    except Exception:
        # une icône abîmée ne doit pas casser le préchauffage
        pass
    if queue:
        QtCore.QTimer.singleShot(
            WARM_UP_STEP_MS, lambda: _warm_up_step(generation, queue))


def warm_up_now():
    """Construit tout de suite les hotboxes en attente (diagnostic, ou
    pour préchauffer volontairement depuis un script de démarrage)."""
    for name in list(_pending):
        _build(name)


def clear_loaded_hotboxes():
    global hotboxes
    hotboxes = {}
    _pending.clear()
    _load_generation[0] += 1
    _warm_up_scheduled[0] = False


def _reader(name):
    """La hotbox `name`, construite à la demande. Si elle manque
    (sous-menu créé ou lié APRÈS le chargement, par exemple), on
    recharge une fois depuis les fichiers ; si elle manque toujours, un
    message clair plutôt qu'un KeyError dans le script editor."""
    reader = hotboxes.get(name) or _build(name)
    if reader is None and _application is not None:
        clear_loaded_hotboxes()
        load_hotboxes(_application)
        reader = _build(name)
    if reader is None:
        warning(
            'Hotbox designer',
            'Hotbox "%s" not found.\nCheck its name in the manager '
            '(personal or shared tab).' % name)
    return reader


def show(name):
    reader = _reader(name)
    if reader is not None:
        reader.show()
        _schedule_warm_up()


def hide(name):
    reader = hotboxes.get(name)   # pas chargée = déjà « cachée »
    if reader is not None:
        reader.hide()


def switch(name):
    reader = _reader(name)
    if reader is None:
        return
    if reader.isVisible():
        return hide(name)
    return show(name)


def hide_submenus():
    for name in hotboxes:
        if hotboxes[name].is_submenu:
            hide(name)


class HotboxManager(QtWidgets.QWidget):
    def __init__(self, application):
        parent = application.main_window
        super(HotboxManager, self).__init__(parent, QtCore.Qt.Tool)
        from hotboxLibrary.theme import apply_dark_theme
        from hotboxLibrary.buttonlibrary import restore_studio_location
        apply_dark_theme(self)
        self.application = application
        # la librairie studio mémorisée est active dès le manager (le
        # registre ƒ et le mode admin la voient sans ouvrir d'éditeur)
        restore_studio_location(application)
        # une fenêtre d'édition par hotbox, toutes ouvrables en même
        # temps (le copier-coller passe par le presse-papier système)
        self.editors = []

        hotboxes_data = load_hotboxes_datas(self.application.local_file)
        self.personnal_model = HotboxPersonalTableModel(hotboxes_data)
        self.personnal_view = HotboxTableView()
        self.personnal_view.set_model(self.personnal_model)
        method = self._personnal_selected_row_changed
        self.personnal_view.selectedRowChanged.connect(method)

        self.toolbar = HotboxManagerToolbar()
        self.toolbar.link.setEnabled(False)
        self.toolbar.unlink.setEnabled(False)
        self.toolbar.newRequested.connect(self._call_create)
        self.toolbar.linkRequested.connect(self._call_add_link)
        self.toolbar.unlinkRequested.connect(self._call_unlink)
        self.toolbar.editRequested.connect(self._call_edit)
        self.toolbar.deleteRequested.connect(self._call_remove)
        self.toolbar.importRequested.connect(self._call_import)
        self.toolbar.exportRequested.connect(self._call_export)
        self.toolbar.saveTemplateRequested.connect(self._call_save_template)
        self.toolbar.manageHotkeysRequested.connect(self._call_manage_hotkeys)
        setter_enabled = bool(application.available_set_hotkey_modes)
        self.toolbar.hotkeyset.setEnabled(setter_enabled)

        self.edit = HotboxGeneralSettingWidget()
        self.edit.optionSet.connect(self._call_option_set)
        self.edit.setEnabled(False)
        self.edit.switch_command.released.connect(self._call_switch_command)

        self.personnal = QtWidgets.QWidget()
        self.hlayout = QtWidgets.QHBoxLayout(self.personnal)
        self.hlayout.setContentsMargins(8, 0, 8, 8)
        self.hlayout.setSpacing(4)
        self.hlayout.addWidget(self.personnal_view)
        self.hlayout.addWidget(self.edit)

        links = load_json(application.shared_file, default=[])
        self.shared_model = HotboxSharedTableModel(links)
        self.shared_view = HotboxTableView()
        self.shared_view.set_model(self.shared_model)
        method = self._shared_selected_row_changed
        self.shared_view.selectedRowChanged.connect(method)

        self.infos = HotboxGeneralInfosWidget()
        self.infos.setEnabled(False)
        self.infos.switch_command.released.connect(self._call_switch_command)

        self.shared = QtWidgets.QWidget()
        self.hlayout2 = QtWidgets.QHBoxLayout(self.shared)
        self.hlayout2.setContentsMargins(8, 0, 8, 8)
        self.hlayout2.setSpacing(4)
        self.hlayout2.addWidget(self.shared_view)
        self.hlayout2.addWidget(self.infos)

        self.tabwidget = QtWidgets.QTabWidget()
        self.tabwidget.addTab(self.personnal, "Personal")
        self.tabwidget.addTab(self.shared, "Shared")
        self.tabwidget.currentChanged.connect(self.tab_index_changed)

        # les raccourcis assignés s'affichent directement dans les
        # listes (2e colonne) — plus besoin d'ouvrir le dialogue
        self._refresh_hotkeys_display()

        self.header = _ManagerHeader()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.tabwidget)

    def get_selected_hotbox(self):
        index = self.tabwidget.currentIndex()
        table = self.shared_view if index else self.personnal_view
        model = self.shared_model if index else self.personnal_model
        row = table.get_selected_row()
        if row is None:
            return
        return model.hotboxes[row]

    def _refresh_hotkeys_display(self):
        """Recharge le registre des raccourcis dans les deux listes."""
        hotkeys = self.application.load_hotkeys()
        self.personnal_model.set_hotkeys(hotkeys)
        self.shared_model.set_hotkeys(hotkeys)

    def save_hotboxes(self, *_):
        save_datas(self.application.local_file, self.personnal_model.hotboxes)
        datas = self.shared_model.hotboxes_links
        save_datas(self.application.shared_file, datas)
        try:
            self.application.update_hotkeys()
        except Exception as e:
            raise e

    def _personnal_selected_row_changed(self):
        hotbox = self.get_selected_hotbox()
        if hotbox is not None:
            self.edit.set_hotbox_settings(hotbox['general'])
            self.edit.set_preview(hotbox)
            self.edit.setEnabled(True)
        else:
            self.edit.setEnabled(False)

    def tab_index_changed(self):
        index = self.tabwidget.currentIndex()
        self.toolbar.edit.setEnabled(index == 0)
        self.toolbar.delete.setEnabled(index == 0)
        self.toolbar.link.setEnabled(index == 1)
        self.toolbar.unlink.setEnabled(index == 1)
        # l'infobulle d'Import dit ce qu'il va faire selon l'onglet
        self.toolbar.import_.setToolTip(
            'Import hotbox file as a shared link (the file stays in place)'
            if index == 1 else 'Import hotbox (copy into my hotboxes)')

    def hotbox_data_modified(self, link, hotbox_data):
        # la hotbox est retrouvée par identité, pas par ligne
        # sélectionnée : plusieurs éditeurs peuvent écrire en parallèle
        try:
            row = self.personnal_model.hotboxes.index(link.data)
        except ValueError:
            return  # hotbox supprimée entre-temps
        self.personnal_model.set_hotbox(row, hotbox_data)
        link.data = self.personnal_model.hotboxes[row]
        clear_loaded_hotboxes()
        self.save_hotboxes()

    def _shared_selected_row_changed(self):
        index = self.shared_view.get_selected_row()
        hotbox = self.shared_model.hotboxes[index]
        if hotbox is not None:
            self.infos.set_hotbox_data(hotbox)
            self.infos.setEnabled(True)
        else:
            self.infos.setEnabled(False)

    def _get_switch_command(self):
        hotbox = self.get_selected_hotbox()
        if not hotbox:
            return warning('Hotbox designer', 'No hotbox selected')
        return SWITCH_COMMAND.format(
            application=self.application.name,
            name=hotbox['general']['name'])

    def _call_switch_command(self):
        CommandDisplayDialog(self._get_switch_command(), self).exec_()

    def _call_edit(self):
        if self.tabwidget.currentIndex():
            return

        hotbox_data = self.get_selected_hotbox()
        if hotbox_data is None:
            return warning('Hotbox designer', 'No hotbox selected')

        # déjà ouverte ? on ramène sa fenêtre au premier plan
        for link in self.editors:
            if link.data is hotbox_data:
                link.editor.show()
                link.editor.raise_()
                link.editor.activateWindow()
                return

        editor = HotboxEditor(
            hotbox_data,
            self.application,
            parent=self.application.main_window,
            # perso ET partagées : un sous-menu peut être une hotbox
            # partagée (au studio, elles le sont presque toutes)
            all_hotboxes=lambda: (self.personnal_model.hotboxes
                                  + self.shared_model.hotboxes))
        link = _EditorLink(editor, hotbox_data)
        editor.hotboxDataModified.connect(
            partial(self.hotbox_data_modified, link))
        self.editors.append(link)
        editor.show()

    def user_templates_folder(self):
        """Templates utilisateur : dans le dossier du fork. Les .json
        d'un ancien dossier `templates/` à la racine des prefs sont
        rapatriés fichier par fichier (on ne déplace pas le dossier en
        bloc : un `templates/` à la racine des prefs pourrait appartenir
        à un autre outil)."""
        from hotboxLibrary.applications import migrate_legacy_file
        folder = os.path.join(
            self.application.get_fork_folder(), 'templates')
        legacy = os.path.join(
            self.application.get_data_folder(), 'templates')
        if legacy != folder and os.path.isdir(legacy):
            for name in os.listdir(legacy):
                if name.lower().endswith('.json'):
                    migrate_legacy_file(
                        os.path.join(legacy, name),
                        os.path.join(folder, name))
            try:
                os.rmdir(legacy)  # seulement s'il est vide
            except OSError:
                pass
        return folder

    def _call_create(self):
        hotboxes_ = self.personnal_model.hotboxes + self.shared_model.hotboxes
        dialog = CreateHotboxDialog(
            hotboxes_, self, templates_folder=self.user_templates_folder())
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Rejected:
            return

        self.personnal_model.layoutAboutToBeChanged.emit()
        self.personnal_model.hotboxes.append(dialog.hotbox())
        self.personnal_model.layoutChanged.emit()
        # retrieve and selected last hotbox in the list (who's the new one)
        hotbox_count = len(self.personnal_model.hotboxes) - 1
        if hotbox_count > -1:
            self.personnal_view.selectRow(hotbox_count)

        self.save_hotboxes()
        clear_loaded_hotboxes()

    def _call_add_link(self):
        filename = import_hotbox_link(self)
        if not filename:
            return  # annulé
        # on VÉRIFIE avant de lier : un lien vers un fichier invalide
        # (ou une liste de hotboxes) cassait l'affichage du manager et
        # le chargement de toutes les hotboxes au raccourci
        try:
            hotboxes = read_hotbox_file(filename)
        except HotboxFileError as error:
            return warning('Import hotbox', str(error), self)
        if len(hotboxes) != 1:
            return warning(
                'Import hotbox',
                '"%s" contains %d hotboxes.\n\nA shared link points to '
                'ONE hotbox. Import this file in the Personal tab, or '
                'export a single hotbox from the manager and link that '
                'file.' % (os.path.basename(filename), len(hotboxes)),
                self)
        links = [os.path.normcase(os.path.abspath(link))
                 for link in self.shared_model.hotboxes_links]
        target = os.path.normcase(os.path.abspath(filename))
        if target in links:
            self.shared_view.selectRow(links.index(target))
            return warning(
                'Import hotbox', 'This file is already linked.', self)
        name = hotboxes[0]['general']['name']
        if name in self._hotbox_names():
            return warning(
                'Import hotbox',
                'A hotbox named "%s" already exists.\n\nRename one of '
                'them first: two hotboxes cannot share a name.' % name,
                self)
        self.shared_model.add_link(filename)
        # retrieve and selected last hotbox in the list (who's the new one)
        hotbox_count = len(self.shared_model.hotboxes) - 1
        if hotbox_count > -1:
            self.shared_view.selectRow(hotbox_count)

        self.save_hotboxes()
        clear_loaded_hotboxes()

    def _call_unlink(self):
        index = self.shared_view.get_selected_row()
        if index is None:
            return warning('Hotbox designer', 'No hotbox selected')
        self.shared_model.remove_link(index)
        self.save_hotboxes()
        clear_loaded_hotboxes()

    def _call_remove(self):
        hotbox = self.get_selected_hotbox()
        if hotbox is None:
            return warning('Hotbox designer', 'No hotbox selected')

        areyousure = QtWidgets.QMessageBox.question(
            self,
            'remove',
            'remove a hotbox is definitive, are you sure to continue',
            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            defaultButton=QtWidgets.QMessageBox.No)

        if areyousure == QtWidgets.QMessageBox.No:
            return

        self.personnal_model.layoutAboutToBeChanged.emit()
        self.personnal_model.hotboxes.remove(hotbox)
        self.personnal_model.layoutChanged.emit()
        self.save_hotboxes()
        clear_loaded_hotboxes()

    def _call_option_set(self, option, value):
        self.personnal_model.layoutAboutToBeChanged.emit()
        hotbox = self.get_selected_hotbox()
        if option == 'name':
            value = get_valid_name(self.personnal_model.hotboxes, value)

        if hotbox is not None:
            hotbox['general'][option] = value
        self.personnal_model.layoutChanged.emit()
        self.save_hotboxes()
        clear_loaded_hotboxes()

    def _hotbox_names(self):
        """Toutes les hotboxes qu'un raccourci peut ouvrir : les perso
        ET les partagées (onglet Shared) — le gestionnaire ne listait
        que les perso, impossible de poser une touche sur une hotbox
        partagée. Dédoublonné, ordre d'affichage conservé."""
        names = []
        for hotbox in (self.personnal_model.hotboxes
                       + self.shared_model.hotboxes):
            name = (hotbox or {}).get('general', {}).get('name')
            if name and name not in names:
                names.append(name)
        return names

    def _call_manage_hotkeys(self):
        """Gestionnaire de raccourcis : liste toutes les hotboxes avec leur
        touche assignée (lue dans le registre), permet d'assigner ou de
        retirer chacune — ce qui manquait jusqu'ici (on ne pouvait
        qu'assigner, jamais voir ni effacer)."""
        modes = self.application.available_set_hotkey_modes
        dialog = HotkeyManagerDialog(
            self._hotbox_names(),
            self.application.load_hotkeys,
            bool(modes),
            self._assign_hotkey,
            self._clear_hotkey,
            parent=self)
        dialog.exec_()

    def _assign_hotkey(self, name):
        """Ouvre le sélecteur de touche pour `name` et pose le raccourci.
        Retourne True si un raccourci a été posé."""
        modes = self.application.available_set_hotkey_modes
        dialog = HotkeySetter(modes, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Rejected:
            return False
        self.application.set_hotkey(
            name=name,
            mode=dialog.mode(),
            sequence=dialog.get_key_sequence(),
            open_cmd=OPEN_COMMAND.format(
                name=name, application=self.application.name),
            close_cmd=CLOSE_COMMAND.format(name=name),
            switch_cmd=SWITCH_COMMAND.format(
                name=name, application=self.application.name))
        self._refresh_hotkeys_display()
        return True

    def _clear_hotkey(self, name):
        self.application.remove_hotkey(name)
        self._refresh_hotkeys_display()

    def _call_export(self):
        hotbox = self.get_selected_hotbox()
        if not hotbox:
            return warning('Hotbox designer', 'No hotbox selected')
        export_hotbox(hotbox)

    def _call_save_template(self):
        """Enregistre la hotbox sélectionnée comme template : elle
        apparaîtra dans « From template » à la création."""
        hotbox = self.get_selected_hotbox()
        if not hotbox:
            return warning('Hotbox designer', 'No hotbox selected')
        path = save_hotbox_as_template(self.user_templates_folder(), hotbox)
        if path is None:
            return warning(
                'Hotbox designer', 'Could not write the template file')
        QtWidgets.QMessageBox.information(
            self, 'Template',
            '"%s" saved as template.\nIt is now available in the '
            '"From template" list when creating a hotbox.'
            % hotbox['general']['name'])

    def _call_import(self):
        """Import : dans l'onglet Personal, une COPIE entre dans ma liste ;
        dans l'onglet Shared, le fichier est LIÉ en place (comme le bouton
        chaîne) — le .json reste où il est, tout le monde suit ses mises
        à jour. Avant, Import copiait toujours dans les perso, quel que
        soit l'onglet (bug remonté au studio)."""
        if self.tabwidget.currentIndex() == 1:
            return self._call_add_link()
        filename = import_hotbox(self)
        if not filename:
            return  # annulé : pas de message
        try:
            incoming = read_hotbox_file(filename)
        except HotboxFileError as error:
            return warning('Import hotbox', str(error), self)
        # noms uniques parmi les perso ET les partagées (deux hotboxes
        # de même nom se marchaient dessus au chargement)
        taken = [{'general': {'name': n}} for n in self._hotbox_names()]
        self.personnal_model.layoutAboutToBeChanged.emit()
        names = []
        for hotbox in incoming:
            name = get_valid_name(taken, hotbox['general']['name'])
            hotbox['general']['name'] = name
            taken.append({'general': {'name': name}})
            self.personnal_model.hotboxes.append(hotbox)
            names.append(name)
        self.personnal_model.layoutChanged.emit()
        self.personnal_view.selectRow(
            len(self.personnal_model.hotboxes) - 1)
        self.save_hotboxes()
        clear_loaded_hotboxes()
        if len(names) > 1:
            QtWidgets.QMessageBox.information(
                self, 'Import hotbox',
                '%d hotboxes imported:\n%s' % (
                    len(names), '\n'.join(names)))


class _EditorLink():
    """Attache une fenêtre d'édition à sa hotbox dans le modèle (l'objet
    est remplacé à chaque modification, on suit le remplacement)."""

    def __init__(self, editor, data):
        self.editor = editor
        self.data = data


class _ManagerHeader(QtWidgets.QWidget):
    """Bandeau du manager : barre verte PLEINE LARGEUR « STUDIO ADMIN »
    en mode lead ; complètement masqué en mode animateur (une bande
    vide ne servait à rien)."""

    def __init__(self, parent=None):
        super(_ManagerHeader, self).__init__(parent)
        from hotboxLibrary.theme import ACCENT
        self.setFixedHeight(32)
        # sans WA_StyledBackground, un QWidget sous-classé ne peint pas
        # le fond défini par stylesheet
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet('_ManagerHeader {background: %s;}' % ACCENT)
        self.admin_badge = QtWidgets.QLabel('STUDIO ADMIN')
        self.admin_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.admin_badge.setStyleSheet(
            'QLabel {color: white; background: transparent;'
            'font-weight: bold; font-size: 12px; letter-spacing: 4px;}')
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.admin_badge)
        self.refresh()

    def refresh(self):
        from hotboxLibrary.buttonlibrary import is_studio_admin
        self.setVisible(is_studio_admin())


class HotboxManagerToolbar(QtWidgets.QToolBar):
    newRequested = QtCore.Signal()
    editRequested = QtCore.Signal()
    deleteRequested = QtCore.Signal()
    linkRequested = QtCore.Signal()
    unlinkRequested = QtCore.Signal()
    importRequested = QtCore.Signal()
    exportRequested = QtCore.Signal()
    saveTemplateRequested = QtCore.Signal()
    manageHotkeysRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(HotboxManagerToolbar, self).__init__(parent)
        self.setIconSize(QtCore.QSize(16, 16))
        self.new = QtWidgets.QAction(icon('manager-new.png'), '', self)
        self.new.setToolTip('Create new hotbox')
        self.new.triggered.connect(self.newRequested.emit)
        self.edit = QtWidgets.QAction(icon('manager-edit.png'), '', self)
        self.edit.setToolTip('Edit hotbox')
        self.edit.triggered.connect(self.editRequested.emit)
        self.delete = QtWidgets.QAction(icon('manager-delete.png'), '', self)
        self.delete.setToolTip('Delete hotbox')
        self.delete.triggered.connect(self.deleteRequested.emit)
        self.link = QtWidgets.QAction(icon('link.png'), '', self)
        self.link.setToolTip('Link to external hotbox file')
        self.link.triggered.connect(self.linkRequested.emit)
        self.unlink = QtWidgets.QAction(icon('unlink.png'), '', self)
        self.unlink.setToolTip('Remove hotbox file link')
        self.unlink.triggered.connect(self.unlinkRequested.emit)
        self.import_ = QtWidgets.QAction(icon('manager-import.png'), '', self)
        self.import_.setToolTip('Import hotbox')
        self.import_.triggered.connect(self.importRequested.emit)
        self.export = QtWidgets.QAction(icon('manager-export.png'), '', self)
        self.export.setToolTip('Export hotbox')
        self.export.triggered.connect(self.exportRequested.emit)
        self.savetemplate = QtWidgets.QAction(icon('save.png'), '', self)
        self.savetemplate.setToolTip(
            'Save hotbox as template (reusable in "From template")')
        self.savetemplate.triggered.connect(self.saveTemplateRequested.emit)
        self.hotkeyset = QtWidgets.QAction(icon('touch.png'), '', self)
        self.hotkeyset.setToolTip('Manage hotkeys')
        self.hotkeyset.triggered.connect(self.manageHotkeysRequested.emit)

        self.addAction(self.new)
        self.addAction(self.edit)
        self.addAction(self.delete)
        self.addSeparator()
        self.addAction(self.link)
        self.addAction(self.unlink)
        self.addSeparator()
        self.addAction(self.import_)
        self.addAction(self.export)
        self.addAction(self.savetemplate)
        self.addSeparator()
        self.addAction(self.hotkeyset)


class HotboxTableView(QtWidgets.QTableView):
    selectedRowChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(HotboxTableView, self).__init__(parent)
        self.selection_model = None
        vheader = self.verticalHeader()
        vheader.hide()
        vheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        hheader = self.horizontalHeader()
        hheader.hide()
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        vheader.setDefaultSectionSize(34)  # lignes plus hautes et aérées
        self.setStyleSheet(
            'QTableView {border: none; background: #313131;'
            'alternate-background-color: #353535;}'
            'QTableView::item {padding: 4px 10px; border: none;}'
            'QTableView::item:selected {background: #6d8c5e;'
            'color: #ffffff;}')

    def selection_changed(self, *_):
        return self.selectedRowChanged.emit()

    def set_model(self, model):
        self.setModel(model)
        hheader = self.horizontalHeader()
        hheader.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        hheader.setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents)
        self.selection_model = self.selectionModel()
        self.selection_model.selectionChanged.connect(self.selection_changed)

    def get_selected_row(self):
        indexes = self.selection_model.selectedIndexes()
        rows = list({index.row() for index in indexes})
        if not rows:
            return None
        return rows[0]


HOTKEY_COLUMN_ROLE_COLOR = '#8c8c8c'


def _hotkey_column_data(hotkeys, name, role):
    """Rendu de la colonne raccourci des listes du manager : la
    séquence assignée, en grisé, alignée à droite."""
    if role == QtCore.Qt.DisplayRole:
        record = hotkeys.get(name) or {}
        return record.get('sequence') or ''
    if role == QtCore.Qt.ForegroundRole:
        return QtGui.QBrush(QtGui.QColor(HOTKEY_COLUMN_ROLE_COLOR))
    if role == QtCore.Qt.TextAlignmentRole:
        return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)


class HotboxPersonalTableModel(QtCore.QAbstractTableModel):

    def __init__(self, hotboxes, parent=None):
        super(HotboxPersonalTableModel, self).__init__(parent=parent)
        self.hotboxes = hotboxes
        self.hotkeys = {}

    def set_hotkeys(self, hotkeys):
        """Registre {nom: {'sequence', …}} affiché en 2e colonne."""
        self.layoutAboutToBeChanged.emit()
        self.hotkeys = hotkeys or {}
        self.layoutChanged.emit()

    def columnCount(self, _):
        return 2

    def rowCount(self, _):
        return len(self.hotboxes)

    def set_hotbox(self, row, hotbox):
        self.layoutAboutToBeChanged.emit()
        self.hotboxes[row] = hotbox
        self.layoutChanged.emit()

    def data(self, index, role):
        row, col = index.row(), index.column()
        hotbox = self.hotboxes[row]
        if col == 1:
            return _hotkey_column_data(
                self.hotkeys, hotbox['general']['name'], role)
        if role == QtCore.Qt.DisplayRole and col == 0:
            return hotbox['general']['name']


class HotboxSharedTableModel(QtCore.QAbstractTableModel):

    def __init__(self, hotboxes_links, parent=None):
        super(HotboxSharedTableModel, self).__init__(parent=parent)
        self.hotboxes_links = hotboxes_links
        # un lien manquant / illisible vaut None (affiché vide) au lieu
        # de faire planter l'ouverture du manager
        self.hotboxes = [load_shared_hotbox(l) for l in hotboxes_links]
        self.hotkeys = {}

    def set_hotkeys(self, hotkeys):
        self.layoutAboutToBeChanged.emit()
        self.hotkeys = hotkeys or {}
        self.layoutChanged.emit()

    def columnCount(self, _):
        return 2

    def rowCount(self, _):
        return len(self.hotboxes_links)

    def add_link(self, hotbox_link):
        self.layoutAboutToBeChanged.emit()
        self.hotboxes_links.append(hotbox_link)
        self.hotboxes.append(load_shared_hotbox(hotbox_link))
        self.layoutChanged.emit()

    def remove_link(self, index):
        self.layoutAboutToBeChanged.emit()
        self.hotboxes_links.pop(index)
        self.hotboxes.pop(index)
        self.layoutChanged.emit()

    def data(self, index, role):
        row, col = index.row(), index.column()
        if col == 1:
            hotbox = self.hotboxes[row]
            name = hotbox['general']['name'] if hotbox else ''
            return _hotkey_column_data(self.hotkeys, name, role)
        if role == QtCore.Qt.DisplayRole and col == 0:
            return self.hotboxes_links[row]


class HotboxGeneralInfosWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HotboxGeneralInfosWidget, self).__init__(parent)
        self.setFixedWidth(200)
        self.label = QtWidgets.QLabel()
        # seule la commande switch reste exposée : un clic ouvre, un
        # re-clic ferme — c'est elle qu'on colle sur un bouton de shelf.
        # show/hide sont câblés automatiquement par les raccourcis.
        self.switch_command = CommandButton('switch')

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(Title('Infos'))
        self.layout.addSpacing(8)
        self.layout.addWidget(self.label)
        self.layout.addSpacing(8)
        self.layout.addStretch(1)
        self.layout.addWidget(Title('Commands'))
        self.layout.addSpacing(8)
        self.layout.addWidget(self.switch_command)

    def set_hotbox_data(self, hotbox_data):
        self.label.setText(hotbox_data_to_html(hotbox_data))


class HotboxGeneralSettingWidget(QtWidgets.QWidget):
    optionSet = QtCore.Signal(str, object)
    applyRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(HotboxGeneralSettingWidget, self).__init__(parent)
        self.setFixedWidth(200)
        self.preview = QtWidgets.QLabel()
        self.preview.setFixedHeight(120)
        self.preview.setAlignment(QtCore.Qt.AlignCenter)
        self.preview.setStyleSheet(
            'background: #2b2b2b; border: 1px solid #494949;'
            'border-radius: 3px;')
        self.name = QtWidgets.QLineEdit()
        self.name.textEdited.connect(partial(self.optionSet.emit, 'name'))
        self.submenu = BoolCombo(False)
        self.submenu.valueSet.connect(partial(self.optionSet.emit, 'submenu'))
        self.triggering = QtWidgets.QComboBox()
        self.triggering.addItems(TRIGGERING_TYPES)
        self.triggering.currentIndexChanged.connect(self._triggering_changed)
        self.aiming = BoolCombo(False)
        self.aiming.valueSet.connect(partial(self.optionSet.emit, 'aiming'))
        self.leaveclose = BoolCombo(False)
        method = partial(self.optionSet.emit, 'leaveclose')
        self.leaveclose.valueSet.connect(method)

        self.switch_command = CommandButton('switch')

        self.layout = QtWidgets.QFormLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setHorizontalSpacing(5)
        self.layout.addRow(Title('Preview'))
        self.layout.addItem(QtWidgets.QSpacerItem(0, 4))
        self.layout.addRow(self.preview)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Options'))
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow('name', self.name)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow('is submenu', self.submenu)
        self.layout.addRow('triggering', self.triggering)
        self.layout.addRow('aiming', self.aiming)
        self.layout.addRow('close on leave', self.leaveclose)
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(Title('Commands'))
        self.layout.addItem(QtWidgets.QSpacerItem(0, 8))
        self.layout.addRow(self.switch_command)

    def set_preview(self, hotbox_data):
        from hotboxLibrary.buttonlibrary import hotbox_thumbnail
        self.preview.setPixmap(hotbox_thumbnail(hotbox_data))

    def _triggering_changed(self, _):
        self.optionSet.emit('triggering', self.triggering.currentText())

    def _touch_changed(self, _):
        self.optionSet.emit('touch', self.touch.text())

    def set_hotbox_settings(self, hotbox_settings):
        self.blockSignals(True)
        self.submenu.setCurrentText(str(hotbox_settings['submenu']))
        self.name.setText(hotbox_settings['name'])
        self.triggering.setCurrentText(hotbox_settings['triggering'])
        self.aiming.setCurrentText(str(hotbox_settings['aiming']))
        self.leaveclose.setCurrentText(str(hotbox_settings['leaveclose']))
        self.blockSignals(False)
