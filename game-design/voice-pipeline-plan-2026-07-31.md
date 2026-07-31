# The voice pipeline: what went wrong today, and the plan

Jafar, after the sixth fix in a row: *"you keep fucking up. think, plan and
build properly before throwing more spaghetti at the wall."* Correct. This is
the think-and-plan, written before any more code.

---

## The root cause is not any of the six bugs

Today produced six real defects, each found by shipping something broken:

| | what | how it was found |
|---|---|---|
| 1 | age filtered out every middle-aged brief | 15 CI runs, then a strided diagnose |
| 2 | one character banked the same speaker N times | **Jafar listened and told me** |
| 3 | the standalone page dropped the speaker ids | a browser check, seconds before publishing |
| 4 | `rm -rf voice-candidates/*` deleted 16 characters | after it had happened |
| 5 | a targeted run re-issued Lena's voice to a crowd slot | checked by luck before publishing |
| 6 | the budget stops at the same row every run | reading the log after a zero-clip run |

Every one is a different subsystem. Fixing them one at a time was always going
to produce exactly this: a day of "fixed it" followed by a new surprise.

**The actual root cause is that I have no way to ask the corpus a question.**
Every fact about VCTK — who is in it, what accents, which speakers are still
free, where they sit in the stream — has been *inferred from the side effects
of a forty-minute fetch*. HuggingFace is blocked from the dev container
(`403 Forbidden` through the proxy), so the only instrument available has been
"run the whole thing and see what falls out".

That is why each answer arrived as a surprise, and why the estimates were
wrong: I was doing experiments where I should have been doing a lookup.

---

## The invariants this pipeline must hold

Written down so they can be checked deliberately rather than discovered.

| # | invariant | enforced by | status |
|---|---|---|---|
| 1 | every candidate under a character is a distinct speaker | `w["used"]` | ✅ |
| 2 | no speaker appears under two characters, **across runs** | `claimed` seeded from the page | ✅ |
| 3 | a run never removes clips for characters it did not fetch | scoped `rm`, per-character guard | ✅ |
| 4 | the page shows the speaker id | `build_page`, builder assertion | ✅ |
| 5 | characters not re-fetched keep their rows on the page | `keep_existing` + full-cast render | ✅ |
| 6 | a pick's audio survives any future run | `game-design/picked-clips/` | ✅ |
| 7 | **a run that fills none of its targets must fail** | — | ❌ **gap** |
| 8 | the fetch can reach speakers a previous run did not claim | `--skip-rows` | ⚠️ untested |
| 9 | a code change never starts a corpus fetch | `if: workflow_dispatch` | ✅ |

**Invariant 7 is open and was found by reading the workflow, not by breaking
it.** The verdict fails when the *total* clip count is zero. A `--who` run for
three characters that banks nothing still sees 53 clips from everyone else and
exits green. The last run did exactly that.

**Invariant 8 is the one that matters and cannot be verified from here.**
`ds.skip()` may jump cheaply or may stream through everything it skips. I do
not know, and guessing is what got us here.

---

## The plan

### Phase 0 — build the instrument (one cheap run)

An `--inventory` mode that reads **only the metadata columns** from the parquet
export — `speaker_id, gender, accent, age` — and never touches the audio
column. Column projection on parquet means the ten gigabytes of audio are never
read. It emits the complete speaker table, and the first row offset each
speaker appears at, as `tools/voice-fetch/vctk-speakers.json`.

This is the thing that has been missing all day. It runs once, and afterwards
every question below is answered locally in seconds instead of in forty
minutes.

Defensive, because it cannot be tested here: if the parquet route fails it
falls back to metadata-only streaming and **says which path it took**. It is a
separate job that writes one JSON file and cannot touch a clip.

### Phase 1 — decide from the table (no run at all)

With the table committed, compute locally:

- how many English men and women VCTK actually contains
- which of them the 53 cast speakers have already used
- therefore whether `crowd_m3`, `crowd_f1`, `crowd_f3` are fillable **at all**
- and if so, the exact speakers and the row offset they live at

If the honest answer is *there are not enough English speakers left*, that is a
finding, not a failure, and the decision is Jafar's:

- accept a smaller crowd pool (3 voices instead of 6)
- let the crowd pool reuse a principal's voice deliberately — the least bad
  option is a voice belonging to somebody who rarely speaks
- widen the crowd briefs to any accent, which for background voices is
  arguably *more* correct in a port town
- a different corpus, which is a purchase and therefore Jafar's call

### Phase 2 — one precise fetch, only if Phase 1 says it can work

Named speakers, known offset. Not a sweep.

### Phase 3 — close invariant 7

A `--who` run that fills none of its named characters fails the job. Currently
it reports success because other characters' clips are still on disk.

---

## What is deliberately NOT being done

No more blind fetches. The 70-minute skip-ahead run dispatched before this
document was written has been cancelled — it was the same gamble as the four
before it, with a bigger number attached.
