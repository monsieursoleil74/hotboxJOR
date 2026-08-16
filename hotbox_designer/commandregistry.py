"""Registre de commandes NOMMÉES, partagé via la librairie studio.

Le problème : les boutons portent leur code Python en dur (chemins de
scripts recopiés dans chaque bouton) — le jour où un script bouge, tous
les boutons qui l'appellent cassent, dans toutes les hotboxes de tout
le monde.

La solution : un fichier ``commands.json`` posé À CÔTÉ de la librairie
studio courante (même dossier serveur). Il associe un NOM à une
commande (``{"TAT.PrepaManager": {"language": "python", "command":
"..."}}``). Les boutons n'appellent plus le code mais le nom ::

    import hotbox_designer
    hotbox_designer.run('TAT.PrepaManager')

Le code est relu dans le registre À CHAQUE clic : mettre à jour la
commande dans le registre met à jour tous les boutons qui l'appellent,
partout, sans toucher aux hotboxes. Édition en mode admin (bouton ƒ du
manager), lecture seule pour les animateurs — même modèle que la
librairie de boutons.

Deux sources, fusionnées :

- ``commands.json`` — les petits snippets, édités via le dialogue ƒ ;
- le sous-dossier ``commands/`` — un VRAI fichier par commande
  (``CAM.flipCam.py``, ``Machin.mel``) : lisible, éditable dans un
  vrai éditeur de code, versionnable. Le nom du fichier (sans
  l'extension) est le nom de la commande ; l'extension donne le
  langage. En cas de doublon avec le json, le FICHIER gagne.
"""
import json
import os

REGISTRY_FILENAME = 'commands.json'


def registry_path():
    """Chemin du registre : ``commands.json`` dans le dossier de la
    librairie studio courante. None sans librairie configurée."""
    from hotbox_designer.buttonlibrary import studio_location
    location = studio_location()
    if not location:
        return None
    folder = location if os.path.isdir(location) else os.path.dirname(
        location)
    return os.path.join(folder, REGISTRY_FILENAME)


def commands_folder():
    """Sous-dossier `commands/` à côté du registre — un fichier .py ou
    .mel par commande. None sans librairie configurée."""
    path = registry_path()
    return os.path.join(os.path.dirname(path), 'commands') if path else None


def _load_command_files():
    """{nom: {'language', 'command', 'file'}} depuis le dossier
    `commands/` : Nom.py -> python, Nom.mel -> mel."""
    folder = commands_folder()
    if not folder or not os.path.isdir(folder):
        return {}
    registry = {}
    for filename in sorted(os.listdir(folder)):
        stem, ext = os.path.splitext(filename)
        language = {'.py': 'python', '.mel': 'mel'}.get(ext.lower())
        if not language or not stem:
            continue
        filepath = os.path.join(folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        registry[stem] = {
            'language': language, 'command': code, 'file': filepath}
    return registry


def load_registry(path=None):
    """{nom: {'language': 'python'|'mel', 'command': code}} — fusion du
    json (snippets) et du dossier commands/ (fichiers .py/.mel, qui
    gagnent en cas de doublon). {} sinon."""
    path = path or registry_path()
    registry = {}
    if path and os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except (ValueError, OSError):
            data = {}
        if isinstance(data, dict):
            registry.update(data)
    registry.update(_load_command_files())
    return registry


def save_command_file(filepath, code):
    """Réécrit le fichier d'une commande (atomique, utf-8)."""
    temporary = filepath + '.tmp'
    with open(temporary, 'w', encoding='utf-8') as f:
        f.write(code)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, filepath)


def save_registry(data, path=None):
    """Écrit le registre (atomique). False si aucun emplacement."""
    from hotbox_designer.data import atomic_write_json
    path = path or registry_path()
    if not path:
        return False
    atomic_write_json(path, data)
    return True


def run(name):
    """Exécute la commande nommée du registre — l'appel que portent les
    boutons. Le code est relu à chaque exécution : les mises à jour du
    registre sont prises en compte immédiatement, partout."""
    from hotbox_designer.languages import execute_code
    record = load_registry().get(name)
    if not record:
        raise ValueError(
            "Command '%s' not found in the registry (%s)" % (
                name, registry_path() or 'no studio library configured'))
    execute_code(
        record.get('language') or 'python', record.get('command') or '')


def run_snippet(name):
    """Le code à poser sur un bouton pour appeler une commande nommée."""
    return 'import hotbox_designer\nhotbox_designer.run(%r)' % str(name)
