
PYTHON = 'python'
MEL = 'mel'
NUKE_TCL = 'nuke tcl'
NUKE_EXPRESSION = 'nuke expression'
HSCRIPT = 'houdini script'
RUMBA_SCRIPT  = 'rumba script'


def execute_code(language, code):
    # garde-fou : l'appel généré par le registre de commandes
    # (`hotbox_designer.run('Nom')`) est TOUJOURS du Python. Posé sur
    # un clic resté en MEL (vieux bouton recyclé), il donnait un
    # « Cannot find procedure "import" » incompréhensible — on
    # l'exécute en Python quoi qu'il arrive.
    if language == MEL and 'hotbox_designer.run(' in code:
        language = PYTHON
    return EXECUTORS[language](code)


def execute_python(code):
    exec(code, globals())


def execute_mel(code):
    from maya import mel
    mel.eval(code.replace(u'\u2029', '\n'))


def execute_nuke_tcl(code):
    import nuke
    nuke.tcl(code)


def execute_nuke_expression(code):
    import nuke
    nuke.expression(code)


def execute_hscript(code):
    import hou
    hou.hscript(code)

def execute_rumba_script(code):
    import script
    script.script_interpreter.exec_script(code, globals())


EXECUTORS = {
    PYTHON: execute_python,
    MEL: execute_mel,
    NUKE_TCL: execute_nuke_tcl,
    NUKE_EXPRESSION: execute_nuke_expression,
    HSCRIPT: execute_hscript,
    RUMBA_SCRIPT: execute_rumba_script
}
