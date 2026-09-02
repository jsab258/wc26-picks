# D12: information surfaces

STATUS: DECIDED 2026-09-02 by Jafar, recorded verbatim in substance by the
resident. This is a design decision at premise level: it governs how the
moat (social memory, consequence persistence, information) is SHOWN.

## The decision

**The player's own memory is fully surfaced in an in-game journal called the
Ledger.** Per-person and per-event entries for everything witnessed, heard
or told. Each entry is tagged:

- `witnessed`
- `heard` (carrying its source and the time)
- `deduced`

**Conversations show the Ledger page for the person you are talking to.**

**NPC minds are never shown as ground truth.** The player sees only their
character's MODEL of what each NPC knows, carrying confidence levels, and
that model is assembled STRICTLY from evidence the player actually has:
the NPC's own statements, observed reactions, third-party reports, and
witnessed sightlines.

**Divergence between the model and the truth is intended design space**, not
a defect to be closed. A player who believes the wrong thing about what
someone knows is the game working.

**Judgment legibility per D11:** when a claim is believed or doubted, the
NPC's actual relevant memory surfaces as the reason.

**Learning what people know is done through diegetic verbs**, and each verb
is itself a perceivable act: asking around, buying gossip, pub talk,
eavesdropping, stealing tapes. There is no free omniscient read.

**The what-they-know HUD from the reference extraction is SCOPED DOWN** to
law enforcement's institutional knowledge during wanted states, and nothing
else.

## Why this is the shape of the moat and not a UI preference

The project's claim is social memory 93 and information 90 against a
best-in-class of 60 and 65. A system that shows the player what NPCs know
directly would score those numbers by fiat and destroy the thing being
scored: if knowing is free, then asking around, buying gossip and
eavesdropping are decorations rather than verbs, and the information layer
has no cost, no risk and no play in it.

Surfacing the player's OWN memory completely while surfacing NPC minds only
as a modelled, evidence-bounded inference is what makes the moat a game
rather than a readout. The divergence clause is the load-bearing half: an
inference the player can be WRONG about is the only kind worth building.

## Open, and named rather than guessed

1. **D11 IS NOT IN THIS REPOSITORY.** The judgment-legibility clause above
   cites it. Searched: `ledger-v2/respec/decision-register/` holds D4 to D9
   and no D10 or D11 file; a repository-wide grep for `D11` outside
   `legacy/` returns nothing. D10 is referenced by name in `ledger/verify.py`
   (template sync retired) but has no record file either. So this record
   cites a decision that cannot be read here, which is a pointer to nothing
   until D11 lands. FOR JAFAR: D11's text, or confirmation it was decided
   outside the repo and should be written down.

2. **No pending v1 decision was found to close.** The ask was to close any
   related pending v1 decision with a pointer here. Searched:
   `game-design/decisions-pending.md` holds three cards (engine tie-break,
   stranger spacing, player progression) and none concerns information
   surfaces; `game-design/decisions-answered.md` holds one adjacent item,
   "Does prison launder the information landscape?", already DECIDED
   2026-07-28. If a card exists that this should close, it is not in either
   file and the search that failed to find it is named here so the next
   reader can widen it rather than repeat it.

## What this does not decide

The Ledger's visual design, its information density, and whether a page is a
book, a card stack or a corkboard. Those are UI work against the standard,
not premise, and they wait for a frame the way everything visual does.
