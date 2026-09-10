# 243. Empty the D18 baseline: the content pass over 197 hits in 121 distinct texts

STATUS: READY, 2026-09-10. Filed by the resident because the lane that built the
gate could not write here. The gate landed clean and DID NOT FIX ANY CONTENT, by
instruction: every existing violation sits in a dated baseline so the gate can
ship green without a content pass blocking every commit.

## The number and where it is

`tools/content-gate.py` reports `hitsNew=0 hitsBaselined=197 staleBaseline=0
stringsScanned=9780 filesOpened=32 declaredAbsent=2`. 197 hits over 121 distinct
texts, stamped `2026-09-10`, keyed on `file|rule|sha1(text)[:12]`.

The key matters for this task. Editing a baselined line by ONE CHARACTER makes
it new writing and the gate fires. Deleting a line without removing its baseline
entry fails with exit 4, stale baseline. So this pass is: fix the text, remove
the entry, in the same change, every time.

By channel, each with its denominator:

| channel | filesExamined | stringsExamined | hits | distinctTexts |
|---|---|---|---|---|
| speech | 7 | 8430 | 157 | 99 |
| prompt | 10 | 319 | 36 | 12 |
| brand | 1 | 48 | 0 | 0 |
| spec | 5 | 964 | 28 | 22 |
| veto | 9 | 19 | 1 | 1 |

## THE 65 AND THE 2 ARE THE SAME THING, AND THEY NEED DIFFERENT PLANS

`game-design/barks.json` carries 65 of the 157 speech hits. They are TWO
authored lines, repeated: `Core/StreetVoice.cs:203` "I'd want it from somebody
sober" and `:227` "I've got children. Talk about the weather."

12 rendered WAVs are keyed to their exact text. Rewording either line ORPHANS
those recordings and needs a re-render on the PC. So this is not a text edit, it
is a text edit plus a render job plus a check that no manifest still points at
an orphan. Do it in that order and print the orphan count before and after.

The rest of the speech hits are ordinary text edits.

## The rest, by group

- **Dialogue bank `pub-regular-v1.json`**: pr-001 the mild, pr-003 pints and a
  bitter, pr-006 stout, pr-011 off-licence, pr-013 a round, pr-028 betting shop,
  pr-037 Your round and drinks bitter, pr-038 pint, pr-046 dog track. This bank
  was authored for a pub that D17 has since voided, so it is the one item here
  that may be a REWRITE rather than an edit. It waits on the written case for
  what people do inside a pub with no drinking, which is Jafar's ruling 6.
- **Cast cards**: viktor/secret and perica/need gambling debts, katja a betting
  slip, filip drinking on shift, tanja whiskey, magda three times plus zdenka,
  nada and irena wine. Each is a character motive built on a thing D18 removes,
  so each needs a REPLACEMENT motive, not a deletion. A cast card with its
  secret cut is a character with no engine.
- **The three no-children hits, which are D18 and not D17**: petra "kids",
  vesna "two hundred babies", vinko "my teenage helper". These are not about
  drink and they are the sharper half of the rule.
- **`production/specs/dialogue-pub-regular-v1.md:26`** instructs writers to use
  beer. A spec that tells the next writer to violate the rule regenerates the
  problem, so fix this one FIRST or the pass has to run twice.
- Remaining: `atlas-02/DELIVERY.md` 19, `tier2-batch-1.json` 17 in each of two
  copies, `imagegen/prompts.json` 4, the fairview sheet files 4, bark-names and
  barks-manifest 2 each, fairview DELIVERY 2, compare-hook 2 each, fairview-pair
  2, copper-row 1, fairview-furniture 1.

## Two things that are NOT in this pass

- **`hitsNew=0`.** Nothing written today violates the rule. This backlog is
  entirely pre-D18 text.
- **The 11 rules the gate cannot enforce.** `--enforceable` prints
  `mechanical=7 notMechanical=11 total=18`. Cruelty as spectacle, killing being
  rare and remembered, racism as fact but never voiced, never rewarded, drugs
  off-screen and never a player verb, religion never mocked and never a
  mechanic, police never a thesis, and what a rendered picture actually shows.
  No word list reaches any of those. They are read by a person or not at all,
  and pretending otherwise is the false-green this project keeps catching.

## Done looks like

`tools/content-gate.py` reports `hitsBaselined=0` with the same
`stringsScanned` denominator or a larger one, `hitsNew=0`, `staleBaseline=0`,
and the `BASELINE` block in the tool is empty with its comment intact. The orphan
WAV count is 0 and printed. No entry was removed without its text being fixed:
prove that by running the gate once with the baseline emptied BEFORE the edits,
and reading the count it then reports as the work list.

## Dependencies and risk

The pub bank waits on ruling 6's written case. Everything else can start now.
Risk: the baseline is a promise, and a baseline nobody empties is just a
permanent exemption with a date on it. That is what this item exists to stop.
