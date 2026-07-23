# hotboxJOR

Fork personnel de [hotbox_designer](https://github.com/luckylyk/hotbox_designer)
de Lionel Brouyère (licence Clear BSD, voir `LICENSE`), avec pour objectif de
moderniser l'éditeur en s'inspirant de
[dwpicker](https://github.com/DreamWall-Animation/dwpicker) (DreamWall
Animation), lui-même dérivé du même projet d'origine.

## Objectif

Garder le cœur « hotbox » de l'original (menu volatile sous le curseur,
maintien de touche, commandes Python/MEL, format JSON) et remplacer l'éditeur
vieillissant par une expérience façon dwpicker :

- viewport avec zoom / pan fluide ;
- undo / redo complet (modèle document + historique) ;
- multi-sélection au rectangle, poignées de transformation ;
- alignement / distribution des shapes ;
- ergonomie générale (raccourcis, panneaux, retours visuels).

## Cible

- Maya d'abord (Python 3, PySide2/PySide6 — Maya 2022+). Les backends
  Nuke/Houdini de l'original sont conservés mais non testés.
- L'éditeur reste lançable **hors Maya** (mode standalone) pour le
  développement et les tests.

## Point de départ

Le premier commit de ce dépôt est une copie verbatim du dépôt amont
(`hotbox_designer/` + `LICENSE` + `README.upstream.md` + `TODO.upstream` +
`documentation/`). Tout ce qui suit dans l'historique git est propre à ce
fork.

## Lancement (comme l'amont, pour l'instant)

Dans Maya (Script Editor, onglet Python) :

```python
import sys
sys.path.insert(0, r"<chemin>/hotboxJOR")
import hotbox_designer
hotbox_designer.launch_manager('maya')
```
