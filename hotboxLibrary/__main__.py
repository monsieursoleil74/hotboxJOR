"""Lancement standalone : ``python -m hotboxLibrary``.

Ouvre le gestionnaire de hotboxes hors de tout DCC (données dans
~/.hotbox). Pratique pour développer et éditer des hotboxes sans
Maya ; les hotkeys globaux restent réservés aux DCC.
"""
import sys

from hotboxLibrary.vendor.Qt import QtWidgets
from hotboxLibrary.manager import launch_manager


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    launch_manager('standalone')
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
