from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4
MARGIN = 15 * mm

# Palette de couleurs pour la solution
SOLUTION_COLORS = [
    colors.HexColor("#FF6B6B"),
    colors.HexColor("#4ECDC4"),
    colors.HexColor("#45B7D1"),
    colors.HexColor("#96CEB4"),
    colors.HexColor("#FFEAA7"),
    colors.HexColor("#DDA0DD"),
    colors.HexColor("#98D8C8"),
    colors.HexColor("#F7DC6F"),
    colors.HexColor("#BB8FCE"),
    colors.HexColor("#85C1E9"),
]


def _cell_size(grid_size: int) -> float:
    """Taille d'une cellule en points selon la taille de grille."""
    available = PAGE_W - 2 * MARGIN
    return min(available / grid_size, 22 if grid_size <= 15 else 17)


def _draw_grid_page(c: canvas, grid_cells: list, theme: str, placed_words: list,
                    word_positions: dict = None, solution: bool = False):
    grid_size = len(grid_cells)
    cell = _cell_size(grid_size)
    font_size = cell * 0.55

    # --- Titre ---
    title = f"MOTS MELES — Theme : {theme.upper()}"
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(PAGE_W / 2, PAGE_H - MARGIN - 10, title)

    label = "SOLUTION" if solution else f"Grille {grid_size}x{grid_size}  •  {len(placed_words)} mots a trouver"
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawCentredString(PAGE_W / 2, PAGE_H - MARGIN - 25, label)
    c.setFillColor(colors.black)

    # --- Grille ---
    grid_w = grid_size * cell
    grid_x = (PAGE_W - grid_w) / 2
    grid_y = PAGE_H - MARGIN - 50 - grid_w  # top of grid in PDF coords

    # Solution: surligner les mots d'abord (dessous les lettres)
    if solution and word_positions:
        for idx, word in enumerate(placed_words):
            positions = word_positions.get(word)
            if not positions:
                continue
            col_color = SOLUTION_COLORS[idx % len(SOLUTION_COLORS)]
            c.setFillColor(col_color)
            c.setStrokeColor(col_color)
            for (row, col) in positions:
                x = grid_x + col * cell
                y = grid_y + (grid_size - 1 - row) * cell
                c.rect(x, y, cell, cell, fill=1, stroke=0)

    # Lettres
    c.setFont("Courier-Bold", font_size)
    c.setFillColor(colors.black)
    for r, row in enumerate(grid_cells):
        for col_idx, letter in enumerate(row):
            x = grid_x + col_idx * cell + cell / 2
            y = grid_y + (grid_size - 1 - r) * cell + (cell - font_size) / 2
            c.drawCentredString(x, y, letter)

    # Bordure grille
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.rect(grid_x, grid_y, grid_w, grid_w, fill=0, stroke=1)

    # --- Liste des mots (page principale uniquement) ---
    if not solution:
        _draw_word_list(c, placed_words, grid_y - 10 * mm)

    # --- Légende solution ---
    if solution and word_positions:
        _draw_solution_legend(c, placed_words, word_positions, grid_y - 10 * mm)

    # --- Pied de page ---
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    today = date.today().strftime("%d/%m/%Y")
    c.drawCentredString(PAGE_W / 2, MARGIN / 2, f"Généré le {today}")
    c.setFillColor(colors.black)


def _draw_word_list(c: canvas, words: list, top_y: float):
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, top_y, "Mots a trouver :")

    cols = 3
    col_w = (PAGE_W - 2 * MARGIN) / cols
    x_starts = [MARGIN + i * col_w for i in range(cols)]
    y = top_y - 15
    line_h = 14

    c.setFont("Courier", 10)
    for i, word in enumerate(words):
        col = i % cols
        row = i // cols
        x = x_starts[col]
        yy = y - row * line_h
        if yy < MARGIN:
            break
        c.drawString(x, yy, f"\u25a1 {word}")


def _draw_solution_legend(c: canvas, words: list, word_positions: dict, top_y: float):
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, top_y, "Legende :")

    cols = 3
    col_w = (PAGE_W - 2 * MARGIN) / cols
    x_starts = [MARGIN + i * col_w for i in range(cols)]
    y = top_y - 15
    line_h = 14

    for i, word in enumerate(words):
        col = i % cols
        row_i = i // cols
        x = x_starts[col]
        yy = y - row_i * line_h
        if yy < MARGIN:
            break
        col_color = SOLUTION_COLORS[i % len(SOLUTION_COLORS)]
        c.setFillColor(col_color)
        c.rect(x, yy, 10, 10, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Courier", 10)
        c.drawString(x + 14, yy, word)


def render_pdf(output_path: str, grid_cells: list, theme: str, placed_words: list,
               word_positions: dict = None, solution: bool = False):
    c = canvas.Canvas(output_path, pagesize=A4)

    # Page 1 : grille puzzle
    _draw_grid_page(c, grid_cells, theme, placed_words,
                    word_positions=word_positions, solution=False)
    c.showPage()

    # Page 2 optionnelle : solution
    if solution and word_positions:
        _draw_grid_page(c, grid_cells, theme, placed_words,
                        word_positions=word_positions, solution=True)
        c.showPage()

    c.save()
    print(f"[OK]  PDF sauvegardé : {output_path}")


if __name__ == "__main__":
    # Quick test with a small hardcoded grid
    from grid_engine import Grid
    g = Grid(size=8, seed=1, langue="fr")
    words = ["LION", "TIGRE", "OURS", "LOUP"]
    placed, _ = g.place_words(words)
    g.fill_random()
    render_pdf("test_output.pdf", g.cells, "animaux", placed,
               word_positions=g.get_word_positions(), solution=True)
    print("[OK]  Test PDF genere : test_output.pdf")
