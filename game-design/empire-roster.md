# Empire v1 Roster (as built, 2026-07-26)

> **STATUS: SPEC.** The design for the Empire v1 roster. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

The M6-kickoff roster proposal, delivered as working code per the player's
broader-scope decision (open-city-spec §5.1). Everything here is data
(EmpireSetup.cs + Tier2Batch) — swappable without touching systems.

## Businesses (acquirable now)

| Business | Owner | Routes in | Books |
|---|---|---|---|
| The pawnshop | **Victor** (generated, promoted; nerve 0.4 folds to a squeeze) | clean $900 · his marker $250 then squeeze · his skim (weak hook) | +$60/day clean, washes $80/day |
| The market stall | **Marla** (ring) | clean $500 · her thumb-on-the-scale (weak hook, Sam knows) | +$40/day clean, washes $30/day |

Next candidates when their owners walk (from the batch): the teahouse
(magda), the steam laundry, the corner bakery (danica), the boarding house.
Rita's fencing operation pairs with Victor's back room as a racket, not a
business, when she goes live.

## Rackets

| Racket | Pay | Base risk | Notes |
|---|---|---|---|
| Collection round | $60/day dirty | 0.35 | the debt book made recurring |
| Protection round | $80/day dirty | 0.5 | higher pay, louder |

Runner competence (from traits at recruitment) shades both witness odds and
story confidence; rotten hook-crew (loyalty < 0.3) skim a quarter, visibly.

## Recruitables and their needs

| Who | Route in | The need |
|---|---|---|
| Sam | $120 | cash, counted twice |
| Joey | $100 | a Downtown reference for his daughter |
| Marla | $150 | someone to lean on her supplier |
| Victor | $200 | a slice of his gambling marker cleared |
| Any live batch resident | $120 default | their card's own need, quoted |

Core cast (Lena, Ada, Rocco, Noor) are not recruitable — they are the life,
not the business.

## The rival

The Dockside street arm, flat structure (Nemesis-safe). Attention rises
only from observable moves (acquisitions, establishments, recruits, racket
witnesses reaching the night circle). Ladder: slow beer (0.25) -> $40/day
street rent (0.5) -> poach the least loyal (0.75; loyal crew warn instead)
-> the wordless threat (0.9). Balance: fully exercised under aggressive
play, dormant under none (balance-findings-open.md).

## Population state

- Live: 7 founding cast + Victor + 14 batch residents = 22 walking.
- Data: 45 more validated batch cards ready to instantiate on demand.
- Pending hand-authored ring (Ferko, Rita, Vesna, Tibor): next promotions,
  slotting into the cab rank, pawnshop back room, chapel, customs shed.

## Round 2-3 additions (2026-07-26, CI run 30204710961)

- **Fencing line** ($100/day, risk 0.4) — requires owning the pawnshop;
  Rita's criminal secret is the natural unlock, her recruitment the natural
  staffing. Rackets can now require fronts (`RequiresBusinessId`).
- **The cut** (§6.5 daily): fair / generous (-$15/day, +loyalty — the
  anti-poach investment) / skim (+$15/day, -loyalty, counted and remembered
  in their memory file). Set in conversation with assigned crew.
- **Businesses**: + Magda's teahouse ($600, +$45/day, washes $40),
  Donna's bakery ($550 or her $150 marker, +$45/day, washes $25) — both
  owners generated, their batch secrets are the leverage route.
- **The break**: skipping drops while the rackets pay recontextualizes the
  outfit cut-off as declared independence (+0.25 rival attention).
- **Empire-aware street**: crew and former owners greet you by HOW it
  happened (clean purchase vs squeeze vs leverage); Noor picks up the
  Dockside-tax story at rival stage 2; Ellis stands down 4 days post-Fall.
- Live population: ~36 walking (7 cast + Victor + ring 4 + 24 batch).

## Round 4-5 additions (2026-07-26)

- **The quit** (§6.5 complete): a need-route crew member skimmed below
  loyalty 0.2 walks — leaves the take on the counter, the round dies with
  them, the reason sits in their memory file. Hook-crew cannot leave; that
  is the hook route's brittle bargain in both directions. Winning a
  quitter back revives their line rather than duplicating it.
- **The day job** (§6.6): Meridian Parcel courier rounds, $40 clean a
  morning, and the cover of steady work (day-circle suspicion decays after
  a worked day). Zlata is the dispatcher now that her card is approved.

## Faction agency (commit 0fc5b9d) — the arms are people

| Arm | Head | Members on the street |
|---|---|---|
| Dockside syndicate | Sera Kest | Joey (dock hand), Ferko (night cab) |
| The machine | Aldous Vane | Tibor (the customs stamp) |
| The New crew | Danny Ro | Rita (the back-room fence) |

Recruiting any of them IS poaching — the same need/hook verbs, aimed at
someone who already had an employer. Their arm loses the roster line,
loses 0.35 standing, gains 0.2 attention; the person's memory records who
they used to answer to. Allegiance: `PledgeTo` (standing ≥ 0.2 required)
flies an arm's colors — their attention decays, their protection is real,
$50/day tribute, the other two read it as a side taken. `BreakWith` always
ends below zero standing and spikes their attention; their people
remember the day.

Still unbuilt (see `agency-model.md` targets): arm-vs-arm relations,
absorbing a broken arm, the heads' authored Table scenes, Hal's
brokerage verbs.
