
import os
import json
import shutil
from hotbox_designer.templates import HOTBOX


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
    names = [hotbox['general']['name'] for hotbox in hotboxes]
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


def _rotate_backups(path, depth):
    """name.json.bak (le plus récent) → .bak2 → .bak3 (rotation)."""
    try:
        for i in range(depth, 1, -1):
            src = (path + '.bak' if i - 1 == 1
                   else '%s.bak%d' % (path, i - 1))
            if os.path.exists(src):
                os.replace(src, '%s.bak%d' % (path, i))
        shutil.copy(path, path + '.bak')
    except OSError:
        pass  # un backup raté ne doit jamais bloquer la sauvegarde


def atomic_write_json(path, payload, backups=0):
    """Écriture SÛRE d'un json : le contenu part dans un fichier
    temporaire du même dossier, puis remplace l'original d'un coup
    (os.replace) — un crash ou une coupure réseau en pleine écriture ne
    peut plus corrompre le fichier. Avec backups>0, les versions
    précédentes sont conservées à côté (.bak, .bak2…)."""
    temporary = path + '.tmp'
    with open(temporary, 'w') as f:
        json.dump(payload, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    if backups and os.path.exists(path):
        _rotate_backups(path, backups)
    os.replace(temporary, path)


def save_datas(filename, hotboxes_data):
    # les hotboxes sont précieuses : écriture atomique + 3 backups
    atomic_write_json(filename, hotboxes_data, backups=3)


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

    return data


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
