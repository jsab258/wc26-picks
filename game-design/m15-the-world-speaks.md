# M15 — The world speaks for itself

> **STATUS: SPEC.** The design for M15 — the world speaks for itself. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

**Status: PROPOSAL, 2026-07-28.** Written after Jafar's first playtest note:
*"overall feel is very text heavy / text adventure game like. that is not the
goal. the goal is to have real-feeling characters (something KCD2 did well,
but improve upon it with LLMs)."* The first answer offered — barks, physical
reactions, visible tells — was correct and too small. This is the bigger one.

## 1. What KCD2 and GTA actually do

Not a feature list. One principle, applied without exception:

> **The simulation IS the interface.**

Neither game has a "reputation meter". KCD2 has villagers who look at your
bloodstained gambeson and step back. GTA has a pedestrian who films you with
a phone. In both, the state of the world is delivered by the world behaving —
and the player learns to read behaviour the way you learn to read a face.

Three things follow from that principle, and all three are load-bearing:

**a. The world is busy without you, and it never announces itself.** Two
villagers argue about a debt you have nothing to do with. A drunk sings. The
information channel is *ambient and overheard*, not addressed to the player.
This is what makes a place feel like it existed before you arrived.

**b. Bodies do the emotional work.** Weight, wind-up, follow-through, gaze.
KCD2's characters *look at you*. When someone recognises you, the recognition
is in the head-turn, not in a notification. Animation is not polish here; it
is the medium the game's meaning travels through.

**c. Your appearance is a running record of what you have done.** Blood,
dirt, torn clothes, the horse you rode in on. You are legible to others
because you carry your history on you — and you *feel* it because strangers
respond to it before you have said a word.

## 2. Where LEDGER actually is

We built a world-class gossip simulation and then hid it behind a text panel.

That is not a figure of speech. `GossipDirector.ReportOverheard` already
detects the exact moment two NPCs exchange a rumour about the player within
six metres — the single most immersive event this game can produce — and its
entire output is:

```
_game.Knowledge.Learn(...);   // a row appears in a panel you press L to read
Overheard++;
```

**The player hears nothing.** Two people are standing in front of him talking
about the warehouse fire, and the game's response is to add a line to a
ledger. Every one of the six playtest notes is downstream of that same
mistake, made in different places:

| What the world knows | How the player currently learns it |
|---|---|
| Who saw you, and how sure they are | a panel, in words, on the L key |
| The street's mood about you | a status line at the top of the screen |
| Somebody just heard a rumour about you | a row in the ledger |
| That person is a night-circle regular | a floating name |
| Your night life collided with your day life | a toast that appears for 14 seconds |

Every row on the right is the world failing to express itself and delegating
the job to text. The legibility law we wrote earlier — *"if a number cannot
be said as somebody's circumstance, do not show it"* — was half the law. We
obeyed it by converting numbers into WORDS and then printing the words. The
whole law is:

> **Do not show it. Stage it.**

## 3. The thing only this game can do

KCD2's barks are recorded, finite, and generic — a guard has forty lines and
you will hear all of them. GTA's pedestrians say one canned thing and cannot
be asked what they meant.

We have an LLM and a causal gossip network. That means:

- A bark can be **specifically, causally true**: this person says *this*
  because they heard it from *that* person who saw you at *that* place. Not
  "I heard you've been busy" — "Rocco says you were down at the warehouse the
  night it went up."
- A bark can be **continued**. In GTA an overheard line is a dead end. Here
  you can stop, press E, and ask them what they just said — and they know,
  because it is in their memory.
- NPCs can **talk to each other, generated, about their own lives** — the
  ambient argument about a debt that has nothing to do with you. That is what
  makes (a) work, and it is currently 100% absent.

**This is the game's actual competitive claim, and it is unshipped.** Not
"conversations with NPCs" — every AI demo has that. *A city that gossips
about you out loud, truthfully, and can be interrogated about what it just
said.*

## 4. The milestone

Four phases. Each is playable on its own; the order is by immersion-per-hour.

### M15.1 — The city becomes audible (system work, no assets)
- **Overheard exchanges become SPEECH.** When the mill passes a player rumour
  between two agents in earshot, they say it — floating world-space lines
  above the speakers, generated from the rumour's actual content, in the
  speakers' voices. The ledger entry becomes a *side effect* of having heard
  it, not the event itself.
- **Ambient two-NPC conversations** about their own lives: debts, weather,
  prices, the fire, each other. Generated in cheap batches, cached per pair
  per day, so cost stays bounded.
- **Chatter volume IS the heat meter.** A hot street is a loud one. Delete
  the status-line heat word once this lands.
- **Barks on recognition**: someone who holds a strong rumour about you says
  something as you pass — and can be stopped and asked.

### M15.2 — Bodies that perceive you (system work, crude on capsules)
- **Gaze**: heads turn to track you at a distance scaled by how interesting
  you are (suspicion, notoriety, the coat).
- **The reaction ladder**, driven by existing state: *notice → watch → comment
  → avoid → refuse → confront*. Conversation in the bar stops when you walk
  in hot. People cross the street. A door does not open.
- **Occupation stations**: NPCs work at a place with a visible activity loop
  rather than standing at a waypoint. The market sells, the docks load.

### M15.3 — The interface disappears (design + UI work)
- **The ledger becomes Mickey's actual book**, a prop on the bar counter you
  walk to and open. Not an L-key panel.
- **Toasts die.** Every one becomes either a spoken line, a world event, or a
  line in the book you chose to open.
- **The HUD reduces to the clock**, and eventually to the sun.

### M15.4 — Real bodies (ASSET work — needs Jafar)
- Character models, an animation set (idle/walk/work/talk/react), and gaze
  rigging. Capsules undermine every hour spent on M15.1–3, because gaze and
  reaction have nothing to read them on.
- This is a **purchase decision** (asset store character system + animation
  library) and therefore Jafar's, per standing rule.

## 5. Honest costs and risks

- **M15.1 is the highest value per hour in the whole project** and needs no
  assets. It is also where the LLM cost model gets real: ambient chatter is
  many small calls. Mitigation: cheap model tier, per-pair-per-day caching,
  strict token caps, and it degrades to silence without a key.
- **M15.2 is cheap to build and looks wrong on capsules.** Worth doing anyway
  — the *behaviour* reads even on a capsule (a capsule that turns to face you
  and then walks away communicates plenty).
- **M15.3 will feel like losing features.** Deleting the ledger panel removes
  a thing that "works". It is still right: the panel is the crutch that let
  the world stay mute.
- **M15.4 is the biggest single lift in the project** and the one that most
  changes how it feels. Everything else is scaffolding for it.

## 6. What this replaces

The design doc's §9 "LLM only fires on player engagement and nightly
reflection batches" is now wrong. Ambient generation is a third channel and
the cost envelope has to be rewritten around it.

## 7. The question for Jafar

The recommendation is **M15.1 first, immediately** — it is pure system work,
it needs nothing bought, and it converts the simulation we already have from
invisible to audible. M15.2 next for the same reason.

M15.4 needs a decision and a budget before anything else in it moves.
