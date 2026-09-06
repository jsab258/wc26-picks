# Ruling: queue 113, the model does not adjudicate. Approved for commit, with four dictated one-liners and three items awaiting numbers

> **STATUS: LOG, 2026-09-06.** Director ruling at spawn 2026-09-06T05:53:25Z
> on the systems-builder's close of queue 113 (`ledger/Assets/Scripts/Core/
> Adjudicator.cs`, `Core/IntentRouter.cs`, `Game/IntentBridge.cs`,
> `CoreTests/Program.cs`, `Adversary/Program.cs`, `production/queue/113`).
> NOT CURRENT once the commit lands and section 9 is applied; from then the
> files are the reading copies and this is the record of why.

VERDICT: APPROVED FOR COMMIT. The Core change is sound, the rejecting case
was watched red against the restored old code, and the fix is the best
available shape rather than the first working one. Four one-line corrections
are dictated in section 9; none blocks the commit, and each is small enough
for the resident's hand under the one-line allowance or for a queue number if
the resident prefers. Three adjacent findings need numbers (section 10) and I
am asking for them rather than choosing.

Mandatory Core review, unchanged by the 2026-09-06 narrowing. Documents in the
same tree (CLAUDE.md, NOW.md, budget.md, queue files 113 to 120) were read for
context and are noted in section 8; they commit on the resident's read and
are not ruled on here.

## 0. What was read, and what was not run

Read in full: `Adjudicator.cs` (211 lines, the new file); the builder's
`Adjudicator.old.cs` in the shared scratchpad (137 lines, the file the builder
reports as `git show HEAD:`); `IntentRouter.cs` (592 lines); `IntentBridge.cs`
(394 lines); `CoreTests/Program.cs` lines 4060 to 4405 and the call sites at
113 to 121; `Adversary/Program.cs` lines 30 to 90, 190 to 280, 360 to 540;
`DialogueUI.cs` lines 1990 to 2126; `Wallet.cs`; `GameTime.cs` lines 1 to 60;
`Gossip.cs` lines 525 to 555 (`DayCircleHeat`); `GameController.cs:288`;
`production/queue/113` and `114`; `legacy/design-doc.md` lines 670 to 694;
`production/NOW.md` lines 220 to 268; the constitution; the builder's two red
captures `red.txt` and `red-final.txt`; `verify-footer.before-113`;
`.claude/agent-log.tsv` lines 268 to 276.

Counted: studio-director rows in the log, 59; the newest is line 275,
`2026-09-06T05:53:25Z`, line 276 is empty, and 0 of 32 decision files carry a
stamp matching `spawn=2026-09-06`, so that row is unclaimed and is this
ruling's row. Call sites of `Adjudicator.Resolve`: 3 (`DialogueUI.cs:2110`,
`CoreTests`, `Adversary:224`). Call sites of `Effects.AltersState`: 3
(`Adjudicator.cs:101`, `Adversary:225`, `Adversary:437`). `Binds` and
`Evaluate` are private and reached only from `Resolve` and from each other.
`ledger/.verify-footer`: absent, as the brief says.

NOTHING WAS RUN. This spawn has no shell. The 4291 CoreTests, 94 adversary
checks and the exit codes are the builder's, read from two captures and one
footer; section 11 makes the resident print them again before the commit. The
arithmetic on the deltas is mine and checks: 4276 to 4291 is +15, and the new
battery has 13 checks (1+1+1+1+1+6+1+1) while the repaired loop gains 1 (the
eighth check) and 1 (the summary); 84 to 94 adversary is +10, and each of the
two new families carries 5 `Require` calls.

PREMISE CHECK, CLAUDE.md section 0 and constitution law 2: this change is
the law itself. "Classification, not adjudication. LLMs choose from closed
sets assembled from live state; deterministic Core computes every outcome the
player feels." The hole was that the closed set for `check` was a set of
NAMES, and membership in a set of names is not the same boundary as
membership in a set the game built from live state. Nothing purchased, no
licence entry, no reference bar cited. Late-analog framing untouched.

THE SPLIT FOR THIS SPAWN: game 1, studio 0, basis spawns, points unmeasured.

## 1. Question 1: is `Floor` a ruler or a taste

The claim under test: every number in `Floor` is the far end of a range the
code declares, not a judgement. I checked each field at the site that
enforces it, not at the comment that describes it.

| Field | Floor | Where the bound is enforced | Verdict |
|---|---|---|---|
| Clean, Dirty | 0 | `Wallet.cs`: constructor `Max(0)`, `Restore` `Max(0)` on both, `Spend` refuses below available, `Earn*` only adds | hard end of a count |
| Crew | 0 | `IntentBridge.cs:276`, `Enumerable.Count` of `ActiveCrew` | hard end of a count |
| Hour | 0 | `GameTime.FromTotalMinutes`: `rem / 60` with `rem` in 0..1439 | the smallest value the clock produces |
| Standing | -1.0 | `Empire.cs` 178, 181, 195, 209, 313, 318, 322 and `Economy.cs` 207, 216, 235, 357 all clamp to -1..1 | declared end, enforced at every write except one (below) |
| Heat | 1.0 | `Gossip.cs:549-554`: noisy-or of rumour confidences, `1 - prod(1 - c)`, which cannot exceed 1 for c in 0..1 | declared end, by construction |
| HoldsHook | false | boolean | the refusing value |

So the claim holds. Two nuances, neither of which changes the verdict:

The comment at `Adjudicator.cs:55-57` calls hour 0 "the day not yet
started". The game day starts at 06:00 (`GameTime.cs:7-8`), so hour 0 is the
small hours, not the morning. The NUMBER is right for the comparison the Hour
check makes (`state.Hour < amount`, so the smallest hour is the hardest
player); the flavour is off. Not dictated; the next person to touch the file
corrects it.

`Empire.cs:1175` restores `arm.Standing` from a save without a clamp. This is
pre-existing and is not a Binds fault: Binds never reads live state, so a
live value outside -1..1 cannot make a formality pass. It belongs on 114's
inventory as a save-path row, not here.

THE DIRECTION OF EVERY DRIFT IS THE THING TO WRITE DOWN. If a real range is
WIDER than the declared one, Binds over-refuses (a requirement that could
have bitten some player is called a formality); that fails closed and is
visible in play as "saying it doesn't make it so" on an honest line. If a
real range is NARROWER in play than declared (heat never reaches 1.0 in a
real game; hours 0 to 5 are rarely played), a requirement pinned just inside
the declared end binds at the Floor and never in practice. That second case
is exactly the "how hard" residue of section 7, and it is the reason the
next rung is a printed series and not a cleverer Floor.

THE ONE WAY FLOOR BITES LATER, and the condition under which it stays a
ruler: Binds is sound for requirements that are MONOTONE in each field with
the hardest value at the Floor. Every check in the vocabulary today is (a
threshold in one direction, or a boolean). A future check shaped as a window
or a band ("between nine and five", "standing near neutral") could refuse the
Floor player while being met by everyone else, and Binds would let it carry
an effect. Both existing loops would stay green (it refuses `broke`, it
passes `rich`). So the standing condition, recorded here and to be carried
into 114's inventory as a column: A NEW CHECK MUST SHOW THAT ITS HARDEST
STATE IS THE FLOOR, or ship its own binding proof.

Ruled: `Floor` is a ruler built from declared and enforced bounds. It is not
a tuning value and may not be edited to make a test pass.

## 2. Question 2: reason (b), checked on the old text

The builder's load-bearing claim is that banning the word `none` at the
router would have left `cash:0`, `dirty_cash:0`, `crew:0`, `hour:0` and
`heat:100` doing the identical job, because the model also supplies the
amount. I checked this on `Adjudicator.old.cs`, not on the builder's
description of it:

- `case Checks.Cash`: `cost = Math.Min(amount, 500)`; refuses only if
  `state.Clean < cost`. At amount 0, `Clean < 0` is false for every wallet
  the code can produce. PASSES EVERYBODY.
- `case Checks.DirtyCash`: same shape. PASSES EVERYBODY.
- `case Checks.Crew`: refuses only if `state.Crew < amount`. At 0, never.
- `case Checks.Hour`: refuses only if `state.Hour < amount`. At 0, never.
- `case Checks.Heat`: refuses only if `state.Heat * 100 > amount`. At 100,
  never for heat in 0..1 (and 900 is the same hole with a bigger number).

Five members of the vocabulary besides `none` had a setting at which no
player alive could fail them, and the model chose the setting. So the two
shapes the brief offered were both inadequate: "none stops being accepted"
leaves five doors open, and "none routes to a check that can still refuse"
leaves the same five open plus whatever that check is at its own vacuous
amount. The builder was right to reject both and to state the rule at the
level of the PROPERTY (an effect that writes travels only on a requirement
that could have refused it) rather than the WORD. This goes in the record
plainly: THE OBVIOUS FIX WOULD HAVE SHIPPED THE SAME HOLE UNDER FIVE OTHER
NAMES.

## 3. Question 3: the red proof

The test is `TestModelCannotChooseAnUnrefusableCheck`, called from `Main` at
line 114 (call-site grep, rule 6). It builds the reply as a JSON string in
the exact shape `BuildPrompt` asks the model for, runs it through
`IntentRouter.Validate`, and hands the resulting `Intent` to
`Adjudicator.Resolve`. That IS the model's path in Core: `RouteAsync` does
nothing with the reply except `return Validate(response.Text, ctx)`
(`IntentRouter.cs:348`). What the test does not and cannot reach is the Game
half, `DialogueUI.cs:2110-2112`, where `if (verdict.Passed) ApplyNovel(...)`
gates the write; CoreTests cannot compile Unity. The test covers that gap by
asserting the refusal hands back `Effect == Nothing`, `Magnitude == 0`,
`CashSpent == 0` (line 4354), so even a Game layer that forgot to read
`Passed` would switch on `Nothing` and spend 0. I read `ApplyNovel` and
confirmed: no case for `Nothing`, spend guarded by `> 0`.

The red captures: `red.txt` ends at line 853 with `FAILED: check:none cannot
carry a change to state, however rich the player is` and a detail containing
an em-dash; `red-final.txt` ends at line 854 with the same failure and the
detail `PASSED, and the model is adjudicating again`, which is the current
test text at line 4353. Two captures, the second after the wording was made
lawful, both red at the same check. Against `Adjudicator.old.cs`, the
reasoning matches the capture: `Validate` parses `check:none` and
`effect:standing_up`, old `Resolve` hits `case Checks.None: break;` and falls
to `Pass`, so `Passed` is true and the check fails with exactly that detail.

What I could not verify: that `Adjudicator.old.cs` is byte-identical to
`HEAD:`. The builder reports an md5 check; section 11 has the resident print
it. It IS consistent with every independent citation of the old file (queue
113 quotes lines 62 to 63; NOW.md cites `Adjudicator.cs:62`; both match).

## 4. Question 4: the false certificate, and the two neighbours

The skip is gone. `TestClosedVocabulariesAreHandled` now runs the
can-refuse loop over `Checks.All` (8 of 8), counts refusals, and asserts
`refused == Checks.All.Length` with the denominator in the detail (lines
4118 to 4133). Note that `broke` (line 4113) is field-for-field the Floor, so
that loop and Binds are one measurement taken twice; the pair with the
can-pass loop on `rich` is what makes it non-vacuous (a Binds that refused
everything would fail the first loop).

THE TWO NEIGHBOURS, stated precisely, because the brief's framing ("three
cases certifying nothing") is half right. The magnitude-clamp loop (now
lines 4185 to 4195) and `TestAdjudicator`'s `wild` case (now 4269 to 4273)
ran on `Checks.None`. UNDER THE OLD ADJUDICATOR THAT WAS NOT VACUOUS: `none`
passed, `Pass()` clamped, the bound was exercised. They WOULD HAVE BECOME
vacuous the moment `none` started refusing, because a refusal reports
`Magnitude 0`, which satisfies `0 <= m <= 0.15` without the clamp running.
The builder caught that consequence of its own fix, moved both onto a check
`rich` meets (`Cash` at 50, `Hook` held) and added `Passed` to both
assertions.

So the finding about our tests is: ONE false certificate (the skip), plus
TWO clamp assertions that had no `Passed` guard and could therefore be
satisfied by any refusal's default. The second is a rule 5b shape (a guard
never watched on the case it should pass) and is worth a line in the
measurement casebook; it is not a second and third instance of the first.

Residual I could not check without a shell: that the old assertions lacked
`.Passed`. Section 11 has the resident read the two hunks.

## 5. Question 5: the adversary control

Family `novel, cannot refuse` (`novelReachesState = false`, 8 forms, all
with an effect drawn from `AltersState`) requires `reachedState == 0`.
Family `novel, a real requirement` (`novelReachesState = true`, 7 forms
`Generous` meets) requires `novel > 0 && reachedState == novel`.

Could both pass for one reason? No. A `Resolve` that refused everything
passes the first and fails the second (0 of 400). A `Resolve` that passed
everything fails the first (400 of 400) and passes the second. A `Validate`
that returned speech for everything passes the first with `state=0/0` and
fails the second on `novel > 0`. The two families demand OPPOSITE outcomes
from the same code path on the same fixture, which is what a control is.
And against the old adjudicator the first family reads `state=400/400`: all
eight forms pass the old switch, by the same arithmetic as section 2.

One gap, non-blocking: the first family's `Require` does not pin `novel ==
rounds`. If that family's generator stopped producing parseable novel JSON,
the gate would pass on `state=0/0`. The printed line shows the denominator,
so a reader would see it; the gate would not. Dictated in section 9.

One overclaim, non-blocking: the comment on `Generous` (`Adversary:424-425`)
says "Every field is the far end of its declared range". For Standing,
Heat, Hour and the hook that is true. For Clean, Dirty and Crew there is no
declared top; 10000, 10000 and 9 are simply larger than any amount the
families name (cost is capped at 500; crew asks for 1). The fixture is fine.
The sentence is not, and it matters because section 1 rests on the
distinction between a bound the code declares and a number somebody chose.
Dictated in section 9.

## 6. `Floor`, `Generous`, `rich`, `broke`: four names for two fixtures

`broke` in CoreTests equals `Floor`. `rich` in CoreTests equals `Generous`
in Adversary. That is acceptable today (the tested layer owns its fixtures)
and worth one sentence here so nobody later "fixes" one of them and leaves
the other, or reads them as four independent measurements.

## 7. Question 6: what the builder left undone, and where each goes

(i) THE MODEL STILL CHOOSES HOW HARD. `cash:1` binds (the Floor cannot pay
£1) and barely constrains anyone; `hour:1` binds and never in practice past
one in the morning. Binds answers "could anybody in the declared range fail
it", not "does anybody in play". A floor price, a floor hour, a floor heat
would each be a bound, and rule 2 says a bound needs a printed series first:
the distribution of wallets, hours and heat in real runs, and the amounts
the model actually names. The builder was right not to invent the numbers.

WHERE IT WENT: the brief says the builder put this in queue 114's trap
section. I read `production/queue/114` in full (43 lines) and grepped
`production/` and every `.md` in the tree for `how hard`, `floor price`,
`cash:1`, `chooses how`: NOT PRESENT. The record claims a thing the tree does
not contain. The note is dictated in section 9 for the resident (114 is a
document and is the resident's), and the follow-on item that prints the
series and sets the floors needs a number: section 10, item A.

(ii) THE VOCABULARY GREW A MEMBER THE DESIGN NEVER SANCTIONED.
`legacy/design-doc.md:688-690` lists "cash, dirty cash, standing, a hook on
a person, crew, hour of day, heat". No `none`. `ledger-v2/` says nothing
about the router at all (0 matches for `novel action`, `intent router`,
`IntentRouter`, `Adjudicator`), so the legacy paragraph is the only design
statement there is. RULED: `none` is sanctioned, with exactly the meaning the
code now enforces: a requirement that may carry only an effect that changes
nothing. The vocabulary of record is `Checks.All` in `IntentRouter.cs`; the
legacy paragraph gets a one-line opportunistic correction, dictated in
section 9, and is not rewritten.

## 8. Findings beyond the brief

These are adjacent, not asked (rule 11). None blocks. Each needs a number
or a row on 114's inventory; I am asking, not allocating.

(a) `novel` + `none` + `nothing` SWALLOWS THE PLAYER'S LINE. `DialogueUI.cs:
2002-2008`: when `TryRouteAsync` returns true the method returns before
`host.SayAsync(text)`, so the NPC never answers. For a novel action that
moved nothing, the player gets `NovelLine`'s default, "It goes the way you
meant it to", instead of the person in front of them replying. That is a
game-feel question in the register Jafar set ("exceptionally good from a
game feel point of view"), and the honest options are: degrade `none/nothing`
to speech so the conversation engine answers; or keep it and author the
narration. Section 10, item B.

(b) NARRATION CLAIMS MORE THAN THE SIM DID. `ApplyNovel` skips the standing
and attention writes when `ArmFor` is null (`IntentBridge.cs:324-333`), and
`NovelLine` still says "It lands". Pre-existing; a rule 4 shape. 114
inventory row or item B's sibling.

(c) A COST ON AN EFFECT OF NOTHING. `cash:200` with `effect:nothing` passes
(Binds is not consulted for `Nothing`, and the cash check is a real
requirement), and `ApplyNovel` spends the £200 for no effect. The requirement
CAN refuse, so this is not the 113 hole; it is money leaving on the model's
say-so with nothing bought, which is squarely 114's question ("every field
that arrives from model JSON and can influence state"). 114 inventory row.

(d) `Empire.cs:1175` restores `Standing` unclamped. Section 1. 114
inventory row, save path.

(e) The documents in the tree. NOW.md lines 224 to 268 state the P0 order
and the review narrowing consistently with the brief. Queue 114 is
consistent with this ruling except that it does not yet carry the how-hard
note (section 7). Not ruled on.

## 9. Dictated one-line edits

The resident may hand-apply these under the one-line allowance, or queue
them; either way they are non-blocking. Quoted text is exact.

9.1 `ledger/Adversary/Program.cs`, the comment ending at line 425. Replace
the sentence `Every field is the far end of its declared range
(AdjudicationInput), not a tuned number.` with:
`Standing, Heat, Hour and the hook sit at the far end of their declared
ranges (AdjudicationInput); Clean, Dirty and Crew have no declared top, so
10000, 10000 and 9 are simply larger than any amount a family here names
(cost is capped at MaxNovelCost, and crew is asked for 1).`

9.2 `ledger/Adversary/Program.cs`, lines 240 to 243. Change
`Require(reachedState == 0,` to `Require(novel == rounds && reachedState == 0,`
and append to that message, before the closing parenthesis:
`; {novel}/{rounds} parsed as novel`.

9.3 `legacy/design-doc.md`, lines 688 to 690. Replace the sentence beginning
`So the router names a **requirement**` with:
`So the router names a **requirement** from a closed vocabulary, cash, dirty
cash, standing, a hook on a person, crew, hour of day, heat, or none (which
may carry only an effect that changes nothing; queue 113), and the game
evaluates it, applying one **effect** from a closed vocabulary with clamped
magnitude.`
This also removes two em-dashes from a legacy line, opportunistically.

9.4 `production/queue/114`, appended to "The trap", for the resident as the
owner of the document:
`AND DO NOT COUNT BINDING AS DIFFICULTY. Adjudicator.Binds refuses a
requirement nobody in the declared range could fail; it says nothing about
a requirement almost nobody in play would fail. cash:1, hour:1 and heat:99
all bind and barely constrain. The model still chooses how hard. A floor on
each amount is a bound, and rule 2 wants the series first: wallets, hours
and heat as played, and the amounts the model names. Inventory the amount
field as "constrained against formality, unconstrained above it" and file
the series as its own item.`

## 10. Items awaiting a number

I may not allocate. Each is named so the resident can file it in one line.

A. THE HOW-HARD SERIES. Print, from real runs, the distribution of `Clean`,
`Dirty`, `Hour` and `Heat` at the moment a novel action is adjudicated, and
the amounts the model names per check; then set floors from the series.
Depends on 114's inventory naming the field. Core, simulation line.

B. `novel/none/nothing` AND THE SWALLOWED LINE. Decide whether a novel
action that moves nothing should be narrated by the game or answered by the
person the player spoke to, and fix `NovelLine`'s "It lands" on a null arm
while there. Game feel, dialogue line. Section 8 (a) and (b).

C. THE MEASUREMENT CASEBOOK LINE for the two clamp assertions with no
`Passed` guard (section 4): a bound that a refusal's default satisfies is a
test that cannot see the code it names. One paragraph, documents.

Rows for 114's inventory, not items: section 8 (c) the cost on `nothing`,
(d) the unclamped standing restore, and section 1's monotonicity column.

## 11. What the resident prints before the commit

1. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer`,
   never from the scrollback; `verify-footer.before-113` is not current and
   is not to be pasted. Expected on the line: `4291 CoreTests`, `94
   adversary checks`, and a cadence reading that pairs this record with row
   `2026-09-06T05:53:25Z`.
2. `git show HEAD:ledger/Assets/Scripts/Core/Adjudicator.cs | md5sum` beside
   `md5sum` of the scratchpad `Adjudicator.old.cs`: equal, or section 3's
   red proof was taken against something other than HEAD.
3. `git diff HEAD -- ledger/CoreTests/Program.cs | grep -n "Checks.None"`:
   the removed lines in the clamp loop and the `wild` case name
   `Checks.None`, and the removed assertions carry no `.Passed`. This closes
   section 4's residual.
4. The commit message carries the three numbers above and names this record.

## 12. Quality ladder: best available, or first working

Best available for the property asked: the rule is stated at the level of
the property, it subsumes both shapes the brief offered, it is enforced in
the tested layer, its ruler is built from bounds the code enforces, the
rejecting case was watched red on the old code, and the false certificate
was replaced with a counted denominator. The next rung is named and is not
blank: item A, the series that turns "binds" into "bites". The rung after
that is design, item B. Neither is a reason to hold this commit.

<!--RULING spawn=2026-09-06T05:53:25Z-->
