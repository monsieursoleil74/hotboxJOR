# hotboxJOR

Fork personnel de [hotbox_designer](https://github.com/luckylyk/hotbox_designer)
de Lionel Brouyère (licence Clear BSD, voir `LICENSE`), avec pour objectif de
moderniser l'éditeur en s'inspirant de
[dwpicker](https://github.com/DreamWall-Animation/dwpicker) (DreamWall
Animation), lui-même dérivé du même projet d'origine.

**📖 Documentation** : [`MANUEL.md`](MANUEL.md) — mode d'emploi complet
(souris, raccourcis, chaque outil et sa logique) ;
[`CHANGELOG.md`](CHANGELOG.md) — historique de ce qui est implémenté,
étape par étape. Les deux sont tenus à jour à chaque fonctionnalité.

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
- **Menu clic droit** dans l'éditeur : copier/coller, style, librairie,
  recherche/remplacement, verrouillage, ordre, suppression, fit zone,
  recadrage.
- **Thème sombre** de toute l'interface (éditeur, manager, librairie) —
  le reader garde l'apparence de la hotbox, évidemment.
- **Snap magnétique** (désactivé par défaut — opt-in via clic droit →
  « Magnet snapping ») : bords et centres s'aimantent à ceux des autres
  shapes et de la zone, guides cyan affichés ; la grille, quand elle
  est active, garde la priorité.
- **Verrouillage** (clic droit → Lock selection) : une shape verrouillée
  — un background typiquement — devient transparente à la sélection ;
  « Unlock all » pour libérer.
- **Recherche / remplacement** (Ctrl+H) dans les commandes gauche/
  droite et les labels — sur la sélection si elle existe, sinon toute la
  hotbox. Pratique pour renommer un namespace de rig.
- **Librairie de boutons** (bouton dans la barre d'outils, drag & drop) :
  sauvegarde n'importe quel bouton configuré (commandes comprises) dans
  une librairie rangée par catégories (`button_library.json` dans les
  préférences), puis glisse-dépose-le dans n'importe quelle hotbox.
  Partageable entre artistes en copiant le fichier.

Et depuis : **librairie studio partagée** (onglets logo TAT en tête de
shelf, catégories officielles), **sous-menus fluides** (un bouton ouvre
une autre hotbox sans code), **gestionnaire de raccourcis** (voir /
assigner / effacer, capture directe de la combinaison), **replace
depuis la librairie** (habiller un template sans replacer), **pipette**
dans le sélecteur de couleurs, **templates avec aperçu** + templates
utilisateur + 7 templates maison, mode « placer l'image » complet
(drag, molette, flèches)… Le détail complet est dans
[`CHANGELOG.md`](CHANGELOG.md), et le mode d'emploi dans
[`MANUEL.md`](MANUEL.md).

## Point de départ

Le premier commit de ce dépôt est une copie verbatim du dépôt amont
(`hotbox_designer/` + `LICENSE` + `README.upstream.md` +
`documentation/`). Tout ce qui suit dans l'historique git est propre à
ce fork.

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

## Migration depuis le hotbox_designer original (déjà déployé)

Si le studio utilise déjà le hotbox_designer de Lionel Brouyère, la
mise à niveau est un **remplacement de dossier** — le fork garde le
même nom de package (`hotbox_designer`) et la même API publique
(`launch_manager` / `initialize` / `show` / `hide` / `switch`) :

- **Remplacer** l'ancien dossier `hotbox_designer` par celui du fork,
  au même endroit (scripts Maya ou chemin pipeline). Ne PAS faire
  coexister les deux : un seul `hotbox_designer` sur le `sys.path`.
- **Les hotboxes existantes marchent telles quelles** : même
  `hotboxes.json` dans les préférences Maya, jamais réécrit à
  l'ouverture (les vieux formats sont convertis à la volée en
  mémoire). Les hotboxes partagées (`shared_hotboxes.json`) aussi.
- **Les hotkeys déjà posés continuent de fonctionner** : les
  nameCommands enregistrés dans Maya par l'ancien outil appellent
  `hotbox_designer.show('nom')` — exactement ce que le fork expose.
  Rien à refaire côté animateurs.
- Si un `userSetup.py` charge l'outil au démarrage
  (`initialize(Maya())`), il reste valable sans modification.

**Cas courant : l'outil est lancé par un bouton de la shelf** (pas de
userSetup). Deux options de bascule :

- **Option A — remplacement sur place** : remplacer le contenu du
  dossier `hotbox_designer` à l'endroit que le bouton de shelf référence
  déjà. Aucun bouton à modifier, bascule invisible.
- **Option B — nouveau chemin** : déposer le fork ailleurs et mettre à
  jour le script du bouton de shelf. Bouton recommandé (il porte AUSSI
  la config de la librairie studio — pas besoin de variable
  d'environnement système ni de userSetup) :

  ```python
  # bouton shelf ANIMATEUR
  import os, sys
  path = r"\\serveur\pipeline\hotboxJOR"
  if path not in sys.path:
      sys.path.insert(0, path)
  os.environ['HOTBOX_STUDIO_LIBRARY'] = r"\\serveur\pipeline\hotbox"
  import hotbox_designer
  hotbox_designer.launch_manager('maya')
  ```

  Le bouton du lead est identique avec
  `launch_manager('maya', studio_admin=True)`.

Seule nuance : le **gestionnaire de raccourcis** du fork tient un
registre (`hotbox_hotkey.json`) que l'ancien outil n'avait pas — les
hotkeys posés AVANT la migration fonctionnent mais s'affichent « — »
dans la liste tant qu'on ne les a pas réassignés une fois (Set…), ce
qui les enregistre au passage.

**Prérequis** : Maya 2022+ (Python 3 ; PySide2 et PySide6 gérés via le
shim Qt.py embarqué). L'original tournait aussi sur des Maya plus
anciens — vérifier le parc avant bascule.

### Tester le fork AVANT le déploiement (sans toucher l'installation)

Le fork peut être essayé **par-dessus** l'installation studio, dans sa
session Maya seulement — redémarrer Maya ramène à l'original, rien
n'est modifié sur le poste ni sur le réseau.

1. **Sauvegarder ses données** (une fois, par prudence — l'outil ne
   réécrit jamais les fichiers à l'ouverture, mais on va éditer) :

   ```python
   import os, shutil
   from maya import cmds
   prefs = cmds.internalVar(userPrefDir=True)
   for f in ('hotboxes.json', 'button_library.json',
             'hotbox_hotkey.json'):
       src = os.path.join(prefs, f)
       if os.path.exists(src):
           shutil.copy(src, src + '.backup')
   ```

2. **Charger le fork en priorité** (Script Editor, onglet Python).
   La purge des modules n'est nécessaire que si l'original a déjà été
   lancé dans la session (bouton de shelf cliqué, userSetup…) — elle
   est de toute façon inoffensive, autant la garder :

   ```python
   import sys
   # 1) purger l'original déjà importé dans la session
   for name in list(sys.modules):
       if name == 'hotbox_designer' or name.startswith(
               'hotbox_designer.'):
           del sys.modules[name]
   # 2) le fork passe DEVANT sur le sys.path (session seulement)
   sys.path.insert(0, r"D:\test\hotboxJOR")
   # 3) config studio locale pour l'essai + lancement admin
   import os
   os.environ['HOTBOX_STUDIO_LIBRARY'] = (
       r"C:\Users\ortzj\Desktop\JOR\hotbox")
   import hotbox_designer
   hotbox_designer.launch_manager('maya', studio_admin=True)
   ```

   Bonus : une fois les modules purgés et le fork en tête de path, même
   les **hotkeys existants** (posés par l'ancien outil) exécutent le
   fork à la prochaine pression — on teste donc aussi la chaîne
   nameCommand → fork en conditions réelles.

3. **Revenir en arrière** : fermer Maya, le rouvrir. L'installation
   déployée reprend la main (le `sys.path.insert` et la purge ne
   vivaient que dans la session). Les `.backup` restent disponibles au
   besoin.

### Images des boutons (chemins portables)

Les hotboxes stockent des chemins absolus : dans l'original, déplacer
son dossier d'icônes cassait tous les logos. Désormais, si le chemin
enregistré n'existe plus, l'image est **retrouvée par son nom de
fichier** dans les dossiers connus :

- le dossier pointé par la variable d'environnement
  `HOTBOX_DESIGNER_ICONS` (recommandé : pointe-la sur ton dossier
  d'icônes, déplace-le quand tu veux) ;
- le dossier de données (préférences Maya) et son sous-dossier
  `icons/` — y poser ses icônes marche donc aussi ;
- les dossiers des hotboxes partagées (une hotbox liée transporte ses
  icônes à côté d'elle).

Le JSON n'est pas réécrit : seul l'affichage résout le chemin.

### Données & hotkeys

- Les hotboxes vivent dans `hotboxes.json` dans les **préférences
  Maya** (`Documents\maya\<version>\prefs\`), comme l'original : les
  hotboxes créées avec l'ancien outil apparaissent telles quelles.
- Bouton **touche** (⌨) du manager : le **gestionnaire de raccourcis**
  liste toutes les hotboxes avec leur touche — Set/Change pour capturer
  une combinaison (on la tape, elle s'affiche), Clear pour la retirer.
  Maya refuse de modifier le set de raccourcis verrouillé
  `Maya_Default` — créer d'abord un set perso dans le Hotkey Editor.

### Librairie studio (équipe)

Pour partager les boutons officiels avec l'équipe, chaque poste pointe
la même librairie via une variable d'environnement (ou le
`userSetup.py` commun) :

```python
import os
os.environ['HOTBOX_STUDIO_LIBRARY'] = r"\\serveur\pipeline\hotbox"
```

Le dossier contient `button_library.json` (+ un `studio_logo.png`
optionnel pour l'icône des onglets). Les catégories studio apparaissent
en tête de la shelf de l'éditeur.

Le rôle se choisit **au lancement** — deux boutons de shelf possibles :

```python
# animateur : librairie studio en RÉFÉRENCE (lecture seule),
# librairie perso libre
import hotbox_designer
hotbox_designer.launch_manager('maya')

# lead : mode ADMIN — librairie officielle éditable (catégories,
# envoi/renommage/rangement de boutons), badge « ★ STUDIO ADMIN »
import hotbox_designer
hotbox_designer.launch_manager('maya', studio_admin=True)
```

Voir `MANUEL.md` § « Librairie de boutons » pour le fonctionnement
complet.

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
