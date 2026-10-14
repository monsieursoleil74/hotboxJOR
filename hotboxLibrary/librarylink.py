"""Lien entre un bouton posé dans une hotbox et son entrée de librairie.

Problème remonté au studio : quand la commande d'un bouton de la
librairie change, les animateurs qui l'avaient déjà glissé dans leur
hotbox gardaient l'ancienne — il fallait supprimer le bouton et le
re-glisser.

Désormais, un bouton venu de la librairie porte une étiquette
``library.link`` : la catégorie et le nom de son entrée (et sa place
dans un set), plus une COPIE des commandes telles qu'elles étaient au
moment du dépôt. Au chargement des hotboxes, chaque bouton étiqueté est
comparé à son entrée :

- l'entrée a changé ET le bouton n'a pas été retouché à la main (ses
  commandes sont encore celles de la copie) → les commandes sont mises
  à jour, la copie aussi ;
- l'animateur a modifié la commande de SON bouton → on n'y touche pas :
  sa version prime (le bouton est « détaché »).

Seules les COMMANDES (clic gauche / droit, langage, fermeture) suivent la
librairie : la place, la taille et le look choisis dans la hotbox
restent ceux de l'animateur.

Les boutons posés AVANT cette étiquette n'ont pas de lien : le bouton
« Update from library » (barre d'outils de l'éditeur, ou clic droit
« Update selected from library ») les reconnaît à leur IMAGE (la
même qu'une entrée, et une seule) et les rattache, après confirmation.
La librairie garde aussi l'historique de ses entrées (anciens scripts,
anciens noms) : les noms servent déjà aux boutons liés quand une entrée
est renommée ou déplacée ; les scripts sont conservés pour plus tard.
"""
from copy import deepcopy

LINK_KEY = 'library.link'
# gardés DANS les entrées de librairie par les gestes d'admin :
# anciennes commandes (Update) et anciens (catégorie, nom) (Rename,
# Move) — pour reconnaître les boutons pas encore rattachés
HISTORY_KEY = 'history'
ALIASES_KEY = 'aliases'
HISTORY_LIMIT = 20
COMMAND_KEYS = ('action.left.command', 'action.right.command')
ACTION_KEYS = (
    'action.left', 'action.left.close', 'action.left.language',
    'action.left.command',
    'action.right', 'action.right.close', 'action.right.language',
    'action.right.command')


def action_snapshot(options):
    """Les commandes d'un bouton (ce qui suit la librairie)."""
    return {key: options.get(key) for key in ACTION_KEYS}


def linked_options(entry, index=None):
    """Options d'un bouton de la librairie, ÉTIQUETÉES avec leur entrée
    — à utiliser pour tout ce qui part de la shelf vers une hotbox
    (drag & drop, Replace). `index` = place dans un set."""
    if index is None:
        options = deepcopy(entry['options'])
    else:
        options = deepcopy(entry['set'][index])
    options[LINK_KEY] = {
        'category': entry.get('category'),
        'name': entry.get('name'),
        'index': index,
        'action': action_snapshot(options)}
    return options


def unlinked(options):
    """Copie des options SANS étiquette — pour ce qui repart vers la
    librairie (Save / Update) : une entrée de librairie ne pointe pas
    sur elle-même."""
    options = dict(options)
    options.pop(LINK_KEY, None)
    return options


def entry_payload(entry):
    """Élément de payload de drag pour une entrée : options étiquetées
    pour un bouton, liste d'options étiquetées pour un set."""
    if 'options' in entry:
        return linked_options(entry)
    return [linked_options(entry, i) for i in range(len(entry['set']))]


class LibraryIndex(object):
    """Entrées des librairies studio puis perso, par (catégorie, nom).
    La studio est consultée d'abord : c'est la référence partagée."""

    def __init__(self, libraries):
        self._entries = {}
        self.entries = []
        aliases = []
        for entries in libraries:
            for entry in entries:
                key = (entry.get('category'), entry.get('name'))
                self._entries.setdefault(key, entry)
                self.entries.append(entry)
                for alias in entry.get(ALIASES_KEY) or []:
                    if isinstance(alias, (list, tuple)) and len(alias) == 2:
                        aliases.append((tuple(alias), entry))
        # un bouton renommé ou changé de catégorie reste trouvable sous
        # ses anciens noms — un nom ACTUEL prime toujours sur un alias
        for key, entry in aliases:
            self._entries.setdefault(key, entry)

    def __bool__(self):
        return bool(self._entries)

    __nonzero__ = __bool__

    def source_options(self, link):
        """Options actuelles de l'entrée liée, ou None (entrée renommée,
        supprimée, set raccourci…)."""
        if not isinstance(link, dict):
            return None
        entry = self._entries.get((link.get('category'), link.get('name')))
        if entry is None:
            return None
        index = link.get('index')
        if index is None:
            return entry.get('options')
        members = entry.get('set') or []
        if not isinstance(index, int) or not 0 <= index < len(members):
            return None
        return members[index]


def load_library_index(application=None):
    """Index des librairies visibles par cet utilisateur. Ne lève
    jamais : sans librairie lisible, l'index est vide."""
    from hotboxLibrary import buttonlibrary as bl
    libraries = []
    try:
        if application is not None:
            bl.restore_studio_location(application)
        libraries.append(bl.load_studio_library())
    except Exception:
        pass
    try:
        if application is not None:
            libraries.append(bl.load_library(bl.library_path(application)))
    except Exception:
        pass
    return LibraryIndex(libraries)


def sync_options(options, index):
    """Met à jour les commandes d'UN bouton lié si sa librairie a changé
    et qu'il n'a pas été retouché à la main. Retourne True s'il a
    changé."""
    link = options.get(LINK_KEY)
    if not isinstance(link, dict):
        return False
    source = index.source_options(link)
    if source is None:
        return False
    current = action_snapshot(options)
    if current != link.get('action'):
        return False  # commande modifiée par l'animateur : il garde la sienne
    fresh = action_snapshot(source)
    if fresh == current:
        return False
    options.update(fresh)
    # NOUVELLE étiquette (jamais modifiée en place) : un bouton dupliqué
    # peut partager le même dict que l'original
    options[LINK_KEY] = dict(link, action=deepcopy(fresh))
    return True


def sync_hotbox(data, index):
    """Met à jour tous les boutons liés d'une hotbox. Retourne le
    nombre de boutons modifiés."""
    if not index:
        return 0
    changed = 0
    for options in data.get('shapes', []):
        try:
            changed += sync_options(options, index)
        except Exception:
            continue  # un bouton abîmé ne bloque pas les autres
    return changed


def _members(entry):
    """(place dans le set ou None, options) de chaque bouton d'une
    entrée."""
    if 'options' in entry:
        return [(None, entry['options'])]
    return list(enumerate(entry.get('set') or []))


def _clean(value):
    return (value or '').strip()


def image_key(path):
    """Chemin d'image comparable : barres et casse unifiées
    (« R:\\Icons\\snap.svg » == « r:/icons/snap.svg »)."""
    return _clean(path).replace('\\', '/').lower()


def _match_entry(options, members):
    """L'entrée d'un bouton NON rattaché, ou None. Règle unique (choix
    du studio, pour l'instant) : la MÊME IMAGE qu'UNE seule entrée. Un
    bouton sans image, ou dont l'image est partagée par plusieurs
    entrées, n'est pas rattaché. Retourne (entry, place, source,
    raison)."""
    image = image_key(options.get('image.path'))
    if not image:
        return None
    matches = {(id(m[0]), m[1]): m for m in members
               if image_key(m[2].get('image.path')) == image}
    if len(matches) != 1:
        return None
    entry, position, source, _ = list(matches.values())[0]
    return entry, position, source, 'same image'


def find_link_candidates(shapes_options, index):
    """Boutons NON rattachés (ou détachés) qu'on peut rattacher à la
    librairie. Retourne une liste de (options, link, source, raison) —
    la raison est montrée dans la fenêtre de confirmation."""
    members = []
    seen = set()
    for entry in index.entries:
        # même bouton dans la librairie studio ET la perso (envoyé au
        # studio depuis la perso) : compté une fois, la studio d'abord —
        # sinon il paraîtrait ambigu et ne serait jamais reconnu
        key = (entry.get('category'), entry.get('name'))
        if key in seen:
            continue
        seen.add(key)
        for position, source in _members(entry):
            members.append((entry, position, source, None))
    candidates = []
    for options in shapes_options:
        link = options.get(LINK_KEY)
        if isinstance(link, dict) and index.source_options(link) is not None:
            current = action_snapshot(options)
            if current == link.get('action'):
                continue  # déjà lié et à jour (ou se mettra à jour seul)
            source = index.source_options(link)
            if current == action_snapshot(source):
                # mêmes commandes que la librairie, copie périmée : on
                # répare l'étiquette sans rien demander
                options[LINK_KEY] = dict(link, action=deepcopy(current))
                continue
            candidates.append(
                (options, link, source, 'modified by hand'))  # détaché
            continue
        match = _match_entry(options, members)
        if match is None:
            continue
        entry, position, source, reason = match
        new_link = {'category': entry.get('category'),
                    'name': entry.get('name'), 'index': position}
        candidates.append((options, new_link, source, reason))
    return candidates


def apply_link(options, link, source, reason=None):
    """Rattache un bouton à son entrée : commandes de la librairie +
    étiquette à jour."""
    fresh = action_snapshot(source)
    options.update(deepcopy(fresh))
    link = dict(link)
    link['action'] = deepcopy(fresh)
    options[LINK_KEY] = link


def remember_commands(entry_options, previous_options, entry):
    """Avant de réécrire une entrée (Update), garde ses ANCIENNES
    commandes dans son historique — un bouton pas encore rattaché qui a
    encore l'ancien script sera reconnu."""
    old = {key: previous_options.get(key) for key in COMMAND_KEYS}
    new = {key: entry_options.get(key) for key in COMMAND_KEYS}
    if old == new or not any(_clean(v) for v in old.values()):
        return
    history = [h for h in entry.get(HISTORY_KEY) or [] if h != old]
    history.append(old)
    entry[HISTORY_KEY] = history[-HISTORY_LIMIT:]


def remember_name(entry, old_category, old_name):
    """APRÈS un renommage / changement de catégorie : garde l'ancien
    (catégorie, nom) — les boutons liés suivent toujours. Rien si le
    nom n'a pas changé."""
    alias = [old_category, old_name]
    if alias == [entry.get('category'), entry.get('name')]:
        return
    aliases = [a for a in entry.get(ALIASES_KEY) or [] if a != alias]
    aliases.append(alias)
    entry[ALIASES_KEY] = aliases[-HISTORY_LIMIT:]
