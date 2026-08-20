# Changelog hotboxJOR

Historique des évolutions du fork, de la plus récente à la plus
ancienne. Chaque entrée correspond à un ou plusieurs commits sur
`main`. Détails d'usage : `MANUEL.md`.

## 2026-08 — Registre de commandes : essayé puis retiré

- **Manuel illustré** : 16 **captures d'écran** commentées (manager,
  éditeur annoté en 4 zones, panneau d'attributs, sélecteur de
  couleurs, shelf, sets, palette flottante, dialogues, raccourcis,
  hotbox en production) et 2 **schémas** (qui a le droit d'écrire où ;
  publier → surveillance → rafraîchissement). Les images sont
  **incrustées** dans `MANUEL.html` (data URI) : le wiki reste un seul
  fichier autonome. Elles sont produites hors écran par
  `docs/make_manual_shots.py`, à relancer quand l'UI change.
- **Manuel : arborescence des fichiers** — nouvelle section « Les
  fichiers sur le disque » (wiki + MANUEL.md) : l'arborescence
  `prefs\` dessinée et annotée (hotboxes.json, dossier hotbox\ et son
  contenu, templates\), le dossier studio réseau, un tableau « qui
  écrit quoi » et les trois garanties (studio jamais écrit hors admin,
  écritures atomiques, migration auto).
- **Import dwpicker retiré** (choix utilisateur — pas de pickers
  dwpicker à convertir) : le bouton Import du manager ne lit plus que
  les hotboxes `.json` ; `dwpickerimport.py`, son test et sa section
  du manuel sont supprimés. L'inspiration dwpicker côté éditeur
  (viewport, ergonomie) ne change pas.
- **Manuel en version wiki** : `MANUEL.html` — page unique autonome
  (double-clic → navigateur), sombre aux couleurs de l'outil, avec
  sommaire latéral, champ de recherche (filtre les sections par leur
  contenu), tableaux de gestes avec touches, encadrés. Même contenu
  que `MANUEL.md`, tenu en phase.
- **Sets de boutons** : plusieurs boutons sélectionnés peuvent être
  sauvegardés comme **un seul élément de librairie** (case « Save the
  N buttons as one set » du dialogue 💾). Le set garde la
  **disposition relative** des boutons, s'affiche avec une **vignette
  groupée** dans la shelf (le nombre de boutons est dans
  l'infobulle), et **se dépose d'un coup** dans
  une hotbox (groupe centré sous le curseur). Rangement, renommage,
  réordonnancement, publication studio : comme un bouton simple.
- **Panneau Image allégé** : champs Width/Height retirés (la taille
  se règle à la molette en mode « Place Image », plus lisible qu'une
  valeur numérique) ; le bouton s'appelle « Place Image » et passe en
  vert tant que le mode placement est actif.
- **Infobulle du badge sans chemin pour les animateurs** : elle
  affiche juste « Studio library (read-only) » — le chemin complet
  reste visible en mode admin (et via « Open library folder »).
- **Dossier de données renommé `prefs/hotbox/`** (au lieu de
  `prefs/hotboxJOR/` ; `~/.hotbox` en standalone) : le suffixe JOR ne
  servait à rien. L'ancien dossier est **renommé automatiquement** au
  premier lancement — librairie perso, raccourcis, templates et
  réglages suivent sans rien faire.
- **Play retiré du bouton switch du manager** : le bouton affiche la
  commande à coller (bouton de shelf Maya), le petit play de test ne
  servait à rien.
- **Filtre de la shelf façon Outliner** (retour utilisateur) : simple
  champ « Search... », onglet de résultats sobre sans compteur.
- **Drag & drop : plus de bascule d'onglet au survol** (retour
  utilisateur) — glisser un bouton vers le canvas traversait la barre
  d'onglets et changeait de catégorie au passage. Le dépôt SUR un
  onglet range toujours le bouton dans cette catégorie.
- **Bandeau STUDIO ADMIN pleine largeur** dans le manager : barre
  verte traversante, texte centré plus gros — impossible à rater. En
  mode animateur, le bandeau disparaît complètement (plus de bande
  vide inutile).
- **Correctif création de hotbox** : en basculant entre « From
  template » et « Empty hotbox », un grand vide apparaissait (la
  fenêtre gardait sa hauteur quand l'aperçu Duplicate se cachait). Le
  dialogue colle désormais toujours à son contenu.

- **Registre de commandes nommées essayé puis RETIRÉ** (choix
  utilisateur) : les boutons appelaient `hotbox_designer.run('Nom')`
  avec le code centralisé à côté de la librairie studio. Trop de
  friction à l'usage — retour au code directement dans les boutons,
  comme avant (Ctrl+H reste l'outil pour les changements en masse).
- **Conservé de cette passe : la librairie studio mémorisée est
  restaurée dès le lancement du manager** — le badge et le mode admin
  la voient sans devoir ouvrir un éditeur d'abord.

## 2026-08 — Grille de templates, vignettes du manager, pastilles sobres

- **Zones de travail des templates d'origine recadrées** sur leurs
  boutons (marge 30 px, même logique que « fit zone to shapes ») :
  leurs vignettes ne montrent plus des boutons minuscules perdus dans
  le vide. La position des boutons par rapport au centre (le curseur)
  est conservée — comportement identique à l'ouverture.

- **Grille de templates à la création** : fini le menu déroulant
  aveugle — chaque template en vignette + nom, tous visibles d'un
  coup, clic = sélectionner, double-clic = créer directement.
- **Vignettes de la liste du manager : essayées puis retirées** (choix
  utilisateur) — le panneau Preview de droite fait déjà le travail, la
  liste reste en texte simple.
- **Filtre de recherche dans la shelf** : champ en haut à gauche —
  taper un bout de nom montre tous les boutons correspondants, toutes
  catégories confondues (perso + studio), dans un onglet unique de
  résultats glissables vers la hotbox. Effacer restaure les onglets.
- **Création de hotbox épurée** (retour utilisateur) : la grande
  preview redondante disparaît en mode template (la vignette de la
  grille EST l'aperçu — vignettes agrandies 128×78, grille pleine
  hauteur) ; elle ne s'affiche plus que pour « Duplicate existing ».
- **Raccourcis visibles dans les listes du manager** : la touche
  assignée s'affiche en grisé à droite du nom de chaque hotbox
  (Personal et Shared), mise à jour dès qu'on assigne/efface — plus
  besoin d'ouvrir le gestionnaire juste pour vérifier.
- **Correctif : les boutons OK/Cancel du sélecteur de couleurs
  prenaient la couleur choisie** (le style de la pastille ruisselait
  sur le dialogue enfant). Style ciblé sur la pastille seule ; et plus
  de texte teinté selon la couleur — sobre, le code hexa vit dans
  l'infobulle (pastille du texte alignée sur celles de l'apparence).

## 2026-08 — Aperçu d'états en direct + template TAT mis à jour

- **Aperçu d'états dans le panneau d'attributs** (section PREVIEW en
  haut, repliable) : le bouton sélectionné rendu dans ses trois états
  Normal / Hover / Click, rafraîchi en direct à chaque réglage —
  on voit ce qu'on fait quand on modifie couleurs, bordures, texte,
  image ou forme.
- **Template TAT mis à jour** (nouvelle version fournie par
  l'utilisateur).

## 2026-08 — Polish UI (panneau d'attributs, dialogues) + fix badge anim

- **Correctif : le badge STUDIO ADMIN s'affichait dans l'éditeur en
  mode animateur** (sur certaines versions de Qt, masquer l'action
  d'un widget de toolbar ne masque pas le widget). Le badge est
  désormais masqué des deux côtés (action + widget) et **suit la
  bascule de mode en cours de session** dans les éditeurs déjà
  ouverts.
- **Panneau d'attributs de l'éditeur retravaillé** : en-têtes de
  section repliables avec chevron ▾/▸, capitales espacées et tiret
  d'accent vert (grisé quand la section est repliée), sous-titres
  soulignés d'un filet, marges et espacements uniformisés — la colonne
  respire au lieu d'être tassée.
- **Dialogues au thème sombre garanti** (création de hotbox,
  raccourcis, commande) même hors parent themé ; création de hotbox :
  aperçu plus grand (240×150, coins arrondis), boutons OK par défaut ;
  gestionnaire de raccourcis : lignes plus hautes, alternance de
  fonds, sans grille.

## 2026-08 — Badge admin dans l'éditeur, aperçu rogné, ménage templates

- **Badge « STUDIO ADMIN »** à droite de la barre d'outils de
  l'éditeur de hotbox : on sait d'un coup d'œil dans quel mode on est.
  Invisible en mode animateur.
- **Le même badge dans le bandeau du manager**, à la place du texte
  « HOTBOX DESIGNER » (redondant : le nom du tool vit dans le titre de
  la fenêtre). La fenêtre s'appelle désormais toujours
  « Hotbox Designer », quel que soit le mode — plus de titre
  « STUDIO ADMIN ».
- **Aperçu de template corrigé** : les formes qui débordent de la zone
  de la hotbox sont rognées comme dans la vraie hotbox — une barre de
  fond plus large que la zone n'envahit plus la vignette.
- **Templates maison retirés** (choix utilisateur) : Pie_8_Directions,
  Mini_Shelf_4x3, Barre_6_Boutons, Manette, Nid_Abeille, Colonnes_TAT,
  Grille_6x4. Restent les templates d'origine et les templates
  utilisateur (« Save hotbox as template »).
- **Template TAT embarqué** : la hotbox de base du studio (29 boutons,
  fournie par l'utilisateur) livrée comme template « From template ».
- **Commandes show/hide retirées du manager** : seule `switch` reste
  exposée (c'est elle qu'on colle sur un bouton de shelf — un clic
  ouvre, un re-clic ferme). show/hide sont câblées automatiquement par
  le gestionnaire de raccourcis, plus besoin de les copier à la main.

## 2026-08 — Robustesse avant déploiement (atomique, refresh auto, CI)

- **Écriture atomique** de tous les json (librairies, hotboxes.json,
  registre des raccourcis, settings) : fichier temporaire + `os.replace`
  — une coupure réseau ou un crash en pleine écriture ne peut plus
  corrompre le fichier (`data.atomic_write_json`).
- **Pas de backups automatiques** (essayés puis retirés, choix
  utilisateur) : l'écriture atomique suffit contre la corruption, et
  l'historique reste à la charge de l'utilisateur (copies manuelles)
  ou des backups quotidiens des serveurs du studio. Aucun fichier
  annexe créé à côté des json.
- **Refresh automatique de la librairie studio** : un
  `QFileSystemWatcher` (débouncé, re-armé après chaque remplacement
  atomique) suit le json courant — le lead publie, les shelves des
  animateurs se mettent à jour toutes seules.
- **CI GitHub Actions** (`.github/workflows/tests.yml`) : pyflakes
  (vendor exclu) + suite de tests headless à chaque push/PR.

## 2026-08 — Palette flottante par catégorie (double-clic sur l'onglet)

- **Double-clic sur un onglet** de la shelf → la catégorie s'ouvre dans
  une fenêtre flottante **toujours au-dessus** (`CategoryPalette`),
  grille multi-lignes scrollable — pratique pour piocher dans une
  catégorie de 30 boutons sans scroller la rangée.
- La palette reste ouverte tant qu'on ne la ferme pas, est réutilisée
  au double-clic suivant, se synchronise à chaque refresh de la
  librairie et se ferme si sa catégorie disparaît (switch de
  librairie).
- Drag vers les hotboxes, réordonnancement, clic droit et gating
  admin/animateur identiques à la shelf (listes factorisées :
  `_configure_list` / `_fill_list`).

## 2026-08 — Organisation de la shelf au drag & drop

- **Glisser un bouton sur un onglet** = le ranger dans cette catégorie
  (l'onglet survolé se sélectionne pendant le drag) ; **glisser dans la
  liste** d'une catégorie = le déposer à une position précise (et donc
  réordonner au sein d'une catégorie).
- **Glisser les onglets** (mode admin) réordonne les catégories,
  persisté dans le json.
- **L'ordre affiché = l'ordre du fichier** (onglets ET boutons) — fini
  l'alphabétique imposé ; le lead met les importants en premier.
- Nouvelles fonctions de structure (`parse_library_structure`,
  `save_library_structure`, `move_entries_to_category`,
  `set_category_order`) : le json est réécrit sous forme canonique
  (marqueur de catégorie puis ses boutons, dans l'ordre).
- Gating conservé : perso toujours, studio en admin ; un drag ne change
  jamais de librairie (perso↔perso, studio↔studio).

## 2026-08 — Créer et ouvrir une librairie : deux boutons distincts

- Le bouton dossier faisait les deux — flou. Désormais : bouton
  **page (new)** = créer une librairie (admin uniquement, nom du .json
  libre, jamais d'écrasement) ; bouton **dossier** = ouvrir/charger une
  librairie existante (tout le monde).

## 2026-08 — Badge et menus sans l'extension .json

- Le badge et la liste des librairies affichent « ringo », plus
  « ringo.json » (le chemin complet reste dans l'infobulle).

## 2026-08 — Fix : librairie neuve = shelf vide (tout semblait disparu)

- Créer/ouvrir une librairie **sans aucune catégorie** laissait la shelf
  à zéro onglet — et Qt cache alors aussi le coin (badge / dossier / ＋),
  donnant l'impression d'avoir tout perdu. En admin, une librairie vide
  affiche désormais un onglet **General** vide : la shelf reste vivante,
  et le premier 💾 y range naturellement les boutons.

## 2026-08 — Sauvegarde : catégorie proposée = l'onglet courant

- Le dialogue 💾 pré-remplit la catégorie avec **l'onglet où l'on est**
  (onglet studio en admin, onglet perso en animateur) au lieu de
  toujours « General » — on se place sur l'onglet, 💾, OK.

## 2026-08 — Clic droit de l'éditeur réduit à l'essentiel

- Le menu contextuel ne garde que **Save selection to library…** et
  **Replace with library button**. Lock/Unlock et Magnet snapping sont
  **retirés** (UI et méthodes — l'option `lock` d'anciennes données
  reste respectée par la sélection) ; Search and replace (Ctrl+H) et
  Frame view (F) restent accessibles au clavier.

## 2026-08 — Sauvegarde : destination fixée par le mode

- Plus de choix Perso/Studio dans le dialogue 💾 : en **admin** on
  enregistre dans la **librairie studio courante** (la ligne Library
  affiche son nom + logo TAT), en animateur dans sa librairie perso.

## 2026-08 — Dialogue de sauvegarde élargi

- Largeur minimale 340 px et champs étirés : les noms de catégories se
  lisent en entier (« ANIMATION » n'est plus tronqué en « ATION ») et le
  menu déroulant des catégories est repérable.

## 2026-08 — Mode admin : plus d'onglets perso dans la shelf

- En mode admin, la shelf n'affiche que les onglets de la **librairie
  studio courante** — le « General » perso (sans logo) n'apparaît plus.
  Le perso reste entier en mode animateur.

## 2026-08 — Zéro librairie par défaut + clic droit épuré pour l'animateur

- **Plus de librairie par défaut** (le chemin de dev codé en dur est
  retiré) : au premier lancement il n'y a AUCUNE librairie studio — on
  en crée/ouvre une explicitement, et seules les librairies réellement
  chargées apparaissent dans la liste. Plus de résidus. La variable
  `HOTBOX_STUDIO_LIBRARY` reste supportée (déploiement studio).
- En mode admin **sans librairie chargée**, le ＋ crée une catégorie
  perso (au lieu d'un avertissement).
- **« Open library folder » masqué sur les onglets studio hors mode
  admin** — le fichier du lead ne regarde pas l'animateur (l'action
  reste sur les onglets perso).

## 2026-08 — Ménage dans la liste des librairies

- Sous-menu **Remove from list** dans le menu du badge : retirer une
  librairie obsolète des récents (le fichier n'est pas touché ; la
  courante n'est pas proposée, et une librairie oubliée ne réapparaît
  pas au switch suivant).
- Les librairies dont le fichier a **disparu** sont marquées
  « (missing) » et non cliquables.

## 2026-08 — Le badge json devient le sélecteur + fix des récents

- Le bouton TAT disparaît : le **badge vert « nom.json » est lui-même le
  bouton de switch** — on voit son environnement, on clique dessus pour
  changer de librairie. Vert pour tout le monde (repère de librairie,
  pas de rôle ; le rôle reste en infobulle).
- **Fix** : la librairie QUITTÉE entre aussi dans les récents — la
  toute première (défaut/variable d'env, jamais choisie via l'UI)
  disparaissait de la liste après un premier switch.

## 2026-08 — Le bouton ＋ suit le mode (catégorie studio en admin)

- En mode **admin**, le ＋ de la shelf crée la catégorie **dans la
  librairie studio courante** (onglet logo TAT) — avant il créait
  toujours une catégorie perso, d'où des onglets sans logo. En mode
  animateur, il crée une catégorie **perso** (façon shelf Maya).
  L'infobulle du ＋ affiche la destination.

## 2026-08 — Sélecteur de librairie refondu (retours d'usage)

- **Badge = nom du json courant** (`ringo.json`…) à la place de
  « STUDIO ADMIN » : vert en mode admin, gris en lecture seule,
  chemin complet en infobulle.
- **Menu du bouton TAT simplifié** : uniquement la liste des librairies
  (récentes + courante cochée). « Use default location » et l'en-tête
  supprimés.
- **Create/open = bouton dossier à part entière** : l'admin crée via un
  « Enregistrer sous » (nom du `.json` **libre**) ou ouvre ; l'animateur
  ouvre seulement.
- **Le logo n'est plus perdu** : à la création d'une librairie, le
  `studio_logo.png` courant est copié à côté du nouveau fichier.

## 2026-08 — Le sélecteur de librairie studio ouvert aux animateurs

- Le bouton **TAT** de la shelf est désormais visible en mode
  **animateur** aussi : chacun choisit sur quelle librairie studio il
  est (par projet), via **Open library…** et les récents. La création
  d'une librairie reste réservée à l'admin (un animateur qui ouvre un
  dossier sans `button_library.json` est prévenu, rien n'est créé), et
  la lecture seule s'applique toujours hors mode admin.

## 2026-08 — Bascule de mode sans redémarrer Maya

- Relancer `launch_manager('maya')` ou
  `launch_manager('maya', studio_admin=True)` dans la même session
  bascule le mode immédiatement : titre du manager, badge et menus des
  shelves déjà ouvertes suivent (`refresh_shelves()` au lancement, badge
  resynchronisé dans `LibraryShelf.refresh`).

## 2026-08 — Sélecteur de librairie studio (par projet)

- Bouton **TAT** à côté du « ＋ » de la shelf (mode admin) : menu avec
  la librairie courante, **Create / open library…** (crée le
  `button_library.json` dans le dossier choisi s'il manque, puis
  bascule), la liste des **librairies récentes** pour switcher par
  projet, et **Use default location** (retour à la variable
  d'environnement).
- Choix **persisté** dans `studio_settings.json` (dossier du fork),
  prioritaire sur `HOTBOX_STUDIO_LIBRARY` ; rechargé au démarrage.
- Le logo des onglets est relu à chaque refresh : un
  `studio_logo.png` différent par librairie/projet est possible.

## 2026-08 — Retrait du mode test (bouton play)

- Le bouton ▶ « Test the hotbox » de la barre d'outils est retiré, jugé
  inutile à l'usage : signal, action, méthode `test_hotbox`, classe
  `_TestReader` et test associé supprimés.

## 2026-08 — Données rangées dans prefs/hotboxJOR + panneau d'attributs élargi

- **Rangement** : la librairie de boutons perso, le registre des
  raccourcis et les templates utilisateur vivent désormais dans
  `prefs\hotboxJOR\` au lieu d'encombrer la racine des prefs Maya.
  **Migration automatique** au premier lancement des fichiers restés à
  la racine (`button_library.json`, `hotbox_hotkey.json`, `templates/`
  — .json déplacés un à un). `hotboxes.json` reste à la racine :
  emplacement de l'original, compatibilité et rollback préservés.
  (`AbstractApplication.get_fork_folder`, surchargé par Maya ;
  Standalone garde ~/.hotboxjor tel quel.)
- **Panneau d'attributs élargi** (290 → 330 px, colonne de libellés
  80 → 95) : « Has command », « Close Hotbox », « Fit to shape » ne
  sont plus tronqués, les champs respirent.

## 2026-08 — Fix catégories du dialogue de sauvegarde + sélection visible dans la shelf

- **Fix** : en basculant la destination sur « Studio (TAT) » dans le
  dialogue 💾, le champ Category gardait le « General » de la liste
  perso au lieu de proposer les catégories studio — il affiche
  désormais la première catégorie de la liste choisie (un nom commun
  aux deux listes est conservé).
- **Sélection/hover de la shelf enfin visibles** : cadre accent arrondi
  + fond teinté sur TOUTE la vignette (icône comprise), survol distinct,
  icône non teintée (palette Highlight alignée sur l'accent, pixmap
  Selected explicite) — fini le simple surlignage du texte.

## 2026-07 — Doc : tester le fork avant déploiement

- README : procédure d'essai **par-dessus** l'installation studio, dans
  la session Maya seulement — sauvegarde des données, purge des modules
  de l'original déjà chargés, `sys.path.insert` du fork, lancement
  admin ; redémarrer Maya = retour à l'original, rien n'est modifié.

## 2026-07 — Doc : migration depuis l'original déjà déployé

- README : nouvelle section « Migration depuis le hotbox_designer
  original » — remplacement de dossier (même nom de package, même API),
  hotboxes et hotkeys existants conservés, nuance sur le registre des
  raccourcis (les anciens hotkeys s'affichent « — » jusqu'à
  réassignation), prérequis Maya 2022+.

## 2026-07 — Deux modes de lancement : animateur / admin studio

- Le rôle se choisit **au lancement** :
  `launch_manager('maya')` = animateur (librairie studio en référence,
  lecture seule, librairie perso libre) ;
  `launch_manager('maya', studio_admin=True)` = lead (librairie
  officielle éditable : catégories, envoi/renommage/rangement).
- En mode admin : badge « ★ STUDIO ADMIN » dans la shelf et titre de
  fenêtre du manager marqué — on sait qu'on édite l'officiel.
- En mode animateur : plus de « New studio category », « Send to studio
  library », Rename/Move sur les onglets studio, ni de destination
  « Studio » à la sauvegarde.
- `set_studio_admin()` / `is_studio_admin()` (drapeau de session) +
  garde `_can_edit()` sur les menus de la shelf.

## 2026-07 — Grand nettoyage avant diffusion au studio

- **Code mort retiré** : `TouchEdit` (remplacé par `HotkeyEdit`),
  `move_up/move_down_array_elements` (boutons d'ordre pas-à-pas
  supprimés plus tôt).
- **Tests** : imports et variables inutiles purgés (pyflakes propre sur
  tout le dépôt hors vendor).
- **`TODO.upstream` supprimé** (liste de tâches du projet amont,
  obsolète pour ce fork).
- **README remis à niveau** : gestionnaire de raccourcis (au lieu de
  l'ancien « Set hotkey »), récap des nouveautés récentes, nouvelle
  section « Librairie studio (équipe) » avec la config
  `HOTBOX_STUDIO_LIBRARY` pour les postes des animateurs.
- MANUEL : titre « disposition radiale » corrigé (fonction retirée).

## 2026-07 — Placer l'image : flèches du clavier

- En mode « Place in button », les **flèches** décalent l'image dans le
  bouton d'1 unité (**Maj** = 10) — réglage fin en complément du drag et
  de la molette. La shape, elle, ne bouge pas.

## 2026-07 — Quatre templates de plus (choisis sur planche de propositions)

- **Manette** : croix directionnelle + A/B/X/Y colorés + gâchettes
  L1/R1 + sel/start — la mémoire musculaire du pad.
- **Nid_Abeille** : 14 boutons ronds en quinconce serré, densité max.
- **Colonnes_TAT** : 4 colonnes titrées SHELF / ANIM / EXTRA / ANIMBOT,
  calquées sur les catégories de la librairie studio.
- **Grille_6x4** : 24 boutons titrés, pour hotbox bien remplie.
- Sélection faite sur deux planches d'aperçus (15 propositions).

## 2026-07 — Trois nouveaux templates embarqués

- **Pie_8_Directions** : marking menu complet à 8 directions (N/NE/E/…)
  autour d'un centre.
- **Mini_Shelf_4x3** : panneau titré avec une grille de 12 boutons,
  façon mini-shelf.
- **Barre_6_Boutons** : bande compacte de 6 boutons carrés.
- Style cohérent avec le thème (gris sombre, survol vert accent, coins
  arrondis), générés depuis les défauts `SQUARE_BUTTON`/`TEXT`/
  `BACKGROUND` (toutes les clés à jour).

## 2026-07 — Replace depuis la librairie, pipette couleur, templates utilisateur

- **Replace with library button** (clic droit dans l'éditeur) : le
  contenu du/des bouton(s) sélectionné(s) est remplacé par le bouton
  choisi dans la shelf, **position et taille conservées** — habiller un
  template sans replacer chaque bouton.
- **Pipette écran ⌖** dans le sélecteur de couleurs (le « Pick Screen
  Color » perdu avec l'abandon du dialogue natif) : aperçu en direct
  sous le curseur, clic = prélever, Échap = annuler.
- **Templates utilisateur** : bouton « Save hotbox as template » dans le
  manager → copie dans `templates/` du dossier de données, listée dans
  « From template » après les templates embarqués
  (`data.save_hotbox_as_template` / `load_templates(user_folder)`).
- **Aperçu dans le dialogue de création** : vignette du template ou de
  la hotbox à dupliquer (réutilise `hotbox_thumbnail`).

## 2026-07 — Fix : hotbox cadrée dès l'ouverture de l'éditeur

- La vue n'était cadrée qu'au **premier** `resizeEvent`, qui arrive
  pendant la mise en place du layout (taille provisoire) → hotbox
  décentrée au démarrage, il fallait presser F. Désormais chaque resize
  recadre la hotbox **tant que l'utilisateur n'a pas navigué lui-même**
  (molette, +/−, pan, F) ; ensuite la vue lui appartient et n'est plus
  touchée.

## 2026-07 — Manipulation allégée dans l'éditeur

- **Tout le contour de la sélection est saisissable** pour
  redimensionner (~8 px écran, coins prioritaires) — plus besoin de
  viser les 8 petites poignées (`Manipulator.get_direction`).
- **Curseurs contextuels** : flèches ↔ ↕ ⤡ ⤢ sur bords/coins, croix de
  déplacement dans la sélection, main pendant le pan.
- **Maj pendant un déplacement** = contrainte à l'axe dominant
  (horizontal/vertical, façon Photoshop) — `Transform.move(constrain=)`.
- **Espace + glisser = pan** (en plus du clic molette), curseur main.
- **Zoom clavier + / −** autour du centre de la vue.

## 2026-07 — Renommer un bouton de shelf + sauvegarder direct dans le studio

- **Rename…** sur un bouton de la shelf (clic droit) : on peut renommer
  un bouton déjà rangé, perso comme studio (`rename_entry_in`).
- **Save selection to library** propose une **destination** : Perso ou
  **Studio (TAT)**. On range donc un bouton directement dans une shelf
  studio à la sauvegarde, sans passer par General + « Move to ». La liste
  de catégories s'adapte à la destination choisie (`SaveToLibraryDialog`
  + `LibraryShelf.save_entries` / `studio_categories`).

## 2026-07 — Fix : les catégories studio vides s'affichent enfin

- Une catégorie studio créée mais pas encore remplie (« New studio
  category… ») restait **invisible** : les onglets studio n'étaient
  construits qu'à partir des boutons, pas des marqueurs de catégorie
  vide. `refresh()` charge désormais aussi `load_extra_categories()` du
  fichier studio — comme il le faisait déjà côté perso. On voit donc
  toutes ses catégories studio, remplies ou non.

## 2026-07 — Librairie studio librement modifiable (retrait du mode mainteneur)

- Retrait de la couche « mainteneur studio » (variable
  `HOTBOX_STUDIO_ADMIN`, garde `_can_edit`, badge « STUDIO ADMIN »)
  ajoutée juste avant : trop tôt. Pour l'instant la librairie studio est
  **pleinement modifiable** par l'utilisateur — créer des catégories
  officielles (écrites dans le `button_library.json` du dossier studio,
  logo TAT), envoyer/renommer/ranger des boutons. La restriction d'accès
  pour les animateurs sera reprise plus tard.

## 2026-07 — Catégories de librairie : créer / renommer / déplacer (perso ET studio)

- On peut désormais **organiser les catégories** de la librairie, y
  compris côté **studio** (le dossier `HOTBOX_STUDIO_LIBRARY`) :
  - clic droit sur un onglet → **New category… / New studio category…**,
    **Rename category…** (ré-étiquette boutons + marqueur), **Delete
    category** (si vide) ;
  - clic droit sur un ou plusieurs boutons → **Move to category…**
    (perso comme studio).
- Le contenu des boutons studio reste protégé ; seules les catégories et
  le rangement sont modifiables (réservé au mainteneur, voir ci-dessus).
- Fonctions par chemin dans `buttonlibrary.py` (`categories_in`,
  `add_category_to`, `rename_category_in`, `delete_empty_category_in`,
  `set_entries_category_in`), partagées par les deux librairies ;
  `add_category`/`delete_category` de la shelf s'appuient dessus.

## 2026-07 — Ordre de superposition simplifié

- Les deux boutons pas-à-pas « Move down » / « Move up » (hérités de
  dwpicker) sont retirés : ils ne servaient à rien. Ne restent que
  « tout au fond » (onbottom) et « tout devant » (ontop). Signaux,
  actions, méthodes et import inutilisés nettoyés.

## 2026-07 — Sous-menu fluide + refonte des raccourcis

- **Sous-menu fluide** : un bouton peut ouvrir une autre hotbox sans
  écrire de code. Le panneau Action gagne un menu « Open sub-hotbox »
  qui liste les hotboxes marquées « is submenu » ; en choisir une génère
  automatiquement la commande `show('nom')` sur le clic gauche du/des
  bouton(s) sélectionné(s).
- **Gestionnaire de raccourcis** : le bouton touche du manager ouvre
  désormais un tableau listant **toutes** les hotboxes avec leur touche,
  pour la **voir**, la **(ré)assigner** ou l'**effacer** — avant on ne
  pouvait qu'assigner, sans jamais revoir ni retirer.
- **Capture directe du raccourci** : le sélecteur de touche remplace les
  trois cases Ctrl/Alt/Shift + champ Touch par une seule zone
  (`HotkeyEdit`) où l'on tape la combinaison — elle s'affiche « Shift+q ».
  Les modificateurs sont lus sur la frappe, Échap efface.
- **Registre commun** `hotbox_hotkey.json` (dossier de données du DCC) :
  `AbstractApplication.record_hotkey / load_hotkeys / remove_hotkey`.
  Maya note désormais ses raccourcis dans ce registre et
  `Maya.remove_hotkey` débranche vraiment la touche (press + release).

## 2026-07 — Retrait radiale + menu clic droit allégé

- **Disposition radiale retirée** (align.arrange_radial, bouton de barre
  d'outils, action associée).
- **Menu clic droit simplifié** : il ne duplique plus la barre d'outils
  (fini copy/paste/style/delete/ordre/library/fit zone). Ne reste que
  ce qui n'est pas ailleurs — sauvegarde en librairie, verrouillage,
  magnet, recherche/remplacement, recadrage.

## 2026-07 — Sélecteur de couleurs moderne (façon Miro)

- Le `QColorDialog` natif (vieillot) est remplacé par un picker maison
  `colorpicker.py` dans le thème sombre : carré saturation/valeur,
  barre de teinte, champ hexa, aperçu et rangée de couleurs
  prédéfinies. Branché sur les pastilles `ColorButton`.

## 2026-07 — Vignettes de librairie propres

- Les boutons **avec image** affichent dans la shelf l'**image seule**,
  ajustée sur fond transparent (fini le rectangle sombre derrière) ;
  les boutons sans image gardent leur pastille colorée. Fond de
  vignette transparent dans tous les cas.

## 2026-07 — Export studio + retrait du double-clic

- **Publier vers la librairie studio** : clic droit sur des boutons de
  la shelf → « Send to studio library » (dédup, crée le fichier/dossier
  studio au besoin) — plus besoin de copier le JSON à la main.
- **Double-clic pour éditer le texte retiré** (à la demande) : le texte
  se modifie via le panneau d'attributs (champ Content).

## 2026-07 — Librairie studio partagée

- Deuxième niveau de librairie **studio, en lecture seule**, désigné
  par la variable d'environnement `HOTBOX_STUDIO_LIBRARY` (fichier .json
  ou dossier ; défaut `C:\Users\ortzj\Desktop\JOR\hotbox`). Ses
  catégories apparaissent en tête de la shelf, non modifiables ; les
  boutons se glissent-déposent normalement. La perso reste locale et
  modifiable.
- **Logo du studio** sur les onglets partagés (au lieu de l'étoile) :
  `studio_logo.png`/`logo.png` dans le dossier studio, ou variable
  `HOTBOX_STUDIO_LOGO`, sinon un logo par défaut embarqué. La
  distinction studio/perso passe désormais par le flag interne, pas par
  le nom de l'onglet.

## 2026-07 — Placement libre de l'image dans un bouton

- Nouvelles options `image.offsetx/offsety` (défaut 0) : l'image n'est
  plus forcée au centre quand « Fit to shape » est off.
- **Mode « placer l'image »** dans l'éditeur (bouton du panneau Image) :
  glisser l'image dans le bouton pour la positionner, molette pour la
  redimensionner, contour vert en pointillés, Échap pour finir ;
  bouton **Center** pour recentrer. Annulable.

## 2026-07 — Épaisseur de bordure au curseur

- L'épaisseur de bordure passe des trois champs N/H/C à **un seul
  curseur** (widget `ValueSlider`, même ergonomie que l'opacité, en px)
  qui pilote les trois états proportionnellement (survol ×1.25,
  clic ×2). Émission au relâchement (undo propre).

## 2026-07 — Direction artistique « pro DCC »

- Palette repensée en **gris neutres désaturés** (façon Maya/Nuke),
  formes plates, contrastes adoucis.
- **Icônes de barre d'outils en monochrome** (fini le bleu à
  l'intérieur — c'était le principal « tell » générique).
- **Accent unique désaturé** (bleu-acier `#5a86a8`) réservé aux états
  actifs : sélection, onglet courant, focus, rectangle de sélection.
  Une seule constante `ACCENT` dans `theme.py` pour le changer.
- Header du manager sobre (capitales espacées, gris) ; titres de
  section neutres.

## 2026-07 — Nettoyage + performances

- **Sauvegarde auto retirée** : plus de dossier `backups/` — on ne
  touche au dossier Maya que pour lire/écrire `hotboxes.json`, rien de
  plus.
- **Gros nettoyage de code** : suppression du code mort (fenêtre
  librairie flottante remplacée par la shelf, ancien widget `ColorEdit`
  et `colorwheel.py` remplacés par les pastilles natives), imports
  inutilisés purgés, `__init__` clarifié (API publique explicite).
  pyflakes clean.
- **Cache des vignettes** : les rendus de boutons ne sont plus
  recalculés à chaque rafraîchissement de la shelf (clé sur
  l'apparence) — plus fluide sur les grosses librairies.
- **Anti-doublon** : un bouton identique (nom + catégorie + options)
  n'est plus stocké deux fois dans la librairie.

## 2026-07 — Aperçu + coins arrondis

- **Vignette d'aperçu** dans le manager : mini-rendu de la hotbox
  sélectionnée en haut du panneau de droite.
- **Coins arrondis** (forme `rounded_rect` + rayon, façon dwpicker) :
  nouvelle forme au sélecteur, compatible avec l'import dwpicker,
  rayons par défaut ajoutés aux anciennes hotboxes.

## 2026-07 — Édition rapide + icônes redessinées

- **Double-clic sur un bouton = éditer son texte** à même le canvas
  (champ posé sur le bouton, à l'échelle du zoom ; Entrée valide, Échap
  annule).
- **Commandes auto-sauvées** : le champ de commande enregistre à la
  perte de focus (CommandTextEdit) — le bouton « save command » et le
  risque de commande perdue disparaissent.
- **Icônes de barre d'outils redessinées** : jeu SVG cohérent, trait
  clair + accent bleu (28 icônes), pensé pour le thème sombre.

## 2026-07 — Mode test + disposition radiale

- **Mode test** (bouton play de la barre d'outils) : ouvre la hotbox
  comme en production (reader) à l'endroit du curseur, pour tester
  survol / clics / états / sous-menus sans quitter l'éditeur ; se ferme
  avec l'éditeur.
- **Disposition radiale** (align.arrange_radial + bouton cible) :
  répartit les boutons sélectionnés en cercle autour du centre de la
  hotbox, façon marking menu (rayon adaptatif, premier en haut, sens
  horaire), annulable.

## 2026-07 — UI du manager rafraîchie

- En-tête « Hotbox Designer JOR », onglets Personal/Shared soulignés
  (accent bleu) au lieu des cartouches, liste de hotboxes aux lignes
  plus hautes et aérées avec sélection bleue pleine largeur.
- Titres de section (Options, Commands, Shape, Background…) en petites
  capitales bleutées ; bandeaux de repli (togglers) plus discrets.

## 2026-07 — Fix cases à cocher + dialogue de création

- **Bug « border visible »** : le signal `clicked` se résout sans
  argument selon le binding Qt — l'émission directe échouait en
  silence et TOUTES les cases du panneau étaient muettes (border
  visible, gras, italique). Corrigé, avec sortie propre du tri-état.
- **Dialogue « Create new hotbox » refondu** : champ de nom pré-rempli,
  menus grisés tant que leur option n'est pas cochée (on voit enfin ce
  qu'on crée), et le nom est validé contre les hotboxes EXISTANTES —
  l'ancien code validait la branche template contre la liste des
  templates, garantissant des noms en double (source des comportements
  étranges).

## 2026-07 — Retours du troisième test studio

- **Shelf plus grande** : vignettes 72×36 (au lieu de 48×24).
- **Création de catégories** : bouton ＋ sur la shelf (persistées même
  vides via un marqueur dans le fichier) ; suppression d'une catégorie
  vide au clic droit sur son onglet.
- **Panneau couleurs aéré** : les 3 états sur une seule ligne de
  pastilles sous une légende Normal/Hover/Click, hexa en infobulle,
  espacement des lignes augmenté.

## 2026-07 — Import dwpicker

- Le bouton Import du manager reconnaît et convertit les fichiers
  `.json` de dwpicker : targets de sélection → `cmds.select(...)` au
  clic gauche, commandes (ancien et nouveau format) réparties sur les
  clics, fonds verrouillés, zone auto-calculée autour des shapes.

## 2026-07 — Librairie en shelf intégrée

- La librairie n'est plus une fenêtre flottante : c'est une **shelf en
  bas de l'éditeur, façon shelf Maya** — un onglet par catégorie,
  vignettes réelles, drag & drop vers le canvas au-dessus (ou un autre
  éditeur), clic droit = supprimer, bouton barre d'outils =
  masquer/afficher. Sauvegarde : l'onglet courant est proposé comme
  catégorie ; toutes les shelves ouvertes se resynchronisent.

## 2026-07 — Panneau d'attributs façon Photoshop

- **Couleurs en pastilles** : le bouton affiche la couleur (hexa en
  surimpression), un clic ouvre le sélecteur natif — fini les champs
  hexa et la pipette capricieuse.
- **Opacité en curseur 0-100 %** (fond et bordure) au lieu de la
  transparence 0-255 inversée ; épaisseurs de bordure sur une ligne
  N/H/C ; cases à cocher (bordure visible, gras, italique).
- **Section Dimensions retirée** (le viewport fait tout) — son champ
  « top » écrivait dans `shape.right` (bug de l'original).
- Format JSON inchangé.

## 2026-07 — Retours du deuxième test studio

- **Magnet désactivé par défaut** : plus aucun snap tant qu'on n'active
  rien — la grille via l'icône aimant, le magnet aux shapes via clic
  droit (opt-in).
- **Presser une shape la sélectionne et le drag la déplace
  directement** (façon dwpicker/Figma). Avant, glisser un icône non
  sélectionné démarrait un rectangle de sélection — d'où l'impression
  de « mode rectangle cassé ».
- **Clic sur un bouton d'une multi-sélection = il est sélectionné
  seul** (la sélection un par un refonctionne ; dans l'original ce
  comportement reposait par accident sur le micro-rectangle du clic).

## 2026-07 — Images portables

- **Résolution des chemins d'images** : un chemin absolu mort est
  résolu par nom de fichier via `HOTBOX_DESIGNER_ICONS`, le dossier de
  préférences (+ `icons/`) et les dossiers des hotboxes partagées. Fini
  les logos à re-pointer après avoir déplacé son dossier d'icônes.

## 2026-07 — Grosse vague éditeur (5 fonctionnalités)

- **Thème sombre** de toute l'interface (éditeur, manager, librairie).
- **Snap magnétique** au déplacement : bords/centres aimantés aux
  autres shapes et à la zone, guides cyan, toggle au clic droit.
- **Lock** : shapes verrouillables (backgrounds), transparentes à la
  sélection ; Unlock all.
- **Recherche/remplacement** (Ctrl+H) dans les commandes et labels,
  portée sélection ou hotbox.
- **Librairie de boutons** : sauvegarde de boutons configurés par
  catégories (`button_library.json`), fenêtre à vignettes réelles,
  drag & drop vers n'importe quel éditeur, partageable.

## 2026-07 — Retours du premier test studio

- **Copier-coller de style** (Ctrl+Maj+C/V) : coller sur la sélection
  en choisissant quoi (forme, taille, couleurs, texte, image,
  commandes).
- **Sélection assainie** : le clic ne prend plus le background sous le
  bouton (le micro-rectangle de sélection au relâchement embarquait
  tout) ; un rectangle n'attrape pas une shape qui l'englobe ;
  rectangle fonctionnel dans les 4 directions.
- **Menu clic droit** dans l'éditeur.
- **Glisser fluide** : le drag suit la souris jusqu'au relâchement (un
  geste rapide « décrochait » dans l'original).
- **Fit zone** : la zone de travail se recadre sur les boutons (centre
  recalé), au lieu de piloter les champs size à la main.
- **Flèches** : déplacer la sélection d'1 unité (Maj = 10).
- **Fix undo** : l'état initial était stocké par référence et corrompu
  par la première modification (bug latent de l'original).

## 2026-07 — Multi-éditeurs & copier-coller inter-hotboxes

- **Plusieurs hotboxes éditables en même temps** (une fenêtre par
  hotbox, titrée) — l'original fermait le premier éditeur en ouvrant le
  second.
- **Ctrl+C/V par le presse-papier système** : copier des boutons d'une
  hotbox et les coller dans une autre, même entre deux sessions.
- Fix : la sauvegarde écrivait dans la hotbox de la ligne sélectionnée
  du manager, pas celle de l'éditeur émetteur.

## 2026-07 — Éditeur nouvelle génération (base dwpicker)

- **Viewport** : zoom molette vers le curseur, pan clic-molette,
  F = recadrer, plan de travail sur fond sombre, éditeur redimensionnable
  (fini le canvas figé 750×550).
- **Poignées à taille d'écran constante** à tout zoom.
- **Alt + glisser = dupliquer** la sélection.
- **Alignement / distribution** (8 boutons, logique dwpicker adaptée).
- Suite de tests headless (`tests/test_editor.py`), enrichie depuis à
  chaque fonctionnalité.

## 2026-07 — Modernisation

- **Python 3 / PySide6** (Maya 2022 → 2026) via mise à jour du shim
  `vendor/Qt.py` (2.0.5) ; corrections Qt6 (QRegExp, QRect/QPoint
  flottants, stylesheets rgba).
- **Mode standalone** : `python -m hotbox_designer` sans DCC (données
  dans `~/.hotboxjor`).

## 2026-07 — Naissance du fork

- Import verbatim de
  [hotbox_designer](https://github.com/luckylyk/hotbox_designer) de
  Lionel Brouyère (Clear BSD). Les améliorations d'éditeur s'inspirent
  de [dwpicker](https://github.com/DreamWall-Animation/dwpicker)
  (DreamWall Animation, MIT) — code adapté et crédité, icônes reprises.
