"""Sauvegardes automatiques horodatées des hotboxes.

À chaque enregistrement, une copie du fichier ``hotboxes.json`` est
déposée dans ``<data>/backups/`` sous le nom
``hotboxes_AAAAMMJJ_HHMMSS.json``. On garde les ``MAX_BACKUPS`` plus
récentes (purge FIFO). Objectif : ne jamais perdre son travail et
pouvoir revenir à une version antérieure.
"""
import os
import shutil
import time

BACKUP_DIRNAME = 'backups'
MAX_BACKUPS = 30
# une sauvegarde au plus toutes MIN_INTERVAL secondes (évite d'en créer
# une à chaque frappe pendant une rafale de modifications)
MIN_INTERVAL = 20

_last_backup_time = {}


def backup_dir(hotboxes_file):
    folder = os.path.join(os.path.dirname(hotboxes_file), BACKUP_DIRNAME)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def _stamp():
    return time.strftime('%Y%m%d_%H%M%S')


def backup_file(hotboxes_file, force=False):
    """Copie le fichier courant dans backups/ (throttlé). Retourne le
    chemin de la sauvegarde, ou None si rien n'a été fait."""
    if not os.path.exists(hotboxes_file):
        return None
    now = time.time()
    last = _last_backup_time.get(hotboxes_file, 0)
    if not force and (now - last) < MIN_INTERVAL:
        return None
    _last_backup_time[hotboxes_file] = now

    base = os.path.splitext(os.path.basename(hotboxes_file))[0]
    folder = backup_dir(hotboxes_file)
    destination = os.path.join(folder, '%s_%s.json' % (base, _stamp()))
    try:
        shutil.copy2(hotboxes_file, destination)
    except OSError:
        return None
    _purge(folder, base)
    return destination


def list_backups(hotboxes_file):
    """Sauvegardes disponibles, de la plus récente à la plus ancienne :
    liste de (chemin, horodatage lisible)."""
    base = os.path.splitext(os.path.basename(hotboxes_file))[0]
    folder = os.path.join(os.path.dirname(hotboxes_file), BACKUP_DIRNAME)
    if not os.path.exists(folder):
        return []
    entries = []
    for name in os.listdir(folder):
        if name.startswith(base + '_') and name.endswith('.json'):
            path = os.path.join(folder, name)
            stamp = name[len(base) + 1:-5]
            entries.append((path, _readable(stamp)))
    entries.sort(key=lambda e: e[0], reverse=True)
    return entries


def _readable(stamp):
    try:
        parsed = time.strptime(stamp, '%Y%m%d_%H%M%S')
        return time.strftime('%d/%m/%Y %H:%M:%S', parsed)
    except ValueError:
        return stamp


def _purge(folder, base):
    backups = sorted(
        name for name in os.listdir(folder)
        if name.startswith(base + '_') and name.endswith('.json'))
    while len(backups) > MAX_BACKUPS:
        try:
            os.remove(os.path.join(folder, backups.pop(0)))
        except OSError:
            break
