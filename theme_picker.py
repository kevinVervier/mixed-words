import random

THEMES = {
    "fr": [
        "animaux", "pays", "villes de France", "fruits", "legumes",
        "prenoms masculins", "prenoms feminins", "sports", "metiers",
        "films", "acteurs", "chanteurs", "marques de voitures",
        "capitales du monde", "fleurs", "arbres", "plats cuisines",
        "instruments de musique", "meubles", "vetements", "outils",
        "super-heros", "personnages historiques", "objets de cuisine",
        "animaux marins", "monuments celebres", "materiaux",
        "couleurs", "boissons", "desserts",
    ],
    "en": [
        "animals", "countries", "US cities", "fruits", "vegetables",
        "male first names", "female first names", "sports", "jobs",
        "movies", "actors", "singers", "car brands",
        "world capitals", "flowers", "trees", "dishes",
        "musical instruments", "furniture", "clothing", "tools",
        "superheroes", "historical figures", "kitchen items",
        "sea animals", "famous landmarks", "materials",
        "colors", "drinks", "desserts",
    ],
}

# Skip very rare letters for better playability
_RARE = set("WXYZ")
LETTERS = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in _RARE]


def pick_theme(langue: str = "fr", seed=None) -> str:
    rng = random.Random(seed)
    return rng.choice(THEMES.get(langue, THEMES["fr"]))


def pick_letter(seed=None) -> str:
    rng = random.Random(seed)
    return rng.choice(LETTERS)
