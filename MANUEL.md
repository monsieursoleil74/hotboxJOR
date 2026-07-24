# Manuel hotboxJOR

Mode d'emploi de l'éditeur et des outils du fork. Tenu à jour à chaque
fonctionnalité ajoutée. Pour l'installation : voir `README.md`. Pour
l'historique des évolutions : voir `CHANGELOG.md`.

---

## Vue d'ensemble

Trois fenêtres :

| Fenêtre | Rôle |
|---|---|
| **Manager** | Liste des hotboxes : créer, éditer, supprimer, importer/exporter, assigner un hotkey Maya. |
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
| **Clic molette maintenu** | Pan (déplacer la vue) |
| **F** | Recadrer : sur la sélection s'il y en a une, sinon sur la hotbox |

À l'ouverture, la hotbox est cadrée automatiquement. Les poignées du
manipulateur et les traits d'interface gardent une **taille constante à
l'écran** quel que soit le zoom.

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
| **Glisser une poignée** | Redimensionner (Maj = carré) |
| **Alt + glisser la sélection** | **Dupliquer** : les copies partent sous le curseur, les originaux restent |
| **Flèches** | Déplacer d'1 unité (**Maj** = 10) |
| **Suppr** | Supprimer la sélection |
| **Ctrl+Z / Ctrl+Y** | Undo / redo (tout est annulable) |

### Snap magnétique 🧲 (désactivé par défaut)

**Aucun snap n'est actif par défaut.** Deux systèmes, au choix :

- La **grille** : bouton aimant rouge de la barre d'outils + pas x/y —
  comme dans l'original.
- Le **magnet aux shapes** (opt-in) : clic droit → « Magnet snapping » —
  bords et centres s'aimantent à ceux des autres shapes et de la zone
  (~6 px écran), guides cyan en pointillés. Si la grille est active,
  elle garde la priorité.

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
  nom + catégorie (libre : Rig, Anim, Selection… — l'onglet courant est
  proposé par défaut). Toutes les shelves ouvertes se rafraîchissent.
- **Réutiliser** : **glisse-dépose** depuis la shelf vers le canvas
  juste au-dessus : le bouton atterrit sous le curseur, sélectionné.
  Multi-sélection possible. Ça marche aussi vers un AUTRE éditeur.
- **Supprimer** : clic droit sur un bouton de la shelf → Delete.
- **Masquer/afficher** la shelf : le bouton librairie de la barre
  d'outils.

Stockage : `button_library.json` dans le dossier de données
(préférences Maya ; `~/.hotboxjor` en standalone). **Partage** : copier
ce fichier à un collègue lui donne la librairie.

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

## Panneau d'attributs (à droite)

Refondu façon Photoshop :

- **Couleurs = pastilles cliquables** : le bouton affiche la couleur
  réelle (code hexa en surimpression, noir ou blanc selon la
  luminosité) ; un clic ouvre le **sélecteur de couleurs natif**. Si la
  sélection a des couleurs différentes, la pastille affiche « … ».
- **Opacité = curseur 0-100 %** (une pour le fond, une pour la
  bordure) — la valeur est convertie vers la « transparence 0-255 »
  historique du JSON, rien ne change dans le format.
- **Cases à cocher** pour bordure visible / gras / italique (état
  intermédiaire si la sélection est mixte).
- **Épaisseurs de bordure** compactées en une ligne N / H / C
  (normal / survol / clic).
- La section **Dimensions a été retirée** (tout se manipule au
  viewport) — son champ « top » écrivait d'ailleurs dans `shape.right`
  (bug de l'original).

## Menu clic droit (récapitulatif)

Copy / Paste / Copy style / Paste style… • Delete • On top / Move up /
Move down / On bottom • Button library… / Save selection to library… •
Search and replace… • Lock selection / Unlock all / Magnet snapping •
Fit zone to shapes / Frame view.

## Barre d'outils, de gauche à droite

Supprimer • copier • coller • copier style • coller style — undo /
redo — grille (aimant rouge) + pas x/y — champs **size** + **fit
zone** — édition du **centre** + coordonnées — ajout : bouton / texte /
background — **librairie** / **enregistrer dans la librairie** — ordre :
dessous / descendre / monter / dessus — alignements (6) — distributions
(2).

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
