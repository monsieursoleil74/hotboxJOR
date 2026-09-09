"""API publique du package : ``hotboxLibrary.launch_manager('maya')``…"""
from hotboxLibrary.reader import HotboxWidget
from hotboxLibrary.data import load_templates, load_json
from hotboxLibrary.manager import (
    launch_manager, initialize, show, hide, switch, load_hotboxes)

__all__ = [
    'HotboxWidget', 'load_templates', 'load_json', 'launch_manager',
    'initialize', 'show', 'hide', 'switch', 'load_hotboxes']
