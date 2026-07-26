# Empire v1 Roster (as built, 2026-07-26)

The M6-kickoff roster proposal, delivered as working code per the player's
broader-scope decision (open-city-spec §5.1). Everything here is data
(EmpireSetup.cs + Tier2Batch) — swappable without touching systems.

## Businesses (acquirable now)

| Business | Owner | Routes in | Books |
|---|---|---|---|
| The pawnshop | **Viktor** (generated, promoted; nerve 0.4 folds to a squeeze) | clean $900 · his marker $250 then squeeze · his skim (weak hook) | +$60/day clean, washes $80/day |
| The market stall | **Mirela** (ring) | clean $500 · her thumb-on-the-scale (weak hook, Sam knows) | +$40/day clean, washes $30/day |

Next candidates when their owners walk (from the batch): the teahouse
(magda), the steam laundry, the corner bakery (danica), the boarding house.
Ruta's fencing operation pairs with Viktor's back room as a racket, not a
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
| Josip | $100 | a Downtown reference for his daughter |
| Mirela | $150 | someone to lean on her supplier |
| Viktor | $200 | a slice of his gambling marker cleared |
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

- Live: 7 founding cast + Viktor + 14 batch residents = 22 walking.
- Data: 45 more validated batch cards ready to instantiate on demand.
- Pending hand-authored ring (Ferko, Ruta, Vesna, Tibor): next promotions,
  slotting into the cab rank, pawnshop back room, chapel, customs shed.

## Round 2-3 additions (2026-07-26, CI run 30204710961)

- **Fencing line** ($100/day, risk 0.4) — requires owning the pawnshop;
  Ruta's criminal secret is the natural unlock, her recruitment the natural
  staffing. Rackets can now require fronts (`RequiresBusinessId`).
- **The cut** (§6.5 daily): fair / generous (-$15/day, +loyalty — the
  anti-poach investment) / skim (+$15/day, -loyalty, counted and remembered
  in their memory file). Set in conversation with assigned crew.
- **Businesses**: + Magda's teahouse ($600, +$45/day, washes $40),
  Danica's bakery ($550 or her $150 marker, +$45/day, washes $25) — both
  owners generated, their batch secrets are the leverage route.
- **The break**: skipping drops while the rackets pay recontextualizes the
  outfit cut-off as declared independence (+0.25 rival attention).
- **Empire-aware street**: crew and former owners greet you by HOW it
  happened (clean purchase vs squeeze vs leverage); Noor picks up the
  Dockside-tax story at rival stage 2; Ossei stands down 4 days post-Fall.
- Live population: ~36 walking (7 cast + Viktor + ring 4 + 24 batch).
