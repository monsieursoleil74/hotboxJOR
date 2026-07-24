# Changelog hotboxJOR

Historique des évolutions du fork, de la plus récente à la plus
ancienne. Chaque entrée correspond à un ou plusieurs commits sur
`main`. Détails d'usage : `MANUEL.md`.

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
