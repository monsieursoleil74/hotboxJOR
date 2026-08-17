# Manuel hotboxJOR

Mode d'emploi de l'éditeur et des outils du fork. Tenu à jour à chaque
fonctionnalité ajoutée. Pour l'installation : voir `README.md`. Pour
l'historique des évolutions : voir `CHANGELOG.md`.

> 💡 **Version wiki** : ouvre **`MANUEL.html`** (double-clic → navigateur)
> pour la version mise en page — sommaire latéral, recherche, fiches de
> raccourcis. Même contenu, tenu en phase avec ce fichier.

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

Le manager se lance en **deux modes** : animateur (par défaut — la
librairie studio est une référence en lecture seule) ou **admin studio**
(`launch_manager('maya', studio_admin=True)` — la librairie officielle
est éditable). Détail : § « Deux modes de lancement ».

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
- Une shape portant l'option `lock` (données d'anciennes versions) est
  transparente à la sélection.

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

### Snap (désactivé par défaut)

**Aucun snap n'est actif par défaut.** La **grille** s'active par le
bouton aimant rouge de la barre d'outils (+ pas x/y), comme dans
l'original.

### Alignement / distribution

Boutons en fin de barre d'outils (à partir de 2 shapes sélectionnées,
3 pour la distribution) :

- Aligner : gauche, centres horizontaux, droite, haut, centres
  verticaux, bas.
- Distribuer : horizontalement / verticalement (les centres se
  répartissent régulièrement entre la première et la dernière shape).

## Copier / coller

| Raccourci | Action |
|---|---|
| **Ctrl+C / Ctrl+V** | Copier/coller des **boutons entiers**. Passe par le presse-papier système (JSON) : fonctionne **entre hotboxes**, entre éditeurs, et même entre deux sessions Maya. Les shapes collées sont sélectionnées. |
| **Ctrl+Maj+C** | **Copier le style** d'une shape (une seule sélectionnée) |
| **Ctrl+Maj+V** | **Coller le style** sur la sélection — un dialogue permet de cocher quoi coller : forme (carré/rond), taille, couleurs & bordure, style de texte, contenu du texte, image, **commandes**. Par défaut : forme + couleurs + style de texte. |

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
  nom + catégorie. La **destination est fixée par le mode** : en
  **admin**, le bouton part dans la **librairie studio courante** (la
  ligne « Library » rappelle laquelle, avec le logo TAT) ; en
  animateur, dans **sa librairie perso**. La **catégorie proposée est
  celle de l'onglet courant** de la shelf — on se met sur l'onglet
  voulu, 💾, OK : rapide. Le champ Category reste un menu déroulant
  (liste complète de la librairie visée) et éditable — taper un nouveau
  nom crée la catégorie. Toutes les shelves ouvertes se
  rafraîchissent.
- **Réutiliser** : **glisse-dépose** depuis la shelf vers le canvas
  juste au-dessus : le bouton atterrit sous le curseur, sélectionné.
  Multi-sélection possible. Ça marche aussi vers un AUTRE éditeur.
- **Sets de boutons** : avec **plusieurs boutons sélectionnés**, le
  dialogue de sauvegarde propose une case **« Save the N buttons as
  one set (keeps layout) »**. Cochée, la sélection devient **UN SEUL
  élément de librairie** qui garde la **disposition relative** des
  boutons (un kit main IK, une rangée de snaps…). Dans la shelf, le
  set se reconnaît à sa **vignette groupée** (l'infobulle précise le
  nombre de boutons) ; au
  **dépôt dans une hotbox**, les N boutons sont recréés d'un coup,
  disposés comme à l'origine et centrés sous le curseur. Un set se
  renomme, se range, se réordonne et se supprime comme un bouton
  simple (et se publie vers la librairie studio pareil) ; seule
  exception : « Replace with library button » demande un bouton
  simple, pas un set. Case décochée (défaut) : comportement
  historique, N boutons indépendants « nom, nom 2, nom 3… ».
- **Renommer un bouton** : clic droit sur un bouton de la shelf →
  **Rename…** (perso toujours ; studio en mode admin). Le bouton garde
  son apparence et sa commande, seul son nom change.
- **Supprimer** : clic droit sur un bouton de la shelf → Delete.
- **Ouvrir le dossier** (JSON brut) : clic droit sur la shelf ou un
  onglet → « Open library folder » — ouvre l'explorateur à
  l'emplacement du `.json` (perso ou studio selon l'onglet). Sur les
  onglets **studio**, l'action n'apparaît qu'en **mode admin**.
- **Organiser les catégories** — clic droit sur un **onglet** :
  - **New category… / New studio category…** — créer une catégorie
    (persistée même vide ; le libellé s'adapte selon que l'onglet est
    perso ou studio). Le bouton **＋** en haut à droite **suit le
    mode** : en admin il crée une catégorie **dans la librairie studio
    courante** (onglet logo TAT) ; en animateur une catégorie
    **perso**, façon shelf Maya. Les catégories studio vivent dans le
    `.json` de la librairie : chaque librairie (ringo.json,
    pipo.json…) a les siennes, switcher change les onglets.
  - **Rename category…** — renommer : tous les boutons de la catégorie
    (et le marqueur de catégorie vide) sont ré-étiquetés.
  - **Delete category** — supprimer (seulement si elle est vide).
  - Ces trois actions marchent aussi sur les onglets **studio**, mais
    uniquement en **mode admin** (elles écrivent dans le
    `button_library.json` du dossier studio).
- **Ranger un bouton dans une autre catégorie** — deux façons :
  - **glisser-déposer** le(s) bouton(s) **sur l'onglet** de la catégorie
    visée (le survoler ne change pas l'affichage — on peut traverser la
    barre vers le canvas sans changer de catégorie), ou **dans la
    liste** d'une catégorie, à la position voulue ;
  - clic droit → **Move to category…** (choisir une catégorie existante
    ou en taper une nouvelle).
  Perso toujours ; studio en mode admin. Le drag reste dans la même
  librairie (perso↔perso, studio↔studio).
- **Réordonner** : l'ordre affiché est celui du fichier — fini
  l'alphabétique imposé. **Glisser un bouton dans sa liste** pour le
  repositionner ; **glisser un onglet** (mode admin) pour réordonner
  les catégories. Tout est persisté dans le `.json` de la librairie.
- **Palette flottante** : **double-clic sur un onglet** → la catégorie
  s'ouvre dans une fenêtre **toujours au-dessus**, en grille
  multi-lignes (fini le scroll dans la rangée pour une catégorie de 30
  boutons). Elle reste ouverte tant qu'on ne la ferme pas, suit les
  changements de la librairie, se ferme si la catégorie disparaît
  (switch de librairie), et tout y marche comme dans la shelf :
  glisser vers une hotbox, réordonner, clic droit, mêmes droits
  admin/animateur. Plusieurs palettes peuvent rester ouvertes côte à
  côte.
- **Filtre de recherche** : le champ en haut à gauche de la
  shelf — taper un bout de nom (« snap ») remplace les onglets par un
  onglet unique de résultats, toutes catégories confondues (perso ET
  studio). Les résultats se glissent vers la hotbox comme d'habitude ;
  effacer le champ restaure les onglets.
- **Masquer/afficher** la shelf : le bouton librairie de la barre
  d'outils.

### Écritures protégées

Chaque écriture d'un fichier de données (librairies, `hotboxes.json`,
raccourcis, réglages) est **atomique** : le contenu part dans un
fichier temporaire puis remplace l'original d'un seul coup — un crash
ou une coupure en pleine écriture ne peut pas corrompre le fichier.
Aucun fichier annexe n'est créé : les sauvegardes historiques restent
à la charge de l'utilisateur (copie manuelle) ou du studio (backups
quotidiens des serveurs).

### Où c'est stocké

Arborescence complète (côté artiste, dans les prefs Maya) :

```
Documents\maya\<version>\prefs\
├─ hotboxes.json          TOUTES les hotboxes — emplacement de
│                         l'original (compatibilité, retour arrière)
└─ hotbox\                le dossier du fork (créé au 1er lancement ;
   │                      l'ancien hotboxJOR est renommé tout seul)
   ├─ button_library.json   librairie perso (boutons, sets, catégories)
   ├─ hotbox_hotkey.json    registre des raccourcis (gestionnaire ⌨)
   ├─ studio_settings.json  librairie studio mémorisée (courante + récentes)
   └─ templates\            templates utilisateur (« Save hotbox as template »)
```

Côté studio (réseau, ex. `R:\pipeline\hotbox\`) : le `.json` de la
librairie partagée (`TAT.json`…) + `studio_logo.png` (icône des
onglets). Hors mode admin, l'outil n'écrit JAMAIS dans ce dossier.

- **Perso** (modifiable) : `button_library.json` dans le **dossier du
  fork** — `Documents\maya\<version>\prefs\hotbox\` sous Maya
  (`~/.hotbox` en standalone). Le registre des raccourcis et les
  templates utilisateur y vivent aussi ; un fichier resté à la racine
  des prefs (anciennes versions) est déplacé automatiquement au premier
  lancement. `hotboxes.json`, lui, reste à la racine des prefs — c'est
  l'emplacement de l'original (compatibilité et retour arrière).
- **Studio** (partagée, catégories officielles) : un fichier commun,
  désigné par la variable d'environnement **`HOTBOX_STUDIO_LIBRARY`**
  (un `.json`, ou un dossier contenant `button_library.json`). À défaut
  de variable, l'outil regarde `C:\Users\ortzj\Desktop\JOR\hotbox`. Les
  catégories studio apparaissent en tête de la shelf avec le **logo du
  studio** (TAT) en icône ; leurs boutons se glissent-déposent
  normalement dans une hotbox.

### Deux modes de lancement (animateur / admin)

Le rôle se choisit **au lancement du manager** — chacun a son bouton de
shelf :

```python
# animateur : la librairie studio est une RÉFÉRENCE en lecture seule
import hotbox_designer
hotbox_designer.launch_manager('maya')

# lead : mode ADMIN — la librairie officielle est éditable
import hotbox_designer
hotbox_designer.launch_manager('maya', studio_admin=True)
```

- **Mode animateur** (par défaut) : il pioche les boutons officiels par
  glisser-déposer et gère librement **sa** librairie perso (catégories,
  rename, delete). Les onglets studio sont intouchables — pas de
  création/renommage de catégorie, pas d'envoi vers le studio, pas de
  destination « Studio » à la sauvegarde.
- **Choisir / changer de librairie studio (par projet)** — dans le
  coin de la shelf, pour **tout le monde** (la librairie reste en
  lecture seule hors mode admin) :
  - le **badge vert** affiche le **nom du fichier** de la librairie
    courante (ex. `ringo.json`) et **c'est lui le sélecteur** : cliquer
    dessus ouvre la liste des librairies (récentes + courante cochée)
    pour switcher de projet. Une librairie dont le fichier a disparu est
    marquée « (missing) » et non cliquable ; le sous-menu **Remove from
    list** retire une librairie obsolète de la liste (le fichier n'est
    pas touché — la courante n'est pas proposée). L'infobulle donne le
    chemin complet et le rôle (admin / lecture seule) ;
  - le bouton **page (new)** — admin uniquement — **crée** une
    librairie : dialogue « Enregistrer sous », nom du `.json` libre
    (`ringo.json`, `projetX.json`…). À la création, le **logo courant
    est copié** à côté du nouveau fichier — la nouvelle librairie garde
    l'identité TAT. (Choisir un fichier existant l'ouvre, jamais
    d'écrasement.)
  - le bouton **dossier** — pour tout le monde — **ouvre/charge** une
    librairie existante.
  **Aucune librairie par défaut** : au tout premier lancement il n'y en
  a pas (pas de badge, pas d'onglets studio) — on en crée/ouvre une
  explicitement, et seules celles qu'on a réellement chargées vivent
  dans la liste. La librairie courante est **surveillée** : quand le
  lead publie un bouton, les shelves ouvertes des animateurs se
  **rafraîchissent automatiquement**. Le choix est **mémorisé entre les
  sessions**
  (`studio_settings.json` dans `prefs/hotbox/`) et prend le pas sur
  la variable d'environnement (`HOTBOX_STUDIO_LIBRARY`, réservée au
  déploiement studio). Un `studio_logo.png` différent par projet est
  possible.
- **Changer de mode sans redémarrer Maya** : il suffit de relancer
  l'autre commande dans le Script Editor — le manager, le badge et les
  shelves déjà ouvertes basculent immédiatement.
- **Mode admin** : la shelf n'affiche QUE les onglets de la librairie
  studio courante (les onglets perso — le « General » sans logo —
  appartiennent au mode animateur). Tout s'ouvre sur les onglets
  studio — créer une
  **catégorie officielle** (*New studio category…*, écrite dans le
  `button_library.json` du dossier studio avec le logo TAT), **envoyer
  des boutons** (*Send to studio library*), renommer, ranger. Un badge
  vert **STUDIO ADMIN** s'affiche dans le bandeau du manager et à
  droite de la barre d'outils de l'éditeur — on sait toujours qu'on
  édite l'officiel. La fenêtre, elle, s'appelle toujours
  « Hotbox Designer », quel que soit le mode.

C'est un garde-fou d'interface (le fichier reste accessible sur le
réseau) ; pour un verrouillage dur, mettre aussi le dossier studio en
lecture seule au niveau des droits Windows pour les animateurs.

  **Logo du studio** : pose un `studio_logo.png` (ou `logo.png`) dans le
  dossier de la librairie studio — il devient l'icône des onglets. On
  peut aussi pointer un fichier précis via la variable
  `HOTBOX_STUDIO_LOGO`. Sans rien, un logo par défaut est utilisé.

### Publier vers la librairie studio (mode admin)

En **mode admin** : clic droit sur un ou plusieurs boutons de la
shelf → **« Send to studio library »**, ou directement 💾 avec la
destination **Studio (TAT)**. Les boutons sont copiés dans la librairie
studio (dédupliqués) et les onglets se rafraîchissent — pas de fichier
à copier à la main. En mode animateur, ces actions n'existent pas.

Alternative manuelle : copier son `button_library.json` dans le dossier
studio.

### Mettre en place la librairie studio (workflow lead)

1. Lancer le manager en **mode admin**
   (`launch_manager('maya', studio_admin=True)`).
2. Créer les catégories officielles (clic droit sur un onglet studio →
   *New studio category…*) et y ranger les boutons (💾 destination
   Studio, ou *Send to studio library* depuis la perso).
3. Chaque animateur voit automatiquement les onglets studio (logo TAT)
   + ses propres onglets perso. Pour pointer un autre chemin :
   définir `HOTBOX_STUDIO_LIBRARY` (variable d'environnement Windows,
   ou dans le `userSetup.py` commun :
   `os.environ['HOTBOX_STUDIO_LIBRARY'] = r"P:\pipeline\hotbox"`).

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

- **Aperçu d'états en haut du panneau** : le bouton sélectionné rendu
  dans ses trois états (Normal / Hover / Click), mis à jour en direct
  à chaque réglage — couleur, bordure, texte, image, forme — sans
  avoir à survoler le vrai bouton dans le viewport. Section repliable
  comme les autres.
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

Réduit à l'essentiel — la librairie : **Save selection to library…** et
**Replace with library button**. (La recherche reste sur Ctrl+H, le
recadrage sur F ; lock et magnet ont été retirés.)

**Replace with library button** : sélectionne UN bouton dans la shelf
du bas, puis clic droit sur un ou plusieurs boutons du canvas →
Replace. Le contenu (couleurs, texte, image, commandes…) vient de la
librairie, **la position et la taille sont conservées** — idéal pour
habiller un template sans replacer chaque bouton à la main.

## Templates

À la création d'une hotbox, les templates s'affichent en **grille de
vignettes cliquables** : tous visibles d'un coup (embarqués puis
persos), clic = sélectionner, **double-clic = créer directement** —
la vignette EST l'aperçu. « Duplicate existing » garde son menu, avec
un aperçu qui n'apparaît que quand cette option est cochée.

Les templates embarqués sont ceux hérités de l'original, plus le
template **TAT** (la hotbox de base du studio : grille de boutons
prête à câbler, icônes et scripts pointant sur la librairie réseau).
Combinés à « Replace with library button », ils permettent de monter
une hotbox rapidement : créer depuis le template, puis remplacer
chaque bouton par un bouton de la shelf.

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

Le raccourci assigné à chaque hotbox s'affiche **directement dans les
listes du manager** (en grisé, à droite du nom, onglets Personal et
Shared) — plus besoin d'ouvrir le gestionnaire juste pour vérifier.

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
  `designer/attributes.py` (panneau de droite), `designer/menu.py`
  (barre d'outils), `interactive.py` (Shape, manipulateur),
  `painting.py` (rendu), `geometry.py` (maths), `buttonlibrary.py`
  (librairies perso/studio, mode admin, vignettes), `colorpicker.py`
  (sélecteur de couleurs + pipette), `dialog.py` (dialogues : création,
  raccourcis…), `data.py` (JSON, templates), `widgets.py` (champs
  réutilisables), `images.py` (chemins portables), `theme.py` (thème
  sombre), `manager.py`, `reader.py`, `applications.py` (backends
  Maya/standalone… + registre des raccourcis).

## Tests

`QT_QPA_PLATFORM=offscreen python tests/test_editor.py` — une
quarantaine de tests headless (interactions souris simulées pas à pas,
format JSON, reader, librairies, raccourcis, templates…). Toute
nouvelle fonctionnalité ajoute les siens.
