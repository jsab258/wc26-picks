# The Open City — Day 8 and Beyond (spec DRAFT, awaiting player approval)

> **STATUS — SPEC.** The design for the open city from day 8. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

Drafted 2026-07-26 after the player flagged design drift: the built prototype
reads as a linear story game, while the founding doc promises an open-city
crime sim × slice-of-life social RPG (§1, §4 outer loop, §6.5 empire). This
spec puts the open game in one place: the campaign reframe, Empire v1, the
generation pipeline that buys density, and the reconciled roadmap position.
DRAFT ONLY — nothing here is wired until approved. Companions:
`act1-draft.md` (the on-ramp), `tier2-pipeline-spec.md` (the people half of
the generation engine), `design-doc.md` §6.5/§6.7/§7 (the systems this
builds toward).

---

## 1. The reframe: the week is the on-ramp, not the game

**Problem being fixed.** "Survive the week" was built (M2) as a stakes
scaffold to make the gossip engine lethal enough to test. It works — but
left in place it silently becomes the game's shape: a scripted week, an
authored act, a rail. The doc's outer loop (§4) is open-ended: grow the
empire while growing the life; acts are pressure points that fire on
conditions, not a sequence of levels.

**The fix.** The week campaign is demoted to what it always secretly was:
**Act I's skeleton** (per `act1-draft.md`, the sandbox week IS arrival →
discovery → collision → verdict). At PP7 — the verdict and the posture
answer — the campaign controller switches modes:

- **Week mode (days 1–7, built):** win/lose verdict, outfit patience,
  survival framing. Unchanged; it is the tutorial arc that teaches every
  system under real stakes.
- **Open mode (day 8 onward, NEW):** no verdict screen, no survival win
  state. The exposure fuse and heat remain (losing is still possible —
  exposure, arrest, the street turning), but *winning* stops being defined.
  The player's posture answer from PP7 sets the opening state, and the two
  ledgers (§4 outer loop) become the game: empire standing and life
  standing, both growable, both attackable, no ceiling.

**Act II+ fire on conditions, not days.** In open mode the authored spine's
pressure points arm on world state — heat thresholds, territory taken,
relationship depths, rival attention — exactly as §8 specifies. A player
who spends twenty days courting Noor and never expands sees Act II late
and shaped by that choice. No timers (§4 rule), no rail.

## 2. Empire v1 — the four firsts

The smallest buildable set that flips the game's shape from rail to
sandbox. Each is an *inversion or extension of a built system* — no new
foundations. One district (The Hook), one of each.

### 2.1 First business (extends: clean/dirty money, debt book, Tier-2 cards)

Businesses become ownable. Every generated business card (see §3) carries
books: clean income range, laundering capacity, an owner with a need,
debt, or secret. Acquisition routes match the doc's "many ways, most
non-violent": buy it clean (slow, expensive), buy the debt (the debt book
inverted — you become the collector), or lean on the owner's secret (a
hook spent). Owning it grants: laundering capacity beyond the bar,
clean income, a place your crew can be, and its staff as recruitable
faces. First candidate: the pawnbroker from the Tier-2 sample ring
(fencing adjacency makes it the natural first rung).

### 2.2 First recruit (extends: hooks v1, loyalty, the need field)

A Tier-2 character joins the outfit. Routes: supply their card's **need**
(loyalty route — slow, sticky) or spend a **hook** (leverage route — fast,
brittle; the doc's loyalty/fear axis made real from day one). A recruit's
card gains crew fields: loyalty (to you, personal history — §6.5), fear,
competence, a breaking point. Crew are not units: they keep their
schedule, their connections keep gossiping, their grievances accumulate in
the same memory files. The first betrayal should be *diagnosable in the
markdown* — that is novelty claim #5 working.

### 2.3 First racket (inverts: the nightly drop machinery)

The drop system played in reverse. In Act I the outfit hands you jobs; in
open mode you *own a route* and staff it. The built machinery (witness
generation, heat corroboration, dirty cash, patience) is reused with the
player on the other side of the ledger: choose the runner (their nerve and
competence set the witness-risk profile), the schedule (the no-timers rule
holds — routes are standing obligations, not countdowns), and take the
income. One racket type at v1: the collection route (the debt book made
recurring — it exists, it's tested, it's on-theme).

### 2.4 One reacting rival (extends: gossip mill, escalation ladder, patience)

The outfit you served all of Act I — the Dockside syndicate's street
operation (§7, The Hook's incumbent) — becomes the rival. Their reaction
is driven by **what their people actually observe through the gossip
system** (your runner seen on their corner, a debtor who stopped paying
them), never by omniscient triggers. Reaction ladder mirrors the built
suspicion escalation: a warning visit → prices raised → your recruit
poached or leaned on → a violence threat (unrealised at v1 — combat stays
cut per doc risk #1). ⚠ Nemesis patent note (§6.5): the rival's internal
structure stays flat at v1; no promotion-by-player-defeat anywhere.

**What Empire v1 deliberately excludes:** multiple districts, the other
two rival organizations, combat, vehicles, protection/smuggling/gambling
rackets, crew-vs-crew operations. One of each first — the slice rule
(doc risk #5) applies to the sandbox too.

## 3. The generation engine — density as a pipeline, not a budget

Player direction (2026-07, reaffirmed 2026-07-26): density comparable to
the big open worlds is reachable by AI generation with human quality
control — not by manual authoring, not by conceding "small game." The
Tier-2 pipeline (`tier2-pipeline-spec.md`) is the people half; this
extends the same architecture to places:

- **District template → place graph.** A district generates as blocks,
  lots, and business slots from an occupation-mix template (The Hook:
  docks-heavy, cash-heavy, few offices). Same shape as character
  generation: LLM proposes, script validator disposes (walkability,
  schedule reachability, business/resident job matching, no orphan lots).
- **Every business is a card.** Owner (Tier-2, generated with need +
  secret + books), staff slots, income profile, laundering capacity —
  which is what makes §2.1 scale: "buyable" is a property of data the
  generator already emits, not a hand-placed flag.
- **Art skins, generation decides.** Purchased modular packs (doc §10)
  render what the generator laid out; the pipeline decides *what exists
  and who lives there*. Swapping art quality never touches world truth.
- **Story flesh stays systemic.** Between authored pressure points, the
  content of open mode is the sim: generated people with generated needs
  colliding with the player's two lives. This is already how the one
  street works; districts multiply it without new story cost.
- **Scale path:** one street (built, 6 cast + sample ring) → The Hook
  full district (~8–12 blocks, 60–100 Tier-2, Empire v1's arena) →
  Copper Row (second district, second economy) → outward per §7's seven.
  Each step is a batch-generation + curation pass, not a content rewrite.

## 4. Roadmap position (amends `roadmap.md` — the plan forward)

Unchanged: M5 vertical slice is next and remains the is-this-fun gate —
Act I polished, voiced, in HDRP. Two amendments:

1. **M6 becomes "The Open City" — Empire v1, first-class.** Immediately
   after the slice: open mode + the four firsts (§2) in The Hook, fed by
   the district generation pass (§3). The former M6 grab-bag (districts,
   acts expansion, productization) shifts to M7+. This is the shape-fixing
   milestone; it exists so the game demonstrably *is* its genre line
   before further story authoring.
2. **The slice gets a day-8 teaser (cheap, recommended).** After PP7's
   verdict, one authored beat over the true books: Lena lays out what the
   street could be — the first business opportunity visible, the campaign
   UI shifting from "survive" to the two ledgers — then the demo ends.
   One scene of writing; it makes the demo promise the sandbox instead of
   promising a story game. (Open question 2 below.)

Act II authoring intentionally *follows* Empire v1: its pressure points
fire on empire state (§8 — growth attracts the rivals and Ellis), so the
sandbox must exist before the act that reacts to it is written.

## 5. Decisions (player, 2026-07-26 — spec APPROVED with amendments)

1. **Empire v1 scope — BROADER than the four firsts** (player overrode the
   minimal recommendation). Multiple businesses and multiple racket types
   ship in the first open-mode milestone, not one of each. §2 stands as
   the *per-type* design (acquisition routes, recruit routes, the drop
   inversion, the observing rival); the M6 kickoff proposes the concrete
   roster (candidate businesses beyond the pawnbroker; racket types beyond
   collections — protection and fencing are the natural nexts, both
   pre-designed in doc §6.5). The §2 exclusions that remain: multiple
   districts beyond The Hook, the other two rival organizations, combat,
   vehicles.
2. **Day-8 teaser in the slice — YES.** One authored scene per §4.2.
3. **District generation — WITH Empire v1.** The Hook's 60–100 residents
   are part of M6; batch generation scheduled for an API-key session.
4. **Open-mode fail state — survivable but scarring.** Prison time, empire
   decay, reputation ruin; the city remembers and the player climbs back.
   No game-over screen in open mode. Design pass owed early in M6.

---

*Nothing in this spec adds a novelty claim; it pays down the two the
prototype hasn't cashed: #4 (living city at honest scale) and #5
(emergent betrayal). Per §2's rule, that is the argument for building it.*
