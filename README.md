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
- **Plusieurs hotboxes éditables en même temps** : le manager ouvre une
  fenêtre d'édition par hotbox (avant, ouvrir la deuxième fermait la
  première), chaque fenêtre porte le nom de sa hotbox.
- **Copier-coller entre hotboxes** : Ctrl+C/Ctrl+V passe par le
  presse-papier système (JSON) — on copie des boutons dans une hotbox et
  on les colle dans une autre, y compris entre deux sessions.
- **Glisser fluide** : le déplacement suit la souris jusqu'au
  relâchement — dans l'original, un geste rapide « décrochait » et il
  fallait recliquer.
- **Ajuster la zone aux shapes** (bouton à côté des champs size, façon
  dwpicker) : on pose ses boutons librement, la zone se recadre autour
  (marge 10) et le centre est recalé — plus de champs à piloter à la main.
- **Flèches = déplacer la sélection** d'1 unité (Maj = 10).
- **Copier-coller de style** (Ctrl+Shift+C / Ctrl+Shift+V, ou les deux
  boutons à côté de copier/coller) : copie les options d'une shape, puis
  colle sur la sélection en choisissant quoi (forme, taille, couleurs &
  bordure, style de texte, contenu, image, commandes) — via le
  presse-papier système, donc entre hotboxes aussi.
- **Sélection assainie** : cliquer un bouton posé sur un background ne
  sélectionne plus que le bouton ; le rectangle de sélection n'attrape
  plus un fond qui l'englobe (il faut le balayer vraiment) ; le
  rectangle fonctionne dans les quatre directions.
- **Menu clic droit** dans l'éditeur : copier/coller, style, ordre,
  suppression, fit zone, recadrage.

## Point de départ

Le premier commit de ce dépôt est une copie verbatim du dépôt amont
(`hotbox_designer/` + `LICENSE` + `README.upstream.md` + `TODO.upstream` +
`documentation/`). Tout ce qui suit dans l'historique git est propre à ce
fork.

## Installation dans Maya

1. Récupérer le code : bouton « Code → Download ZIP » sur GitHub, ou
   `git clone https://github.com/monsieursoleil74/hotboxJOR.git`
   (un `git pull` suffira ensuite pour les mises à jour).
2. Copier le dossier **`hotbox_designer`** (le dossier intérieur, celui
   qui contient `manager.py`) dans le dossier de scripts Maya :
   `C:\Users\<toi>\Documents\maya\scripts\hotbox_designer`.
   S'il y avait déjà le hotbox_designer d'origine, le remplacer — les
   hotboxes ne sont pas dedans (voir plus bas), rien n'est perdu.
3. Lancer, dans le Script Editor (onglet Python) :

   ```python
   import hotbox_designer
   hotbox_designer.launch_manager('maya')
   ```

   Glisser ces deux lignes sur la shelf avec le clic molette pour en
   faire un bouton permanent.

Variante sans copier (le dépôt reste où il est) :

```python
import sys
sys.path.insert(0, r"D:\chemin\vers\hotboxJOR")
import hotbox_designer
hotbox_designer.launch_manager('maya')
```

### Données & hotkeys

- Les hotboxes vivent dans `hotboxes.json` dans les **préférences
  Maya** (`Documents\maya\<version>\prefs\`), comme l'original : les
  hotboxes créées avec l'ancien outil apparaissent telles quelles.
- Bouton « Set hotkey » du manager : Maya refuse de modifier le set de
  raccourcis verrouillé `Maya_Default` — créer d'abord un set perso
  dans le Hotkey Editor.

### Chargement auto au démarrage (optionnel)

Pour que les hotkeys fonctionnent sans lancer le manager, dans
`Documents\maya\scripts\userSetup.py` :

```python
from maya import utils

def _load_hotboxes():
    import hotbox_designer
    from hotbox_designer.applications import Maya
    hotbox_designer.initialize(Maya())

utils.executeDeferred(_load_hotboxes)
```

## Lancement hors Maya (standalone)

`pip install PySide6` puis, depuis le dossier du dépôt :
`python -m hotbox_designer` — les données standalone vivent dans
`~/.hotboxjor`, séparées de celles de Maya.

## Tests

`QT_QPA_PLATFORM=offscreen python tests/test_editor.py` (headless).
