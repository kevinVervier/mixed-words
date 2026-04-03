# CLAUDE.md — Générateur de Grilles de Mots Mêlés

## Vue d'ensemble du projet

Créer un programme Python en ligne de commande qui génère des grilles de mots mêlés (word search) prêtes à imprimer, à partir d'un thème, d'un nombre de mots et d'une taille de grille.

---

## Fonctionnalités attendues

### Entrées (CLI)
```
python generator.py --theme "animaux" --nb-mots 12 --taille 15 --output grille.pdf
```

| Paramètre     | Description                              | Défaut  |
|---------------|------------------------------------------|---------|
| `--theme`     | Thème des mots cachés (ex: "océan")      | requis  |
| `--nb-mots`   | Nombre de mots à cacher dans la grille   | 10      |
| `--taille`    | Côté de la grille carrée (N×N)           | 15      |
| `--output`    | Nom du fichier PDF de sortie             | grille.pdf |
| `--langue`    | Langue des mots (`fr` ou `en`)           | `fr`    |
| `--solution`  | Inclure une page solution dans le PDF    | False   |

### Génération des mots
- Appeler l'API Claude (`claude-sonnet-4-20250514`) pour obtenir une liste de mots liés au thème
- Prompt : demander exactement `--nb-mots` mots, sans accents, en MAJUSCULES, format JSON
- Valider que les mots tiennent dans la grille (longueur ≤ taille)
- Filtrer les mots trop longs et en redemander si nécessaire

**Prompt API suggéré :**
```
Donne-moi {nb_mots} mots en français sur le thème "{theme}".
Contraintes : sans accents ni caractères spéciaux, en majuscules, longueur max {taille} lettres.
Réponds UNIQUEMENT en JSON : {"mots": ["MOT1", "MOT2", ...]}
```

### Règles de placement des mots

**Directions autorisées et leurs probabilités :**
| Direction          | Orientation               | Probabilité |
|--------------------|---------------------------|-------------|
| Horizontal (→)     | gauche → droite           | 45%         |
| Vertical (↓)       | haut → bas                | 45%         |
| Diagonale (↘)      | haut-gauche → bas-droite  | 10%         |

**Contraintes strictes :**
- Toujours de **gauche à droite** (jamais droite→gauche)
- Toujours de **haut en bas** (jamais bas→haut)
- Les mots peuvent se **croiser** sur une lettre commune
- Pas de chevauchement de lettres différentes
- Maximum **50 tentatives** de placement par mot avant abandon
- Si un mot ne peut pas être placé, le signaler et continuer

### Remplissage
- Les cases vides sont remplies avec des **lettres aléatoires majuscules**
- Utiliser une distribution de lettres réaliste pour la langue (ex: fréquences du français)

---

## Architecture du code

```
wordsearch/
├── CLAUDE.md           ← ce fichier
├── generator.py        ← point d'entrée CLI
├── word_fetcher.py     ← appel API Claude pour obtenir les mots
├── grid_engine.py      ← logique de placement et génération de grille
├── pdf_renderer.py     ← rendu PDF avec reportlab
├── requirements.txt
└── output/             ← dossier de sortie par défaut
```

### `word_fetcher.py`
- Fonction `fetch_words(theme, nb_mots, taille, langue) -> list[str]`
- Appel API Anthropic avec gestion d'erreur
- Parse JSON de la réponse
- Retry si pas assez de mots valides

### `grid_engine.py`
- Classe `Grid(size: int)`
- Méthode `place_word(word: str, direction: str) -> bool`
- Méthode `fill_random()`
- Méthode `get_word_positions() -> dict` (pour la solution)
- Répartition aléatoire pondérée des directions (45/45/10)

### `pdf_renderer.py`
- Utiliser **`reportlab`** pour générer le PDF
- Format A4 portrait
- Police **monospace** (Courier) pour la grille — espacement uniforme
- Taille de cellule adaptée à la taille de grille (grille 15×15 ≈ 22pt, 20×20 ≈ 17pt)

---

## Format du PDF de sortie

### Page 1 — La grille
```
┌─────────────────────────────────────┐
│  MOTS MÊLÉS — Thème : ANIMAUX       │
│  Grille 15×15 • 12 mots à trouver  │
│                                     │
│  A B C D E F G H I J K L M N O     │
│  P Q R S T U V W X Y Z A B C D     │
│  ...                                │
│                                     │
│  Mots à trouver :                   │
│  □ LION    □ TIGRE   □ ELEPHANT    │
│  □ GIRAFE  □ ZEBRE   □ DAUPHIN    │
│  ...                                │
└─────────────────────────────────────┘
```

**Détails de mise en page :**
- Titre en haut, centré, gras (18pt)
- Sous-titre : thème + dimensions + nombre de mots (11pt, gris)
- Grille : police Courier Bold, lettres bien espacées
- Liste des mots en bas : 3 colonnes, avec case à cocher □
- Pied de page : date de génération

### Page 2 (optionnelle) — Solution
- Même grille mais avec les mots **surlignés** (rectangle coloré autour)
- Chaque mot dans une couleur différente
- Légende : couleur → mot

---

## Dépendances

```txt
# requirements.txt
anthropic>=0.25.0
reportlab>=4.0.0
click>=8.0.0
```

Installation :
```bash
pip install -r requirements.txt
```

---

## Exemples d'utilisation

```bash
# Grille simple
python generator.py --theme "fruits" --nb-mots 8 --taille 12

# Grille avec solution
python generator.py --theme "capitales du monde" --nb-mots 15 --taille 20 --solution

# Grille en anglais
python generator.py --theme "space" --nb-mots 10 --taille 15 --langue en --output espace.pdf
```

---

## Gestion des erreurs

| Cas | Comportement |
|-----|-------------|
| API Claude indisponible | Message d'erreur clair, arrêt propre |
| Mot trop long pour la grille | Ignoré, log en warning |
| Grille trop petite pour tous les mots | Placer le maximum possible, avertir |
| Moins de mots placés que demandé | Indiquer le nombre réel dans le PDF |
| Fichier de sortie non accessible | Erreur avec chemin suggéré |

---

## Critères de qualité

- [ ] Tous les mots sont présents dans la grille (ou un avertissement clair sinon)
- [ ] Directions respectées : → et ↓ uniquement pour 90%, ↘ pour 10%
- [ ] Pas de dépassement de grille
- [ ] Le PDF est lisible et imprimable sur A4
- [ ] Le code est modulaire et chaque fichier fait < 200 lignes
- [ ] Les logs sont clairs (`[OK]`, `[WARN]`, `[ERR]`)

---

## Notes pour Claude Code

1. **Commencer par** `grid_engine.py` et tester la logique de placement avec des mots codés en dur avant d'intégrer l'API.
2. **Valider visuellement** la grille en l'affichant dans le terminal avant de générer le PDF.
3. **L'appel API Anthropic** : utiliser la variable d'environnement `ANTHROPIC_API_KEY` — ne jamais hardcoder la clé.
4. **Pour le PDF** : tester d'abord avec une petite grille (8×8) pour ajuster les marges et la taille de police.
5. **Seed aléatoire** : accepter un paramètre `--seed` optionnel pour des grilles reproductibles (debug).
