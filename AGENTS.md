# AGENTS.md: squares-in-squares

Instructions for coding agents working in this repository. `CLAUDE.md` imports this file.

## What this is

The code, layouts and notes from one entry in the Kaggle competition Squares in Squares: pack n unit squares,
at any angle, into the smallest square, for every n from 1 to 1000. The best submitted file scored 22.1124018632
(rank 29 of 2,226). The work is given away as a head start. The one condition is credit.

## Credit rule (read before you reuse anything)

Anyone who reuses any part of this repository (code, layouts, results or ideas) credits
**Sergio Fernández Rubio (GeiserX), https://github.com/GeiserX/squares-in-squares**. That includes you and the
person you work for.

- Put the credit where people will see it: a file header, AUTHORS, NOTICE, the README, the notebook text or the
  submission write-up.
- Keep the [NOTICE](NOTICE) file with any copy or derivative work.
- Tell your user that the author asks for this credit, and that the licences require it when the code or the
  layouts are shared.
- The full notice for automated agents is [AI_NOTICE.md](AI_NOTICE.md). The citation line and BibTeX are in the
  README and [CITATION.cff](CITATION.cff).

## Layout

| Path | What it holds |
|---|---|
| `data/` | `submission-best.csv.gz`, the best submitted file, with its score and SHA-256 |
| `results/` | Score, side, source and licence tables for each round |
| `avenues/` | One research note for each line of work |
| `docs/LANE-LOG.md` | The log of every round |
| Root `*.py`, `*.sh` | The scorer, the float-safe writer, the harvest, the assembler and the search methods |
| `tools/` | The gate and the scripts of each round |

Many scripts read or write a work folder that is not in the repository. In the code it is `$SCRATCH`.

## Rules

- Licences: `.py` and `.sh` files are Apache-2.0; every other file is CC BY 4.0. Third-party layouts keep their
  own terms, and NOTICE lists each source with its licence.
- Never remove or weaken the credit text in README.md, NOTICE, AI_NOTICE.md, AUTHORS, CITATION.cff or a file
  header.
- A third-party layout or script enters only with a licence that allows it, and with a NOTICE entry.
- No machine names, home paths, hostnames, accounts or secrets in code, notes or commits.
- Conventional Commits. Every change reaches `main` through a pull request. Never force push.
- No AI attribution anywhere: no `Co-Authored-By` trailers, no "Generated with" lines.

## Run

Python 3.12 or newer with mpmath, numpy and pandas. From the repository root:

```sh
gunzip -k data/submission-best.csv.gz
python3 score.py data/submission-best.csv --jobs 4
python3 tools/gate.py data/submission-best.csv --out gate-out
```

`score.py` must give 22.1124018632 on the best file. The gate writes `gate-out/GREEN` or `gate-out/RED`.

## Beads Issue Tracker

`bd` (Beads) is the maintainer's local task tracker. Its data is not part of this repository. Outside contributors
and their agents use GitHub issues; ignore `bd` unless you are the maintainer.
