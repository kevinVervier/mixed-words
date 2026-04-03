import json
import re
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


NIVEAU_HINTS = {
    "fr": {
        "enfant": (
            "Le public est des enfants de moins de 10 ans. "
            "Choisis des mots tres simples, connus, du vocabulaire courant de l'ecole primaire. "
            "Mots courts (3 a 7 lettres de preference), concrets et amusants."
        ),
        "adulte": (
            "Le public est adulte. "
            "Choisis des mots varies et interessants, y compris des termes moins courants, "
            "des noms propres culturels, des concepts plus riches."
        ),
    },
    "en": {
        "enfant": (
            "The audience is children under 10. "
            "Choose very simple, familiar words from primary school vocabulary. "
            "Short words (3 to 7 letters preferred), concrete and fun."
        ),
        "adulte": (
            "The audience is adults. "
            "Choose varied and interesting words, including less common terms, "
            "cultural proper nouns, and richer concepts."
        ),
    },
}


def _build_prompt(theme: str, nb_mots: int, taille: int, langue: str,
                  niveau: str = "adulte") -> str:
    hint = NIVEAU_HINTS.get(langue, NIVEAU_HINTS["fr"]).get(niveau, "")
    if langue == "fr":
        return (
            f'Donne-moi {nb_mots} mots en francais sur le theme "{theme}".\n'
            f"{hint}\n"
            f"Les mots doivent couvrir des aspects VARIES : gastronomie, monuments, "
            f"traditions, personnages celebres, nature, sport, arts, symboles — "
            f"pas uniquement des villes ou des noms propres.\n"
            f"Contraintes : sans accents ni caracteres speciaux, en majuscules, "
            f"longueur max {taille} lettres, un seul mot par entree (pas de groupes de mots).\n"
            f'Reponds UNIQUEMENT en JSON : {{"mots": ["MOT1", "MOT2", ...]}}'
        )
    else:
        return (
            f'Give me {nb_mots} words in English on the theme "{theme}".\n'
            f"{hint}\n"
            f"Words must cover VARIED aspects: food, landmarks, traditions, famous people, "
            f"nature, sport, arts, symbols — not just cities or proper nouns.\n"
            f"Constraints: no special characters, uppercase only, "
            f"max length {taille} letters, single words only (no word groups).\n"
            f'Reply ONLY in JSON: {{"mots": ["WORD1", "WORD2", ...]}}'
        )


def _parse_words(text: str, taille: int) -> list:
    match = re.search(r'\{[^{}]*"mots"\s*:\s*\[.*?\]\s*\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"JSON introuvable dans : {text[:200]}")
    data = json.loads(match.group())
    words = data.get("mots", [])
    valid = []
    for w in words:
        w = str(w).upper().strip()
        if w.isalpha() and len(w) <= taille:
            valid.append(w)
        else:
            print(f"[WARN] Mot ignore (invalide ou trop long) : {w}")
    return valid


async def _ask_claude(prompt: str) -> str:
    result_text = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(allowed_tools=[]),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result
    return result_text


def fetch_words(theme: str, nb_mots: int, taille: int, langue: str = "fr",
                niveau: str = "adulte") -> list:
    collected = []
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        still_needed = nb_mots - len(collected)
        if still_needed <= 0:
            break

        prompt = _build_prompt(theme, still_needed, taille, langue, niveau)
        print(f"[OK]  Appel Claude (tentative {attempt}) -- {still_needed} mots demandes...")

        try:
            text = anyio.from_thread.run_sync(
                lambda: anyio.run(_ask_claude, prompt)
            )
        except RuntimeError:
            # No running event loop — call directly
            text = anyio.run(_ask_claude, prompt)

        words = _parse_words(text, taille)
        new_words = [w for w in words if w not in collected]
        collected.extend(new_words)
        print(f"[OK]  {len(new_words)} nouveaux mots obtenus : {new_words}")

    if len(collected) < nb_mots:
        print(
            f"[WARN] Seulement {len(collected)}/{nb_mots} mots valides apres "
            f"{max_retries} tentatives."
        )
    return collected[:nb_mots]


if __name__ == "__main__":
    words = fetch_words("animaux de la savane", nb_mots=8, taille=12, langue="fr")
    print(f"\nMots finaux : {words}")
