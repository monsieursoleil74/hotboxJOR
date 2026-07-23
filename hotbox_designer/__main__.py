"""Lancement standalone : ``python -m hotbox_designer``.

Ouvre le gestionnaire de hotboxes hors de tout DCC (données dans
~/.hotboxjor). Pratique pour développer et éditer des hotboxes sans
Maya ; les hotkeys globaux restent réservés aux DCC.
"""
import sys

from hotbox_designer.vendor.Qt import QtWidgets
from hotbox_designer.manager import launch_manager


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    launch_manager('standalone')
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
