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

Les boutons posés AVANT cette étiquette n'ont pas de lien : la commande
« Link buttons to library… » de l'éditeur les reconnaît par leur
apparence (même texte et même image qu'une entrée, et une seule) et
les rattache, après confirmation.
"""
from copy import deepcopy

LINK_KEY = 'library.link'
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
        for entries in libraries:
            for entry in entries:
                key = (entry.get('category'), entry.get('name'))
                self._entries.setdefault(key, entry)
                self.entries.append(entry)

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


def _look(options):
    return (options.get('text.content') or '', options.get('image.path') or '')


def find_link_candidates(shapes_options, index):
    """Boutons NON liés (ou détachés) qu'on peut rattacher à la
    librairie, reconnus par leur apparence : même texte ET même image
    qu'UNE seule entrée (bouton simple ou membre de set). Retourne une
    liste de (options, link, source_options)."""
    looks = {}
    for entry in index.entries:
        if 'options' in entry:
            members = [(None, entry['options'])]
        else:
            members = list(enumerate(entry.get('set') or []))
        for position, source in members:
            look = _look(source)
            if look == ('', ''):
                continue  # un bouton sans texte ni image : trop ambigu
            looks.setdefault(look, []).append((entry, position, source))
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
            candidates.append((options, link, source))  # détaché
            continue
        matches = looks.get(_look(options), [])
        if len(matches) != 1:
            continue
        entry, position, source = matches[0]
        new_link = {'category': entry.get('category'),
                    'name': entry.get('name'), 'index': position}
        candidates.append((options, new_link, source))
    return candidates


def apply_link(options, link, source):
    """Rattache un bouton à son entrée : commandes de la librairie +
    étiquette à jour."""
    fresh = action_snapshot(source)
    options.update(deepcopy(fresh))
    link = dict(link)
    link['action'] = deepcopy(fresh)
    options[LINK_KEY] = link
