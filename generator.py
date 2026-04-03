import os
import sys
import click
from grid_engine import Grid
from word_fetcher import fetch_words
from pdf_renderer import render_pdf


@click.command()
@click.option("--theme", required=True, help="Theme des mots caches (ex: ocean)")
@click.option("--nb-mots", default=10, show_default=True, help="Nombre de mots a cacher")
@click.option("--taille", default=15, show_default=True, help="Cote de la grille NxN")
@click.option("--output", default="grille.pdf", show_default=True, help="Fichier PDF de sortie")
@click.option("--langue", default="fr", show_default=True, type=click.Choice(["fr", "en"]),
              help="Langue des mots")
@click.option("--solution", is_flag=True, default=False, help="Inclure une page solution")
@click.option("--seed", default=None, type=int, help="Graine aleatoire (reproductibilite)")
@click.option("--niveau", default="adulte", show_default=True,
              type=click.Choice(["adulte", "enfant"]),
              help="Niveau de difficulte : adulte ou enfant (moins de 10 ans)")
def main(theme, nb_mots, taille, output, langue, solution, seed, niveau):
    """Generateur de grilles de mots meles pretes a imprimer."""

    click.echo(f"\n=== Mots Meles - Theme : {theme} | Niveau : {niveau} ===")

    # 1. Recuperer les mots via l'API Claude
    click.echo(f"\n[->] Recuperation de {nb_mots} mots (langue={langue}, niveau={niveau})...")
    try:
        words = fetch_words(theme, nb_mots, taille, langue, niveau)
    except (EnvironmentError, RuntimeError) as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    if not words:
        click.echo("[ERR] Aucun mot obtenu depuis l'API. Abandon.", err=True)
        sys.exit(1)

    click.echo(f"[OK]  {len(words)} mots prets : {words}")

    # 2. Construire la grille
    click.echo(f"\n[->] Construction de la grille {taille}x{taille}...")
    grid = Grid(size=taille, seed=seed, langue=langue)
    placed, failed = grid.place_words(words)

    if failed:
        click.echo(f"[WARN] {len(failed)} mot(s) non places : {failed}")
    click.echo(f"[OK]  {len(placed)}/{len(words)} mots places.")

    grid.fill_random()

    # Affichage terminal (validation visuelle)
    click.echo("\n--- Apercu terminal ---")
    grid.display()
    click.echo("-----------------------\n")

    # 3. Generer le PDF
    output_dir = os.path.dirname(output)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            click.echo(f"[ERR] Impossible de creer le dossier '{output_dir}': {e}", err=True)
            sys.exit(1)

    click.echo(f"[->] Generation du PDF : {output}")
    try:
        render_pdf(
            output_path=output,
            grid_cells=grid.cells,
            theme=theme,
            placed_words=placed,
            word_positions=grid.get_word_positions(),
            solution=solution,
        )
    except OSError as e:
        click.echo(f"[ERR] Impossible d'ecrire '{output}': {e}", err=True)
        suggestion = os.path.join("output", os.path.basename(output))
        click.echo(f"      Essayez : --output {suggestion}", err=True)
        sys.exit(1)

    pages = 2 if solution else 1
    click.echo(f"\n[OK]  Termine ! PDF {pages} page(s) -> {os.path.abspath(output)}")
    if len(placed) < nb_mots:
        click.echo(f"[WARN] {len(placed)} mots sur {nb_mots} demandes ont ete places.")


if __name__ == "__main__":
    main()
