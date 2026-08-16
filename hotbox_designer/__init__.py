"""API publique du package : ``hotbox_designer.launch_manager('maya')``…"""
from hotbox_designer.reader import HotboxWidget
from hotbox_designer.data import load_templates, load_json
from hotbox_designer.manager import (
    launch_manager, initialize, show, hide, switch, load_hotboxes)

__all__ = [
    'HotboxWidget', 'load_templates', 'load_json', 'launch_manager',
    'initialize', 'show', 'hide', 'switch', 'load_hotboxes']
