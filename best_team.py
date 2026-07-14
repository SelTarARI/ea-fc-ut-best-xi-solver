#!/usr/bin/env python3
"""
EA FC 26 Ultimate Team — Best XI solver.

Finds the optimal starting XI (maximum total rating) for one formation or
ranks ALL 29 FC 26 Ultimate Team formations, using the Hungarian algorithm
(optimal assignment, not greedy). Pure Python, no dependencies.

Player file format (one player per line, '#' starts a comment).
A name before a comma is optional -- no brackets, no quotes:
    91: GK
    Arda, 92: CAM CM
    89: LW LM ST

Positions (case-insensitive; Turkish abbreviations also accepted):
    GK  LB  RB  CB  CDM  CM  CAM  LM  RM  LW  RW  ST

Usage:
    python3 best_team.py players.txt                     # rank all formations
    python3 best_team.py players.txt --formation 4-3-3   # one formation
    python3 best_team.py players.txt --top 5             # detail only top 5
"""

import argparse
import sys

# ---------------------------------------------------------------- positions

POSITIONS = {"GK", "LB", "RB", "CB", "CDM", "CM", "CAM",
             "LM", "RM", "LW", "RW", "ST"}
# Turkish abbreviations accepted as input aliases
TR_TO_EN = {
    "KL": "GK", "SLB": "LB", "SGB": "RB", "STP": "CB", "MDO": "CDM",
    "MO": "CM", "MOO": "CAM", "SLO": "LM", "SGO": "RM", "SLK": "LW",
    "SGK": "RW", "SNT": "ST",
}


def normalize_pos(token):
    t = token.strip().upper().strip(",;")
    if t in POSITIONS:
        return t
    if t in TR_TO_EN:
        return TR_TO_EN[t]
    raise ValueError(f"unknown position '{token}'")


# ---------------------------------------------------------------- formations
# All 29 EA FC 26 Ultimate Team formations, verified against FUT.GG
# (positions section of each formation page), July 2026.
# Rows are ordered attack -> goalkeeper, for pitch-style printing.

B4 = ["LB", "CB", "CB", "RB"]                 # back four
B5 = ["LB", "CB", "CB", "CB", "RB"]           # back five (LB/RB in FC 26)
B3 = ["CB", "CB", "CB"]                       # back three

FORMATIONS = {
    "3-1-4-2":       [["ST", "ST"], ["LM", "CM", "CM", "RM"], ["CDM"], B3, ["GK"]],
    "3-4-1-2":       [["ST", "ST"], ["CAM"], ["LM", "CM", "CM", "RM"], B3, ["GK"]],
    "3-4-2-1":       [["ST"], ["CAM", "CAM"], ["LM", "CM", "CM", "RM"], B3, ["GK"]],
    "3-4-3":         [["LW", "ST", "RW"], ["LM", "CM", "CM", "RM"], B3, ["GK"]],
    "3-5-2":         [["ST", "ST"], ["CAM"], ["LM", "CDM", "CDM", "RM"], B3, ["GK"]],
    "4-1-2-1-2":     [["ST", "ST"], ["CAM"], ["LM", "RM"], ["CDM"], B4, ["GK"]],       # wide diamond
    "4-1-2-1-2 (2)": [["ST", "ST"], ["CAM"], ["CM", "CM"], ["CDM"], B4, ["GK"]],       # narrow diamond
    "4-1-3-2":       [["ST", "ST"], ["LM", "CM", "RM"], ["CDM"], B4, ["GK"]],
    "4-1-4-1":       [["ST"], ["LM", "CM", "CM", "RM"], ["CDM"], B4, ["GK"]],
    "4-2-1-3":       [["LW", "ST", "RW"], ["CAM"], ["CDM", "CDM"], B4, ["GK"]],
    "4-2-2-2":       [["ST", "ST"], ["CAM", "CAM"], ["CDM", "CDM"], B4, ["GK"]],
    "4-2-3-1":       [["ST"], ["CAM", "CAM", "CAM"], ["CDM", "CDM"], B4, ["GK"]],
    "4-2-3-1 (2)":   [["ST"], ["LM", "CAM", "RM"], ["CDM", "CDM"], B4, ["GK"]],        # wide
    "4-2-4":         [["LW", "ST", "ST", "RW"], ["CM", "CM"], B4, ["GK"]],
    "4-3-1-2":       [["ST", "ST"], ["CAM"], ["CM", "CM", "CM"], B4, ["GK"]],
    "4-3-2-1":       [["ST"], ["CAM", "CAM"], ["CM", "CM", "CM"], B4, ["GK"]],
    "4-3-3":         [["LW", "ST", "RW"], ["CM", "CM", "CM"], B4, ["GK"]],
    "4-3-3 (2)":     [["LW", "ST", "RW"], ["CM", "CM"], ["CDM"], B4, ["GK"]],          # holding
    "4-3-3 (3)":     [["LW", "ST", "RW"], ["CM"], ["CDM", "CDM"], B4, ["GK"]],         # defend
    "4-3-3 (4)":     [["LW", "ST", "RW"], ["CAM"], ["CM", "CM"], B4, ["GK"]],          # attack
    "4-4-1-1 (2)":       [["ST"], ["CAM"], ["LM", "CM", "CM", "RM"], B4, ["GK"]],
    "4-4-2":         [["ST", "ST"], ["LM", "CM", "CM", "RM"], B4, ["GK"]],
    "4-4-2 (2)":     [["ST", "ST"], ["LM", "CDM", "CDM", "RM"], B4, ["GK"]],           # holding
    "4-5-1":         [["ST"], ["CAM", "CAM"], ["LM", "CM", "RM"], B4, ["GK"]],         # attack
    "4-5-1 (2)":     [["ST"], ["LM", "CM", "CM", "CM", "RM"], B4, ["GK"]],             # flat
    "5-2-1-2":       [["ST", "ST"], ["CAM"], ["CM", "CM"], B5, ["GK"]],
    "5-2-3":         [["LW", "ST", "RW"], ["CM", "CM"], B5, ["GK"]],
    "5-3-2":         [["ST", "ST"], ["CM", "CM"], ["CDM"], B5, ["GK"]],
    "5-4-1":         [["ST"], ["LM", "CM", "CM", "RM"], B5, ["GK"]],
}


# ---------------------------------------------------------------- player file

class Player:
    __slots__ = ("name", "rating", "positions", "idx")

    def __init__(self, name, rating, positions, idx):
        self.name = name
        self.rating = rating
        self.positions = positions
        self.idx = idx

    def label(self):
        return f"{self.rating} {self.name}" if self.name else str(self.rating)


def parse_players(path):
    players = []
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            name = None
            body = line
            # optional "Name," prefix (name may not contain ':')
            if "," in line.split(":", 1)[0]:
                name, body = line.split(",", 1)
                name = name.strip()
            if ":" in body:
                rating_part, pos_part = body.split(":", 1)
            else:
                parts = body.split(None, 1)
                if len(parts) != 2:
                    sys.exit(f"{path}:{lineno}: cannot parse '{raw.strip()}'")
                rating_part, pos_part = parts
            try:
                rating = int(rating_part.strip())
            except ValueError:
                sys.exit(f"{path}:{lineno}: bad rating in '{raw.strip()}'")
            if not (1 <= rating <= 99):
                sys.exit(f"{path}:{lineno}: rating {rating} out of range 1-99")
            try:
                positions = sorted({normalize_pos(p) for p in pos_part.split()})
            except ValueError as e:
                sys.exit(f"{path}:{lineno}: {e}")
            if not positions:
                sys.exit(f"{path}:{lineno}: no positions given")
            players.append(Player(name, rating, positions, len(players)))
    if not players:
        sys.exit(f"{path}: no players found")
    return players


# ------------------------------------------------------- Hungarian algorithm

def hungarian_min(cost):
    """Jonker-Volgenant style Hungarian algorithm.
    cost: n x m matrix (n <= m). Returns list: row i -> assigned column."""
    n, m = len(cost), len(cost[0])
    INF = float("inf")
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)      # p[j] = row matched to column j (1-based, 0 = none)
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    assign = [-1] * n
    for j in range(1, m + 1):
        if p[j]:
            assign[p[j] - 1] = j - 1
    return assign


FORBIDDEN = 10 ** 6


def best_xi(formation_rows, players):
    """Optimal assignment of players to the formation's 11 slots.
    Returns (total, assignment) where assignment[slot_index] = Player,
    or (None, None) if the formation cannot be filled."""
    slots = [pos for row in formation_rows for pos in row]
    n, m = len(slots), len(players)
    if m < n:
        return None, None
    # maximization -> minimization; forbidden edges get a huge cost
    cost = [
        [
            (100 - pl.rating) if slot in pl.positions else FORBIDDEN
            for pl in players
        ]
        for slot in slots
    ]
    assign = hungarian_min(cost)
    chosen = []
    total = 0
    for si, pj in enumerate(assign):
        if pj < 0 or cost[si][pj] >= FORBIDDEN:
            return None, None       # some slot only fillable by forbidden edge
        chosen.append(players[pj])
        total += players[pj].rating
    return total, chosen


# ---------------------------------------------------------------- output

def print_pitch(name, formation_rows, xi, total):
    width = 64
    avg = total / 11
    print(f"--- {name}  |  total {total}  |  avg {avg:.2f} ---")
    i = 0
    for row in formation_rows:
        cells = []
        for pos in row:
            pl = xi[i]
            i += 1
            cells.append(f"[{pos} {pl.label()}]")
        line = "   ".join(cells)
        print(line.center(width))
    print()


def infeasible_reason(formation_rows, players):
    """Human-readable hint: which positions lack enough eligible players.
    (Necessary but not sufficient — a full check is the matching itself.)"""
    from collections import Counter
    need = Counter(pos for row in formation_rows for pos in row)
    lack = []
    for pos, k in sorted(need.items()):
        have = sum(1 for p in players if pos in p.positions)
        if have < k:
            lack.append(f"{pos} (need {k}, have {have})")
    return ", ".join(lack) if lack else "overlapping multi-position conflicts"


def main():
    ap = argparse.ArgumentParser(description="EA FC 26 best-XI solver")
    ap.add_argument("players_file")
    ap.add_argument("--formation", "-f",
                    help="single formation, e.g. '4-3-3' or '4-2-3-1 (2)'")
    ap.add_argument("--top", "-t", type=int, default=None,
                    help="show detailed XI only for the top N formations")
    args = ap.parse_args()

    players = parse_players(args.players_file)
    print(f"Loaded {len(players)} players from {args.players_file}\n")

    if args.formation:
        key = args.formation.strip().lower()
        match = [n for n in FORMATIONS if n.lower() == key]
        if not match:
            match = [n for n in FORMATIONS if n.lower().startswith(key)]
        if not match:
            sys.exit(f"Unknown formation '{args.formation}'. Available:\n  "
                     + "\n  ".join(sorted(FORMATIONS)))
        if len(match) > 1:
            sys.exit(f"'{args.formation}' is ambiguous: {', '.join(sorted(match))}")
        name = match[0]
        total, xi = best_xi(FORMATIONS[name], players)
        if total is None:
            sys.exit(f"{name}: cannot field a legal XI — missing: "
                     f"{infeasible_reason(FORMATIONS[name], players)}")
        print_pitch(name, FORMATIONS[name], xi, total)
        return

    results = []
    for name, rows in FORMATIONS.items():
        total, xi = best_xi(rows, players)
        results.append((name, rows, total, xi))
    results.sort(key=lambda r: (-(r[2] if r[2] is not None else -1), r[0]))

    print(f"{'#':>2}  {'Formation':<18} {'Total':>5}  {'Avg':>6}")
    print("-" * 38)
    rank = 0
    for name, rows, total, xi in results:
        if total is None:
            print(f" -  {name:<18} {'—':>5}  {'—':>6}   "
                  f"infeasible: {infeasible_reason(rows, players)}")
        else:
            rank += 1
            print(f"{rank:>2}  {name:<18} {total:>5}  {total/11:>6.2f}")
    print()

    shown = 0
    for name, rows, total, xi in results:
        if total is None:
            continue
        if args.top is not None and shown >= args.top:
            break
        print_pitch(name, rows, xi, total)
        shown += 1


if __name__ == "__main__":
    main()
