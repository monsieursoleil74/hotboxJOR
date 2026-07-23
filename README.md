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

## Nouveautés du fork (éditeur)

- **Viewport zoom / pan** dans l'éditeur de hotbox, façon dwpicker :
  - molette = zoom vers le curseur ;
  - clic molette maintenu = déplacement de la vue ;
  - **F** = recadrer (sur la sélection s'il y en a une, sinon sur la hotbox) ;
  - la zone de la hotbox est un « plan de travail » posé sur un fond
    sombre infini, l'éditeur s'étire avec la fenêtre.
- **Alignement / distribution** (boutons en fin de barre d'outils) :
  aligner gauche/droite/haut/bas/centres, distribuer horizontalement ou
  verticalement (à partir de 3 shapes) — annulable par Ctrl+Z.
- **Poignées à taille d'écran constante** : le manipulateur et le
  rectangle de sélection restent lisibles et saisissables à tout zoom.
- **Alt + glisser** une sélection = la dupliquer et déplacer les copies
  (façon Photoshop/Figma), annulable par Ctrl+Z.

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
