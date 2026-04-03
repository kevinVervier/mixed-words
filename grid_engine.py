import random

# Fréquences de lettres françaises (approximatives)
FREQ_FR = (
    "EEEEEEEEEEEAAAAAAAAIIIIIIISSSSSSNNNNNNTTTTTTRRRRRUUUUULOOOOODDDCCPPMM"
    "VVGGFFBBHHQJXKWYZ"
)
FREQ_EN = (
    "EEEEEEEEEEETTTTTTTAAAAAAAOOOOOOIIIIIINNNNNNSSSSSSHHHHHRRRRRDDDLLLCCUU"
    "MMWWFFGGPPBBVVKJXQYZ"
)

DIRECTIONS = {
    "H": (0, 1),   # horizontal →
    "V": (1, 0),   # vertical ↓
    "D": (1, 1),   # diagonal ↘
}
DIR_WEIGHTS = ["H"] * 45 + ["V"] * 45 + ["D"] * 10


class Grid:
    def __init__(self, size: int, seed: int = None, langue: str = "fr"):
        self.size = size
        self.langue = langue
        self.cells = [["" for _ in range(size)] for _ in range(size)]
        self.word_positions = {}  # word -> [(row, col), ...]
        self.rng = random.Random(seed)

    def _can_place(self, word: str, row: int, col: int, dr: int, dc: int) -> bool:
        for i, letter in enumerate(word):
            r, c = row + i * dr, col + i * dc
            if r < 0 or r >= self.size or c < 0 or c >= self.size:
                return False
            if self.cells[r][c] not in ("", letter):
                return False
        return True

    def place_word(self, word: str, direction: str = None) -> bool:
        if direction is None:
            direction = self.rng.choice(DIR_WEIGHTS)
        dr, dc = DIRECTIONS[direction]

        for _ in range(50):
            # Compute valid starting positions
            max_r = self.size - len(word) * dr if dr > 0 else self.size - 1
            max_c = self.size - len(word) * dc if dc > 0 else self.size - 1
            if max_r < 0 or max_c < 0:
                return False
            row = self.rng.randint(0, max_r)
            col = self.rng.randint(0, max_c)
            if self._can_place(word, row, col, dr, dc):
                positions = []
                for i, letter in enumerate(word):
                    r, c = row + i * dr, col + i * dc
                    self.cells[r][c] = letter
                    positions.append((r, c))
                self.word_positions[word] = positions
                return True
        return False

    def place_words(self, words: list) -> list:
        placed = []
        failed = []
        for word in words:
            if self.place_word(word):
                placed.append(word)
                print(f"[OK]   Mot placé : {word}")
            else:
                failed.append(word)
                print(f"[WARN] Impossible de placer : {word}")
        return placed, failed

    def fill_random(self):
        pool = FREQ_FR if self.langue == "fr" else FREQ_EN
        for r in range(self.size):
            for c in range(self.size):
                if self.cells[r][c] == "":
                    self.cells[r][c] = self.rng.choice(pool)

    def get_word_positions(self) -> dict:
        return dict(self.word_positions)

    def display(self):
        print("   " + " ".join(f"{c:2}" for c in range(self.size)))
        for r, row in enumerate(self.cells):
            print(f"{r:2} " + " ".join(f" {cell}" for cell in row))


if __name__ == "__main__":
    # Quick sanity test
    test_words = ["LION", "TIGRE", "ZEBRE", "GIRAFE", "DAUPHIN", "ELEPHANT"]
    g = Grid(size=15, seed=42)
    placed, failed = g.place_words(test_words)
    g.fill_random()
    print()
    g.display()
    print(f"\nPlacés: {placed}")
    if failed:
        print(f"Échoués: {failed}")
    print(f"\nPositions: {g.get_word_positions()}")
