"""Résolution portable des chemins d'images des boutons.

Les hotboxes stockent des chemins absolus : déplacer son dossier
d'icônes cassait tous les logos (il fallait les re-pointer un par un).
Ici, si le chemin enregistré n'existe plus, on retrouve l'image par son
NOM DE FICHIER dans des dossiers connus :

- la variable d'environnement ``HOTBOX_DESIGNER_ICONS`` (un dossier) ;
- les dossiers enregistrés par l'application (dossier de données des
  préférences, dossiers des hotboxes partagées…) ;
- leurs sous-dossiers ``icons``.

Il suffit donc de poser ses icônes dans un de ces endroits (ou de
pointer la variable d'environnement sur son dossier) pour que les
images survivent aux déménagements.
"""
import os

ICONS_ENV_VARIABLE = 'HOTBOX_DESIGNER_ICONS'
_image_roots = []

# --- caches -------------------------------------------------------------
# Résoudre un chemin coûte des accès disque, et charger une image la
# DÉCODE entièrement. L'éditeur re-synchronise les images très souvent
# (à chaque frame d'un déplacement) : sans cache, une hotbox dont les
# icônes vivent sur un disque RÉSEAU devient poussive — c'est la
# lourdeur constatée au studio. On garde donc en mémoire le chemin
# résolu et le pixmap décodé, par chemin d'origine.
_resolved_paths = {}
_pixmaps = {}
CACHE_LIMIT = 512


def clear_image_cache():
    """Oublie les chemins résolus et les images décodées — à appeler si
    les fichiers d'icônes ont changé sur le disque."""
    _resolved_paths.clear()
    _pixmaps.clear()


def register_image_root(folder):
    """Déclare un dossier où chercher les images manquantes."""
    if folder and folder not in _image_roots:
        _image_roots.append(folder)
        # un nouveau dossier peut résoudre des images jusque-là
        # introuvables : les échecs mémorisés ne valent plus
        clear_image_cache()


def image_roots():
    roots = []
    env_root = os.environ.get(ICONS_ENV_VARIABLE)
    if env_root:
        roots.append(env_root)
    roots.extend(_image_roots)
    return roots


def resolve_image_path(path):
    """Retourne un chemin existant pour l'image, si possible.

    Chemin valide → inchangé. Sinon on cherche le nom de fichier dans
    les dossiers connus (et leurs sous-dossiers ``icons``). En dernier
    recours le chemin d'origine est rendu tel quel. Le résultat est mis
    en cache (voir ``clear_image_cache``).
    """
    if not path:
        return path
    resolved = _resolved_paths.get(path)
    if resolved is not None:
        return resolved
    resolved = _resolve_image_path(path)
    if len(_resolved_paths) > CACHE_LIMIT:
        _resolved_paths.clear()
    _resolved_paths[path] = resolved
    return resolved


def _resolve_image_path(path):
    expanded = os.path.expandvars(os.path.expanduser(path))
    if os.path.exists(expanded):
        return expanded
    # nom de fichier, robuste aux chemins Windows lus ailleurs
    basename = os.path.basename(expanded.replace('\\', '/'))
    if not basename:
        return expanded
    for root in image_roots():
        for candidate in (
                os.path.join(root, basename),
                os.path.join(root, 'icons', basename)):
            if os.path.exists(candidate):
                return candidate
    return expanded


def image_pixmap(path):
    """Le QPixmap d'une image de bouton, DÉCODÉ UNE SEULE FOIS.

    Toutes les shapes qui pointent la même image partagent le même
    pixmap : il n'est jamais modifié, seulement dessiné."""
    from hotboxLibrary.vendor.Qt import QtGui
    if not path:
        return QtGui.QPixmap()
    pixmap = _pixmaps.get(path)
    if pixmap is not None:
        return pixmap
    pixmap = QtGui.QPixmap(resolve_image_path(path))
    if len(_pixmaps) > CACHE_LIMIT:
        _pixmaps.clear()
    _pixmaps[path] = pixmap
    return pixmap
