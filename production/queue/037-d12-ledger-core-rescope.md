line: production (the moat: information layer, Core)
spec: ledger-v2/respec/decision-register/D12-information-surfaces.md, D11-player-progression.md; game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 3
acceptance: (1) production/specs/d12-ledger-core.md, LIVE, one row per D12 and D11 clause naming the Core type and line that carries it or MISSING, with the CoreTests names that prove each carried one and the counts printed; (2) a call-site list, by grep with the pattern quoted, of every Game-layer read of NPC memory, Fact or GossipMill state that reaches a player-facing surface, each marked allowed (through PlayerKnowledge) or D12-violating, with the number examined; (3) the guard's shape named as the spec's next rung (a verify.py lint over Game files), NOT built
max_sessions: 1
status: READY 2026-09-02. systems-builder, one session, engine-neutral C#. FIRST UE-WAIT FILLER: the second builder slot of a day, ahead of every governance item, never the first slot, which is 027's.

## Why this item exists, and it is the finding

D11 and D12 landed on 2 September and the queue held TWENTY-TWO ready items
with no moat item among them. The moat is social memory 93, consequence
persistence 95 and information 90 against a best in class of 60, 85 and 65,
and everything else is in service of it. A queue that cannot spend a slot on
the thing the project is for has drifted, whatever each individual item's
merits.

It is engine-neutral C# in Core, so it is NOT blocked by D1 and does not
wait on Unreal. Doing it now is the cheapest those clauses will ever be:
Phase 1 ports Core once, and a clause added before that port is carried
across for free.

## FACTS INLINE, so the session is spent writing rather than reading

Core: `PlayerKnowledge.cs` (83 lines; `KnownLead` carries HolderId,
TopicKey, Summary, Source, ConfidenceWhenLearned, LearnedAt, Sensitive,
Handled; the class comment already says never ground truth).
`Gossip.cs` line 43 (`Hops`, 0 meaning witnessed first-hand, and the ONLY
provenance a Fact carries today). `Claims.cs` (a typed sentence becomes a
Fact; `ProcessClaim` moves suspicion). `Informing.cs`. `Reliability.cs`.
`Homicide.cs` (`TestimonyGrade`).

Game call sites of PlayerKnowledge and KnownLead: `GameController.cs` 92
and 180 to 183; `DialogueUI.cs` 1052, 2173, 2183, 2194; `SimDirector.cs`
13813. `CoreTests/Program.cs` carries 21 mentions.

## The clauses to survey

- witnessed / heard(source, time) / deduced, per entry
- per-event entries beside per-person
- the conversation page for the person present
- the model of what an NPC knows, with confidence, assembled ONLY from
  evidence the player holds
- D11's per-NPC record of the player's claims, surfaceable as the reason a
  claim is believed or doubted
- NO stored global credibility number anywhere. Grep for it and PRINT THE
  COUNT; a zero here needs its denominator like any other
- the what-they-know HUD scoped to law enforcement in wanted states

## The trap

Do not build the guard. Name its shape as the spec's next rung. A lint
written before the spec it enforces is a lint written against a guess.
