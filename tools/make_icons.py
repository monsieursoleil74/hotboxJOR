"""Génère un jeu d'icônes SVG->PNG modernes, cohérentes (trait clair,
style ligne), pour la barre d'outils de l'éditeur."""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, '/workspace/hotboxjor')
from hotbox_designer.vendor.Qt import QtWidgets, QtGui, QtCore, QtSvg

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

OUT = '/workspace/hotboxjor/hotbox_designer/resources/icons'
STROKE = '#d8d8d8'
ACCENT = '#4d9bf5'
SIZE = 32

# chaque icône : contenu SVG (24x24 viewBox), trait clair
S = 'stroke="%s" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"' % STROKE
SA = 'stroke="%s" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"' % ACCENT
FA = 'fill="%s"' % ACCENT
FS = 'fill="%s"' % STROKE

ICONS = {
    # play (mode test) — triangle plein accent
    'play': '<path d="M8 5 L19 12 L8 19 Z" %s/>' % FA,
    'delete': '<path d="M5 7 h14 M9 7 V5 h6 v2 M7 7 l1 12 h8 l1-12" %s/>' % S,
    'copy': '<rect x="8" y="8" width="11" height="11" rx="2" %s/>'
            '<path d="M5 15 V5 a1 1 0 0 1 1-1 h9" %s/>' % (S, S),
    'paste': '<rect x="6" y="6" width="12" height="14" rx="2" %s/>'
             '<rect x="9" y="3" width="6" height="4" rx="1" %s/>' % (S, FS),
    'copy_settings': '<rect x="8" y="8" width="11" height="11" rx="2" %s/>'
                     '<path d="M5 15 V5 a1 1 0 0 1 1-1 h9" %s/>'
                     '<circle cx="13.5" cy="13.5" r="2" %s/>' % (S, S, SA),
    'paste_settings': '<rect x="6" y="6" width="12" height="14" rx="2" %s/>'
                      '<rect x="9" y="3" width="6" height="4" rx="1" %s/>'
                      '<circle cx="12" cy="13" r="2" %s/>' % (S, FS, SA),
    'undo': '<path d="M9 7 L4 12 L9 17 M4 12 h10 a5 5 0 0 1 5 5" %s/>' % S,
    'redo': '<path d="M15 7 L20 12 L15 17 M20 12 H10 a5 5 0 0 0-5 5" %s/>' % S,
    'snap': '<path d="M6 4 v8 a6 6 0 0 0 12 0 V4" %s/>'
            '<path d="M4 4 h4 M16 4 h4" %s/>' % (SA, SA),
    'addbutton': '<rect x="4" y="8" width="16" height="8" rx="2" %s/>'
                 '<path d="M12 5 v3 M12 16 v3" fill="none" stroke="%s" '
                 'stroke-width="2" stroke-linecap="round"/>' % (S, ACCENT),
    'addtext': '<path d="M6 6 h12 M12 6 V18 M9 18 h6" %s/>'
               '<path d="M18 4 v4 M16 6 h4" stroke="%s" stroke-width="2" '
               'stroke-linecap="round" fill="none"/>' % (S, ACCENT),
    'addbg': '<rect x="4" y="4" width="16" height="16" rx="2" %s/>'
             '<path d="M8 12 h8 M12 8 v8" stroke="%s" stroke-width="2" '
             'stroke-linecap="round" fill="none"/>' % (S, ACCENT),
    'picker': '<rect x="4" y="4" width="7" height="7" rx="1" %s/>'
              '<rect x="13" y="4" width="7" height="7" rx="1" %s/>'
              '<rect x="4" y="13" width="7" height="7" rx="1" %s/>'
              '<rect x="13" y="13" width="7" height="7" rx="1" %s/>'
              % (S, S, S, SA),
    'save': '<path d="M5 5 h11 l3 3 v11 a1 1 0 0 1-1 1 H5 a1 1 0 0 1-1-1 V5 z" '
            '%s/><rect x="8" y="13" width="8" height="6" %s/>'
            '<path d="M8 5 h6 v4 H8 z" %s/>' % (S, S, FS),
    'onbottom': '<rect x="6" y="12" width="12" height="7" rx="1" %s/>'
                '<path d="M9 8 h6 M9 5 h6" %s/>' % (FS, S),
    'ontop': '<rect x="6" y="5" width="12" height="7" rx="1" %s/>'
             '<path d="M9 16 h6 M9 19 h6" %s/>' % (FS, S),
    'movedown': '<path d="M12 4 v12 M7 11 l5 5 l5-5" %s/>'
                '<path d="M5 20 h14" %s/>' % (S, S),
    'moveup': '<path d="M12 20 v-12 M7 13 l5-5 l5 5" %s/>'
              '<path d="M5 4 h14" %s/>' % (S, S),
    'center': '<circle cx="12" cy="12" r="3" %s/>'
              '<path d="M12 3 v4 M12 17 v4 M3 12 h4 M17 12 h4" %s/>' % (SA, S),
    'fit_zone': '<path d="M4 8 V4 h4 M16 4 h4 v4 M20 16 v4 h-4 M8 20 H4 v-4" '
                '%s/><rect x="9" y="9" width="6" height="6" rx="1" %s/>'
                % (S, SA),
    'align_left': '<path d="M4 4 v16" %s/>'
                  '<rect x="7" y="6" width="11" height="4" rx="1" %s/>'
                  '<rect x="7" y="14" width="7" height="4" rx="1" %s/>'
                  % (SA, FS, FS),
    'align_right': '<path d="M20 4 v16" %s/>'
                   '<rect x="6" y="6" width="11" height="4" rx="1" %s/>'
                   '<rect x="10" y="14" width="7" height="4" rx="1" %s/>'
                   % (SA, FS, FS),
    'align_top': '<path d="M4 4 h16" %s/>'
                 '<rect x="6" y="7" width="4" height="11" rx="1" %s/>'
                 '<rect x="14" y="7" width="4" height="7" rx="1" %s/>'
                 % (SA, FS, FS),
    'align_bottom': '<path d="M4 20 h16" %s/>'
                    '<rect x="6" y="6" width="4" height="11" rx="1" %s/>'
                    '<rect x="14" y="10" width="4" height="7" rx="1" %s/>'
                    % (SA, FS, FS),
    'align_h_center': '<path d="M12 4 v16" %s/>'
                      '<rect x="4" y="6" width="16" height="4" rx="1" %s/>'
                      '<rect x="7" y="14" width="10" height="4" rx="1" %s/>'
                      % (SA, FS, FS),
    'align_v_center': '<path d="M4 12 h16" %s/>'
                      '<rect x="6" y="4" width="4" height="16" rx="1" %s/>'
                      '<rect x="14" y="7" width="4" height="10" rx="1" %s/>'
                      % (SA, FS, FS),
    'arrange_h': '<rect x="3" y="9" width="4" height="6" rx="1" %s/>'
                 '<rect x="10" y="9" width="4" height="6" rx="1" %s/>'
                 '<rect x="17" y="9" width="4" height="6" rx="1" %s/>' % (FS, FS, FS),
    'arrange_v': '<rect x="9" y="3" width="6" height="4" rx="1" %s/>'
                 '<rect x="9" y="10" width="6" height="4" rx="1" %s/>'
                 '<rect x="9" y="17" width="6" height="4" rx="1" %s/>' % (FS, FS, FS),
}


def render(name, body):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
           '%s</svg>' % body)
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg.encode('utf-8')))
    pixmap = QtGui.QPixmap(SIZE, SIZE)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.save(os.path.join(OUT, name + '.png'))


for name, body in ICONS.items():
    render(name, body)
print('généré', len(ICONS), 'icônes')
