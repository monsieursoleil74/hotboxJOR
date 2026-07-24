"""Import de pickers dwpicker (.json).

dwpicker descend du même projet : les shapes partagent la plupart des
clés. Ce module convertit un picker dwpicker en hotbox :

- ``action.targets`` (contrôleurs à sélectionner, le cœur d'un picker)
  → commande Python ``cmds.select(...)`` sur le clic gauche ;
- ``action.commands`` (système de commandes de dwpicker ≥ 0.11, une
  liste) et l'ancien format ``action.left.command`` → clics
  gauche/droite de la hotbox ;
- shapes ``rounded_rect``/``custom`` → ``square`` (pas de chemins
  vectoriels côté hotbox pour l'instant) ;
- les shapes marquées ``background`` sont importées **verrouillées** ;
- la zone de la hotbox est calculée autour des shapes (comme le bouton
  « fit zone ») puisque dwpicker n'a pas de zone fixe.

Les panneaux multiples, layers de visibilité et menus contextuels de
dwpicker n'ont pas d'équivalent : ils sont fusionnés/ignorés.

La détection est automatique : le bouton Import du manager reconnaît
un fichier dwpicker et le convertit à la volée.
"""
from hotbox_designer.templates import SQUARE_BUTTON, HOTBOX

ZONE_MARGIN = 10
KNOWN_LANGUAGES = ('python', 'mel')


def is_dwpicker_data(data):
    """Un JSON dwpicker et une hotbox se ressemblent : on tranche sur
    les clés propres à dwpicker."""
    try:
        general = data['general']
        shapes = data['shapes']
    except (KeyError, TypeError):
        return False
    if not isinstance(general, dict) or not isinstance(shapes, list):
        return False
    if 'panels' in general or 'panels.names' in general:
        return True
    return any(
        isinstance(shape, dict) and (
            'action.targets' in shape or 'action.commands' in shape)
        for shape in shapes)


def targets_to_command(targets):
    lines = [
        'from maya import cmds',
        'cmds.select(%r, replace=True)' % (list(targets),)]
    return '\n'.join(lines)


def convert_shape(dwshape):
    """Convertit une shape dwpicker vers le format hotbox."""
    options = dict(SQUARE_BUTTON)
    for key in list(options):
        if key in dwshape:
            options[key] = dwshape[key]
    if options['shape'] not in ('square', 'round'):
        options['shape'] = 'square'

    # actions reconstruites de zéro
    for side in ('left', 'right'):
        options['action.%s' % side] = False
        options['action.%s.close' % side] = False
        options['action.%s.language' % side] = 'python'
        options['action.%s.command' % side] = ''
    free = {'left': True, 'right': True}

    def set_action(side, language, command):
        if language not in KNOWN_LANGUAGES:
            language = 'python'
        options['action.%s' % side] = True
        options['action.%s.language' % side] = language
        options['action.%s.command' % side] = command
        free[side] = False

    # 1) les targets de sélection -> clic gauche
    targets = dwshape.get('action.targets') or []
    if targets:
        set_action('left', 'python', targets_to_command(targets))

    # 2) commandes nouveau format (liste), en respectant le bouton
    #    déclaré quand le slot est libre
    for command in dwshape.get('action.commands') or []:
        if not isinstance(command, dict) or not command.get('command'):
            continue
        wanted = command.get('button', 'left')
        if wanted in free and free[wanted]:
            side = wanted
        elif free['left']:
            side = 'left'
        elif free['right']:
            side = 'right'
        else:
            continue  # plus de slot : commande surnuméraire ignorée
        set_action(
            side, command.get('language', 'python'), command['command'])

    # 3) ancien format dwpicker (avant 0.11) : mêmes clés que la hotbox
    for side in ('left', 'right'):
        command = dwshape.get('action.%s.command' % side)
        if command and free[side]:
            set_action(
                side,
                dwshape.get('action.%s.language' % side, 'python'),
                command)

    # un fond de picker arrive verrouillé (insélectionnable)
    if dwshape.get('background'):
        options['lock'] = True
    return options


def convert_dwpicker_to_hotbox(data):
    shapes = [
        convert_shape(shape) for shape in data['shapes']
        if isinstance(shape, dict)]

    if shapes:
        min_left = min(s['shape.left'] for s in shapes)
        min_top = min(s['shape.top'] for s in shapes)
        max_right = max(s['shape.left'] + s['shape.width'] for s in shapes)
        max_bottom = max(s['shape.top'] + s['shape.height'] for s in shapes)
        dx = ZONE_MARGIN - min_left
        dy = ZONE_MARGIN - min_top
        for shape in shapes:
            shape['shape.left'] += dx
            shape['shape.top'] += dy
        width = int(round(max_right - min_left)) + 2 * ZONE_MARGIN
        height = int(round(max_bottom - min_top)) + 2 * ZONE_MARGIN
    else:
        width, height = 600, 400

    general = dict(HOTBOX)
    general.update({
        'name': data['general'].get('name') or 'dwpicker',
        'width': width,
        'height': height,
        'centerx': int(width / 2),
        'centery': int(height / 2)})
    return {'general': general, 'shapes': shapes}
