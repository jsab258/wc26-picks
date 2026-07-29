# Pending Player Decisions

Standing queue for anything the autonomous build loop cannot decide alone.
Each entry has options and a recommendation so they can be answered in batch.
Answered items move to the decision log in `process.md`.
Standing rule (2026-07-26): every queued decision is ALSO spelled out in chat
as answerable options — the doc is the record, the chat is the interface.

## ~~is violence a verb?~~ ANSWERED 2026-07-29 — YES, and it needs a weapon system

> *"That's an easy decision. So on question one, yes. Can also kill,
> obviously. And then question two, weapon. Yes. We need different weapons.
> So, yes, fists, and then knives, and then later on we said we'll look at
> guns. So we have to build it properly from the start."*

Also: an inventory, and acquisition by buying / stealing / finding.
Researched and proposed in **`weapons-spec.md`**. Nothing is built until it
is approved.

**Approval state, 2026-07-29:**

| Point | State |
|---|---|
| The reframing — crime game in a city that perceives and remembers | **APPROVED** |
| Perception first, weapons second | **APPROVED** |
| Guns at the last phase rather than never | **APPROVED** |
| The delivery window — a witness is a person walking somewhere to tell someone | **APPROVED** |
| Feel and legibility in general | **APPROVED** |
| Acquisition and carry — a coat not a grid, four social routes in | **APPROVED** |
| The observation model | Rebuilt in v2.1 §4; sent back as *"I don't get it"*, explained in chat — **open** |
| The weapon roster | *"7 feels too few and low budget"* → rebuilt in **v2.2 §5.2** as seven families, ~16 objects, the environment, and kit — **open** |
| How the player knows they were noticed | *"depends a lot on how clearly we model and animate characters"* → rebuilt in **v2.2 §6.2** as four redundant channels led by audio — **open** |

Three points open, listed in `weapons-spec.md` §12.

The standing quality bar was restated at the same time and applies to
everything from here: **as close to the best games in the genre as our
limits allow.**

The original framing is kept below because the reasoning is the record.

## (original) NEEDS YOU — is violence a verb? (2026-07-29)

**Nothing calls `Core/Combat`.** Not one line outside the file references
`Fighter`, `Blow`, `Footing` or `Resolve`, and `GameController.RecordKilling`
— the entry point that files a killing with the gossip mill and starts the
police inquiry — is never called by anything.

**I am fairly sure this is deliberate and I have not changed it.**
`GameController` says so: *"violence is deferred as a thing you DO and present
as a thing that has happened to you"* (roadmap M11). The half that is live is
`HarmBook` — injuries, feuds, capability loss — and it reports green in every
CI run (`injuries=2 feuds=1 harmOk=True`).

I raise it because I found it during an audit that had, an hour earlier, found
the entire post-processing stack had never executed a single frame: built,
tested, correct, attached to nothing. **From the outside those two look
identical.** One was a months-old bug; this is a decision. That is too thin a
margin to leave to a comment in an unrelated file, so the decision is now
stated at the top of `Core/Combat.cs` as well.

What is sitting there, finished: phases 1, 2, 3b and 4, with stamina, guard
and footing retuned after a fight lab found that mashing won 76% of fights and
took the least damage. Plus `Violence.Saw` for witnesses, `KillingConfidence`,
`Notoriety`, and `Homicide`'s procedure/investigation/manhunt ladder.

**RECOMMEND: leave it dormant for now, and decide it against a playtest rather
than against a build.** The game's whole claim is that the antagonist is
gossip; a punch button is the single fastest way to teach a player otherwise,
and no amount of simulation will tell you whether it cheapens the thing. It is
a few hours of wiring whenever you want it — the expensive half is already
written and tuned.

If you do want it, say so and it goes in with a sim gate that proves a fight
resolves and a witness files a rumour, the same way every other system here is
proved.

## Open now — 2026-07-27, six decisions

Ordered by how much they block. 1 and 2 are blocking real work right now;
3-6 are cheap and I will proceed on the recommendation if you say nothing.

**All six answered by Jafar the same day.** Kept here with the answers rather
than deleted, because the reasoning is the record of why the game is shaped
the way it is.

### 1. ~~Act III's crisis~~ — ANSWERED: **audit**. Wired and shipped 2026-07-27.

> *"1 audit"* — Jafar, 2026-07-27.

The act now opens off world state, names its date, fires its five pressure
points, and resolves into one of the five endings. See `roadmap.md` (ACT III —
SHIPPED) for what was actually built and what in it is still thin.

**The proposal, for the record: an audit.** Somebody with a mandate asks to see the bar's books,
and the books are the one document in this game that has been lying since day
one. Everything you did to the ledger becomes evidence in the other direction,
and it is wrong in both directions — launder too little and the night money has
nowhere to have come from, launder too much and the bar earned more than a bar
on this street possibly could.

**RECOMMEND: keep it.** It is the least dramatic instrument available and that
is exactly why it works — a courteous procedural letter is frightening in a way
a raid is not, it cannot be fought or shot, and it converts three acts of
quiet laundering decisions into the thing that convicts you. It is also the
only crisis that makes Lena's loyalty the most valuable thing in the game.

Alternatives, all defensible: **a raid** (dramatic, but fightable and therefore
smaller), **a betrayal** (a crew member turns — strong, but the empire systems
already do betrayal), **a death** (the biggest, and it would eat the ending).

### 2. Copper Row's character — BLOCKING a re-cut

Your design doc says: *"Copper Row (immigrant market quarter) — dense street
life, cash economies, loyalty."*

What I built this morning drifted **industrial**: a foundry, a smelt yard, a
ropewalk, kiln terraces. That is arguably Ironside's brief, not Copper Row's.
I invented it without checking the doc first.

**RECOMMEND: re-cut it as the market quarter the doc describes.** About twenty
minutes, the grid stays, the places get renamed — and it is the better district
for this game, because a cash-economy market quarter is where the purse system
and the debt system bite hardest. The industrial character can go to Ironside
when Ironside gets built.

### 3. UI has no automated test coverage — none at all

Every one of the 1182 tests is Core logic. Nothing tests a panel. This is the
weakest verification in the project, and it is why I could not honestly answer
"is the front end complete everywhere" without going and reading the code —
where I immediately found three keybindings that could not be rebound.

**RECOMMEND: a smoke-test pass in the CI sim** — open every panel, close every
panel, assert nothing traps the player and no panel is empty. Cheap, catches
the class of bug I just found, and does not need a UI test framework.

### 4. ~~Which district next, and how many~~ — OVERTAKEN by events, and the two docs disagreed (2026-07-29)

**All seven now exist as graybox** (M14 built Downtown, The Strip, Fairview and
Gullwing). So the original question — "build a third" — was answered while
nobody updated this entry, and `the-gap.md` §4 asks the opposite one: with
content volume the row on the comparison table that *cannot* be closed,
spreading a fixed budget of detail across seven districts buys seven thin ones.

**DONE, by recommendation:** stopped building geography and made detail
*concentrate*. Two dense cores — Hook, where the whole first week happens, and
Copper Row, because the writing already leans on it — with everything else
thinning by distance to a **floor rather than to nothing**. A bare street is
worse than a sparse one, and the whole argument for concentrating is that the
far places still have to read as places.

A distance ramp, deliberately not a per-district multiplier: a street where
clutter stops dead at a boundary the player cannot see reads as a bug, and is
more damaging than the uniform sparseness it replaced.

**If you want a different pair of dense districts, it is two coordinates in
`WorldBuilder.DenseCores`.** That is the whole knob.

*Superseded recommendation, for the record: build Ironside next and stop at
three. Ironside is still referenced by the population generator as though it
were real, which remains true and is now a writing loose end rather than a
build one.*

### 5. The sim bot's carelessness

The bot used to go bare-faced until day 3. With gossip running at its designed
rate it now loses the week on day 3, which costs CI every gate that only exists
in the open city. I changed it to coat up from night two.

**RECOMMEND: keep the change**, and treat the underlying number as a real
balance question for your playtest — the week may now be harder than intended
for a careless player, and only playing will say.

### 6. Purses in more payment paths

Currently debts only. Bribes, payoffs and supplier payments still assume the
other side has infinite pockets.

**RECOMMEND: extend to bribes and payoffs, not to supplier payments.** Paying a
supplier is money leaving *your* pocket, which is already finite; bribing
somebody who cannot make change is the interesting case.

### 7. ~~Options cannot be reached mid-game~~ — DONE 2026-07-27

Found during the front-end pass. The pause menu has Resume, Save now, Save
and quit to menu, Save and quit to desktop — **and no Options.** The only way
to change text size, sensitivity, volume or a keybinding is to quit to the main
menu and go in from there.

**RECOMMEND: lift the options panel out of MainMenu into its own component and
show it from both.** It is the standard expectation and the current shape fails
it. Roughly an hour, and it is the last structural gap in P1.

**Built.** `OptionsScreen` is now one screen that both the main menu and the
pause menu open, on its own overlay canvas so it works over a live city. It was
an EXTRACTION rather than a second copy on purpose: the last time this front end
had two lists of the same thing, they drifted and three keys became
un-rebindable. Escape backs out one level like everywhere else, and the screen
owns the keyboard while it is up — the first version of that guard sat after the
Talk key, so a player adjusting the volume could still start a conversation with
whoever they were standing next to.

### 8. The inspector's name — DECIDED, override freely

Act III's audit had no face, which was its biggest gap: the letter arrived,
the date passed, and the books were read offstage by nobody.

**Built as Tobias Reese, Board of Excise, nineteen years.** Fifty-ish, grey,
the sort of man who is already sitting down when you notice he came in. Not
corrupt — and that is load-bearing rather than characterisation, because an
inspector with a price collapses the ending matrix into "did you save up".
Not cruel either: he explains each step because the procedure requires it,
and says "of course" when you refuse him.

Taken on the same basis as Tom Novak (*"0 — you choose a name"*). Say the
word and he becomes somebody else; nothing but the name and the card moves.

### 9. ~~The rackets are the last infinite pocket~~ — ANSWERED: **couple it**. Built 2026-07-27.

> Jafar, 2026-07-27: *"Couple it."*

`Empire.DailyTick` now takes a street factor and the take scales with it, so a
starved district pays less. It is not silent about it: below 0.7 somebody says
*"They're not holding out. There's nothing on that street to hold out with."*
The CoreTest that pinned the OLD behaviour was flipped to demand the coupling,
plus one asserting that a person says why.

Measured over 400 worlds: cautious rounds fell 468 → 434 as prosperity dropped
to 0.40. The squeeze is now two turns of the same screw, which was the idea.

*(Original writeup below, kept because it is the reasoning that got the answer.)*

`counterparty-purses-spec.md` excluded rackets, and gave a reason:

> NOT in scope: rackets (already coupled through prosperity — a per-business
> till would double-count the same pressure)

I went to extend purses into the remaining payment paths and checked that
claim. **It is half true, and the half that is missing is the half that
matters.** In `Empire.DailyTick` the take is literally `int income =
r.IncomePerDay` — a flat number, modified afterwards by your crew's cut, the
New crew's tax and any treaty, and by nothing about the street.

- Rackets → prosperity: **yes**. `racketToday` feeds `Economy.DailyTick`, so
  squeezing the street does make it poorer.
- Prosperity → rackets: **no**. Nothing anywhere scales the take by what the
  street can actually pay.

So you collect the same sixty a day from a district you have starved as from
a prosperous one. That is the exact shape the purse system exists to
delete — a payout table wearing a person's face — and it is sitting on the
player's primary income in the open city.

It also quietly weakens the living economy's best idea. The squeeze is
supposed to be *two turns of the same screw, and the second is the one that
hurts*: you drain the street, and a few days later you are the one who
notices. Right now only the bar's takings notice. The rackets never do.

**RECOMMEND: couple it, at the district level rather than per-business.**
Scale the daily take by the same `Economy.FactorFor` the bar already uses, so
a starved street pays less, and let a very poor district produce the fourth
collection outcome that already exists for debts — *paid what they could*,
said as somebody's circumstance rather than a number. That is one line of
coupling plus a line of text, it does not need per-shop tills, and it does
not double-count anything, because right now it does not count at all.

**Against it:** it makes the aggressive path materially harder, and the
balance lab has never run against it. If you would rather feel that in play
before I change it, say so and I will leave it and note it in the lab's
findings instead.

**Not doing anything until you answer.** Decision 6 (bribes and payoffs) is
already built — money you spend on people lands in their drawer, and a
bribed man carries cash he cannot account for.

### 10. ~~The inspector may be too decisive~~ — ANSWERED: **halve the relief**. Built 2026-07-27.

> Jafar, 2026-07-27: *"Halve the relief now."*

`ScopeFactor`'s cooperation term went 0.09 → 0.045. Stonewalling KEPT its full
0.15, and the asymmetry is deliberate: being difficult moves him further than
cooperating does.

What it did, 400 worlds a row:

| plan | before | after |
|---|---|---|
| Aggressive, answered every morning | 100% Kingdom | **100% Burn Both** |
| Cautious, answered every morning | 100% Kingdom | **48% Kingdom / 52% Burn** |
| Cautious, answered + deflected | 13% Both | 15% Both |

Six mornings of paperwork no longer outweighs three acts of laundering.
**Whether it now FEELS right is a playtest question**, and it is still one
constant — dial it either way in a minute.

*(Original writeup below.)*

#### The original case — a tuning judgement, with numbers

The ending matrix has now been measured for the first time
(`balance-findings-endings.md`, 400 worlds a row). Three real holes came out
of it and I fixed all three, because each was a violation of something
already decided rather than a preference:

- a player who never built an empire had **no ending but Burn Both**;
- **Both fired 51-58%** against a design that calls it rare and your
  decision that it should not be reachable on a first playthrough (now 13%,
  and only for a careful campaign);
- empire kept + life kept + audit survived fell through the matrix into
  Burn Both, having survived the thing that was supposed to take it.

**What is left is genuinely a judgement, so it is yours.** On the aggressive
plan the inspector swings the result completely:

| | ignored | answered every morning |
|---|---|---|
| Aggressive | 100% Burn Both | 100% Kingdom |

Six mornings of producing what a revenue man asks for currently outweighs
three acts of laundering decisions. In its favour: that row is *perfect* play
against him, five cooperations out of six possible, and the verb was built
precisely so the last week is playable rather than a wait. Against it: the
whole crisis is supposed to be the bill for how you ran the business, and
right now the bill can be argued down almost entirely at the counter.

**RECOMMEND: leave it until you have played it.** It is a single constant
(`ScopeFactor`'s 0.09 per cooperation) and it is trivially dialled either
way; what it should feel like is exactly the sort of thing the numbers
cannot tell us and one playthrough can. If you would rather I weaken it
now, halving the per-morning relief puts the aggressive answered row at
roughly a coin flip instead of a certainty.

## Previously open

*(nothing blocking — the all-night run works on standing mandates. Items
for whenever you surface, in the order I'd want them answered:)*

0. **~~The protagonist has no name.~~ ANSWERED 2026-07-27 — delegated to me.**
   He is **Tom Novak**, Mickey's sister's boy, off the boat with a suitcase
   and a letter. Novak sits beside Sedlak, Brela and Farid without sounding
   imported, it is two syllables and hard to soften, and it is a word
   (willow) — the kind of name a city shortens without affection.

   **The part that turned out to be a design decision:** I came to this
   expecting to find-and-replace "the new owner" and that would have been
   wrong. *"The new owner" is not a placeholder — it is what people call
   you before they know you*, and this is a game about being known. So the
   name is something the street LEARNS, and what somebody calls you is now
   a readout of where you stand:

   | | |
   |---|---|
   | the new owner | they know the bar changed hands, not who you are |
   | Novak | you are a fact on this street now |
   | Tom | they decided about you, and it was fine |
   | Toma | two or three people, ever |

   Appended to every conversation's scene, so the model uses the right one
   without it being hand-written into thirty character cards. Renaming is
   free and field-by-field — it is data, not a constant — and gender is
   deliberately still unset, since the street mostly uses the surname.

0b. **Day length.** A day is 12 real minutes. Nobody has ever checked
   whether that feels right, because nobody has played it. This is the
   single number most likely to be wrong and the cheapest to change — one
   constant. Judge it in the first session: does the drop window feel like
   an obligation or a countdown, and does the morning arrive too fast to
   act on what you learned last night?

1. **Empire tuning taste check.** This has moved since it was written. With
   the living economy in (M7), aggressive play now nets $94 LESS than
   running no rackets at all, despite $1697 of racket income — because
   squeezing the street makes the street poorer and your bar takes less.
   That is the intended shape ("position over profit", now with a real
   mechanism), but it is a strong reading and only play will say whether it
   reads as a meaningful trade or as futility. RECOMMEND: feel it first;
   `SqueezeCostsProsperity` is the one knob and it is documented.
2. **Playtest when ready** — the latest green LEDGER-Windows artifact is
   the whole game now. A suggested first session (~45 min):
   - Play the week straight: talk to Lena day 1 (the cellar line), meet
     Noor day 2 (she'll bring up the fire), honor Ada's tea (day 3) and
     Rocco's toast (day 5), make your drops in the coat.
   - Day 7: answer Lena's question over the true books. Then press SPACE.
   - In the open city: talk to Sam (sort what he needs, put him on the
     collection round), find Victor (buy his marker with dirty cash, then
     turn the key), then talk to Rita once the shop is yours — her line is
     the best money on the street. Press L: THE TWO BOOKS.
   - Watch what the Dockside arm does about it. Try skimming someone's
     envelope for a few days and read their memory file (F1) after.
   - Things to judge: does the week feel like a tutorial or a slog? Does
     day 8 feel like an opening? Is the empire's pace right? Chips useful?

## Will need you at the vertical slice (M5) — ALL DEFERRED as long as possible (player, 2026-07-26)

Player direction: delay purchases/accounts/manual steps as far as they can be
delayed and keep building everything else on procedural/fallback assets. Each
item below now lists its true blocking point — the moment further delay stops
being possible:

1. **Asset budget release** (~$40–60 city pack; Character Creator ~$99/yr
   go/no-go). Blocks: only the final art pass of M5 — layout, lighting,
   systems, story all proceed on AssetLibrary procedural fallbacks (designed
   for exactly this: pack drops in with no code change).
2. **HDRP swap session** (human in the Unity editor). Blocks: final slice
   visuals only; built-in RP remains the working target until then.
3. **ElevenLabs voice** (account, key, casting). Blocks: voiced-slice gate
   only; subtitles-first design (§9) means everything ships text until then.
4. **The is-this-fun gate** — your playtest verdict on the M2–M4 loop (the
   LEDGER-Windows artifact from any green build). Cannot be deferred
   indefinitely: it decides whether M5 polishes this design or we iterate
   the core first. Also watch: drop-window feel (obligation vs countdown).
5. **API-key batch session** for Tier-2 district generation (Open City
   decision 3: generation ships WITH Empire v1/M6). Blocks: M6 kickoff.

## ~~Traffic: can you run people over?~~ ANSWERED 2026-07-27 — the middle option

**Collisions that hurt but do not kill**, as chosen. Built the same morning.

A knock at walking pace is nothing; the top of the arcade speed range is a
broken bone and a very bad morning, and that is the whole range. Nothing in
the code can produce a death, which is a property rather than a tuning
value.

What it costs the player is the interesting part, and none of it is new
machinery — it all lands in systems that already existed:

- The victim is really hurt, on the M11 harm system: it persists, it shows,
  it turns if nobody treats it.
- They remember it in their own words, and lose a lot of loyalty. *"It was
  not on purpose. That is not the same as it being nothing."*
- Everyone nearby holds it as a hard fact at 0.95 confidence — **and this
  is the one thing the coat cannot soften**, because they did not see a
  figure, they saw a car and what it did.
- It records a low-heat exchange rather than a feud. An accident is not a
  war. It is the kind of thing that becomes one if it goes unanswered, and
  that is left to the player.
- Your car stops hard, so you get the beat where you understand what just
  happened instead of leaving it behind at forty.

AI drivers still brake for everybody, always. An NPC car maiming a
pedestrian while the player watches is a consequence with no decision
attached, which is the definition of noise. **Only the player's car can
strike anybody**, because the player is holding the wheel — and that is
exactly the difference between a system and a decision.

## The old writeup, for the record

**Was: no.** Cars brake for anybody in the road and wait there while
they stand in it. That is enforced in Core and held as a test, so it is a
design position rather than something that merely has not been built.

I built it that way and flagged it rather than deciding it, because it is a
real fork and it is yours:

- **Keep it (recommended).** Vehicular death would eat the gossip and
  investigation systems whole — every witness in the district would have
  exactly one thing to talk about for the rest of the campaign, and the
  careful machinery around disguise, confidence decay and hard facts would be
  drowned out by the loudest possible event. It also makes the streets safe
  to walk, which is what makes the crowd usable as ambience.
- **Add it as a consequence system.** Doable, but it is not "turn off the
  brake": it needs manslaughter as a state the world reacts to — a body, a
  crowd, an investigation with a different shape from the ones we have, and
  a rival/police response. That is a milestone, not a flag.
- **Middle option.** Collisions that hurt but do not kill: knocked down,
  gets up, is furious, remembers your car. This sits inside the systems we
  already have — it is a hard fact with a vehicle attached — and costs a
  fraction of the second option.

No action needed before you play. The city works either way.

## ~~Does prison launder the information landscape?~~ DECIDED 2026-07-28 — option C, by recommendation (Jafar delegated: "go with your recommendations")

**The mechanics today.** The Fall deletes every live player rumor (the street
stops speculating — now they KNOW) and writes `did_time` into everyone's head
as hard knowledge. But no heat consumer reads knowledge — heat is computed
from live rumors only. So an audit that closes after a Fall reads the day
circle's racket heat as ZERO, Act III's "managed information landscape" leg
credits you for it, and the epilogue calls your street quiet. Three days in
prison is mechanically the best information-management move in the game.

**Why it isn't obviously wrong.** "You did the time; the ledger is settled"
is a real position — the Fall already costs you the outfit's patience, the
scarring, and every live lead dying is TRUE (nobody needs to speculate).
The surviving-lead machinery added for the Both ending reads correctly here:
a served conviction is not a live lead Ellis can take to a magistrate.

**Why it smells.** A state inspector, of all people, can read a conviction
record. The whole day circle watched you go. Crediting that player with a
managed landscape — the same credit as someone who spent three weeks
leashing witnesses and buying silence — flattens the act's central skill.

**Options.**
- **A. Status quo, documented.** Prison settles the books. Cheapest; the
  Fall's other costs already price it.
- **B. Heat floor.** Public `did_time` floors the audit's heat read (~0.3):
  the street being certain is hotter than the street speculating. Touches
  the epilogue too.
- **C. Strain term (recommended).** `did_time` as street knowledge adds a
  modest term to what the INSPECTION sees (SeenStrain), leaving heat and
  the epilogue alone. A conviction is exactly the thing an auditor can
  read; the street's mood is separate. Small, targeted, testable in the
  lab before wiring.

**Built:** SeenStrain reads a PublicRecord term (x1.15) when the street
KNOWS did_time — knowledge, not rumor, so no leash or denial touches it.
Heat and the epilogue stay as they were: the street stops talking, the
state does not stop reading. Measured over ~400 worlds/cell: Control and
Cautious rows essentially unchanged (Both still 6.1/12.9%); aggressive
campaigns that FELL now mostly cannot keep the kingdom through the audit
(deflect road 100% -> 30.4%, strain 0.60 against the 0.62 keep-nothing
line). The ledger comes due, which is the name of the act.

## ~~Should dirty money pay the drayman?~~ DECIDED 2026-07-28 — keep it, written into the fiction, by recommendation (delegated)

The wallet's own rule says dirty cash is for criminal counterparties — but
weekly supplier deliveries and MakeAmends are paid with dirtyOk: true, so
unwashed money buys the drink and the flour. Two readings:

- **Enforce the rule (clean only).** Purist; makes washing matter more.
  But a dirty-heavy campaign short on clean cash starts losing suppliers,
  which shifts balance noticeably — I did not want to move that the night
  before you play.
- **Keep it, as written into the fiction (recommended).** A supplier to a
  mob bar taking cash off the counter is not a bank; he is exactly the
  kind of grey counterparty the rule contemplates. If you keep this, the
  wallet comment should say so, so the next audit doesn't flag it again.

**Built:** the line is in Wallet.cs — the drayman is a grey counterparty
and the fiction says so; the next audit reads intent, not an oversight.

## M15 — the immersion milestone, and one purchase (2026-07-28)

Playtest note: *"overall feel is very text heavy / text adventure like...
the goal is real-feeling characters (KCD2 did well, improve with LLMs)."*

Full proposal in `m15-the-world-speaks.md`. The diagnosis in one line: we
built a causal gossip simulation and hid it behind a text panel —
`ReportOverheard` already detects two NPCs trading a rumour about you six
metres away, and its entire output is a row in the ledger. The player
hears nothing.

**Proceeding without asking on M15.1 and M15.2** (system work, no
purchases): make the city audible — overheard exchanges become generated
speech in the speakers' voices, ambient NPC-to-NPC conversation, chatter
volume as the heat meter, recognition barks you can stop and interrogate;
then bodies that perceive you — gaze, the notice/watch/comment/avoid/
refuse/confront ladder, occupation stations.

**NEEDS YOU — M15.4, real bodies.** Character models plus an animation set
(idle/walk/work/talk/react) and gaze rigging. Capsules undermine every hour
spent on gaze and reaction, because there is nothing to read them on. This
is an asset-store PURCHASE and therefore yours by standing rule. Options:
a character system (Character Creator-class pipeline) plus an animation
library, or a cheaper stylised character pack if we want to lean away from
realism. Say the word and I will spec exact candidates and prices rather
than buying anything.

**Also needs you eventually:** M15.3 deletes the ledger panel and the
toasts in favour of Mickey's actual book as a prop. That removes things
that currently "work", so I will not do it until you have seen M15.1-2.

## THE VOICE — engine decided, casting is yours (2026-07-28)

### Engine: CHATTERBOX. Decided by me, on measured evidence.

Four engines were benchmarked on real game dialogue. Jafar's verdicts:

| engine | direction (BORED vs GRAVE) | emphasis on "your" | consistency | verdict |
|---|---|---|---|---|
| **chatterbox** | **different** | **slightly emphasised** | *"was, alive"* | **chosen** |
| kokoro | *"exactly the same"* | — | — | crowd ambience only |
| piper | *"same"* | *"no stress"* | *"all sound the same"* | the floor |
| xtts | never ran | — | — | moot, see below |

This is a technical decision on measured evidence, so I made it. It is here
because you should be able to see the reasoning and overturn it.

**Why it is not close.** Direction was the one criterion that mattered, for
the reason argued in production-plan §1d: the game already knows how every
speaker feels, and an engine that ignores that gives us pre-recorded voice
acting with extra steps. Three engines failed it identically. Chatterbox is
the only one that passed, and it passed the harder consistency test too —
*alive* rather than piper's degenerate *uniform*.

**XTTS is now moot and I am not asking you to run it again.** Its unique
selling point was cloning; chatterbox clones as well. Running it would buy a
comparison, not a decision, and it has already cost enough of your evening.
The dependency fix is committed in case we ever want it.

### NEEDS YOU — 1. Where do the reference voices come from?

> *"don't like the actual voice but I guess there are many we can generate
> with"* — Jafar, 2026-07-28

Better than that: **we do not pick from a menu, we define the voice.**
Chatterbox clones from about ten seconds of reference audio, so whatever we
give it becomes Lena. The v6 benchmark already reads `lena.wav`,
`lena.grave.wav` and `lena.bored.wav` and picks by the line's stage
direction — which means the reference clips carry the CASTING and the
DIRECTION at the same time.

Three routes:

**A. ~~Record our own~~ — RULED OUT by Jafar, 2026-07-28.**

> *"I'm not going to record anything. if anything you can collect suitable
> samples and use those"*

His call, and it stands. What follows is how I do B without walking into the
consent problem I raised against it.

**B. A public-domain corpus** (LibriVox and similar). Free, enormous
variety, legally clean as to copyright — the recordings are released public
domain.

**C. Buy voice samples.** Unnecessary; A and B cover it.

**So: B, sourced by me, under one rule.** The concern I raised was never
copyright — it was consent, and "the file was free" does not answer it. But
that concern has a clean solution short of recording ourselves: use corpora
whose contributors donated their voices **specifically to build speech
technology**, rather than corpora that merely happen to be free to copy.

| Corpus | Licence | Donated for speech tech? | Accent |
|---|---|---|---|
| **Mozilla Common Voice** | CC0 | **Yes, explicitly — that is its entire purpose** | many US English |
| LibriTTS / LibriSpeech | CC BY 4.0 | No — audiobook readers, repurposed | US English, clean |
| LJSpeech | Public domain | No | one US female |
| VCTK | CC BY 4.0 | Yes | mostly British/Scottish — wrong for us |

**Common Voice is the one I will use.** Contributors record clips knowing
they are building speech technology and release them CC0; that is as close
to consent for synthesis as a public corpus gets, and it has the accent the
setting needs. LibriTTS is the fallback if a particular timbre is missing.

Two rules I will hold to without being asked: **no identifiable public
figures**, and no corpus whose licence does not cover synthesis. If a
character needs a voice I cannot source cleanly, I will say so rather than
quietly reach for something looser.

**What I will bring back:** a shortlist of candidate clips per character,
already trimmed to ~10 seconds and matched to the character notes by
timbre. You approve by ear — listening to five clips, not researching
licences.

### ~~2. Who sounds like what?~~ DONE — I cast it, as delegated

Full briefs for all five principals, eight street characters and the crowd
are in `game-design/voice-casting.md`. Written as briefs rather than
preferences: each says what must come through, so any clip carrying it is a
valid casting — which is what makes it sourceable at all.

Three of them are cast deliberately against the obvious reading, and those
are the ones worth arguing with if you disagree:

- **Mara Ellis** gets the WARMEST, most reasonable voice in the shortlist.
  A cold detective is a villain; a courteous one is inevitable, and the
  menace is entirely that she never has to raise her voice.
- **Hal** gets the least distinctive voice in the game, on purpose. He
  carries messages and nobody knows his first name. Being forgettable is
  his job.
- **Rocco** is not a tough-guy voice. He is a tired one.

The rest of the roster — Tibor, Ferko, June, Victor, Zlata and the others —
deliberately get NO dedicated clips until playtest says one of them needs
to be somebody. Spending a voice on a character nobody remembers is how a
cast becomes a phone book.

### THE REMAINING BLOCKER — sourcing. FETCHER BUILT 2026-07-28.

Common Voice, HuggingFace and OpenSLR are all blocked from my environment.
I checked rather than assumed; it is the same wall that stops me reaching
the CC0 texture sites. So the clips have to come from your machine — and
your part is now two commands and about fifteen minutes.

```
cd tools/voice-fetch
python ledger_voice_fetch.py          # streams candidates, opens a page
# listen, write picks into ledger-voices-out/picks.txt
python ledger_voice_fetch.py --install
```

It builds its own environment, **streams** Common Voice rather than
downloading it (the English tarball is tens of gigabytes and we need three
and a half minutes of it), filters on the age and gender each brief asks
for, and prints the brief above each character's players so you are judging
against the character rather than against which voice is nicest.

**Nineteen clips, not thirty-seven** — and that is a correction rather than
a saving. Common Voice contributors read neutral sentences, so the "grave"
and "bored" clips the casting doc asked for were never sourceable from that
corpus at all. What the direction test actually proved is that chatterbox's
exaggeration control does moods, which you heard yourself. So the reference
clip decides IDENTITY and the parameter decides DIRECTION.

**What I could not test is the download itself**, for the reason above. So
the fetcher reports per character what it could not find instead of failing
quietly, and there is a `--source libritts` fallback whose rows carry no age
or gender — the script says so rather than pretending the filter worked.
The assembly logic (which is the part that is actually hard: a Common Voice
sentence is three to six seconds and a clone needs eleven, so a candidate is
the same speaker concatenated with real silence between sentences) has 22
checks that touch no network at all.

**Your part is a listening pass, not research.**

### (superseded) Who sounds like what — a listening task, not a research task

Casting stays yours because it is a creative call, but you should not have
to start from a blank page or read a licence. I will bring a shortlist of
trimmed candidate clips per character; you say which one is Lena.

### Kokoro: dropped, not deferred

> *"why are we using kokoro? will it be better than what we generated now,
> because that sounds like shit"*

We should not have been. It was kept for live crowd murmur and that
justification does not hold: crowd ambience is the most pre-generatable
speech in the game, so it never needed to be live, and a second engine buys
a second voice identity and a second quality ceiling — a crowd that audibly
does not belong to the same world as the cast. Chatterbox does the crowd in
the same overnight batch. One engine.

## Standing rules honored meanwhile

- Design/story/character decisions → this queue, with a recommendation,
  AND spelled out in chat.
- Purchases/keys/accounts → never without you; now also: as late as possible.
- Model/config → unchanged unless you ask.
