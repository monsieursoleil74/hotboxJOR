
OPEN_COMMAND = """\
import hotboxLibrary
from hotboxLibrary import applications
hotboxLibrary.initialize(applications.{application}())
hotboxLibrary.show('{name}')
"""

CLOSE_COMMAND = """\
import hotboxLibrary
hotboxLibrary.hide('{name}')
"""

SWITCH_COMMAND = """\
import hotboxLibrary
from hotboxLibrary import applications
hotboxLibrary.initialize(applications.{application}())
hotboxLibrary.switch('{name}')
"""
