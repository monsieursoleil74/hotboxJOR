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


def register_image_root(folder):
    """Déclare un dossier où chercher les images manquantes."""
    if folder and folder not in _image_roots:
        _image_roots.append(folder)


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
    recours le chemin d'origine est rendu tel quel.
    """
    if not path:
        return path
    path = os.path.expandvars(os.path.expanduser(path))
    if os.path.exists(path):
        return path
    # nom de fichier, robuste aux chemins Windows lus ailleurs
    basename = os.path.basename(path.replace('\\', '/'))
    if not basename:
        return path
    for root in image_roots():
        for candidate in (
                os.path.join(root, basename),
                os.path.join(root, 'icons', basename)):
            if os.path.exists(candidate):
                return candidate
    return path
