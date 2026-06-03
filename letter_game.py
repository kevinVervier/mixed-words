import sys
import time
import select
import anyio
import click

from theme_picker import pick_theme, pick_letter


# ── Claude validation ──────────────────────────────────────────────────────────

async def _ask_claude(prompt: str) -> str:
    from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
    result = ""
    async for msg in query(prompt=prompt, options=ClaudeAgentOptions(allowed_tools=[])):
        if isinstance(msg, ResultMessage):
            result = msg.result
    return result


def _validate(theme: str, lettre: str, answers: list, langue: str) -> str:
    if langue == "fr":
        answers_str = ", ".join(answers) if answers else "(aucune reponse)"
        prompt = (
            f'Jeu : le joueur devait nommer des elements sur le theme "{theme}" '
            f"commencant par la lettre {lettre}.\n"
            f"Reponses : {answers_str}\n\n"
            f"Pour chaque reponse, indique VALIDE ou INVALIDE (avec une breve raison). "
            f"Sois indulgent pour les accents manquants. "
            f"Conclus avec : Score final = X / {len(answers)}."
        )
    else:
        answers_str = ", ".join(answers) if answers else "(no answers)"
        prompt = (
            f'Game: the player had to name items related to "{theme}" '
            f"starting with the letter {lettre}.\n"
            f"Answers: {answers_str}\n\n"
            f"For each answer, say VALID or INVALID (brief reason). "
            f"Conclude with: Final score = X / {len(answers)}."
        )
    try:
        return anyio.run(_ask_claude, prompt)
    except RuntimeError:
        return anyio.from_thread.run_sync(lambda: anyio.run(_ask_claude, prompt))


# ── Input collection ───────────────────────────────────────────────────────────

def _collect_timed(seconds: int, langue: str) -> list:
    """Read words from stdin until empty line or timer expires."""
    if langue == "fr":
        print(f"  Tapez vos reponses, une par ligne.")
        print(f"  Ligne vide = terminer avant la fin du temps.\n")
    else:
        print(f"  Type your answers, one per line.")
        print(f"  Empty line = stop before time is up.\n")

    words = []
    deadline = time.time() + seconds
    last_announced = seconds + 1

    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            msg = "\n  Temps ecoule !" if langue == "fr" else "\n  Time's up!"
            print(msg)
            break

        remaining_int = int(remaining)
        if remaining_int != last_announced and (remaining_int % 10 == 0 or remaining_int <= 5):
            suffix = "s restantes..." if langue == "fr" else "s remaining..."
            print(f"  [{remaining_int}{suffix}]")
            last_announced = remaining_int

        ready, _, _ = select.select([sys.stdin], [], [], 0.5)
        if not ready:
            continue

        line = sys.stdin.readline().strip().upper()
        if not line:
            break
        words.append(line)

    return words


def _collect_unlimited(langue: str) -> list:
    """Read words until empty line."""
    if langue == "fr":
        print("  Tapez vos reponses, une par ligne. Ligne vide = terminer.\n")
    else:
        print("  Type your answers, one per line. Empty line = stop.\n")
    words = []
    while True:
        try:
            line = input().strip().upper()
        except EOFError:
            break
        if not line:
            break
        words.append(line)
    return words


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--langue", default="fr", show_default=True,
              type=click.Choice(["fr", "en"]), help="Langue du jeu")
@click.option("--temps", default=60, show_default=True,
              help="Duree en secondes (0 = sans limite)")
@click.option("--lettre", default=None, help="Forcer une lettre specifique")
@click.option("--theme", default=None, help="Forcer un theme specifique")
@click.option("--seed", default=None, type=int, help="Graine aleatoire (reproductibilite)")
def main(langue, temps, lettre, theme, seed):
    """Jeu de lettres : nommez le plus d'elements possible sur un theme donne."""

    drawn_letter = lettre.upper() if lettre else pick_letter(seed=seed)
    drawn_theme = theme if theme else pick_theme(langue=langue, seed=seed)

    sep = "=" * 50
    click.echo(f"\n{sep}")
    if langue == "fr":
        click.echo("       JEU DE LETTRES")
        click.echo(sep)
        click.echo(f"  Theme  : {drawn_theme.upper()}")
        click.echo(f"  Lettre : {drawn_letter}")
        click.echo(sep)
        click.echo(f"\n  Nommez le plus d'elements possible")
        click.echo(f'  sur le theme "{drawn_theme}"')
        click.echo(f"  commencant par la lettre  {drawn_letter}  !\n")
        time_label = f"{temps} secondes" if temps > 0 else "sans limite de temps"
        click.echo(f"  Duree : {time_label}\n")
        input("  Appuyez sur Entree pour commencer...")
    else:
        click.echo("       LETTER GAME")
        click.echo(sep)
        click.echo(f"  Theme  : {drawn_theme.upper()}")
        click.echo(f"  Letter : {drawn_letter}")
        click.echo(sep)
        click.echo(f"\n  Name as many items as possible")
        click.echo(f'  on the theme "{drawn_theme}"')
        click.echo(f"  starting with the letter  {drawn_letter}  !\n")
        time_label = f"{temps} seconds" if temps > 0 else "no time limit"
        click.echo(f"  Time: {time_label}\n")
        input("  Press Enter to start...")

    click.echo()
    start = time.time()

    if temps > 0:
        answers = _collect_timed(temps, langue)
    else:
        answers = _collect_unlimited(langue)

    elapsed = time.time() - start

    click.echo()
    if langue == "fr":
        click.echo(f"  {len(answers)} reponse(s) en {elapsed:.0f}s.")
        click.echo("\n[->] Validation par Claude en cours...\n")
    else:
        click.echo(f"  {len(answers)} answer(s) in {elapsed:.0f}s.")
        click.echo("\n[->] Validating with Claude...\n")

    try:
        result = _validate(drawn_theme, drawn_letter, answers, langue)
    except Exception as e:
        click.echo(f"[ERR] Validation impossible : {e}", err=True)
        click.echo(f"  Reponses soumises : {answers}")
        sys.exit(1)

    click.echo(result)
    click.echo()


if __name__ == "__main__":
    main()
