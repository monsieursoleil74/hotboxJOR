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
import types

QT_MODULE = __name__ + '.Qt'
BINDINGS = ('PySide6', 'PySide2')

# Qt.py charge par défaut une trentaine de modules Qt (QtPositioning,
# QtSensors, QtWebSockets…). L'outil n'en utilise que quatre. Les autres
# coûtaient du temps au premier lancement et, sur les postes où une
# stratégie de sécurité Windows bloque certaines DLL Qt, affichaient
# « Qt.py [warning]: ImportError(QtPositioning): DLL load failed… ».
KEEP_MODULES = ('QtCore', 'QtGui', 'QtWidgets', 'QtSvg')
# modules annexes déclarés par binding (QtUiTools, QtSvgWidgets…) :
# aucun ne sert ; « sip » est gardé pour un repli PyQt éventuel.
# (shiboken2 / shiboken6 sont chargés à part, ils restent.)
KEEP_EXTRAS = ('sip',)


def site_config(previous=None):
    """Module « QtSiteConfig » (point d'entrée prévu par Qt.py) qui
    limite NOTRE Qt.py aux modules utiles. Un QtSiteConfig du studio,
    s'il existe, est appliqué d'abord : on ne retire rien de ce qu'il
    configure pour les modules gardés."""
    module = types.ModuleType('QtSiteConfig')

    def update_members(members):
        if previous is not None and hasattr(previous, 'update_members'):
            previous.update_members(members)
        for name in list(members):
            if name not in KEEP_MODULES:
                del members[name]

    def update_misplaced_members(members):
        if (previous is not None
                and hasattr(previous, 'update_misplaced_members')):
            previous.update_misplaced_members(members=members)
        for entries in members.values():
            extras = entries.get('__extras__')
            if extras is not None:
                entries['__extras__'] = [
                    name for name in extras if name in KEEP_EXTRAS]

    def update_compatibility_members(members):
        if (previous is not None
                and hasattr(previous, 'update_compatibility_members')):
            previous.update_compatibility_members(members=members)

    module.update_members = update_members
    module.update_misplaced_members = update_misplaced_members
    module.update_compatibility_members = update_compatibility_members
    return module


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


def _studio_site_config():
    """Le QtSiteConfig du studio s'il y en a un, sinon None."""
    if 'QtSiteConfig' in sys.modules:
        return sys.modules['QtSiteConfig']
    try:
        import QtSiteConfig
    except Exception:
        return None
    return QtSiteConfig


def _import_qt():
    from importlib import import_module
    if QT_MODULE in sys.modules:
        return
    # liaison : celle de l'hôte, pour notre Qt.py seulement
    binding = host_binding()
    key = 'QT_PREFERRED_BINDING_JSON'
    previous_env = os.environ.get(key)
    if binding is not None:
        os.environ[key] = preferred_bindings_json(binding, previous_env)
    # modules : seulement ceux qu'on utilise. QtSiteConfig n'est remplacé
    # que le temps de NOTRE import, puis rétabli (les autres outils du
    # studio voient le leur, ou aucun)
    studio_site = _studio_site_config()
    sys.modules['QtSiteConfig'] = site_config(studio_site)
    try:
        import_module(QT_MODULE)
    finally:
        # le module du studio (même s'il vient d'être importé ici) reste
        # en place tel quel ; sans module studio, rien ne reste
        if studio_site is not None:
            sys.modules['QtSiteConfig'] = studio_site
        else:
            sys.modules.pop('QtSiteConfig', None)
        if binding is not None:
            if previous_env is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous_env


_import_qt()
