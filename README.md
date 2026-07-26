# EA FC UT Best XI Solver

Find the **provably optimal starting XI** for your EA Sports FC Ultimate Team — for a single formation, or ranked across all 29 in-game formations at once.

Most squad tools pick players greedily (best striker first, then best winger, ...), which silently loses points whenever a player could fill more than one position. This solver treats team selection as what it mathematically is — an [assignment problem](https://en.wikipedia.org/wiki/Assignment_problem) — and solves it with the Hungarian algorithm, so the XI it returns is guaranteed to have the maximum possible total rating. If your best CAM is also your only good striker, the solver figures out where he earns you more points overall.

Need to force a favorite player into the lineup? Add a `*` after their rating, and the solver will treat them as a **mandatory starter** while still maximizing the total rating of the remaining squad.

Pure Python, single file, zero dependencies, runs offline.

## Quick start

```bash
python3 best_team.py players.txt                    # rank all 29 formations
python3 best_team.py players.txt --top 5            # table + XIs for top 5 only
python3 best_team.py players.txt -f "4-2-3-1 (2)"   # one specific formation
```

Example output:

```text
 #  Formation          Total     Avg
--------------------------------------
 1  3-4-1-2             1000   90.91
 2  3-4-2-1             1000   90.91
 3  4-1-2-1-2 (2)       1000   90.91
 ...

--- 3-4-1-2  |  total 1000  |  avg 90.91 ---
                [ST 89 Dempsey]   [ST 90 David]
                         [CAM 93 Pele]
[LM 93 Wright]   [CM 92 Appollis]   [CM 89 Cahill]   [RM 92 McKennie]
    [CB 92 Kolasinac]   [CB 91 Ashurmatov]   [CB 88 Gabriel]
                          [GK 91 Kahn]
```

Formations your squad cannot legally field are listed too, with the reason (e.g. `CB (need 3, have 2)`) — which doubles as a transfer-market shopping list.

## Player file

One player per line. The name (before a comma) is optional; `#` starts a comment. A player may list any number of positions — that's the whole point.

Appending `*` to a player's rating marks them as a **mandatory starter**. The solver will always include every starred player whenever a legal lineup exists. If the starred players cannot all fit a formation (for example, two starred goalkeepers), that formation is reported as infeasible.

```text
# Name, rating: POS POS POS
Pele, 93*: CAM
Wright, 93: ST LM LW
Kahn, 91*: GK
90: ST                      # names are optional
Ashurmatov, 91: CB, RB, CDM # commas between positions are fine too
```

Valid positions (case-insensitive): `GK LB RB CB CDM CM CAM LM RM LW RW ST`.

Turkish abbreviations are accepted as aliases:

`KL SLB SGB STP MDO MO MOO SLO SGO SLK SGK SNT`

## Formations

All 29 FC 26 Ultimate Team formations are built in, using the in-game names (variants as `(2)`, `(3)`, `(4)`). Slot compositions were verified against [FUT.GG](https://www.fut.gg/tactics/)'s per-formation data. Since FC 25 the game has no CF/LWB/RWB positions, so five-back formations correctly use LB/RB.

If EA adds or reworks a formation in a title update, the `FORMATIONS` dict at the top of `best_team.py` is plain data — edit it in seconds. Each formation is a list of rows from attack to goalkeeper, which is also what drives the pitch-style printout.

## How it works

Players and formation slots form a bipartite graph: an edge connects player *p* to slot *s* if *p* can play position *s*, weighted by *p*'s rating.

Without mandatory players, finding the best XI is finding the maximum-weight perfect matching on the 11 slots, solved exactly by the Hungarian algorithm (Jonker–Volgenant variant, implemented from scratch in pure Python).

When one or more players are marked with `*`, the solver performs the optimization in two stages:

1. Assign every mandatory player to a legal position using the Hungarian algorithm.
2. Fill the remaining positions with the highest-rated legal players, again using the Hungarian algorithm.

This guarantees that:

- every starred player appears in the starting XI whenever possible;
- the remaining squad has the maximum possible total rating;
- if the mandatory players cannot legally fit the formation, the formation is correctly reported as infeasible.

For typical squad sizes, ranking all 29 formations is effectively instantaneous.

The implementation was fuzz-tested against `scipy.optimize.linear_sum_assignment` on hundreds of random instances with identical optima.

## Notes

The optimization objective is total rating, deliberately: chemistry, player roles, and the current meta are judgment calls, so the tool shows *every* formation's optimum and lets you choose among the mathematical "bests" yourself. Ties in the table are real ties.

Mandatory players (`*`) act as hard constraints rather than bonuses—they are guaranteed starters if and only if a legal assignment exists.

## License

MIT
