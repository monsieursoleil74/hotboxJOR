# Manuel hotboxJOR

Mode d'emploi de l'éditeur et des outils du fork. Tenu à jour à chaque
fonctionnalité ajoutée. Pour l'installation : voir `README.md`. Pour
l'historique des évolutions : voir `CHANGELOG.md`.

---

## Vue d'ensemble

Trois fenêtres :

| Fenêtre | Rôle |
|---|---|
| **Manager** | Liste des hotboxes : créer, éditer, supprimer, importer/exporter, **gérer les raccourcis** (voir/assigner/effacer). |
| **Éditeur** | Là où on construit une hotbox. Plusieurs éditeurs peuvent être ouverts en même temps (un par hotbox). |
| **Reader** | La hotbox en production : ce qui s'affiche sous le curseur dans Maya. Non themé — son apparence, c'est ta hotbox. |

Les hotboxes vivent dans `hotboxes.json` dans les préférences Maya
(`Documents\maya\<version>\prefs\`) — compatibles avec l'original
hotbox_designer, jamais altérées par une simple ouverture.

---

## L'éditeur — navigation (viewport)

La zone de la hotbox est un **plan de travail** posé sur un fond sombre
infini, façon dwpicker/Figma.

| Geste | Action |
|---|---|
| **Molette** | Zoom vers le curseur (×0.1 à ×8) |
| **+ / −** | Zoom au centre de la vue |
| **Clic molette maintenu** | Pan (déplacer la vue) |
| **Espace + glisser** | Pan aussi (façon Photoshop — curseur main) |
| **F** | Recadrer : sur la sélection s'il y en a une, sinon sur la hotbox |

À l'ouverture, la hotbox est **cadrée automatiquement** — et le reste
tant qu'on n'a pas zoomé/panné soi-même (redimensionner la fenêtre
recadre proprement). Dès qu'on navigue (molette, +/−, pan, F), la vue
nous appartient et n'est plus touchée. Les poignées du manipulateur et
les traits d'interface gardent une **taille constante à l'écran** quel
que soit le zoom.

## L'éditeur — sélection

| Geste | Action |
|---|---|
| **Presser** un bouton | Le sélectionne immédiatement — le drag qui suit le **déplace** directement (façon dwpicker/Figma) |
| **Clic** sur un bouton d'une multi-sélection | Le sélectionne **seul** |
| **Glisser sur le fond** (zone vide ou shape verrouillée) | Rectangle de sélection multiple |
| **Maj + clic/rectangle** | Ajoute à la sélection |
| **Ctrl + clic/rectangle** | Retire de la sélection |
| **Ctrl+Maj + clic/rectangle** | Inverse |
| **Ctrl+A** | Tout sélectionner |
| **Ctrl+D** | Tout désélectionner |
| **Ctrl+I** | Inverser la sélection |

Logique particulière :

- Un rectangle de sélection **n'attrape pas une shape qui l'englobe
  entièrement** — un background n'est pris que si on le balaie vraiment.
  Pour sélectionner le fond, clique une zone nue.
- Une shape **verrouillée** (voir Lock) est transparente à la sélection.
- **Conseil** : verrouille ton background — comme presser une shape la
  déplace, un fond verrouillé laisse le rectangle de sélection
  fonctionner partout.

## L'éditeur — manipulation

| Geste | Action |
|---|---|
| **Glisser la sélection** | Déplacer (suit la souris jusqu'au relâchement, même en geste rapide) |
| **Maj pendant le déplacement** | Contrainte à l'**axe dominant** (horizontal ou vertical, façon Photoshop) |
| **Glisser un bord ou un coin** | Redimensionner — **tout le contour est saisissable** (~8 px), pas seulement les 8 poignées ; Maj = carré |
| **Alt + glisser la sélection** | **Dupliquer** : les copies partent sous le curseur, les originaux restent |
| **Flèches** | Déplacer d'1 unité (**Maj** = 10) |
| **Suppr** | Supprimer la sélection |
| **Ctrl+Z / Ctrl+Y** | Undo / redo (tout est annulable) |

Le **curseur annonce le geste** : flèches de redimensionnement (↔ ↕ ⤡ ⤢)
sur les bords et coins, croix de déplacement à l'intérieur de la
sélection, main quand Espace est enfoncé.

### Snap magnétique 🧲 (désactivé par défaut)

**Aucun snap n'est actif par défaut.** Deux systèmes, au choix :

- La **grille** : bouton aimant rouge de la barre d'outils + pas x/y —
  comme dans l'original.
- Le **magnet aux shapes** (opt-in) : clic droit → « Magnet snapping » —
  bords et centres s'aimantent à ceux des autres shapes et de la zone
  (~6 px écran), guides cyan en pointillés. Si la grille est active,
  elle garde la priorité.

### Alignement / distribution / disposition radiale

Boutons en fin de barre d'outils (à partir de 2 shapes sélectionnées,
3 pour la distribution) :

- Aligner : gauche, centres horizontaux, droite, haut, centres
  verticaux, bas.
- Distribuer : horizontalement / verticalement (les centres se
  répartissent régulièrement entre la première et la dernière shape).

## Mode test ▶️

Bouton **play** (tout à gauche de la barre d'outils) : affiche la
hotbox **exactement comme en production** (le reader), à l'endroit du
curseur. On teste le survol, les clics gauche/droite, les couleurs
d'état et les sous-menus sans quitter l'éditeur. Échap ferme ; la
fenêtre de test se ferme aussi avec l'éditeur. (Dans Maya, les
commandes des boutons s'exécutent réellement — c'est un vrai test.)

## Copier / coller

| Raccourci | Action |
|---|---|
| **Ctrl+C / Ctrl+V** | Copier/coller des **boutons entiers**. Passe par le presse-papier système (JSON) : fonctionne **entre hotboxes**, entre éditeurs, et même entre deux sessions Maya. Les shapes collées sont sélectionnées. |
| **Ctrl+Maj+C** | **Copier le style** d'une shape (une seule sélectionnée) |
| **Ctrl+Maj+V** | **Coller le style** sur la sélection — un dialogue permet de cocher quoi coller : forme (carré/rond), taille, couleurs & bordure, style de texte, contenu du texte, image, **commandes**. Par défaut : forme + couleurs + style de texte. |

## Lock (verrouillage)

Clic droit → **Lock selection** : les shapes sélectionnées deviennent
insélectionnables et indéplaçables (clé `lock` dans leurs options).
Usage type : verrouiller le background pour qu'il ne gêne plus jamais.
Clic droit → **Unlock all (n)** pour tout libérer.

## Recherche / remplacement — **Ctrl+H**

Remplace du texte dans :

- les commandes **clic gauche** et/ou **clic droit** ;
- les **labels** des boutons (optionnel).

Portée : la **sélection** si elle existe, sinon **toute la hotbox**.
Affiche le nombre de remplacements. Annulable. Usage type : renommer un
namespace de rig dans tous les boutons d'un coup.

## Zone de travail (« Fit zone »)

La zone = la taille de la fenêtre du reader dans Maya. Plutôt que de
piloter les champs `size` à la main : pose tes boutons librement,
puis clique le bouton **cadre** (à côté des champs size, aussi au clic
droit) — la zone se recadre sur la bounding box des boutons (marge 10),
les shapes et le **centre** sont recalés (la hotbox apparaîtra au même
endroit relatif sous le curseur), la vue est recadrée. Annulable.

## Librairie de boutons 📚 (shelf intégrée, façon shelf Maya)

L'idée : configurer un bouton une fois (commande, couleurs, texte…),
le ranger, le réutiliser dans toutes ses hotboxes. La librairie est une
**shelf en bas de l'éditeur** : un onglet par catégorie, chaque bouton
affiché avec son vrai rendu en vignette.

- **Sauvegarder** : sélectionne un ou plusieurs boutons → bouton 💾 de
  la barre d'outils (ou clic droit → « Save selection to library… ») →
  nom + **destination** + catégorie. La **destination** (« Library »)
  permet de choisir **Perso** ou **Studio (TAT)** dès la sauvegarde : on
  peut donc ranger un bouton directement dans une shelf TAT, sans passer
  par General puis « Move to ». Le choix n'apparaît que si un
  emplacement studio est configuré ; les catégories proposées s'adaptent
  à la destination (l'onglet courant est proposé par défaut). Toutes les
  shelves ouvertes se rafraîchissent.
- **Réutiliser** : **glisse-dépose** depuis la shelf vers le canvas
  juste au-dessus : le bouton atterrit sous le curseur, sélectionné.
  Multi-sélection possible. Ça marche aussi vers un AUTRE éditeur.
- **Renommer un bouton** : clic droit sur un bouton de la shelf →
  **Rename…** (perso comme studio). Le bouton garde son apparence et sa
  commande, seul son nom change.
- **Supprimer** : clic droit sur un bouton de la shelf → Delete.
- **Ouvrir le dossier** (JSON brut) : clic droit sur la shelf ou un
  onglet → « Open library folder » — ouvre l'explorateur à
  l'emplacement du `button_library.json` (perso ou studio selon
  l'onglet).
- **Organiser les catégories** — clic droit sur un **onglet** :
  - **New category… / New studio category…** — créer une catégorie
    (persistée même vide ; le libellé s'adapte selon que l'onglet est
    perso ou studio). Le bouton **＋** en haut à droite crée toujours
    une catégorie **perso**.
  - **Rename category…** — renommer : tous les boutons de la catégorie
    (et le marqueur de catégorie vide) sont ré-étiquetés.
  - **Delete category** — supprimer (seulement si elle est vide).
  - Ces trois actions marchent aussi sur les onglets **studio** (elles
    écrivent dans le `button_library.json` du dossier studio).
- **Ranger un bouton dans une autre catégorie** : clic droit sur un ou
  plusieurs boutons → **Move to category…** (choisir une catégorie
  existante ou en taper une nouvelle). Fonctionne côté perso ET studio.
- **Masquer/afficher** la shelf : le bouton librairie de la barre
  d'outils.

### Où c'est stocké

- **Perso** (modifiable) : `button_library.json` dans le dossier de
  données — préférences Maya (`Documents\maya\<version>\prefs\`), ou
  `~/.hotboxjor` en standalone.
- **Studio** (partagée, catégories officielles) : un fichier commun,
  désigné par la variable d'environnement **`HOTBOX_STUDIO_LIBRARY`**
  (un `.json`, ou un dossier contenant `button_library.json`). À défaut
  de variable, l'outil regarde `C:\Users\ortzj\Desktop\JOR\hotbox`. Les
  catégories studio apparaissent en tête de la shelf avec le **logo du
  studio** (TAT) en icône ; leurs boutons se glissent-déposent
  normalement dans une hotbox.

  Pour l'instant la librairie studio est **pleinement modifiable** :
  créer une **catégorie officielle** (clic droit sur un onglet studio →
  *New studio category…*) l'écrit dans le `button_library.json` du
  dossier studio, avec le logo TAT ; on peut y **envoyer des boutons**
  (*Send to studio library*), les renommer, les ranger. La restriction
  d'accès pour les animateurs viendra plus tard.

  **Logo du studio** : pose un `studio_logo.png` (ou `logo.png`) dans le
  dossier de la librairie studio — il devient l'icône des onglets. On
  peut aussi pointer un fichier précis via la variable
  `HOTBOX_STUDIO_LOGO`. Sans rien, un logo par défaut est utilisé.

### Publier vers la librairie studio (export)

Le plus simple : **clic droit sur un ou plusieurs boutons de la
shelf → « Send to studio library »**. Les boutons sont copiés dans la
librairie studio (dédupliqués), et les onglets se rafraîchissent — pas
de fichier à copier à la main. (L'action n'est disponible que si un
emplacement studio est configuré et accessible en écriture.)

Alternative manuelle : copier son `button_library.json` dans le dossier
studio.

### Organiser la librairie studio

1. Le lead construit ses boutons officiels (IK/FK, sélections,
   playblast…) dans sa librairie perso, catégories claires.
2. Il les publie : clic droit → « Send to studio library » (ou copie
   manuelle du `button_library.json` dans le dossier studio).
3. Chaque animateur voit automatiquement les onglets studio (logo TAT)
   + ses propres onglets perso. Pour pointer un autre
   chemin : définir `HOTBOX_STUDIO_LIBRARY` (variable d'environnement
   Windows, ou dans le `userSetup.py` commun :
   `os.environ['HOTBOX_STUDIO_LIBRARY'] = r"P:\pipeline\hotbox"`).

## Import de pickers dwpicker

Le bouton **Import** du manager accepte aussi les fichiers `.json` de
**dwpicker** — la détection est automatique, rien à choisir :

- les **targets de sélection** (le cœur d'un picker) deviennent une
  commande `cmds.select([...])` sur le clic gauche ;
- les **commandes** (nouveau format ≥ 0.11 comme l'ancien) sont
  réparties sur les clics gauche/droite, langage conservé ;
- les shapes `rounded_rect`/`custom` deviennent des rectangles (pas de
  chemins vectoriels côté hotbox) ;
- les **fonds** de picker arrivent **verrouillés** (Unlock all pour les
  libérer) ;
- la **zone** est calculée automatiquement autour des shapes (comme le
  bouton fit zone), le centre au milieu.

Limites : panneaux multiples fusionnés, layers de visibilité et menus
contextuels ignorés, une seule commande par clic (les surnuméraires
sont ignorées).

## Images des boutons (chemins portables)

Les chemins d'images sont stockés en absolu dans le JSON ; déplacer son
dossier d'icônes cassait tous les logos. Désormais, si le chemin ne
mène plus nulle part, l'image est **retrouvée par son nom de fichier**
dans :

1. le dossier pointé par la variable d'environnement
   **`HOTBOX_DESIGNER_ICONS`** (recommandé) ;
2. le dossier de préférences et son sous-dossier `icons/` ;
3. les dossiers des hotboxes partagées.

Le JSON n'est jamais réécrit — seule la résolution d'affichage change.

## Placer une image dans un bouton

Quand un bouton a une image et que **« Fit to shape » est sur False**,
la section Image affiche deux boutons :

- **◈ Place in button** : active le mode placement. On **glisse
  l'image** dans le bouton pour la positionner, la **molette** la
  redimensionne, et les **flèches** la décalent d'1 unité (**Maj** = 10)
  pour un réglage au pixel près. **Échap** (ou re-cliquer le bouton)
  termine. Un contour vert en pointillés montre la position de l'image.
- **Center** : recentre l'image dans le bouton.

Tout est annulable (Ctrl+Z). Le placement n'est possible que sur un
seul bouton à la fois.

## Formes des boutons

Trois formes : **square** (rectangle), **rounded** (rectangle à coins
arrondis, façon dwpicker — le rayon se règle dans le champ « Corner ») et
**round** (ellipse). Le sélecteur est en haut du panneau d'attributs.

## Aperçu dans le manager

La hotbox sélectionnée est affichée en **vignette** (mini-rendu de tous
ses boutons) en haut du panneau de droite — pour la reconnaître d'un
coup d'œil.

## Panneau d'attributs (à droite)

Refondu façon Photoshop :

- **Couleurs = pastilles cliquables**, les trois états (Normal / Hover /
  Click) **sur une seule ligne** sous une petite légende ; le code hexa
  est dans l'**infobulle** (survole la pastille). Un clic ouvre le
  **sélecteur de couleurs** maison (façon Miro) : carré
  saturation/valeur, teinte, hexa, couleurs prédéfinies, et la
  **pipette ⌖** pour prélever une couleur n'importe où à l'écran (clic =
  prélever, Échap = annuler — le « Pick Screen Color » du dialogue
  natif). Si la sélection a des couleurs différentes, la pastille
  affiche « … ».
- **Opacité = curseur 0-100 %** (une pour le fond, une pour la
  bordure) — la valeur est convertie vers la « transparence 0-255 »
  historique du JSON, rien ne change dans le format.
- **Cases à cocher** pour bordure visible / gras / italique (état
  intermédiaire si la sélection est mixte).
- **Épaisseur de bordure = un curseur** (comme l'opacité, en px) : il
  pilote les trois états d'un coup — survol ×1.25 et clic ×2 par
  rapport à la valeur normale.
- La section **Dimensions a été retirée** (tout se manipule au
  viewport) — son champ « top » écrivait d'ailleurs dans `shape.right`
  (bug de l'original).
- **Sous-menu fluide** — en haut de la section **Action**, un menu
  déroulant « Open sub-hotbox » liste les autres hotboxes marquées
  « is submenu » (dans le manager). En choisir une **génère toute seule**
  la commande d'ouverture (`show('nom')`) sur le clic gauche du/des
  bouton(s) sélectionné(s) : plus besoin d'écrire une ligne de Python à
  la main pour enchaîner deux hotboxes. La liste reste cachée tant
  qu'aucune hotbox n'est marquée sous-menu.

## Menu clic droit (récapitulatif)

Volontairement court : il ne reprend PAS ce qui est déjà dans la barre
d'outils. Seulement — Save selection to library… / **Replace with
library button** • Lock selection / Unlock all / Magnet snapping •
Search and replace… (Ctrl+H) / Frame view (F).

**Replace with library button** : sélectionne UN bouton dans la shelf
du bas, puis clic droit sur un ou plusieurs boutons du canvas →
Replace. Le contenu (couleurs, texte, image, commandes…) vient de la
librairie, **la position et la taille sont conservées** — idéal pour
habiller un template sans replacer chaque bouton à la main.

## Templates

À la création d'une hotbox (« From template »), un **aperçu** du
template s'affiche dans le dialogue (idem pour « Duplicate existing »).

Aux templates hérités de l'original s'ajoutent des templates maison,
dans le style du thème : **Pie_8_Directions** (marking menu à 8
directions), **Mini_Shelf_4x3** (panneau titré + grille de 12 boutons),
**Barre_6_Boutons** (bande compacte), **Manette** (croix
directionnelle + boutons A/B/X/Y colorés + gâchettes, façon manette de
jeu), **Nid_Abeille** (14 boutons ronds en quinconce serré),
**Colonnes_TAT** (4 colonnes titrées SHELF / ANIM / EXTRA / ANIMBOT,
calquées sur les catégories studio) et **Grille_6x4** (24 boutons).
Combinés à « Replace with library button », ils permettent de monter
une hotbox en quelques minutes : créer depuis le template, puis
remplacer chaque bouton par un bouton de la shelf.

**Créer ses propres templates** : sélectionne une hotbox dans le
manager → bouton **Save hotbox as template** (💾 de la barre d'outils du
manager, à côté d'export). Elle est copiée dans `templates/` du dossier
de données et apparaît dès lors dans la liste « From template », après
les templates embarqués. Un template est une copie figée : modifier la
hotbox d'origine ne le change pas.

## Barre d'outils, de gauche à droite

Supprimer • copier • coller • copier style • coller style — undo /
redo — grille (aimant rouge) + pas x/y — champs **size** + **fit
zone** — édition du **centre** + coordonnées — ajout : bouton / texte /
background — **librairie** / **enregistrer dans la librairie** — ordre :
tout au fond / tout devant — alignements (6) — distributions
(2).

## Raccourcis clavier (gestionnaire)

Le bouton **touche** de la barre d'outils du manager (⌨) ouvre le
**gestionnaire de raccourcis** : un tableau qui liste **toutes** les
hotboxes avec la touche qui leur est assignée.

- **Voir** — chaque ligne montre la hotbox et sa touche (ou « — » si
  aucune). Avant, on pouvait assigner un raccourci mais jamais le revoir.
- **Set… / Change…** — ouvre le sélecteur de touche : on **tape
  directement** la combinaison (ex. Maj+Q) dans le champ **Shortcut** et
  elle s'affiche telle quelle (« Shift+q »). Plus besoin de cocher
  Ctrl/Alt/Shift : les modificateurs sont lus sur la frappe. Échap
  efface. On choisit ensuite le type d'événement.
- **Clear** — **retire** le raccourci. Sous Maya, la touche est
  réellement débranchée (press ET release), pas seulement oubliée.

Sous le capot, un petit fichier `hotbox_hotkey.json` (dossier de
données du DCC) tient le registre des raccourcis, commun à tous les
backends — c'est lui qui alimente le tableau. Les raccourcis globaux
n'existent que dans un DCC (Maya, Nuke…) : hors DCC le tableau
l'indique et les boutons Set sont désactivés. Si le set de hotkeys Maya
courant est verrouillé (`Maya_Default`), l'éditeur de hotkeys de Maya
s'ouvre pour le changer.

---

## Logique interne (pour s'y retrouver dans le code)

- **Coordonnées** : les shapes vivent dans l'espace de la hotbox
  (« unités ») — le JSON est donc identique à l'original. Le viewport
  applique zoom + translation au rendu (`ViewportMapper` dans
  `geometry.py`, adapté de dwpicker) ; les événements souris sont
  convertis en unités avant toute logique.
- **Undo** : modèle « snapshot » — chaque modification pousse une copie
  profonde de la hotbox complète (`UndoManager`,
  `designer/application.py`).
- **Presse-papier** : boutons et styles transitent par le presse-papier
  **système** en JSON avec une clé marqueur (`SHAPES_CLIPBOARD_KEY`,
  `STYLE_CLIPBOARD_KEY`) — d'où le fonctionnement inter-fenêtres et
  inter-sessions.
- **Multi-éditeurs** : le manager lie chaque fenêtre d'édition à sa
  hotbox par identité d'objet (`_EditorLink`), pas par ligne
  sélectionnée.
- **Fichiers clés** : `designer/editarea.py` (viewport + interactions),
  `designer/application.py` (fenêtre d'édition, actions),
  `designer/menu.py` (barre d'outils), `interactive.py` (Shape,
  manipulateur), `painting.py` (rendu), `geometry.py` (maths),
  `buttonlibrary.py` (librairie), `images.py` (chemins portables),
  `theme.py` (thème sombre), `manager.py`, `reader.py`,
  `applications.py` (backends Maya/standalone…).

## Tests

`QT_QPA_PLATFORM=offscreen python tests/test_editor.py` — 14 familles
de tests headless (interactions souris simulées pas à pas, format JSON,
reader, librairie…). Toute nouvelle fonctionnalité ajoute les siens.
