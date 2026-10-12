"""Dépendances embarquées (Qt.py).

Qt.py 2.x essaie PySide6 AVANT PySide2. Dans Maya 2024 (Qt 5 /
PySide2), un PySide6 installé ailleurs sur le poste (pour un autre
outil, un pip dans le dossier utilisateur…) était donc choisi : l'outil
tournait sur une AUTRE version de Qt que Maya. Symptôme remonté au
studio : « applications.py line 226: You need a shiboken-based type »
au lancement, sur un seul poste.

On impose donc à NOTRE copie de Qt.py la liaison de l'application hôte
(Maya fait foi : Qt 5 → PySide2, Qt 6 → PySide6). La préférence passe
par QT_PREFERRED_BINDING_JSON, clé = le nom de notre module seulement,
et la variable d'environnement est rétablie juste après : les autres
outils du studio qui utilisent leur propre Qt.py ne sont pas touchés.
"""
import json
import os
import sys

QT_MODULE = __name__ + '.Qt'
BINDINGS = ('PySide6', 'PySide2')


def host_binding():
    """Liaison Qt de l'application hôte, ou None si on ne sait pas."""
    try:
        from maya import cmds
        version = cmds.about(qtVersion=True)
    except Exception:
        version = None
    if version:
        return 'PySide6' if str(version).strip().startswith('6') else (
            'PySide2')
    # hors Maya : la liaison déjà chargée par l'hôte, si elle est seule
    loaded = [name for name in BINDINGS if name in sys.modules]
    if len(loaded) == 1:
        return loaded[0]
    return None


def preferred_bindings_json(binding, current=None):
    """Valeur de QT_PREFERRED_BINDING_JSON qui place `binding` en tête
    pour NOTRE Qt.py, en gardant les préférences déjà définies pour les
    autres modules."""
    try:
        preferences = json.loads(current) if current else {}
    except ValueError:
        preferences = {}
    if not isinstance(preferences, dict):
        preferences = {}
    others = [name for name in BINDINGS if name != binding]
    preferences[QT_MODULE] = [binding] + others
    return json.dumps(preferences)


def _import_qt():
    from importlib import import_module
    if QT_MODULE in sys.modules:
        return
    binding = host_binding()
    if binding is None:
        import_module(QT_MODULE)
        return
    key = 'QT_PREFERRED_BINDING_JSON'
    previous = os.environ.get(key)
    os.environ[key] = preferred_bindings_json(binding, previous)
    try:
        import_module(QT_MODULE)
    finally:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


_import_qt()
