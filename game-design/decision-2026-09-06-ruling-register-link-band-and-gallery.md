# Ruling: the Producer register's link band, the gallery page, and the morning brief in its new shape

> **STATUS: LOG, 2026-09-06. NOT CURRENT** once the commit lands and sections
> 8 and 9 are applied. Director ruling on the one-builder batch
> uncommitted in the tree: `tools/producer-check.py` (modified),
> `tools/gallery.py` (new, 659 lines), `tools/publish-glance.py`,
> `tools/morning-brief.py`, `.github/workflows/publish-glance.yml`,
> `production/briefs/2026-09-06.md`, `STATUS.md` (derived). Escalated because
> it changes a conclusion and changes a gate that blocks commits. ONE REVIEW,
> TWO SPAWN ROWS: `2026-09-06T07:22:43Z` (killed by a session limit before it
> wrote anything) and `2026-09-06T09:03:18Z` (the resume that did the reading
> and wrote this record); section 12 records what that exposed, and both rows
> are stamped at the foot. NOT CURRENT once the commit lands and sections 8
> and 9 are applied; from then the files are the reading copies and this is
> the record of why.

VERDICT: LAND WITH AMENDMENTS. Four dictated changes go into the same commit
(section 8), and the first of them is BLOCKING: the gate may not land grading
files by the date typed into their own names. Everything else in the batch is
approved as read, including the link band, the whole-URL destination list, the
gallery generator, the publisher's third page, the workflow's third request,
and the brief's new shape. Nothing here has been seen on glass: no browser has
rendered gallery.html and no run has requested it from Pages. Section 6 says
what that leaves unproven.

The standard judged against is Jafar's ruling of 2026-09-06, quoted in
`production/NOW.md` lines 327 to 332: images as Telegram images and never as
links; at most two links per message and never to a repository markdown file,
only the glance, map or gallery; everything else in plain words; lead with
where the project stands and what changed for the game; a gallery beside the
glance, latest frames and clips, biggest first, nothing else.

## 0. What was read, what was not run, and the numbers taken on report

NOTHING WAS RUN. This spawn has no shell: it can read, search and write. Every
selftest count below is the builder's, and the resident prints them again
before the commit (section 9). What I did instead was count the assertion
sites in the code, which tells whether a reported count is the SHAPE of the
suite and nothing about whether it went green.

Read in full: `tools/producer-check.py` (1796 lines); `tools/gallery.py` (659);
`tools/publish-glance.py` (841); `tools/morning-brief.py` (930);
`.github/workflows/publish-glance.yml` (289); the three briefs dated 5 and 6
September and the head of `latest.md`; both outbox messages;
`production/decision-queue.md` lines 28 to 58; `production/NOW.md` lines 70 to
94, 241 to 335, 515 to 554 and 655 to 668; the 4 September ruling on queue 077
(the precedent for a filename clock); the 6 September ruling on queue 113 (the
shape of this record); `ledger/verify.py` lines 273 to 340, 1049 to 1120, 1269
to 1311, 2766 to 2784, 2946 to 3006, 3420 to 3457, 3640 to 3680, 3755 to 3795
and 4315 to 4363; `tools/glance.py` lines 74 to 93, 308, 436 to 455 and 833 to
848; `.claude/agents/producer.md` lines 23 to 73; `.claude/agent-log.tsv`
lines 1 to 3 and 278 to 287; `production/queue/124`; STATUS.md lines 1 to 40.
Opened as a picture: `production/d1-probe/ue-vign_camA_day.png` (section 4).

Counted by hand: `ok()` call sites in `producer-check.py`'s selftest, 64 (8
accepting unprompted, 2 answer, 1 empty NEEDS YOU, 2 brief, 4 bad briefs, 15
bad fixtures, 1 one-rule check, 8 unit cases, 4 gate accepting, 1 served, 1
three-clock ladder, 1 clock, 1 wall-clock detector, 1 dated ladder, 9 gate
rejecting, 1 missing tree, 1 rotten frozen entry, 3 single-file). Keys in
`BAD`, 15. Entries in `RULES`, 10. `ok()` sites in `gallery.py`, 12, over 10
`CHECKS` and 5 rejecting fixtures. All four figures match the builder's two
count lines. That is consistency, not evidence of a pass.

Taken from the coordinator, who ran `ledger/verify.py` in this session, twice:
before this record existed, `producer register PASS filesChecked=4
filesExempt=5 filesWalked=9 filesDatePinned=4/4`; `DIRECTOR RAN BUT DID NOT
RULE: 1282 changed line(s) (623 tracked + 659 untracked in 1 new file(s)) vs
100 threshold, rulingRowsUnruled=1/1`; `UNTRACKED/ABSENT TOOL(S):
tools/gallery.py(untracked)`; docs 143/143; CLAUDE.md 1996/2000 words. After
the first version of this record: `rulingRecords=1/33 rulingRowsUnruled=1/2
rulingUnruledNewest=2026-09-06T09:03:18Z`, reported as still red. Section 12
reads those keys against the code.

PREMISE CHECK, CLAUDE.md section 0 and the weekend order (NOW.md 294 to 313):
the weekend is game work only, with one named exception, "the brief register
and the gallery page, since the first brief was wrong and he wants today's
rewritten in the new shape and SENT so he can judge it". This batch is that
exception and nothing wider. Nothing purchased, no licence entry, no reference
bar cited, late-analog framing untouched. Every process item found below goes
to the queue and waits, per the same order.

THE SPLIT FOR THIS SPAWN: studio 1, game 0, basis spawns, points unmeasured.

## 1. The ruling asked for: rules graded by the date in the filename

The builder's design: `RULED_ON` dates two rules (`linkcap`, `linkdest`) at
2026-09-06; the gate measures each file at the ISO date in its own name and
switches off any rule ruled after that date; `link_ok` falls back to the
retired host list (`github.com`, `raw.githubusercontent.com`) for files dated
before the ruling; an undated name gets every rule; the single-file check
measures at the wall clock. The stated reason: tightening retroactively turns
three already-written messages red inside `verify.py`, which deletes the
footer and blocks every commit until somebody edits a message that was
correct when written. The monotone-subset argument is correct and I checked it
at `link_ok` lines 389 to 408: the site pages are tested first in both
generations, so anything legal today was legal before.

RULED: NOT SOUND AS AN INSTRUMENT. The problem it solves is real and the
solution already exists twelve hundred lines lower in the same file. The
failure mode, named:

(a) THE GATE READS ITS RULEBOOK OFF THE SPECIMEN. The date at the front of a
filename is typed by the writer of the file. A message written next week and
saved as `production/outbox/2026-09-05-anything.unprompted.md` is graded with
no cap and the retired host list, and prints `pass`. The suite proves it: the
dated ladder at lines 1288 to 1312 takes one text with ten repository links,
names it twice, and asserts `accepted dated 2026-09-05, refused dated
2026-09-06`. The builder reads that as the ruling biting where it was ruled.
It is equally the exploit, watched green.

(b) THE "REVIEWED DIFF" DEFENCE DOES NOT HOLD HERE. The comment at lines 121
to 127 says backdating would have to be done in a reviewed diff. Since the
2026-09-06 narrowing (CLAUDE.md, the studio split), documents commit on the
resident's read with no director; an outbox message is a document; the reader
is the writer. The list inside the tool is instrument code, and changing it is
what spawns a director (this spawn is the proof).

(c) THE WALL-CLOCK HALF HAS NO PROVEN CALL SITE. The design's second safeguard
is that the single-file check measures at the wall clock, so anything sent
today meets every rule. Nothing in the tree proves that check ever runs before
a send; the 4 September ruling said so (section 2) and queue 080 is still
open. The one call site that is proven is the gate inside `verify.py`, and the
gate is the half with the hole. `--now` on the single-file check is a second
way through the same door.

(d) A FALSE GREEN IS IN THE FOOTER TODAY. The gate prints `pass` for
`production/outbox/2026-09-05-the-console-run.unprompted.md`, which I counted
at fifteen URLs, two to the site and thirteen to github.com, nine of those
occurrences (eight distinct) to markdown files. That is the message whose
shape Jafar rejected. A `pass` that means "fine under rules since retired" is
the footer turning into a noun; the coordinator's `filesChecked=4` carries
three such passes, and nothing in the key says so.

(e) TWO MECHANISMS FOR ONE IDEA, IN ONE FILE. "This file predates a ruling" is
already handled by `PRE_REGISTER` (lines 1472 to 1484): a frozen list of
NAMES, a marker in the file, red when either half is present without the
other, and the file's own argument for why: "what stops the marker being an
escape hatch any future session can type at the top of a 600-word message".
A date at the front of a filename is exactly a thing any future session can
type. The builder wrote the argument against the design forty lines before
writing the design.

(f) THE PREMISE "ALREADY-SENT" IS NOT ESTABLISHED. NOW.md lines 265 to 268
record `outbound: records=0` and state that the report written on 2026-09-05
was never sent. The 2026-09-03 message predates the transport (queue 088
landed 2026-09-05). Whether either reached Jafar by hand I could not
determine. So the argument "correct when it was sent" is an argument about
drafts in the tree. The drafts must not be rewritten (they are the record of
what was written); nothing about them supports grading them as `pass`.

THE PRECEDENT, distinguished rather than overruled. The 4 September ruling
accepted the filename date as the gate's CLOCK for the deadline rule, named
the same backdating hole, and accepted it because the two other instants were
worse and the gate's promise was narrowed to one it can keep. That was a date
used to compute a quantity. This is a date used to switch rules off. A ruler
with a soft zero and a switch on the outside of the box are different classes
of instrument fault, and the alternative here is not a worse instant but a
better mechanism the file already has.

WHAT REPLACES IT, dictated as amendment 1 in section 8: the three files
written before the link band was ruled are named in a frozen tuple; for those
names the gate does not enforce `linkcap` or `linkdest` and the floor reads
the retired host list; every other file, whatever its name says, gets every
rule; the exception is printed per file and counted in the footer; the date
keeps one job, a selftest that no name on the list carries a date on or after
2026-09-06, which is the consistency check a date is good for. The decisive
rung of the suite becomes: the same ten-link text under a LISTED name passes,
and under an UNLISTED name dated 2026-09-05 is refused. That is the test that
tells the two designs apart, and today's suite cannot run it.

## 2. Both outcomes of every guard, read rather than watched

`producer-check.py`. Accepting case first at line 1063, on a fixture carrying
two site links; the two-instant ladder at 1077 to 1086 is well built; each
rejecting fixture is required to trip its own rule and only its own rule
(1151 to 1169), which is the right shape. The gate's accepting cases run
against a synthetic tree and then the live repository (1210 to 1229). All
unrun by me. After amendment 1 the dated ladder is replaced, not deleted; the
three-clock verdict ladder at 1248 to 1260 stands.

`gallery.py`. Accepting case first is the live repository (491 to 508), which
is the ruled fixture for a tool that checks this project. FINDING: the third
assertion (504 to 508) reads `model["shots"]`, and `build()` sets that to
`kept` (line 368), the pictures that survived packing. It therefore asserts
two facts under one name: that the four Unreal frames are the newest four by
commit time (a dating fact), and that they fitted the byte budget (a packing
fact that depends on Pillow being installed). Without Pillow,
`glance.encode_image` (glance.py 444 to 450) embeds raw bytes; the workflow's
own comment puts the four frames at 0.6 to 1.1 MB each against a budget of
1,000,000 bytes, so all four drop, the assertion fails, exit 3, and the
workflow step at lines 205 to 209 fails the job. The workflow comment at 184
to 191 says a failed Pillow install is not fatal on purpose. The two
statements disagree, and the selftest is the one that wins. Amendment 2 makes
the dating assertion read the dating. The five rejecting fixtures (541 to 582)
are synthetic and each names the check it expects to refuse; accepted.

`morning-brief.py`. `leads_with_the_game` has two call sites and both are in
the selftest (lines 791 and 802); `compose()` never calls it. It is a property
test of the tool's own composition, which is a legitimate shape, but it does
not guard the live brief the daily wake writes. It reads the HEADLINE only
and looks for five engineering words; section 4 shows the WHAT CHANGED line
carrying two of them. Noted, not amended: the words move out of the message
under amendment 4 rather than the guard growing to chase them.

`publish-glance.py`. The dated-sentence reading now iterates `PAGES` (687 to
694) with the rejecting half at 697 to 701; the stub generators are planted
from `PAGES` too (616 to 617), so a fourth page cannot fall out of the fixture.
Accepted.

## 3. The denominator: filesChecked=4 filesExempt=5 filesWalked=9

What it counted, from the tree: the gate walks `production/outbox` (README,
the 3 September message, the 5 September message) and `production/briefs`
(31 August, 2 September, `latest.md`, the 3 September step-1 report, 5
September, 6 September), nine files. Five exempt: README by name, and the
four `PRE_REGISTER` director documents that predate the register Jafar ruled
on 2026-09-03, each carrying the marker in its head (I read the marker in
`latest.md`, which is a stale copy of the 2 September brief; queue 074 owns
that). Four checked: both outbox messages and the two tool-written briefs.

So five of nine is the history, honestly counted, and the gate's own output
splits it (by name, pre-register) even though the footer key does not. What
the footer HIDES is inside the four: three of the four checked files are
dated before 2026-09-06 and were graded under the retired destination list
with no cap; one, today's brief, was graded under Jafar's ruling.
`filesDatePinned=4/4` says four names carried a date. It does not say what
those dates did. After amendment 1 the footer carries
`filesLegacyLinks=3/4` beside `filesChecked`, so a reader sees that one file
in this repository has been measured against the register as it now stands.

## 4. The brief, read as Jafar will read it on a phone

The text, verbatim from `production/briefs/2026-09-06.md`:

    HEADLINE: Four new pictures of the town since the previous brief, and
    one decision is waiting for you.
    WHAT CHANGED: The town has four new pictures to look at, biggest and
    newest first. Behind them, thirteen changes have landed; the work list
    stands at ninety-three ready, eight blocked and eleven finished.
    [the gallery]
    NEEDS YOU: How close should strangers stand?
    [where it all stands]
    NEXT VISIBLE THING: unknown until the day is planned against your order.
    BUDGET: Your newest reading was thirty-three percent on the meter that
    governs, taken today. Seventeen sessions went to the studio and fifteen
    to the game since the previous brief, counted in sessions and not
    points until the rate is measured.

Links: two, `gallery.html` and the glance root, both under the site origin,
none to markdown. Compliant. Leads with the game: in shape, yes; the first
sentence is pictures and a decision, not the queue. 116 of 150 words. Four
findings, two of them amended here.

(a) "PICTURES OF THE TOWN" IS NOT WHAT THE FRAME SHOWS. I opened
`production/d1-probe/ue-vign_camA_day.png`: a grey untextured blockout street
under a white sky, flat grey buildings, a checker test tile on one wall. The
5 September message described the same frames as "the street's test pattern
tiles properly, not Meridian yet"; NOW.md line 299 says the street still
renders the engine checker. The tool writes "of the town" for any image under
`production/d1-probe`, at `morning-brief.py` lines 450 to 471, and this
sentence is the one he taps to open a gallery whose hero is that checker
blockout. Rule 4: the words claim more than the artifact shows, in the first
brief he has been asked to judge. Amendment 3: the tool says "of the street",
which is true of every source directory it walks today (the D1 vignette is
one street, in both engines) and promises nothing about Meridian.

(b) THE STATUS DUMP MOVED DOWN ONE LINE. "Behind them, thirteen changes have
landed; the work list stands at ninety-three ready, eight blocked and eleven
finished" is the rejected headline's content in words, one line lower. The
headline guard reads the headline only, so this satisfies it by position. The
counts are already on the tool's provenance lines for anyone auditing; on his
phone they are the paperwork he said is not a director update. Amendment 4
cuts the work-list clause and keeps the landed clause as the one studio
sentence.

(c) A DECISION WITHOUT ITS OPTIONS, AND A GATE THAT CANNOT SEE IT. NEEDS YOU
poses "How close should strangers stand?" and nothing else. The card
(`production/decision-queue.md` lines 40 to 45) carries three options, a
recommendation, a default and a deadline of 2026-09-07. The register Jafar
ruled on 2026-09-03 (`producer.md` line 23) requires all four in the message.
`needs_you_items` (lines 774 to 805) drops an item that has no option,
recommendation or default, so the options and deadline rules see zero items
and pass. The 5 September brief had the identical shape and "passed the
register", so this is not this landing's regression, and the card's option
lines carry digits (0.7 m, 1.0 m, 1.4 m) the ban list would refuse, so
carrying them is not a one-line change. Queued in two halves (section 7), and
said plainly here: the brief he will judge asks him a question without giving
him the choices, and today's gate cannot tell.

(d) THE REST READS RIGHT. The budget sentence, the split sentence in
sessions, and an honest "unknown" for the next visible thing.

THE STRUCTURAL LIMIT, named so nobody mistakes it for a bug. A brief generated
from repository state can count and cannot judge; `producer.md` wants
judgement and never a status dump; Jafar's own item 1c of 2026-09-05 made the
brief a tool's output. Both are his. The next rung that reconciles them is a
one-line, dated, director-written "what changed for the game" that the tool
reads and includes when it passes the register, and otherwise says nothing
measured. Section 7.

## 5. The two conclusions this batch overturns, checked against the files

(a) "THE 5 SEPTEMBER MESSAGE WAS IN REGISTER." Confirmed overturned, and
wider than the builder said. Counted in the file: fifteen URLs, thirteen to
github.com, of which nine occurrences to `.md` files (eight distinct: queue
062 twice under different anchors, decision-queue, inbox README, NOW, queue
105, the 5 September ruling, roadmap-v2, budget) and four to a png, a txt, a
tree and a tsv. Under the host list it passed with thirteen "good" links; the
builder's `urls=15 goodLinks=13 findings=0` is the same count. The SAME
overturn applies to `production/briefs/2026-09-05.md`, which carries three
repository links (a jpg, the queue directory, decision-queue.md), zero to the
site, and is recorded as having "passed the register" in three places: queue
095's status line, the 5 September ruling at lines 270 to 272 and 432, and
`producer register PASS filesChecked=2` taken on report at line 321. All three
were true of the host check and are false of the ruling. Corrections in
section 8, amendment 5, in the shape the 4 September ruling set: LOG records
get a dated line appended at the site, LIVE files get the sentence replaced.
One more premise to correct while there: none of these messages is known to
have been sent (section 1 f).

(b) "PUBLISH-GLANCE PRINTED A DENOMINATOR SMALLER THAN THE SET EXAMINED."
Partly. The current file records the old reading at lines 680 to 684: `2/2
published page(s)`, hand-typed. Before this tree the site had two generator
pages, so 2 of 2 was true then; the fault is a denominator that could not
grow, which bit the moment this same tree added a third page. That is a set
examined smaller than the site, with a denominator honest about what it
examined and silent about what it left out. The precise sentence for the
record is "a clean reading over a list that stopped growing", which is the
builder's own comment at line 683. The old hunk is not in the tree and I could
not open it; section 9 has the resident print it and record which of the two
sentences is exact.

## 6. What no number in this batch can stand in for

No browser has rendered `gallery.html`. No run has requested it from Pages.
There is no `gallery.html` at the repository root (glob: `index.html`,
`glance.html`, `map.html` only), so the only gallery ever built was in the
selftest's memory and was discarded. `check_biggest_first` measures the
`data-w` attributes in document order, which is the ruled property as bytes;
it is not the property as seen. The workflow's third `--check` will prove
status, type, stamp and commit for the served page, and nothing about what is
on it: a gallery whose foot reads "0 of 36 shown" passes that check green.
The resident writes the page and opens it before the commit (section 9), and
Jafar's eyes are the first measurement of the layout.

The untracked `tools/gallery.py` is the state of an uncommitted tree, not a
finding for the builder, and it is a RED: `tools_tracked()` at `verify.py`
lines 273 to 339 checks every tool a workflow names by path with `git
ls-files --error-unmatch` and returns False at line 337 when one is
untracked. The workflow names `tools/gallery.py` at line 209, so this check
refuses the tree until the file is in the index. Staging it clears the check
(`ls-files` reads the index, and the ruling lands in the same commit it
authorises, per the comment at lines 2776 to 2778). It is the one check I can
see in this tree that refuses it for a reason other than the ruling, and
section 12 leans on that.

The evidence channel for the served pages is still the step log and the step
summary, which `.claude/rules/ci.md` names as channels that have failed. No
file is committed by this workflow. Pre-existing from queue 097; queued.

## 7. Queue items, named for the resident to file

Not built this weekend, by Jafar's order. Each is one line to file.

A. NEEDS YOU CANNOT BE A BARE QUESTION. Two halves: the gate refuses a NEEDS
YOU section that asks a question and carries no option (rule 5b, the case it
cannot see today); the brief carries the card's options, recommendation,
default and deadline when each line passes the register, and otherwise says
the card is waiting and where. Documents and instrument, small.

B. WHAT CHANGED FOR THE GAME, WRITTEN BY A DIRECTOR, READ BY THE TOOL. One
dated line in a named file; included when dated today or yesterday and clean
under the register; "nothing measured about what changed for the game"
otherwise. Closes the count-versus-judgement gap in section 4.

C. THE SERVED-PAGE VERDICT AS A COMMITTED FILE, per ci.md, and the gallery
check reads the foot's "N of M shown" into a key, so a thin gallery is a
number in the footer rather than a green in a log.

D. THREE SELFTESTS WITH NO ROW IN `TOOL_SELFTESTS` (verify.py 1060 to 1065):
`producer-check.py`, `morning-brief.py`, `gallery.py`. All three print the
`N passed, M failed` shape the one parser reads. A row each, no new copy.

E. Queue 080 stands and is now load-bearing twice: the send check's accepting
instant stamped into the file is the only thing that will ever prove the
wall-clock half of the register ran.

F. Queue 124, already filed by the coordinator, is re-scoped by section 12
before anything is built on it.

## 8. Dictated amendments, all in the same commit

A1, BLOCKING, builder pass on `tools/producer-check.py`. Replace the
date-as-switch with a name list, in the file's own `PRE_REGISTER` shape:

- A frozen tuple `LEGACY_LINK_RULES` naming exactly
  `production/outbox/2026-09-03-batch-landed-and-the-wait.unprompted.md`,
  `production/outbox/2026-09-05-the-console-run.unprompted.md` and
  `production/briefs/2026-09-05.md`, with the sentence: written before the
  link band was ruled on 2026-09-06, may never gain a member whose filename
  date is on or after 2026-09-06, and widens only in a reviewed diff. No
  marker line goes into the messages: they are the record of what was
  written, and the printed per-file line is the reader-visible half.
- `check()` takes `legacy_links=False`. When true, `linkcap` and `linkdest`
  are not enforced and are printed under NOT ENFORCED with the words "legacy
  link rules by name", and `link_ok` accepts the retired host list for the
  floor. `as_of` no longer selects any rule; `RULED_ON` and `not_yet` go, or
  stay as documentation with no effect on a verdict. `--now` therefore
  touches deadlines only.
- The gate sets `legacy_links = rel in LEGACY_LINK_RULES`, prints it on the
  file's own line (`pass` becomes `pass-legacy-links` for those three), and
  the footer carries `filesLegacyLinks=3/4` beside `filesChecked` on both the
  PASS and the FAIL line. A listed name no longer in the tree prints as a
  note, the way `listed_absent` does.
- Selftest rungs, accepting first: the live repository passes with
  `filesLegacyLinks=3/4`; the same ten-repository-link text passes under a
  LISTED name and is refused under an UNLISTED name dated 2026-09-05, by
  `linkcap` and `linkdest`; every listed name's date precedes 2026-09-06; the
  three-clock verdict ladder is unchanged.

A2, builder, `tools/gallery.py` lines 504 to 508. The "newest four are the
Unreal frames" assertion reads the order from `find_pictures(ROOT)[0][:4]`,
not from `model["shots"]`. A second assertion may say whether those four were
kept, printed beside `resizer=`, and must not fail the suite when the resizer
is absent; the build step's exit 1 and its NOTE already carry that fact.

A3, builder, `tools/morning-brief.py` lines 450 to 471. Every "of the town"
and "The town has" becomes "of the street" and "There are ... of the street":
`"%s new %s of the street since the previous brief"`, `"No new picture of the
street since the previous brief"`, `"There are %s new %s of the street to look
at, biggest and newest first."`, `"... the gallery still holds the last
picture of the street."`, `"No picture of the street this morning, because
%s."` Add `"street"` to `GAME_WORDS`. The docstring says why: measured
2026-09-06, every walked directory holds frames of the one D1 street and none
of them yet holds Meridian.

A4, builder, `tools/morning-brief.py` lines 472 to 482. The three `studio`
strings end in a full stop and the work-list clause (lines 481 to 482) goes.
The queue counts stay on the provenance lines and the done line, where they
already are.

A5, resident, documents. Append under the 5 September ruling's line 272 and
line 432 one dated line each: "CORRECTION 2026-09-06: passed the register as
it stood on 2026-09-05, a host allowlist; refused under the link band Jafar
ruled on 2026-09-06 (three repository links, none to the site); grandfathered
by name, ruling of 6 September on the register's link band, section 5." Queue
095's status line gains the same clause. NOW.md lines 270 to 272 have the
sentence REPLACED with the current fact. The outbox README gains one sentence
naming the legacy list and that it never widens. Rule 1: grep for the
SENTENCE "passed the register" repo-wide before editing and report the hit
count in the commit message; I found three sites and NOW.md may phrase it
differently.

After A3 and A4 the brief is regenerated by the tool, never edited by hand,
and the file in the commit is the tool's output.

## 9. What the resident prints before the commit

1. `python3 tools/producer-check.py --selftest`: the count line, and the two
   lines of the listed/unlisted rung, quoted.
2. `python3 tools/producer-check.py --gate`: the four per-file lines with
   their `asOf` and legacy tag, and the footer keys including
   `filesLegacyLinks=3/4`.
3. `python3 tools/gallery.py --selftest` with its `resizer=` reading, then
   `python3 tools/gallery.py` writing `gallery.html`; open the file and quote
   the foot line and the first two `data-w` values. Decide whether the root
   copy is tracked the way `index.html` and `map.html` are, by
   `git ls-files` on those two, and say which.
4. `python3 tools/morning-brief.py --dry-run --date 2026-09-06`: the message
   between the rules, quoted whole in the commit message.
5. `git diff HEAD -- tools/publish-glance.py` at the `2/2` hunk, and one
   sentence in the commit message saying which of section 5(b)'s two
   descriptions is exact.
6. `python3 ledger/verify.py`, footer pasted from `ledger/.verify-footer`,
   pairing this record with rows `2026-09-06T07:22:43Z` and
   `2026-09-06T09:03:18Z`.
7. The commit message names this record and carries the grep count from A5.
8. THE MEASUREMENT SECTION 12 TURNS ON, taken twice and quoted both times:
   the footer's director-cadence sentence (it begins either `director cadence
   ok` or `DIRECTOR RAN BUT DID NOT RULE`) and the tool-inventory sentence
   (`UNTRACKED/ABSENT TOOL(S)` or `... workflow-named tool(s) ... tracked`),
   once with `tools/gallery.py` unstaged and once after `git add
   tools/gallery.py`. Two sentences, two runs, nothing else changed between
   them.

## 10. Quality ladder at close

The link band is best available once A1 lands: whole-URL destinations, both
ends of the band cited to Jafar, monotone across the change, exceptions by
name and counted. The gallery is first working: it is measured as bytes and
has never been a page on glass; the next rung is section 7 C and Jafar's
phone. The brief is first working by construction, and its next rung is not
blank: section 7 B is the sentence a director writes and the tool carries.

## 11. What this spawn did not get to

Nothing was run, so every green in this record is the builder's until section
9 reprints it. I did not read `tools/glance.py`'s `check_formatting` body, so
whether an underscore in a frame's stem (`ue-vign_camA_day` as alt text) can
trip it is unread; the resident's gallery run in section 9 answers it.

## 12. One review, two spawn rows: what the first version of this record exposed

THE ROWS, from `.claude/agent-log.tsv`: line 280, `2026-09-06T07:22:43Z`,
studio-director, the original spawn, killed by a session limit before it had
written anything; line 282, `2026-09-06T09:03:18Z`, studio-director, the
resume that did every read above and wrote this record. The first version of
this record carried the 07:22:43Z stamp alone, because that was the row
quoted to it. The coordinator is right that this was inaccurate on its own
terms, not merely unsatisfying to a gate: the reading and the amendments were
produced in the 09:03:18Z spawn. Corrected below.

HOW THE CORRECTION IS MADE, read from the code rather than guessed.
`_cadence_rulings` (verify.py 2990 to 3006) runs `RULING_RE.findall` over
each decision file and pairs EVERY stamp against the log; fixture a12 (4320
to 4331) plants three stamps in one document and asserts all three count with
`rulingUnmatched=0`. `rulingUnmatched` rises only for a stamp naming no real
director row (2999 to 3000), and both rows here are real. So this record
carries BOTH stamps: dropping the first would erase the fact that the review
was interrupted, and the tool accepts two by fixture. Neither stamp is a
resident's: both are written here, by the director, in the resumed spawn.

A THIRD ROW I DO NOT CLAIM: line 286, `2026-09-06T09:13:12Z`,
studio-director, logged after the coordinator's message that cited lines 280
to 285 was written. It is probably the resume that delivered that message to
me, and I cannot attribute it from the log, which carries two columns, `when`
and `agent`. A stamp must name the row the ruling answers; a probable row is
not that, so it is left unstamped and named here. If it is this review's
third row, it prints on a green line as an unruled spawn beside a batch that
was reviewed, which is the case fixture a14 documents.

THE CLAIM "A RESUMED DIRECTOR CANNOT SATISFY THE GATE, BY CONSTRUCTION" IS
NOT WHAT THE CODE SAYS, and queue 124 is built on it. Read at verify.py 3444
to 3455: the state becomes `unruled` only when the batch is over threshold
AND `ruling_fresh == 0`, and `ok` is `state == "ok"`. One stamp naming ANY
fresh director row clears it. Fixture a14 (4346 to 4363) is the accepting case
for exactly this situation, in its own words: "one killed and RESUMED (which
writes a second row), would otherwise turn a real review red"; two fresh
spawns, one ruling, GREEN, with `rulingRowsUnruled=1/2` printed as a reading
and no bound on it, "because there is no landed series yet and a bound
invented here is the thing rule 2 forbids" (4350 to 4352). So the 07:22:43Z
stamp, naming a real row newer than the reference commit, should have read as
`director cadence ok (... over threshold, REVIEWED; rulingRowsUnruled=1/2
...)`. The keys the coordinator quoted, `rulingRecords=1/33
rulingRowsUnruled=1/2`, are the shape of that green line.

WHAT WAS RED, THEN. Rule 3: suspect the instrument, and the instrument here is
the reading "verify.py is still red", which attributed the colour to the
cadence gate by inference from `rulingUnruledNewest`. That key prints on green
lines too (3655 to 3661). The one check I can see that refuses this tree for a
reason other than the ruling is `tools_tracked()` returning False at line 337
on `tools/gallery.py(untracked)` (section 6), which is red until the file is
staged and was red in both of the coordinator's runs. Section 9 item 8 is the
decisive measurement: two footer sentences, before and after staging, quoted.
I could not run it.

RULED, PENDING THAT MEASUREMENT: queue 124 is not built as filed. If item 8
shows the cadence sentence green with the 07:22:43Z stamp alone, 124's
acceptance ("drives `rulingRowsUnruled` to 0/N in ONE pass") puts a bound on a
reading the gate's author deliberately left unbounded, and the item is
re-scoped to its true residue, which is documentary: a stamp cannot name a
row that does not exist when it is written, so a resumed director stamps the
rows it can attribute and says so, as this section does. If item 8 shows the
cadence sentence RED with `rulingRecords=1/33`, then the code at 3449 and the
run disagree, that disagreement is the finding, and 124 is rewritten around
it with the two sentences as evidence. Either way the two row timestamps
above stand as the first instance of a director review spanning two rows, and
that is the observation the coordinator asked this record to carry.

<!--RULING spawn=2026-09-06T07:22:43Z-->
<!--RULING spawn=2026-09-06T09:03:18Z-->
