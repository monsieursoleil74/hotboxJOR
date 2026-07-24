"""Thème sombre de l'interface (éditeur, manager, librairie).

Parti pris « pro DCC » (façon Maya/Nuke/dwpicker) : palette de gris
neutres et désaturés, formes plates, et un accent unique utilisé avec
parcimonie — sélection active, onglet courant, focus. Le reste reste
calme pour laisser ressortir le contenu (les boutons colorés).

Le reader n'est volontairement PAS themé : son apparence, c'est la
hotbox elle-même.

Pour changer la couleur d'accent, modifier ACCENT ci-dessous.
"""

# gris neutres
BG = '#393939'          # fond principal
PANEL = '#313131'       # panneaux, listes
INPUT = '#272727'       # champs de saisie
RAISED = '#454545'      # boutons
RAISED_HOVER = '#505050'
BORDER = '#242424'      # séparations franches
BORDER_SOFT = '#484848'  # bordures internes
TEXT = '#c8c8c8'
TEXT_DIM = '#8c8c8c'

# accent unique, désaturé (vert-gris façon Maya) — réservé aux états
# actifs (sélection, onglet courant, focus)
ACCENT = '#6d8c5e'
ACCENT_DIM = '#4a5f3d'


DARK_STYLESHEET = """
QWidget {{
    background-color: {BG};
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}
QToolBar {{
    background-color: {PANEL};
    border: none;
    border-bottom: 1px solid {BORDER};
    spacing: 1px;
    padding: 3px;
}}
QToolBar::separator {{
    background: {BORDER_SOFT};
    width: 1px;
    margin: 5px 4px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 2px;
    padding: 3px;
}}
QToolButton:hover {{ background: {RAISED}; }}
QToolButton:pressed, QToolButton:checked {{ background: {ACCENT_DIM}; }}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {INPUT};
    border: 1px solid {BORDER};
    border-radius: 2px;
    padding: 2px 4px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {ACCENT};
}}
QLineEdit:disabled {{ color: {TEXT_DIM}; background-color: {PANEL}; }}
QComboBox {{
    background-color: {INPUT};
    border: 1px solid {BORDER};
    border-radius: 2px;
    padding: 2px 6px;
}}
QComboBox:hover {{ border-color: {BORDER_SOFT}; }}
QComboBox::drop-down {{ border: none; width: 16px; }}
QComboBox QAbstractItemView {{
    background-color: {INPUT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT_DIM};
}}
QPushButton {{
    background-color: {RAISED};
    border: 1px solid {BORDER};
    border-radius: 2px;
    padding: 4px 12px;
}}
QPushButton:hover {{ background-color: {RAISED_HOVER}; }}
QPushButton:pressed {{ background-color: {ACCENT_DIM}; }}
QPushButton:default {{ border-color: {ACCENT_DIM}; }}
QTableView, QTreeView, QTreeWidget, QListView {{
    background-color: {PANEL};
    alternate-background-color: #353535;
    border: 1px solid {BORDER};
    outline: none;
}}
QHeaderView::section {{
    background-color: {PANEL};
    border: none;
    border-right: 1px solid {BORDER};
    padding: 3px;
}}
QTabWidget::pane {{ border: none; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 16px;
    margin-right: 2px;
    color: {TEXT_DIM};
}}
QTabBar::tab:selected {{
    color: {TEXT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{ color: {TEXT}; }}
QMenu {{
    background-color: {PANEL};
    border: 1px solid {BORDER};
    padding: 4px;
}}
QMenu::item {{ padding: 5px 24px 5px 10px; border-radius: 2px; }}
QMenu::item:selected {{ background-color: {ACCENT_DIM}; }}
QMenu::separator {{ height: 1px; background: {BORDER_SOFT}; margin: 4px 8px; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 13px; height: 13px;
    border: 1px solid {BORDER_SOFT};
    border-radius: 2px;
    background: {INPUT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QRadioButton::indicator {{ border-radius: 7px; }}
QScrollBar:vertical {{ background: {PANEL}; width: 11px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {BORDER_SOFT}; border-radius: 3px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: #5a5a5a; }}
QScrollBar:horizontal {{ background: {PANEL}; height: 11px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {BORDER_SOFT}; border-radius: 3px; min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background: #5a5a5a; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QSlider::groove:horizontal {{
    height: 4px; background: {INPUT}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px; margin: -5px 0; background: {TEXT}; border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{ background: #ffffff; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QToolTip {{
    background-color: {INPUT};
    color: {TEXT};
    border: 1px solid {BORDER_SOFT};
}}
""".format(
    BG=BG, PANEL=PANEL, INPUT=INPUT, RAISED=RAISED,
    RAISED_HOVER=RAISED_HOVER, BORDER=BORDER, BORDER_SOFT=BORDER_SOFT,
    TEXT=TEXT, TEXT_DIM=TEXT_DIM, ACCENT=ACCENT, ACCENT_DIM=ACCENT_DIM)


def apply_dark_theme(widget):
    widget.setStyleSheet(DARK_STYLESHEET)
