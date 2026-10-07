
import io
import os
import re
import json
from hotboxLibrary.templates import HOTBOX


DEFAULT_NAME = 'MyHotbox_{}'
TRIGGERING_TYPES = 'click only', 'click or close'
HOTBOX_REPRESENTATION = """\
<b>Name </b>{name}<br>
<b>Submenu </b>{submenu}<br>
<b>Triggering </b>{triggering}<br>
<b>Aiming </b>{aiming}<br>
<b>Close on leave </b>{leaveclose}<br>
"""


def get_new_hotbox(hotboxes):
    options = HOTBOX.copy()
    options.update({'name': get_valid_name(hotboxes)})
    return {
        'general': options,
        'shapes': []}


def get_valid_name(hotboxes, proposal=None):
    # un lien partagé cassé vaut None dans les modèles du manager
    names = [hotbox['general']['name'] for hotbox in hotboxes if hotbox]
    index = 0
    name = proposal or DEFAULT_NAME.format(str(index).zfill(2))
    while name in names:
        if proposal:
            name = proposal + "_" + str(index).zfill(2)
        else:
            name = DEFAULT_NAME.format(str(index).zfill(2))
        index += 1
    return name


def load_hotboxes_datas(filename):
    datas = load_json(filename, default=[])
    return [ensure_old_data_compatible(data) for data in datas]


def load_json(filename, default=None):
    if not os.path.exists(filename):
        return default
    with open(filename, 'r') as f:
        return json.load(f)


class HotboxFileError(ValueError):
    """Fichier choisi à l'import qui n'est pas (ou pas lisible comme)
    une hotbox. Le message est destiné à l'utilisateur."""


def read_json_text(path):
    """json lu en UTF-8 (avec ou sans BOM), sinon en latin-1 : un
    fichier retouché à la main sous Windows (accents) ne bloque plus
    l'import."""
    try:
        with io.open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except UnicodeDecodeError:
        with io.open(path, 'r', encoding='latin-1') as f:
            return json.load(f)


def is_hotbox_data(data):
    """Une hotbox = un dict avec `general` (qui porte un nom) et une
    liste `shapes`. Écarte une librairie de boutons, un picker, etc."""
    if not isinstance(data, dict):
        return False
    general = data.get('general')
    return (isinstance(general, dict) and bool(general.get('name'))
            and isinstance(data.get('shapes'), list))


def read_hotbox_file(path):
    """Toutes les hotboxes d'un fichier, prêtes à l'emploi. Accepte une
    hotbox seule (fichier exporté) OU une liste de hotboxes (le
    `hotboxes.json` des prefs, qu'on se passe souvent tel quel) — avant,
    une liste faisait planter l'import sans un mot. Lève
    HotboxFileError avec un message lisible si rien n'est importable."""
    name = os.path.basename(path)
    try:
        data = read_json_text(path)
    except (OSError, IOError) as error:
        raise HotboxFileError(
            'Could not open "%s":\n%s' % (name, error))
    except ValueError as error:
        raise HotboxFileError(
            '"%s" is not a valid json file:\n%s' % (name, error))
    items = data if isinstance(data, list) else [data]
    hotboxes = [ensure_old_data_compatible(item)
                for item in items if is_hotbox_data(item)]
    if not hotboxes:
        raise HotboxFileError(
            '"%s" is not a hotbox file.\n\nPick a file exported from '
            'the hotbox manager (or your hotboxes.json). A button '
            'library or a picker file cannot be imported here.' % name)
    return hotboxes


def load_shared_hotbox(path):
    """La hotbox d'un lien partagé, ou None si le fichier manque, est
    illisible ou n'est pas UNE hotbox — un lien cassé ne doit jamais
    empêcher les autres hotboxes de se charger."""
    try:
        hotboxes = read_hotbox_file(path)
    except HotboxFileError:
        return None
    return hotboxes[0] if len(hotboxes) == 1 else None


# sur un partage réseau Windows, os.replace échoue PAR INTERMITTENCE
# (« accès refusé ») quand le fichier est ouvert ailleurs à cet instant :
# la shelf d'un collègue qui le relit après une publication, l'antivirus
# qui inspecte le .tmp… On réessaie un court moment avant d'abandonner
# — au studio il fallait « sauver plusieurs fois ».
REPLACE_ATTEMPTS = 12
REPLACE_DELAY = 0.15   # secondes entre deux essais (~1,8 s au total)


def atomic_write_json(path, payload):
    """Écriture SÛRE d'un json : le contenu part dans un fichier
    temporaire du même dossier, puis remplace l'original d'un coup
    (os.replace) — un crash ou une coupure réseau en pleine écriture ne
    peut plus corrompre le fichier. Le remplacement est réessayé
    quelques instants si le fichier est momentanément verrouillé ;
    au-delà, l'OSError remonte et le temporaire est nettoyé."""
    import time
    temporary = path + '.tmp'
    with open(temporary, 'w') as f:
        json.dump(payload, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(temporary, path)
            return
        except OSError:
            if attempt == REPLACE_ATTEMPTS - 1:
                try:
                    os.remove(temporary)
                except OSError:
                    pass
                raise
            time.sleep(REPLACE_DELAY)


def save_datas(filename, hotboxes_data):
    atomic_write_json(filename, hotboxes_data)


def copy_hotbox_data(data):
    copied = {}
    copied['general'] = data['general'].copy()
    copied['shapes'] = [shape.copy() for shape in data['shapes']]
    return copied


def ensure_old_data_compatible(data):
    """
    Tests and update datas done with old version of the script
    This function contain all the data structure history to convertion
    """
    try:
        del data['submenu']
    except:
        pass
    try:
        data['general']['submenu']
    except KeyError:
        data['general']['submenu'] = False
    try:
        data['general']['leaveclose']
    except KeyError:
        data['general']['leaveclose'] = False

    # coins arrondis (façon dwpicker) : rayons par défaut si absents
    for shape in data.get('shapes', []):
        shape.setdefault('shape.cornersx', 8)
        shape.setdefault('shape.cornersy', 8)
        # décalage manuel de l'image dans le bouton
        shape.setdefault('image.offsetx', 0)
        shape.setdefault('image.offsety', 0)
        # fond verrouillable (« lock background », façon dwpicker)
        shape.setdefault('background', False)
        # boutons de sous-menu écrits par l'ancien outil : ils
        # appellent `hotbox_designer.show(...)` — depuis le renommage,
        # ce module est l'outil du pipe (ou n'existe plus). On les
        # rebranche sur ce package, sinon « le sous-menu ne s'ouvre pas »
        for side in ('left', 'right'):
            key = 'action.%s.command' % side
            if key in shape:
                shape[key] = migrate_legacy_command(shape[key])

    return data


LEGACY_MODULE = re.compile(r'\bhotbox_designer\b')


def migrate_legacy_command(command):
    """`import hotbox_designer … hotbox_designer.show('x')` →
    `hotboxLibrary`. Ne touche qu'au nom du module (mot entier) ; une
    commande qui ne le cite pas revient telle quelle."""
    if not command or 'hotbox_designer' not in command:
        return command
    return LEGACY_MODULE.sub('hotboxLibrary', command)


def load_templates(user_folder=None):
    """Templates embarqués + templates de l'utilisateur (dossier
    `templates/` du dossier de données, alimenté par « Save hotbox as
    template » du manager)."""
    path = os.path.join(os.path.dirname(__file__), 'resources', 'templates')
    folders = [path]
    if user_folder and os.path.isdir(user_folder):
        folders.append(user_folder)
    templates = []
    for folder in folders:
        for file_ in sorted(os.listdir(folder)):
            if not file_.lower().endswith('.json'):
                continue
            filepath = os.path.join(folder, file_)
            try:
                with open(filepath, 'r') as f:
                    templates.append(json.load(f))
            except (ValueError, OSError):
                continue  # un template corrompu ne bloque pas les autres
    return templates


def save_hotbox_as_template(user_folder, hotbox):
    """Écrit la hotbox comme template utilisateur (copie indépendante).
    Retourne le chemin écrit, ou None si le dossier est inaccessible."""
    try:
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
    except OSError:
        return None
    name = hotbox['general'].get('name') or 'template'
    safe = ''.join(c if c.isalnum() or c in '-_ ' else '_' for c in name)
    safe = safe.strip() or 'template'
    filepath = os.path.join(user_folder, safe + '.json')
    index = 1
    while os.path.exists(filepath):
        filepath = os.path.join(user_folder, '%s_%d.json' % (safe, index))
        index += 1
    try:
        with open(filepath, 'w') as f:
            json.dump(copy_hotbox_data(hotbox), f, indent=2)
    except OSError:
        return None
    return filepath


def hotbox_data_to_html(data):
    return HOTBOX_REPRESENTATION.format(
        name=data['general']['name'],
        submenu=data['general']['submenu'],
        triggering=data['general']['triggering'],
        aiming=data['general']['aiming'],
        leaveclose=data['general']['leaveclose'])
