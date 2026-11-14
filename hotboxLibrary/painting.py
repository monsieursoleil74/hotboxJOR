from hotboxLibrary.vendor.Qt import QtCore, QtGui
from hotboxLibrary.qtutils import VALIGNS, HALIGNS
from hotboxLibrary.geometry import grow_rect


MANIPULATOR_BORDER = 5
SELECTION_COLOR = '#6D8C5E'  # accent vert-gris (cohérent avec le thème)


def draw_editor(painter, rect, snap=None):
    # draw border
    pen = QtGui.QPen(QtGui.QColor('#333333'))
    pen.setStyle(QtCore.Qt.DashDotLine)
    pen.setWidth(3)
    brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 25))
    painter.setPen(pen)
    painter.setBrush(brush)
    painter.drawRect(rect)

    if snap is None:
        return
    # draw snap grid
    pen = QtGui.QPen(QtGui.QColor('red'))
    painter.setPen(pen)
    x = 0
    y = 0
    while y < rect.bottom():
        painter.drawPoint(x, y)
        x += snap[0]
        if x > rect.right():
            x = 0
            y += snap[1]


def draw_editor_center(painter, rect, point):
    color = QtGui.QColor(200, 200, 200, 125)
    painter.setPen(QtGui.QPen(color))
    painter.setBrush(QtGui.QBrush(color))
    painter.drawRect(rect)

    path = get_center_path(QtCore.QPointF(point[0], point[1]))
    pen = QtGui.QPen(QtGui.QColor(50, 125, 255))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawPath(path)


def get_center_path(point):
    ext = 12
    int_ = 5
    path = QtGui.QPainterPath(point)
    path.moveTo(QtCore.QPointF(point.x() - ext, point.y()))
    path.lineTo(QtCore.QPointF(point.x() - int_, point.y()))
    path.moveTo(QtCore.QPointF(point.x() + int_, point.y()))
    path.lineTo(QtCore.QPointF(point.x() + ext, point.y()))
    path.moveTo(QtCore.QPointF(point.x(), point.y() - ext))
    path.lineTo(QtCore.QPointF(point.x(), point.y() - int_))
    path.moveTo(QtCore.QPointF(point.x(), point.y() + int_))
    path.lineTo(QtCore.QPointF(point.x(), point.y() + ext))
    path.addEllipse(point, 1, 1)
    return path


# halo de survol (hotbox en production) : traits concentriques de plus
# en plus larges et transparents autour du bouton ; GLOW_ALPHA = opacité
# du trait intérieur à intensité pleine
GLOW_LAYERS = 10
GLOW_SPREAD = 1.2     # pixels gagnés par trait (halo de ~12 px)
GLOW_ALPHA = 46


def _painter_scale(painter):
    """Échelle du painter (1.0 = pixels logiques), ou None si la
    transformation tourne / cisaille (pas de calage possible)."""
    transform = painter.worldTransform()
    if transform.m12() or transform.m21():
        return None
    return abs(transform.m11()), abs(transform.m22())


def device_ratio(painter):
    device = painter.device()
    try:
        return float(device.devicePixelRatioF())
    except AttributeError:
        try:
            return float(device.devicePixelRatio())
        except AttributeError:
            return 1.0


def crisp_rect(rect, pen_width, ratio=1.0):
    """`rect` calé sur la grille des pixels RÉELS de l'écran. Un contour
    de 1 px posé à x = 54.97 s'étalait sur deux pixels à moitié colorés :
    bord flou. On arrondit les bords au pixel physique, puis on décale
    d'un demi-pixel quand l'épaisseur du trait (en pixels physiques) est
    impaire, pour qu'il tombe pile sur une rangée de pixels."""
    ratio = ratio or 1.0
    left = round(rect.left() * ratio)
    top = round(rect.top() * ratio)
    right = round(rect.right() * ratio)
    bottom = round(rect.bottom() * ratio)
    offset = 0.5 if int(round(pen_width * ratio)) % 2 == 1 else 0.0
    return QtCore.QRectF(
        (left + offset) / ratio, (top + offset) / ratio,
        max(right - left, 1) / ratio, max(bottom - top, 1) / ratio)


def _shape_path(options, rect):
    path = QtGui.QPainterPath()
    if options['shape'] == 'round':
        path.addEllipse(rect)
    elif options['shape'] == 'rounded_rect':
        path.addRoundedRect(
            rect, options.get('shape.cornersx', 8),
            options.get('shape.cornersy', 8))
    else:
        path.addRect(rect)
    return path


def draw_glow(painter, shape, rect):
    """Halo doux autour d'un bouton survolé ; son intensité `shape.glow`
    (0 → 1) est animée par la hotbox. Couleur : celle du contour au
    survol, sinon le fond au survol — OPAQUE, quelle que soit la
    transparence du bouton (un bouton image sans fond a aussi son
    halo)."""
    glow = getattr(shape, 'glow', 0.0)
    if glow <= 0.0:
        return
    options = shape.options
    visible_border = (
        options['border'] and options['bordercolor.transparency'] < 255)
    color = QtGui.QColor(
        options['bordercolor.hovered'] if visible_border
        else options['bgcolor.hovered'])
    path = _shape_path(options, rect)
    painter.save()
    painter.setBrush(QtCore.Qt.NoBrush)
    for layer in range(GLOW_LAYERS, 0, -1):
        layer_color = QtGui.QColor(color)
        fade = 1.0 - float(layer - 1) / GLOW_LAYERS
        layer_color.setAlpha(int(GLOW_ALPHA * glow * fade * fade))
        pen = QtGui.QPen(layer_color)
        pen.setWidthF(layer * GLOW_SPREAD * 2)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
    painter.restore()


def contained_image_rect(options, rect, image_size):
    """Zone de l'image en mode « Inside » : DANS le bouton, centrée,
    proportions gardées, à l'intérieur du contour avec une marge de
    `image.margin` % du petit côté. Avant, « fit » étirait l'image sur
    tout le bouton : décentrée si elle n'était pas au format du bouton,
    et le contour était mangé."""
    rect = QtCore.QRectF(rect)
    if options.get('shape') == 'round':
        # disque : le carré inscrit (≈ 70 %), comme pour le texte
        side = min(rect.width(), rect.height()) * 0.7071
        base = QtCore.QRectF(0, 0, side, side)
        base.moveCenter(rect.center())
    else:
        base = rect
    border = 0.0
    if options.get('border') and options.get(
            'bordercolor.transparency', 0) < 255:
        border = float(options.get('borderwidth.normal', 0) or 0)
    margin = max(float(options.get('image.margin', 12) or 0), 0.0)
    inset = border + min(base.width(), base.height()) * margin / 100.0
    inner = base.adjusted(inset, inset, -inset, -inset)
    if inner.width() <= 1 or inner.height() <= 1:
        inner = base
    width = float(image_size.width()) if image_size else 0.0
    height = float(image_size.height()) if image_size else 0.0
    if width <= 0 or height <= 0:
        target = QtCore.QRectF(inner)
    else:
        scale = min(inner.width() / width, inner.height() / height)
        target = QtCore.QRectF(0, 0, width * scale, height * scale)
        target.moveCenter(inner.center())
    target.translate(
        float(options.get('image.offsetx', 0) or 0),
        float(options.get('image.offsety', 0) or 0))
    return target


def draw_shape(painter, shape):
    options = shape.options
    content_rect = shape.content_rect()
    # lissage des images : sans lui, une icône agrandie / réduite pour
    # remplir son bouton était CRÉNELÉE (pixels répétés)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    if shape.clicked:
        bordercolor = QtGui.QColor(options['bordercolor.clicked'])
        backgroundcolor = QtGui.QColor(options['bgcolor.clicked'])
        bordersize = options['borderwidth.clicked']
    elif shape.hovered:
        bordercolor = QtGui.QColor(options['bordercolor.hovered'])
        backgroundcolor = QtGui.QColor(options['bgcolor.hovered'])
        bordersize = options['borderwidth.hovered']
    else:
        bordercolor = QtGui.QColor(options['bordercolor.normal'])
        backgroundcolor = QtGui.QColor(options['bgcolor.normal'])
        bordersize = options['borderwidth.normal']
    textcolor = QtGui.QColor(options['text.color'])
    alpha = options['bordercolor.transparency'] if options['border'] else 255
    bordercolor.setAlpha(255 - alpha)
    backgroundcolor.setAlpha(255 - options['bgcolor.transparency'])

    # pixels réels : dessin à l'échelle 1 (hotbox, aperçus, éditeur à
    # 100 %) → contours calés sur la grille de l'écran et icônes rendues
    # à leur taille d'affichage. Éditeur zoomé : dessin habituel, lissé.
    scale = _painter_scale(painter)
    ratio = device_ratio(painter)
    pixel_exact = scale is not None and scale == (1.0, 1.0)
    rect = (crisp_rect(shape.rect, bordersize, ratio) if pixel_exact
            else shape.rect)

    draw_glow(painter, shape, rect)

    pen = QtGui.QPen(bordercolor)
    pen.setStyle(QtCore.Qt.SolidLine)
    pen.setWidthF(bordersize)
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    if options['shape'] == 'round':
        painter.drawEllipse(rect)
    elif options['shape'] == 'rounded_rect':
        radius_x = options.get('shape.cornersx', 8)
        radius_y = options.get('shape.cornersy', 8)
        painter.drawRoundedRect(rect, radius_x, radius_y)
    else:  # square (défaut)
        painter.drawRect(rect)

    if shape.pixmap is not None and not shape.pixmap.isNull():
        if options.get('image.fit') and options.get('image.contain'):
            image_rect = contained_image_rect(
                options, rect, shape.pixmap.size())
        else:
            image_rect = shape.image_rect or content_rect
        drawn = False
        if pixel_exact:
            from hotboxLibrary.images import sharp_pixmap
            # zone calée sur les pixels physiques + image rendue à cette
            # taille exacte : copie 1:1, aucun ré-échantillonnage
            target = crisp_rect(QtCore.QRectF(image_rect), 0, ratio)
            sharp = sharp_pixmap(
                options.get('image.path'), target.width(), target.height(),
                ratio)
            if not sharp.isNull():
                painter.drawPixmap(target, sharp, QtCore.QRectF(sharp.rect()))
                drawn = True
        if not drawn:
            painter.drawPixmap(
                QtCore.QRectF(image_rect), shape.pixmap,
                QtCore.QRectF(shape.pixmap.rect()))

    painter.setPen(QtGui.QPen(textcolor))
    painter.setBrush(QtGui.QBrush(textcolor))
    option = QtGui.QTextOption()
    flags = VALIGNS[options['text.valign']] | HALIGNS[options['text.halign']]
    option.setAlignment(flags)
    font = QtGui.QFont()
    font.setBold(options['text.bold'])
    font.setItalic(options['text.italic'])
    font.setPixelSize(options['text.size'])
    painter.setFont(font)
    text = options['text.content']
    painter.drawText(QtCore.QRectF(content_rect), flags, text)


def draw_selection_square(painter, rect, zoom=1.0):
    bordercolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor = QtGui.QColor(SELECTION_COLOR)
    backgroundcolor.setAlpha(85)
    pen = QtGui.QPen(bordercolor)
    pen.setWidthF(1.0 / zoom)
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(backgroundcolor))
    painter.drawRect(rect)


def draw_manipulator(painter, manipulator, cursor, zoom=1.0):
    hovered = manipulator.hovered_rects(cursor)

    if manipulator.rect in hovered:
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
        brush = QtGui.QBrush(QtGui.QColor(125, 125, 125))
        brush.setStyle(QtCore.Qt.FDiagPattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawPath(manipulator.hovered_path)

    pen = QtGui.QPen(QtGui.QColor('black'))
    brush = QtGui.QBrush(QtGui.QColor('white'))
    painter.setBrush(brush)
    for rect in manipulator.handler_rects():
        pen.setWidthF((3 if rect in hovered else 1) / zoom)
        painter.setPen(pen)
        painter.drawEllipse(rect)

    pen.setWidthF(1.0 / zoom)
    pen.setStyle(QtCore.Qt.DashLine)  # if not moving else QtCore.Qt.SolidLine)
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 0)))
    painter.drawRect(manipulator.rect)


def draw_aiming_background(painter, rect):
    pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 1))
    painter.setPen(pen)
    painter.setBrush(brush)
    painter.drawRect(rect)


def draw_aiming(painter, center, target):
    pen = QtGui.QPen(QtGui.QColor(35, 35, 35))
    pen.setWidth(3)
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor(0, 0, 0, 0))
    painter.drawLine(center, target)


def get_hovered_path(rect, zoom=1.0):
    path = QtGui.QPainterPath()
    path.addRect(rect)
    path.addRect(grow_rect(rect, MANIPULATOR_BORDER / zoom))
    return path