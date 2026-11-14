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
    _sharp.clear()


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


# --- rendu NET à la taille d'affichage ---------------------------------
# Une icône était décodée à sa taille d'origine (un SVG de 24 px reste
# 24 px), puis ÉTIRÉE à la taille du bouton et à l'échelle de l'écran
# (125 / 150 % sous Windows) : flou, voire crénelé sans lissage. Ici on
# produit l'image directement à la taille où elle sera vue, en pixels
# RÉELS de l'écran : un SVG est redessiné en vectoriel, une image
# bitmap est réduite / agrandie avec lissage. Une fois par taille.
_sharp = {}


def sharp_pixmap(path, width, height, ratio=1.0):
    """QPixmap de `path` rendu pour une zone de `width` x `height`
    pixels logiques sur un écran à `ratio` (devicePixelRatio). Même
    géométrie que l'ancien drawPixmap(rect, pixmap) : l'image remplit la
    zone. Le pixmap porte son devicePixelRatio : on le dessine avec
    drawPixmap(rect, pixmap), sans ré-échantillonnage. Pixmap nul si
    l'image est introuvable."""
    from hotboxLibrary.vendor.Qt import QtCore, QtGui
    if not path or width <= 0 or height <= 0:
        return QtGui.QPixmap()
    ratio = max(float(ratio or 1.0), 1.0)
    device_w = max(int(round(width * ratio)), 1)
    device_h = max(int(round(height * ratio)), 1)
    key = (path, device_w, device_h)
    pixmap = _sharp.get(key)
    if pixmap is not None:
        return pixmap
    pixmap = QtGui.QPixmap()
    resolved = resolve_image_path(path)
    if resolved and resolved.lower().endswith('.svg'):
        pixmap = _render_svg(resolved, device_w, device_h)
    if pixmap.isNull():
        source = image_pixmap(path)
        if not source.isNull():
            pixmap = source.scaled(
                device_w, device_h, QtCore.Qt.IgnoreAspectRatio,
                QtCore.Qt.SmoothTransformation)
    if not pixmap.isNull():
        pixmap.setDevicePixelRatio(ratio)
    if len(_sharp) > CACHE_LIMIT:
        _sharp.clear()
    _sharp[key] = pixmap
    return pixmap


def _render_svg(path, device_w, device_h):
    from hotboxLibrary.vendor.Qt import QtCore, QtGui
    try:
        from hotboxLibrary.vendor.Qt import QtSvg
        renderer = QtSvg.QSvgRenderer(path)
    except Exception:
        return QtGui.QPixmap()
    if not renderer.isValid():
        return QtGui.QPixmap()
    image = QtGui.QImage(
        device_w, device_h, QtGui.QImage.Format_ARGB32_Premultiplied)
    image.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    renderer.render(painter, QtCore.QRectF(0, 0, device_w, device_h))
    painter.end()
    return QtGui.QPixmap.fromImage(image)
