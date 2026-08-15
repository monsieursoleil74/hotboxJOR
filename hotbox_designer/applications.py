import os
import json
import shutil
from hotbox_designer.vendor.Qt import QtWidgets
from hotbox_designer.dialog import warning
from hotbox_designer.languages import (
    MEL, PYTHON, NUKE_TCL, NUKE_EXPRESSION, HSCRIPT, RUMBA_SCRIPT)


HOTBOXES_FILENAME = 'hotboxes.json'
SHARED_HOTBOXES_FILENAME = 'shared_hotboxes.json'
HOTKEYS_FILENAME = 'hotbox_hotkey.json'
# sous-dossier des données PROPRES au fork (librairie de boutons,
# registre des raccourcis, templates utilisateur) — pour ne pas
# encombrer la racine des prefs Maya. hotboxes.json, lui, RESTE à la
# racine : c'est le format/emplacement de l'original (compatibilité et
# retour arrière garantis).
FORK_FOLDER_NAME = 'hotboxJOR'
SETMODE_PRESS_RELEASE = 'open on press | close on release'
SETMODE_SWITCH_ON_PRESS = 'switch on press'


def execute(command):
    exec(command)


def migrate_legacy_file(legacy_path, new_path):
    """Déplace une bonne fois un fichier de l'ancien emplacement (racine
    des prefs) vers le dossier hotboxJOR/. Sans effet si la destination
    existe déjà, si la source n'existe pas, ou si les chemins sont
    identiques."""
    if legacy_path == new_path or os.path.exists(new_path):
        return
    if not os.path.exists(legacy_path):
        return
    try:
        folder = os.path.dirname(new_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        shutil.move(legacy_path, new_path)
    except OSError:
        pass  # au pire on continue de lire l'ancien emplacement


class AbstractApplication(object):

    def __init__(self):
        self.name = type(self).__name__
        folder = self.get_data_folder()
        # les images manquantes seront recherchées par nom de fichier
        # dans ce dossier (et son sous-dossier icons/)
        from hotbox_designer.images import register_image_root
        register_image_root(folder)
        self.local_file = os.path.join(folder, HOTBOXES_FILENAME)
        self.shared_file = os.path.join(folder, SHARED_HOTBOXES_FILENAME)
        self.main_window = self.get_main_window()
        self.reader_parent = self.get_reader_parent()
        self.available_languages = self.get_available_languages()
        self.available_set_hotkey_modes = self.get_available_set_hotkey_modes()

    @staticmethod
    def get_data_folder():
        raise NotImplementedError

    def get_fork_folder(self):
        """Dossier des données propres au fork. Par défaut le dossier de
        données lui-même (Standalone : ~/.hotboxjor est déjà dédié) ;
        Maya le range dans `prefs/hotboxJOR/`."""
        return self.get_data_folder()

    @staticmethod
    def get_reader_parent():
        raise NotImplementedError

    @staticmethod
    def get_main_window():
        raise NotImplementedError

    @staticmethod
    def get_available_languages():
        raise NotImplementedError

    @staticmethod
    def get_available_set_hotkey_modes():
        raise NotImplementedError

    @staticmethod
    def update_hotkeys():
        # Do not use 'raise NotImplementedError' in case other DCCs don't
        # have that feature
        pass

    def set_hotkey(self, mode, sequence, open_cmd, close_cmd, switch_cmd):
        raise NotImplementedError

    # --- registre des raccourcis (commun à tous les DCC) -----------------
    # Historiquement Maya posait ses hotkeys directement dans `cmds.hotkey`
    # sans aucune trace : impossible de LISTER ou de RETIRER un raccourci
    # déjà assigné. On tient désormais un petit fichier JSON
    # `hotbox_hotkey.json` dans le dossier de données, partagé par tous les
    # backends, qui alimente le gestionnaire de raccourcis.

    def get_hotkey_file(self):
        path = os.path.join(self.get_fork_folder(), HOTKEYS_FILENAME)
        # les registres écrits à la racine des prefs (versions
        # antérieures) sont rapatriés une fois pour toutes
        migrate_legacy_file(
            os.path.join(self.get_data_folder(), HOTKEYS_FILENAME), path)
        return path

    def load_hotkeys(self):
        """Registre `{nom_hotbox: {'sequence': ..., 'mode': ...}}`.

        Tolérant à l'ancien format Nuke/Rumba (`{'sequence', 'command'}`)
        pour rester lisible par le gestionnaire."""
        path = self.get_hotkey_file()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except (ValueError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def record_hotkey(self, name, sequence, mode):
        """Note (ou met à jour) le raccourci d'une hotbox dans le registre."""
        data = self.load_hotkeys()
        data[name] = {'sequence': sequence, 'mode': mode}
        with open(self.get_hotkey_file(), 'w') as f:
            json.dump(data, f, indent=2)

    def remove_hotkey(self, name):
        """Retire le raccourci du registre. Les backends qui posent un
        vrai raccourci DCC (Maya) surchargent pour le débrancher aussi."""
        data = self.load_hotkeys()
        if name in data:
            del data[name]
            with open(self.get_hotkey_file(), 'w') as f:
                json.dump(data, f, indent=2)


class Standalone(AbstractApplication):
    """Backend hors DCC : développement, tests et édition de hotboxes
    sans Maya/Nuke/Houdini. Les données vivent dans ~/.hotboxjor et les
    hotkeys globaux ne sont pas disponibles (ils appartiennent au DCC)."""

    @staticmethod
    def get_data_folder():
        folder = os.path.expanduser('~/.hotboxjor')
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    @staticmethod
    def get_main_window():
        return None

    @staticmethod
    def get_reader_parent():
        return None

    @staticmethod
    def get_available_languages():
        return [PYTHON]

    @staticmethod
    def get_available_set_hotkey_modes():
        return []

    def set_hotkey(self, *args, **kwargs):
        pass


class Maya(AbstractApplication):

    @staticmethod
    def get_data_folder():
        from maya import cmds
        return cmds.internalVar(userPrefDir=True)

    def get_fork_folder(self):
        """Les données du fork vivent dans `prefs/hotboxJOR/` au lieu
        d'encombrer la racine des prefs Maya."""
        folder = os.path.join(self.get_data_folder(), FORK_FOLDER_NAME)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except OSError:
                return self.get_data_folder()  # repli : racine des prefs
        return folder

    @staticmethod
    def get_main_window():
        """Get the main window for maya.

        Returns:
            shiboken2.wrapInstance: The pointer to the maya main window.
        """
        import maya.OpenMayaUI as omui
        try:
            import shiboken2 as shiboken
        except ImportError:
            import shiboken6 as shiboken
        if os.name == 'posix':
            return None
        ptr = omui.MQtUtil.mainWindow()
        if ptr is not None:
            return shiboken.wrapInstance(int(ptr), QtWidgets.QWidget)

    @staticmethod
    def get_reader_parent():
        return None

    @staticmethod
    def get_available_languages():
        return [MEL, PYTHON]

    @staticmethod
    def get_available_set_hotkey_modes():
        return [SETMODE_PRESS_RELEASE, SETMODE_SWITCH_ON_PRESS]

    def set_hotkey(
            self, name, mode, sequence, open_cmd, close_cmd, switch_cmd):
        from maya import cmds, mel
        current_hotkey_set = cmds.hotkeySet(current=True, query=True)
        if current_hotkey_set == 'Maya_Default':
            msg = (
                'The current hotkey set is locked,'
                'change in the hotkey editor')
            warning('Hotbox designer', msg)
            return mel.eval("hotkeyEditorWindow;")

        use_alt = 'Alt' in sequence
        use_ctrl = 'Ctrl' in sequence
        use_shift = 'Shift' in sequence
        touch = sequence.split("+")[-1]
        show_name = 'showHotbox_' + name
        hide_name = 'hideHotbox_' + name
        switch_name = 'switchHotbox_' + name
        if mode == SETMODE_PRESS_RELEASE:
            cmds.nameCommand(
                show_name,
                annotation='show ' + name + ' hotbox',
                command=format_command_for_mel(open_cmd),
                sourceType="python")
            cmds.nameCommand(
                hide_name,
                annotation='hide ' + name + ' hotbox',
                command=format_command_for_mel(close_cmd),
                sourceType="python")
            cmds.hotkey(
                keyShortcut=touch,
                altModifier=use_alt,
                ctrlModifier=use_ctrl,
                shiftModifier=use_shift,
                name=show_name,
                releaseName=hide_name)
        else:
            cmds.nameCommand(
                switch_name,
                annotation='switch ' + name + ' hotbox',
                command=format_command_for_mel(switch_cmd),
                sourceType="python")
            cmds.hotkey(
                keyShortcut=touch,
                altModifier=use_alt,
                ctrlModifier=use_ctrl,
                shiftModifier=use_shift,
                name=switch_name)
        # trace dans le registre pour pouvoir lister/retirer ensuite
        self.record_hotkey(name, sequence, mode)

    def remove_hotkey(self, name):
        """Débranche le raccourci Maya (press ET release) puis le retire du
        registre. Sans effet si le set de hotkeys courant est verrouillé."""
        from maya import cmds
        record = self.load_hotkeys().get(name)
        if record and record.get('sequence'):
            if cmds.hotkeySet(current=True, query=True) == 'Maya_Default':
                warning(
                    'Hotbox designer',
                    'The current hotkey set is locked, change in the '
                    'hotkey editor')
            else:
                sequence = record['sequence']
                touch = sequence.split('+')[-1]
                cmds.hotkey(
                    keyShortcut=touch,
                    altModifier='Alt' in sequence,
                    ctrlModifier='Ctrl' in sequence,
                    shiftModifier='Shift' in sequence,
                    name='',
                    releaseName='')
        super(Maya, self).remove_hotkey(name)


def format_command_for_mel(command):
    '''
    cause cmds.nameCommand fail to set python command, this method
    embed the given command to a mel command callin "python" function.
    It put everylines in a single one cause mel is not supporting multi-lines
    strings. Hopefully Autodesk gonna fixe this soon.
    '''
    command = command.replace("\n", ";")
    command = 'python("{}")'.format(command)
    return command


class Nuke(AbstractApplication):

    @staticmethod
    def get_data_folder():
        return os.path.expanduser('~/.nuke')

    @staticmethod
    def get_main_window():
        for widget in QtWidgets.QApplication.instance().topLevelWidgets():
            if widget.inherits('QMainWindow'):
                return widget

    @staticmethod
    def get_reader_parent():
        return None

    @staticmethod
    def get_available_languages():
        return PYTHON, NUKE_TCL, NUKE_EXPRESSION

    @staticmethod
    def get_available_set_hotkey_modes():
        return [SETMODE_SWITCH_ON_PRESS]

    def set_hotkey(
            self, name, mode, sequence, open_cmd, close_cmd, switch_cmd):
        self.save_hotkey(name, sequence, switch_cmd)
        self.create_menus()

    def get_hotkey_file(self):
        hotkey_file = os.path.join(
            self.get_data_folder(), 'hotbox_hotkey.json')
        return hotkey_file

    def load_hotkey(self):
        hotkey_file = self.get_hotkey_file()
        if not os.path.exists(hotkey_file):
            return {}
        with open(hotkey_file, 'r') as f:
            return json.load(f)

    def save_hotkey(self, name, sequence, command):
        data = self.load_hotkey()
        data[name] = {
            'sequence': sequence,
            'command': command}
        with open(str(self.get_hotkey_file()), 'w+') as f:
            json.dump(data, f, indent=2)

    def create_menus(self):
        import nuke
        nuke_menu = nuke.menu('Nuke')
        menu = nuke_menu.addMenu('Hotbox Designer')
        hotkey_data = self.load_hotkey()
        for name, value in hotkey_data.items():
            menu.addCommand(
                name='Hotboxes/{name}'.format(name=name),
                command=str(value['command']), shortcut=value['sequence'])


class Houdini(AbstractApplication):

    @staticmethod
    def get_data_folder():
        return os.path.expanduser('~/houdini17.0')

    @staticmethod
    def get_main_window():
        import hou
        return hou.qt.mainWindow()

    @staticmethod
    def get_reader_parent():
        return None

    @staticmethod
    def get_available_languages():
        return [PYTHON, HSCRIPT]

    @staticmethod
    def get_available_set_hotkey_modes():
        return [SETMODE_SWITCH_ON_PRESS]

    def set_hotkey(
            self, name, mode, sequence, open_cmd, close_cmd, switch_cmd):
        from hotbox_designer.qtutils import set_shortcut
        from functools import partial
        set_shortcut(sequence, self.main_window, partial(execute, switch_cmd))

class Rumba(AbstractApplication):

    @staticmethod
    def get_data_folder():
        return os.path.expanduser('~/.rumba')

    @staticmethod
    def get_main_window():
        import rumbapy
        return rumbapy.widget("MainWindow")

    @staticmethod
    def get_reader_parent():
        return None

    @staticmethod
    def get_available_languages():
        return [RUMBA_SCRIPT, PYTHON]

    @staticmethod
    def get_available_set_hotkey_modes():
        return [SETMODE_SWITCH_ON_PRESS]

    def set_hotkey(
            self, name, mode, sequence, open_cmd, close_cmd, switch_cmd):
        self.save_hotkey(name, sequence, switch_cmd)
        self.create_menus(reload=True)

    def update_hotkeys(self):
        hotkey_file = self.get_hotkey_file()
        updated_hotkeys = self.remove_hotbox_item(
            self.load_hotboxes(), self.load_hotkey()
        )
        with open(hotkey_file, 'w') as f:
            json.dump(updated_hotkeys, f, indent=2)

    def get_hotboxes_file(self):
        hotboxes_file = os.path.join(
            self.get_data_folder(), HOTBOXES_FILENAME)
        return hotboxes_file

    def get_hotkey_file(self):
        hotkey_file = os.path.join(
            self.get_data_folder(), 'hotbox_hotkey.json')
        return hotkey_file

    def load_hotboxes(self):
        hotboxes_file = self.get_hotboxes_file()
        if not os.path.exists(hotboxes_file):
            return []
        with open(hotboxes_file, 'r') as f:
            return json.load(f)
        
    def load_hotkey(self):
        hotkey_file = self.get_hotkey_file()
        if not os.path.exists(hotkey_file):
            return {}
        with open(hotkey_file, 'r') as f:
            return json.load(f)

    def save_hotkey(self, name, sequence, command):
        hotkey_data = self.load_hotkey()
        updated_hotkey_data = self.remove_hotbox_item(self.load_hotboxes(), hotkey_data)
        updated_hotkey_data[name] = {
            'sequence': sequence,
            'command': command}
        with open(str(self.get_hotkey_file()), 'w') as f:
            json.dump(updated_hotkey_data, f, indent=2)

    def delete_menu(self, menu_bar: QtWidgets.QMenuBar, menu_title: str):
        """Find and delete a menu with a specific title from the menu bar."""
        menus = menu_bar.actions()
        for menu in menus:
            if menu.menu() and menu.text() == menu_title:
                menu_bar.removeAction(menu)

    def create_menus(self, reload=False):
        """Create the Hotbox Designer menu in Rumba's menu bar."""
        import rumbapy
        from functools import partial

        main_window = rumbapy.widget("MainWindow")
        menu_bar = main_window.menubar
        menu_title = "&Hotbox Designer"

        if reload:
            self.delete_menu(menu_bar, menu_title)

        hotbox_menu = menu_bar.addMenu(menu_title)

        hotkey_data = self.load_hotkey()

        for name, value in hotkey_data.items():
            action = rumbapy.action.new(
                name=name,
                widget=main_window,
                trigger=partial(lambda cmd: exec(cmd), value['command']),
                icon=None,
                shortcut=value["sequence"]
            )
            hotbox_menu.addAction(action)

    def remove_hotbox_item(self, hotboxes, hotbox_hotkey):
        """
        Remove hotbox items that are not present in the current hotboxes
        """
        hotbox_items = {item.get("general", {}).get("name") for item in hotboxes}
        
        updated_hotkey = {
            key: value for key, value in hotbox_hotkey.items()
            if key in hotbox_items
        }
        
        return updated_hotkey
