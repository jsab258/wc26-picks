# The decision queue

STATUS: LIVE. The single home for decisions awaiting Jafar, and the single
record of what he ruled. Written by the Producer, read by the dashboard and by
the bot. Chat is never a record: anything decided in conversation is written
here in the same turn.

THE FLOW, ruled by Jafar 2026-09-03. A card waits here until he rules. A ruled
card becomes a register entry: a D-record under
`ledger-v2/respec/decision-register/` when it affects architecture or identity,
a lighter RULED entry in this file otherwise. The dashboard reads WAITING for
its needs-you count and the register for what is decided.

Every card carries: a CLASS, two to four options, a recommendation, a default,
and a deadline no shorter than 24 hours, because until the bot exists Jafar may
not open this for a day.

THE CLASS IS A FIELD, NOT A JUDGEMENT MADE AT SEND TIME, so routing is data:
`CLASS: BLOCKING | DECISION | REVIEW | FYI`, defined in
`production/interrupt-classes.md`. BLOCKING pushes now, DECISION rides the
morning brief, REVIEW waits for the weekly, FYI is never pushed. A card with no
CLASS line is UNCLASSIFIED and is reported as such, never routed as FYI by
default: a default route is how a Blocking item lands on a page nobody opened.
Irreversible items wait for Jafar and never guess.

---

## WAITING

### When does the last bus leave Meridian?
CLASS: DECISION
added 2026-09-09, from the atlas-02 transport research

The research says outright that the last-bus time is a design decision and not
a researched one, so nobody is going to find the answer in a timetable. It
matters more than it sounds: closing time is 23:00 with twenty minutes drinking
up, so the bus either catches the pub crowd or strands it, and the walk home
through a dark port town is where a lot of this game happens.

- A. About half past ten, before last orders. Everyone still in Mickey's at the
  bell walks home through the town at night, or rings the minicab office, which
  the research names as a natural gossip node.
- B. About quarter past eleven, after drinking up. The pub crowd can still catch
  it and the town empties faster.
- C. No evening service on the Hook's route at all, only the main road. Harshest,
  and truest to a deregulated port town after the 1985 Act.

RECOMMENDATION A, because the walk home is where the game happens and B quietly
removes it.
DEFAULT A if unruled by 2026-09-11.
EVIDENCE: `production/art/atlas-02/research/transport-timetables.md`, section 1
and its HOLE 1.

---
### Is this the visual ladder?
CLASS: DECISION
added 2026-09-09, from your own item 5 this morning

Written out as you dictated it, in `production/ladder.md`, and it is now the
first screen of the map: rung 1 the built street matched to the lower panel of
Codex's Hook sheet, same viewpoint, rain, wet road, worn materials, sky, judged
by you side by side; rung 2 props reading as their materials with the first
batch of clutter placed per the catalogue; rung 3 Mickey's frontage on the
street from the design; rung 4 people on the street with varied bodies; rung 5
a face that moves and a voice, per D2; rung 6 Mickey's enterable; then your
thirty minute dry run. The crime and gossip work continues underneath.

Rung 1 has started. This card is about the ORDER of what follows it, which is
the one thing the ladder cannot settle for itself.

- A. As you dictated it. Seven rows, unchanged.
- B. People before Mickey's frontage, swapping rungs 3 and 4. A street with
  people on it reads alive one rung sooner, and one more building on a street
  that is already six bays does less for the first impression than bodies do.
- C. Collapse rungs 5 and 6 into one. The face, the voice and walking into the
  pub are judged together in a single sitting rather than two, which is fewer
  handoffs to you but a bigger step to get wrong.

RECOMMENDATION A, because it is your order and the one argument against it, B,
is a guess about what reads alive faster that nobody here has measured. If you
want B, say so and it costs nothing to swap; if you are unsure, A and we find
out at rung 3 whether the street wanted people first.
DEFAULT A if unruled by 2026-09-11.
EVIDENCE: `production/ladder.md`, and the map's first screen once this morning's
batch lands.

---
### Is Mickey's a free house or a tied house?
CLASS: DECISION
added 2026-09-08, from the first in-house art commission

Canon says your uncle "left him the pub", which reads as a freehold rather
than a brewery tenancy. But 1989 to 1992 is the exact window the Beer Orders
were reshaping, with brewers under a 31 October 1992 deadline to sell or free
thousands of pubs, so which one Mickey's is decides who can lean on you.

- A. Free house, owned outright. The Beer Orders are WEATHER around you:
  rivals buying up newly freed pubs, brewers dumping stock, nobody with a
  contractual hold on your cellar.
- B. Tied house with a brewery landlord. Real leverage over you, a rent
  review somebody can weaponise, and a legal right to one guest cask beer.
  Richer pressure, but it sits awkwardly with inheriting the place.

RECOMMENDATION A, because the premise is a man who inherits something and
finds it half dead, not a man who inherits a landlord.
DEFAULT A if unruled by 2026-09-11.
EVIDENCE: `production/art/atlas-02/research/small-pub-plan-measured.md`, the
licensing and Beer Orders section, with the 1989 dates cited.

---
### How big is Mickey's on Quay Street?
CLASS: DECISION
added 2026-09-08, from the first in-house art commission

The built street is six shopfront bays of 6.0 m each. The pub takes some of
them and the number quietly sets its class.

- A. Two bays. 12.0 m frontage by 8.0 m deep, 96 square metres, a derived
  capacity near 130 and a busy Friday staged at about 44 adults.
- B. Three bays. 18.0 m frontage. Reads as a corner house or a former
  coaching inn, and raises the pub's standing whether or not you meant it to.

WHICH BAYS, which depends on the bay card above: under the bay card's A this
takes bays 0 and 1 and moves the fish market fascia to bay 3, the unlettered
one; under B it takes bays 2 and 3 and moves nothing else. Three bays under A
takes Rita's Pawn too.

RECOMMENDATION A, because a two-bay back-street local is the pub a half-dead
inheritance comes with.
DEFAULT A if unruled by 2026-09-11.
FOLDED IN UNLESS YOU SAY OTHERWISE: the rooms survive, a public bar and one
snug NOT knocked through. The pubs that were not knocked through are the ones
whose licensee never had the money, which is the state the premise starts
from.
EVIDENCE: `production/art/atlas-02/research/small-pub-plan-measured.md`, the
carcass taken from the street's own scene file and the capacity derived from
published fire floor-space factors.

---
### The gully grate is under the road. Raise it flush, or cut the ground?
CLASS: DECISION
added 2026-09-09, from run 33's own placed-bounds reading

Run 33 placed 22 of 23 props as real meshes with collision. The drainage grate is
one of them and NOTHING CAN SEE IT: it sits under 20.00 mm of cover at the west
edge of its own footprint and 10.00 mm at the east, both taken at the footprint
edges rather than mixed with the cell-centre figures, under the carriageway slab and
the channel slab both, which overlap by 0.469 mm with no gap between them. It is a
verified piece and it is invisible, and it is the piece you named as the accepting
case for the whole prop route.

The placement is DELIBERATE in the scene file, which says a grate "sits IN the
ground rather than on it". The fault is not that intent, it is that the ground
planes are emitted as continuous slabs over the top of it. There is no CSG here:
nothing cuts a hole.

- A. THE GRATE RISES AND TAKES THE CROSS-FALL. y_m -0.0925 to -0.077502 and
  pitch_deg 0 to 1.432096, so it sits flush with the channel along its own width.
  The pitch is part of the fix and not a refinement: a flat grate raised to be
  flush at its centre line leaves a 5 mm lip a shoe would catch.
- B. THE GROUND IS CUT. The channel and carriageway emitters leave a 0.40 m gap at
  the gully and the grate stays where it is, sitting in an open dish. More
  faithful to how a real gully is built, and it is a change to how 593 pieces are
  generated rather than to one row.

RECOMMENDATION A, because a gully grate in a British street IS flush with the
channel invert; that is what makes water reach it. B is more faithful to the
masonry and buys nothing a camera can see, at ten times the risk.
DEFAULT A if unruled by 2026-09-11. The studio is proceeding on A tonight so that
a clip can exist; if you rule B, A is two numbers to revert.
A HAS NOW BEEN EXECUTED AND IT LANDED, recorded 2026-09-09: the grate rises and
takes the cross-fall, and run 36 photographed it. Its diagonal slots are legible
in the frame. The piece count did not move, 593 either side, and exactly one line
of the scene file differs. So a tap on B now reverts something you can see, which
is a better position to rule from than the one this card was written in.

ONE HONEST QUALIFICATION, added the same day after opening the picture rather
than the verdict. THE SHAPE IS RIGHT AND THE COLOUR IS WRONG. In that frame the
bars and the gaps between them are both pale grey, nearly white, with almost no
separation: it reads as white plastic and not as iron. That is a separate fault
already on the list as a near-white road across the whole near half of the frame,
and it is not caused by raising the grate. It does not change this card's
question, which is where the grate SITS; it does mean the picture is not yet one
that would survive a stranger's first thirty seconds.
EVIDENCE: `production/d1-probe/ue-crime-verdict.txt`,
propBurialSubject=prop_drainage_grate_01_0/via=loaded-asset/collision=YES/
buried=100.0pct, and
`game-design/decision-2026-09-09-the-twelve-clauses-and-the-buried-grate.md`
section 3, which checked the arithmetic off the spec file twice and killed the
first proposed fix (cutting the channel alone) by finding the carriageway over it.

---
### Which bay is Mickey's?
CLASS: DECISION
added 2026-09-08, from the vignette recipe's `bayHintConflict=`

The built street's glazing centres sit at x 6.869 + 6n. The Mickey's fascia
decal is at x 6, which is bay 0; the interior bar-back card is at x 18, which
is bay 2, where the Rita's Pawn fascia also sits. A pawnbroker's window with a
bar back behind it. D15 left WHICH BAY a small authored choice and did not
decide it, so the recipe prints the conflict and refuses to resolve it.

- A. Bay 0, where the lettering already is. The bar-back card moves from x 18
  to x 6 and the shop-shelves card from x 6 to x 18: two fields in
  `vignette-scene.json`, and the piece list regenerates.
- B. Bay 2, where the bar back already is. The Mickey's and Rita's Pawn
  fascias swap x.

RECOMMENDATION A, because a fascia is what a player reads from the street and
what the crime's witness names, while the interior card is a generated 768x512
image that moves by one field.
DEFAULT A if unruled by 2026-09-11. Until you rule, the recipe's default of bay
0 stands and says so on every run.
EVIDENCE: `game-design/decision-2026-09-08-crimeprobe-the-grate-and-the-art-line.md`
section 4.1, which reads the x values off `production/specs/vignette-scene.json`
577 to 580 rather than off the recipe's claim about them.

---
### How close should strangers stand?
CLASS: DECISION
added 2026-08-04, still open, and it now has the picture it was waiting for

Crowds pack to 45 cm apart, which is touching distance, and 36 people can
stand inside a two-metre circle. That is the separation rule working exactly
as written: it only stops bodies overlapping and nothing models personal
space. Whether that reads as a busy street or as a riot is a judgement off a
picture, not a number the studio should pick.

- A. 0.7 m. Crowded market street, people almost touching.
- B. 1.0 m. Normal British pavement distance between strangers.
- C. 1.4 m. Reserved, wary, a town where people keep their distance.

RECOMMENDATION B, because Meridian is a working port town and not a festival.
DEFAULT B if unruled by 2026-09-07, the Monday reset.
EVIDENCE: `game-design/sim-shots/vign_camA_night.jpg` is the street with people
absent; the crowd still that would settle this does not exist yet, which is the
honest reason this has waited a month.

THE DEADLINE PASSED AND THE DEFAULT TOOK, RECORDED 2026-09-09, TWO DAYS LATE.
By this card's own terms B took effect on 2026-09-07 when the Monday reset came
and went unruled. NOBODY APPLIED IT: no commit since that date changes a
separation number, checked with a log search over the term rather than recalled,
and the card went on reading "still open" in the waiting list. So the studio has
been running on 0.45 m, which is A and then some, while its own record said the
answer was B.
THIS IS THE DECAY THE DEFAULT MECHANISM EXISTS TO PREVENT, happening to the
mechanism itself: a default is only worth having if something applies it, and
nothing here watches a deadline. THE CARD IS NOT MOVED TO RULED, because that
would claim a change that has not been made. It stays here, saying what it is:
ruled by default, unapplied, and the smallest fix is the one that also stops the
next one, a check that reads every DEFAULT line's date.

---
## ON US, NOT ON HIM

A card sits here when it was a real ask and a later measurement showed the
nearest blocker is the studio's own, so there is nothing for Jafar to do yet.
It returns to WAITING the moment our half is cleared and the ask is still live.
Nothing here is pushed to his phone, by construction: `cards.waiting_cards`
filters on the WAITING heading and this is not it.

### The pages cannot be published until the studio's branch may deploy
CLASS: DECISION
added 2026-09-06, from queue 139

Every publish run since 2026-09-05T17:19, eleven of eleven, has failed in
seconds with zero steps executed:

    Branch "claude/game-dev-ai-automation-2h67ix" is not allowed to
    deploy to github-pages due to environment protection rules.

So the glance, the map and the gallery have never been served from this
branch, and every link the Producer's register allows points at a page
that does not exist yet. The card ruled A on 2026-09-05 said Pages "is
not refused"; that was true of the repository setting it measured and
not of the environment rule that refuses the deploy. Only a repository
admin can change it.

- A. GitHub, Settings, Environments, github-pages, deployment branches:
  add `claude/game-dev-ai-automation-2h67ix`.
- B. Name a branch already allowed; the studio publishes from it.

RECOMMENDATION A: one setting, nothing else moves.
DEFAULT: the studio waits. There is no action it can take in your place.
DEADLINE: none set. Nothing decays while it waits, and every day it waits
the Producer's messages link to nothing.

AMENDED 2026-09-09, AND THE AMENDMENT MOVES IT OFF HIS PHONE. Measured on publish
run 48 (commit 650f0755, 06:28Z): the job now fails BEFORE it reaches the deploy,
on our own gate.

    tools/gallery.py --selftest: FAILED. 11 passed, 1 failed, over 10 check(s)
      FAIL the live repository renders a gallery and every check passes
             got: failed=pageBytes
    ##[error]Process completed with exit code 3.

The gallery embeds every picture as base64, the live repository outgrew its own
1000000 byte budget (1000108, twelve pictures dropped), and the publisher runs
that selftest as a gate. Eight consecutive runs this morning, numbers 41 to 48,
failed this way. So the sentence at the top of this card, "every publish run has
failed in seconds with zero steps executed", describes 2026-09-06 and is NOT what
is happening today: runs now execute, get further, and die on us.

AND THE CARD'S OTHER SENTENCE IS ALSO WRONG, CORRECTED 2026-09-09 08:50Z. It says
the three pages "have never been served from this branch". Of 48 publish runs,
FOUR SUCCEEDED: 12, 13, 14 and 18, the last at 2026-09-07T20:23:12Z on commit
45de6c21, which is exactly the pageCommit recorded in production/map-notified.json.
THE PAGES EXIST AND ARE ABOUT 36 HOURS STALE. That is why this card is here rather
than on his phone: the ask it carries was written against a total outage that is
not the current fault, and the current fault is ours.

WHAT IS STILL UNKNOWN, and it is named rather than guessed: whether the
environment protection rule also still refuses the deploy. No run has reached the
deploy step since, so there is no evidence either way. The step summary still
prints `pagesEnableHttp: 403`, which is the agent proxy's answer and not
GitHub's, so it is not evidence about the environment either. The order of
operations is therefore ours first: un-embed the gallery, let a run reach the
deploy, and read what it says. That is the standing rule in `.claude/rules/ci.md`,
run the existing entry point and read its output before proposing a mechanism. If
the environment rule bites after that, this card returns to WAITING unchanged and
option A is still one setting.

---

## RULED THIS WEEK

### RULED 2026-09-06 BY JAFAR: A, keep both checkpoint repairs.

His word: "Ruling on the open card: A, keep both checkpoint repairs." So the
roadmap keeps them. Phase 4's gate now needs a resolved blow from a caller
outside Core, counted and printed, rather than being satisfied by
`Combat.StaminaAfterMoving` in the walk loop, which is what made it green today
before phase 1. Phase 1's gate now names arrest reachable from live play,
rather than going green while `CoatHost.Arrested` has zero callers.

Both rows now say the project is LESS far along than they said before, which is
the point of them and why the option to strike was real.

### RULED 2026-09-05 BY JAFAR: run 21 goes, item 6 of his standing order.

His words, recorded in production/NOW.md item 6 of the 2026-09-05 standing
order: "Then the game: 062 step 2, run 21. THE FIRST TEXTURED FRAMES COME TO
HIM AS IMAGES." That lifts the "wait for now" of 2026-09-03 and is condition
two of
game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md
section 5. Condition one, step 2 committed, is met by the commit carrying this
entry. Dispatch follows in its own commit with the sha captured first. If 21
prints materialConnections=12/14 that is the answer, reported and not retried.

### RULED 2026-09-05 BY JAFAR: A. Run the wake test tonight.

His words: "Card 1: A, run the wake test tonight." So the fifteen-minute
night is authorised: twenty-four firings, priced to within four hundredths of
a point, with the kill switch and the self-deleting trigger the card named.
ONE THING THE CARD DID NOT ANTICIPATE AND THE RESIDENT MUST HONOUR: the same
message ordered continuous building today, and the test night's own acceptance
refuses a contaminated window. So the window opens only when the build run has
stopped, and it needs his two readings at both ends. Queue 092 carries it.

### What may the studio spend to wake for your messages at night?
CLASS: DECISION
added 2026-09-05, from today's ruling on your standing order

You asked that anything you send the bot reach the studio within a few
minutes. The transport is built and lands today; the first message you send the bot is its test. The waking half does not.
Nothing on your PC can reach into the studio to start it, a turn begins only
when a trigger fires or you type, and the only trigger in place fires once a
day. So a message sent while the studio is asleep waits for the next turn, up
to 24 hours.

A fourth route, a doorbell your PC could ring to wake the session (a webhook),
[was tested and is shut](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/production/queue/088-the-inbound-path-from-his-phone-to-this-session.md):
it refused the exact request your PC would send, because its key is sealed to
one service. Of the three routes left, only a fast recurring trigger closes
your item as you wrote it, and it is not armed because what one firing costs
has never been measured. Choosing a cadence without that number would be
guessing with your meter.

The test night, if you choose one: the studio wakes on a trigger with nothing
to do but read the inbox and answer anything waiting, and you type both meter
readings as whole numbers, once when the window opens and once when it closes.
Anything else using the account inside that window, you or the studio,
contaminates the number, and a contaminated number is refused rather than
published. There is a kill switch: one command to the bot from your phone
stops the firings at the next one, because the studio cannot read the meter
and a night running hot cannot notice by itself. The trigger removes itself
when the window ends.

Whichever you choose, until one wake has been priced and you have set the
cadence against that price, your item reads as
[the ruling](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md)
amends it: anything you send lands as a dated note and reaches the studio
within a minute of its next turn; the bot's reply says whether the studio is
awake or asleep and, if asleep, when it next wakes.

- A. Every fifteen minutes for one six-hour night: twenty-four firings, each
  priced to within four hundredths of a point. The studio's guess for the
  whole night is about one point, and that is a guess, not a measurement.
- B. Every hour for one night first: six firings, each priced only to within
  a sixth of a point. Cheaper, and too coarse to price a five-minute cadence.
- C. Awake-only this week, no test. A message sent at night waits for the
  morning.

RECOMMENDATION A: it prices the cadence you actually asked for, at a cost
small enough to spend once.
DEFAULT C if unruled, because a default may not spend your meter; only your
ruling can.
DEADLINE 2026-09-07, the Monday reset. Nothing is armed before you rule, and
the night runs only when you can give both readings.

### RULED 2026-09-05 BY JAFAR: A. Publish as designed.

His words: "Card 2: A, publish as designed." The glance publishes with the
budget bar, on a page anyone with the URL can read, which he has now ruled
knowingly. Queue 097 is unblocked and does not wait for the default.

### The glance would be readable by anyone: publish it as designed?
CLASS: DECISION
added 2026-09-05, from today's ruling on your standing order

CORRECTED 2026-09-06: the repository setting is not refused; the environment
rule is, on every deploy since. See the card above and queue 139.

You asked to be told if GitHub Pages were refused. It is not refused: the
project on GitHub is public, so Pages is available and the glance can open on your
phone. What needs your ruling is the consequence, not the refusal. A Pages
site on a public project is readable by anyone who has the URL, and the glance
carries your budget percentages on both meters, the needs-you count and the
top item. Nothing new is exposed, because
[the budget page](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/production/budget.md)
those percentages come from is already public in the same project. That is a
reason this is not a new leak. It is not a reason it is fine, which is why
this is your call and not a builder's, and why the work that publishes it
[waits for your ruling](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/production/queue/097-publish-the-glance-so-it-opens-on-his-phone.md).

- A. Publish as designed, budget bar and all.
- B. Publish without the budget bar. The needs-you count and the top item
  still show; the meters do not.
- C. Do not publish. The glance stays a file inside the project, and a glance
  you cannot open from your phone is a file, not a glance.

RECOMMENDATION A: the exposure already exists, and the glance is the one thing
built to open on your phone.
DEFAULT A if unruled, because the exposure already exists and holding the page
back would not undo it. The default acts only once this card has reached you,
by the bot with a receipt or by your own word in the session, and 24 hours have
passed since; until then the deadline moves with it.
DEADLINE 2026-09-07, the Monday reset.



### 2026-09-04: the Telegram bot exists. RULED A, and it is done.

Jafar created the bot and put the token and chat id into
`tools/runner/config.local` on the PC, gitignored. The card asked for five
minutes; it got them before the deadline it named.

WHAT THIS UNBLOCKS: queue 067 goes from BLOCKED to READY and takes third place
in Monday's order, behind 062 step 2 and Unreal run 21. It was going to be
first after the reset; it moved back one place because the two Unreal items
end in something Jafar can look at and the bot does not.

THE STANDING RULE THAT COMES WITH IT, and it binds every agent: the file is
never printed, echoed, committed, quoted into a log or included in an error
message. A tool that cannot read it says `config.local unreadable` and quotes
nothing. `.gitignore` line 98 already covers the path, checked rather than
assumed, but a gitignore stops a commit and does not stop a print, and a print
is how this class of file actually leaks.

DO NOTHING WITH IT BEFORE MONDAY 14:00 CEST. Ruled by Jafar 2026-09-04.

### 2026-09-03: the next builder goes on the Unreal wire, not the Ledger
CLASS: DECISION
RULED BY JAFAR. Option A. One session.

Phase C is one unconnected pin from a textured Unreal street: 563 of 593
objects carry textures and every frame is grey because the texture coordinates
are unwired. The alternative was starting the Ledger, the social memory
system. A was chosen because it finishes something.

CARRIED INTO: `production/queue/062-uv-chain-head-refuses-to-wire.md`, which
is the live blocker, and it becomes the first show-moment row, "first textured
Unreal street", when item 9 of the console lands.
LIGHTER RULING, not a D-record: it schedules work rather than changing
architecture or identity.

## RULED THIS WEEK, in Jafar's own words

Recorded here on the director's instruction 2026-09-08, because the studio was
about to act on a paraphrase of a sentence that exists in no file. His words:

> "No further channel work this week. The supervisor's staleness is a recorded
> finding."

### The overnight standing order, 2026-09-08

Recorded for the same reason, and with a limit on it stated up front. THIS IS
NOT THE WHOLE MESSAGE. It survives only through a session summary written when
the context window filled, and that summary elided the middle of three priority
lines with an ellipsis. The elisions are Jafar's sentences, lost in the handoff;
they are marked below and must not be filled in by a later reader. What is
quoted is exact.

> "Readings: total 6, Fable 8, taken now, window not clean. Regime change: the
> plan is now Max 20x; every rate computed before this reading is void. Ceiling
> stays 75 on the governing meter. Overnight standing order. I am asleep until
> morning. Work continuously until the ceiling or a limit; on a limit arm the
> resume trigger and continue. Do not stop for me; anything that needs my taste
> becomes a Telegram card with a default and a deadline, and you carry on.
> Nothing reaches me outside Telegram. Priorities, in order: 1. The crime item
> [ELIDED]. This is the night's one required outcome. 2. The grate [ELIDED].
> Clip to my phone. 3. If 1 lands with budget left: the overheard consequence
> [ELIDED]. 4. The art line moves in-house [ELIDED]. Open art/atlas-02, pinned
> to tonight's HEAD [ELIDED]. 5. Images, when the runner is idle and behind
> every game build [ELIDED]. 6. Art budget share: at most a quarter of the
> week's points, yielding to game work for the PC and the runner. The weekly
> planner reports the split. Rules: no channel work; the supervisor's staleness
> stays a recorded finding. New findings go to the findings file, not the queue.
> Findings that block items 1 to 3 are fixed; nothing else is. Morning brief at
> 06:00: what landed, every clip and image, what needs my taste as cards, the
> split, the budget. If item 1 did not land, say why in one sentence, first."

WHAT THE RESIDENT DID WITH ITEM 3's ELISION, so the choice is auditable rather
than invisible: item 3 is being read as queue 147, which is the only filed item
whose line is "narrative (the overheard consequence)" and whose acceptance is
the rung above what run 32 achieved. Run 32 already printed overheardStatus=
HEARD, so item 3 cannot mean the beat itself and must mean its next rung. If
that reading is wrong, the work is not wasted, but the priority was.

HOW IT WAS APPLIED THE SAME DAY, so the exception is visible rather than
implied. The mesh import's evidence fault shipped: its verdict step died on
directory ownership and published nothing while the run had measured all
sixteen assets, which is CLAUDE.md rule 12, a blocked feedback channel, and
rule 12 outranks a scheduling preference. The art preview workflow has the
IDENTICAL fault and did NOT ship: it is queue 152, waiting, because nothing is
currently trying to read its output. The test applied was whether a channel
somebody is reading is blocked, not whether the word "channel" appears in the
task.

THE SUPERVISOR STALENESS is `production/findings.txt`, the entry titled "THE
SUPERVISOR HAS THE STALENESS IT WAS BUILT TO PREVENT, AND NO ROUTE TO FIX
ITSELF". It stays a finding this week by his ruling.

---

## RETIRED

`game-design/decisions-pending.md` is retired as of 2026-09-03. Its one live
card is above. Its answered cards stay there as history and are not migrated;
the ones that became decisions are D11, D12 and D13 in the register, and the
engine tie-break and deadline rulings live in the 2 September decision records.
