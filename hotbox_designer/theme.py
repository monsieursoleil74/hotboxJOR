"""Thème sombre de l'interface (éditeur, manager, librairie).

Le reader n'est volontairement PAS themé : son apparence, c'est la
hotbox elle-même. Les icônes dwpicker sont dessinées pour un fond
sombre.
"""

DARK_STYLESHEET = """
QWidget {
    background-color: #3c3c3c;
    color: #d8d8d8;
    selection-background-color: #3388ff;
    selection-color: #ffffff;
}
QToolBar {
    background-color: #333333;
    border: none;
    spacing: 2px;
    padding: 2px;
}
QToolBar::separator {
    background: #555555;
    width: 1px;
    margin: 4px 3px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 2px;
}
QToolButton:hover { background: #4a4a4a; border-color: #5a5a5a; }
QToolButton:pressed, QToolButton:checked { background: #2b6bbf; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 2px 4px;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #3388ff;
}
QLineEdit:disabled { color: #777777; background-color: #353535; }
QComboBox {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 2px 6px;
}
QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    border: 1px solid #555555;
}
QPushButton {
    background-color: #4a4a4a;
    border: 1px solid #5a5a5a;
    border-radius: 3px;
    padding: 4px 12px;
}
QPushButton:hover { background-color: #565656; }
QPushButton:pressed { background-color: #2b6bbf; }
QTableView, QTreeView, QTreeWidget, QListView {
    background-color: #2f2f2f;
    alternate-background-color: #343434;
    border: 1px solid #494949;
}
QHeaderView::section {
    background-color: #3a3a3a;
    border: none;
    border-right: 1px solid #494949;
    padding: 3px;
}
QTabWidget::pane { border: none; }
QTabBar::tab {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 16px;
    margin-right: 2px;
    color: #999999;
}
QTabBar::tab:selected {
    color: #ffffff;
    border-bottom: 2px solid #3388ff;
}
QTabBar::tab:hover:!selected { color: #cccccc; }
QMenu {
    background-color: #333333;
    border: 1px solid #555555;
}
QMenu::item { padding: 4px 24px 4px 8px; }
QMenu::item:selected { background-color: #2b6bbf; }
QMenu::separator { height: 1px; background: #555555; margin: 3px 6px; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 13px; height: 13px;
    border: 1px solid #666666;
    border-radius: 2px;
    background: #2b2b2b;
}
QCheckBox::indicator:checked { background: #3388ff; }
QScrollBar:vertical {
    background: #333333; width: 12px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #555555; border-radius: 4px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #666666; }
QScrollBar:horizontal {
    background: #333333; height: 12px; margin: 0;
}
QScrollBar::handle:horizontal {
    background: #555555; border-radius: 4px; min-width: 24px;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QSlider::groove:horizontal {
    height: 4px;
    background: #2b2b2b;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 12px;
    margin: -5px 0;
    background: #d8d8d8;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover { background: #3388ff; }
QSlider::sub-page:horizontal {
    background: #2b6bbf;
    border-radius: 2px;
}
QToolTip {
    background-color: #2b2b2b;
    color: #d8d8d8;
    border: 1px solid #555555;
}
"""


def apply_dark_theme(widget):
    widget.setStyleSheet(DARK_STYLESHEET)
