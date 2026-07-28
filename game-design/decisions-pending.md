# Pending Player Decisions

Standing queue for anything the autonomous build loop cannot decide alone.
Each entry has options and a recommendation so they can be answered in batch.
Answered items move to the decision log in `process.md`.
Standing rule (2026-07-26): every queued decision is ALSO spelled out in chat
as answerable options — the doc is the record, the chat is the interface.

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

### 4. Which district next, and how many

Two of seven exist. Ironside is referenced by the population generator and the
research notes as though it is real.

**RECOMMEND: build Ironside next and stop at three for now.** It is the one the
code already half-believes in, it is the doc's "places without witnesses" which
is directly useful to night work, and three districts is enough to prove the
district system without spending the whole runway on geography.

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

**Built as Tobias Reisz, Board of Excise, nineteen years.** Fifty-ish, grey,
the sort of man who is already sitting down when you notice he came in. Not
corrupt — and that is load-bearing rather than characterisation, because an
inspector with a price collapses the ending matrix into "did you save up".
Not cruel either: he explains each step because the procedure requires it,
and says "of course" when you refuse him.

Taken on the same basis as Tomas Vrba (*"0 — you choose a name"*). Say the
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
   He is **Tomas Vrba**, Marek's sister's boy, off the boat with a suitcase
   and a letter. Vrba sits beside Sedlak, Brela and Farid without sounding
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
   | Vrba | you are a fact on this street now |
   | Tomas | they decided about you, and it was fine |
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
     collection round), find Viktor (buy his marker with dirty cash, then
     turn the key), then talk to Ruta once the shop is yours — her line is
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

## Does prison launder the information landscape? (audit finding, 2026-07-28)

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
a served conviction is not a live lead Ossei can take to a magistrate.

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

No action taken — this changes what an ending means, so it is yours.

## Standing rules honored meanwhile

- Design/story/character decisions → this queue, with a recommendation,
  AND spelled out in chat.
- Purchases/keys/accounts → never without you; now also: as late as possible.
- Model/config → unchanged unless you ask.
