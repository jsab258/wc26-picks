> **STATUS — LOG, 2026-08-26. NOT CURRENT after the next change to
> `ledger/verify.py` or `tools/`.** Tier-2 audit, read-only. Findings, never
> fixes. Written up by the resident from the auditor's output — the auditor
> has no Write tool and the brief wrongly asked it to write the file.

# Denominator sweep — is the printed denominator the set examined?

## Coverage, stated first

**89 executable tools** under `tools/`; the 7-lint family was out of scope
(swept separately). **24 run, 18 read.** **51 check functions** in
`verify.py`'s `main()` tuple: **all 51 return-strings swept mechanically, 16
bodies read.**

**Not reached, named:** the `voice-live/` (33), `voice-fetch/` (6),
`voice-gen/`, `imagegen/`, `mixamo-pick/`, `citypack/`, `props/` and
`tts-benchmark/` subtrees — ~50 files, mostly one-shot fetchers rather than
repeated checkers — plus `gates.py`, `gate-detail.py`, `frame-drift.py`,
`template-sync.py`, `ref-bench.py`, `decal-ink.py`, `prop-dimensions.py`,
`body-proportions.py`, `clip-motion.py`, `hang-report.py`, `landed.py`,
`report-frame.py`, `verdict-read.py`, `ci-checks.sh`, `sim-shots-*.sh`.

---

## 1 — SEVERE. Six footer strings are byte-identical across 259 landed commits, and four discard a denominator that already exists

| footer fragment | landed identical | the denominator one process boundary away |
|---|---|---|
| `0 lint errors` | **259/259** | `lint-usings.py` prints `checked 185 files`; the capture is discarded |
| `0 shadowed Core types` | **259/259** | `lint-shadow.py` prints `(285 type(s), 88 Game file(s))`; verify's string is a hardcoded literal |
| `0 stale anchors` | **259/259** | none anywhere — the walk covers 22 break specs / 205 anchors |
| `shape ok (clips, barks, manifests)` | **259/259** | none — and see finding 2 |
| `voice cast ok (0 uncast principal(s))` | **259/259** | `0 uncast` is the FINDING, not the denominator |
| `clip picker ok` | **259/259** | no number of any kind |

**The contrast is inside the same footer line, which is what makes this
checkable rather than arguable.** Checks that ship a live denominator MOVE:

    0 shape errors (177 files) x10 -> (178) x3 -> (179) x3 -> (180) x144 -> (181) x38
    docs 57/57 x9 -> 59/59 x212 -> 60/60 x2 -> 103/103 x1
    clips ok (62 read) x2 -> (64 read) x251 -> (67 read) x6

**A moving series is a denominator attached to something real. A string
unchanged in 259 commits is a claim with nothing behind it** — `0 stale
anchors` and `clip picker ok` would print identically if `ledger/breaks/`
were empty or the picker selftest had zero cases.

## 2 — SEVERE. The manifest check reports `ok` having examined ZERO paths

`shape-check.py:249`. Measured today:

    top-level game-design/*.json walked: 4  (of 7 — glob, not rglob)
    string values seen: 12,345 ; path-shaped: 1 ; CHECKED: 0
    dropped for containing a space: 1
    arithmetic: 0 checked + 1 dropped = 1 path-shaped of 12,345 in 4 of 7 files

The one path-shaped string is prose, correctly dropped. The tool is honest at
its own layer — it prints `(0 checked)` — and **`verify.py:1016` compresses it
to `shape ok (clips, barks, manifests)`, so the word "manifests" is a claim
over zero examined paths, repeated in 259 commit messages.** The three
unwalked `.json` (one literally `voice-conds/manifest.json`) contribute 0
path-shaped strings today, so widening changes nothing now — **the fault is
that nothing says the walk stopped at one level.**

## 3 — HIGH. 48 of 50 truncating red-path messages carry no count

The known `1 finding of 9` is not one site.

    red-path messages that truncate: 50
      carrying a count:               2  (lines 642, 3298)
      carrying NO count, no (+N more): 48

`verify.py:1383` keeps four names and drops the number, so a run losing 4 keys
and one losing 40 print the same line — while `verdict-keys.py` underneath
already prints `{len(missing)} measurement(s) STOPPED BEING REPORTED`.
**CLAUDE.md's own `| head -3` incident, 48 times, inside the enforcement
tool.** The two sites that already carry a count are the accepting fixtures.

## 4 — MEDIUM. Three checks PASS when nothing was measured

`runs_map_to_commits()` returns True on "no runs directory yet" / "no run
files yet" while its green branch knows how to print `{hit} of {n}`.
`backend_compiles()` is the model and is CORRECT: its skip announces itself
in the footer string.

## 5 — MEDIUM, latent, and the discipline here is the point

`slopcheck` examines **336 of 2,604** bark lines; 18 pair-slots (2,268 lines)
are skipped by a comment claiming they are "the same lines twice" — **false as
written, checked: the two halves differ in all 2,268.** The auditor then
suspected its own reading and measured the overlap:

    distinct utterances in pair slots: 266 ; also in the examined set: 266
    NEVER EXAMINED: 0

**So the skip is lossless today and this is not a wrong conclusion.** It is a
filter whose 87%-of-lines bite is unannounced and whose safety rests on an
invariant nothing checks.

## 6 — MEDIUM. `lint-unreached` misnames both what it counted and where it looked

    files walked: 94 = 88 Game + 6 Assets/Editor   (all 94 called "Game-layer")
    declarations matched: 426 ; dropped as Unity lifecycle: 13 (silent)
      collapsed by setdefault (name collision): 62 (silent) ; distinct: 351
    arithmetic: 351 + 13 + 62 = 426

The repair already exists in the same file: the 2 workflow exclusions ARE
printed by name; the 13 Unity ones are not. One idea, two implementations.
Bounded: it is a reading, not a gate, and the numerator is unaffected.

## 7-8 — LOW, latent

`verdict-keys`'s `OPTIONAL` set can suppress up to 12 GONE reports with no
line saying so (**suppresses 0 today**; on a run where the clip-sheet family
does not render it would print `0 missing` while 11 required measurements are
absent). `lint-namespace` skips 2 of 764 (file, segment) pairs silently — the
same shape that was 19x in `lint-static`.

## Checked and CLEAN, with counts, so a short list and an incomplete audit do not look alike

`verdict-characters.sh` (announces both caps, prints `wc -l` when it finds
nothing), `queue-check.py`, `gamecheck.py` (allow-list FAILS when an entry
stops matching), `slopcheck`'s report layer, `verdict-keys.py`'s summary,
`lint-filetype.py` (trap set printed BECAUSE it is the denominator),
`reach-check.sh`, `verdict-emit-dupkeys.py`, `attribution-check.py` (asserts
its own coverage claim), `verify::backend_compiles`, `verify::tools_tracked`
(walks references transitively), `runs_map_to_commits`'s green branch.
`ps-check` is a model: *"NO POWERSHELL — nothing was parsed, which is not the
same as nothing being wrong."*

**One unclassified:** `docs-check.py:125` prints `N/N clean` where the
denominator counts DOCUMENTS and the numerator subtracts failing CHECKS (155
ran today). Harmless green; in red, `3 problem(s)` reads as three documents.
Whether it has ever misled anyone needs the incident record, not the code.

## What to send next, in order

1. **`tools/gates.py`** — unswept, and it is the instrument every other
   reading is checked against. A denominator fault there corrupts the
   evidence base itself.
2. **`verify.py::director_cadence`** — gates every commit; its selftest
   fixture count (38->53) is a printed number nobody has checked against what
   it walks.
3. **`verdict-read.py --spaced`** — forwarded ungated as "39 of 110"; a live
   series worth reading before it becomes a bound.
