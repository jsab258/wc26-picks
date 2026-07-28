# Audit findings — 2026-07-27 (Fable session)

**Status update 2026-07-28: FIX PHASE — ALL 25 HIGH FINDINGS RESOLVED.**
104 findings, 160 clean checks from the 15-dimension sweep. The adversarial
verify wave failed four separate ways (session limit x2, structured-output
harness fault, then a subagent permission-handler fault that blocked every
tool call), so verification moved into the fix phase itself, solo: every
fix begins with the finding's failing case shown to fail (or an empirical
probe where the claim was about a test that cannot fail), which is stronger
verification than a verdict. Findings that were wrong would not have
produced a failing test; all 25 produced one or were confirmed by direct
read/probe.

**Fixed (17 distinct defects from the 25 high findings, several were
duplicate sightings):** decision-9 street coupling (was wired to the bar's
drayman via a null-id lookup); Director demand due-day on late fire; the
save/load cluster (harm, purses, Ossei interviews never saved; inspector
and summit head never respawned on load; crowd-gossiper restore ordering —
restore is two-pass now; sim overwrote the player save); gossip re-tell
guard value-blind (unbounded rumor growth on conflicting values); empire
RNG seeded per-day-only (lab variance collapse — re-measured, decisions 9
and 10 hold); CI wait-timeout mismatch; the sim reclaim that never
reclaimed (CONFIRMED finding below — fixed via Core SimClock); lost-week
gate miscalibration; the takings-floor tautology test; the UI smoke test's
two self-satisfying checks + the InputLocked recompute that erased Plan and
Phone panel locks; ledger raw-confidence figure; doorman refusal lines
displaying zero frames; Both-ending deflect-only (act3-draft answer 3 now
honored via GossipMill.StrongestSurvivingPlayerLead, re-measured in the
lab).

**Design question raised, not decided:** post-Fall heat laundering (does
prison count as a managed information landscape?) → decisions-pending.md.

**2026-07-28, second wave: ALL MEDIUM AND LOW FINDINGS RESOLVED.** The 33
mediums landed in six batches (gossip core, CoreTests tautologies, clock
jumps, act promises, legibility, infrastructure); the 45 lows in three
sweeps (codec/clock/purity, player-facing surface, instruments). 40 of the
45 lows are code fixes; five are dispositioned with reasons:

- Injunction expiring during a Fall: waiting it out in a cell still waits
  it out — narratively sound, kept.
- Money-conservation invariant: impossible by design; the economy mints
  and burns daily. Accepted.
- Dirty cash paying suppliers: a defensible design call either way —
  logged in decisions-pending.md with a recommendation, not changed the
  night before a playtest.
- Staged-fall in-flight state: substantially covered by the demand
  due-day fix; jobs resolve at the close and a beat lapsed while inside
  is acceptable fiction.
- ShapeCheck's PascalCase blind spot: inherent to the CS0103 heuristic;
  documented as a known limit rather than pretended away.

**Fix-phase CI build: GREEN** (run 30326027427, 2026-07-28 03:28Z). The
in-engine run exercised the fixes for real: daysSkipped=3 — the reclaim
extended a run past its landing for the first time; the bot lost the week,
so the lost-week gate discounts were exercised and passed; both acts
resolved; the save-key assertions raised nothing. One iteration was needed:
the smoke-test rewrite first asserted absolute lock-policy reads and redded
when another panel was legitimately open — both assertions are deltas
against a per-panel baseline now. (Pre-fix green state: trials 81-83.)

---

## CONFIRMED (adversarially verified)

### [MEDIUM] `ledger/Assets/Scripts/Game/SimDirector.cs:219` (gates)

**Claim:** The _endDay reclaim can never actually reclaim a day in any reachable run: every reachable Fall fires on day >= 9 and lands on fallDay+3, the reclaim adds exactly landing-fallDay-1 = 2 days making _endDay equal the landing day, and `now.Day >= _endDay` (line 489) fires Finish on the landing frame — so the two 'reclaimed' days are never simulated, the post-Fall world gets zero sim time, and MaxReclaimedDays is dead code.

**Failing input:** Standard won-week CI run: _endDay = 1+9 = 10; staged fall at day 9 hour 10 (line 446) -> RunTheFall sets Now = (12, 8:00) (GameController.cs:1022); next SimDirector.Update computes skipped = 12-9-1 = 2, _endDay = 12, then line 489: 12 >= 12 -> Finish() same frame. Perturbation proof: delete the whole reclaim block and behavior is identical (12 >= 10 also finishes at landing). The last lived moment is day 9 10:00 (~8.4 of the promised 9 days), and .github/workflows/ledger-build-windows.yml line 20 raised the sim timeout 20->25 min because 'the run now reclaims the days the Fall skips... about four extra minutes' — time that is never used. Open-mode falls before day 9 are unreachable (open mode starts day 8 and EnterOpenMode/ForceOpenMode reset ExposedStreak, so the earliest organic fuse is the day-9 close), so the reclaim never extends any run.

**Verifier:** Confirmed by tracing. _endDay = 1+9 = 10 (`Now = new GameTime(1, 9, 0)` GameController.cs:14; `_endDay = _game.Now.Day + SimMode.Days` SimDirector.cs:95; CI passes -simdays 9). No fall can precede day 9: FallPending needs OpenMode plus ExposedStreak>=2 from once-per-day closes (`if (Now.Hour >= 8 && Now.Day > _lastClosedDay)` GC:1335; `if (OpenMode) FallPending = true;` Campaign.cs:162), open mode starts day 8 at earliest and both EnterOpenMode/ForceOpenMode do `ExposedStreak = 0;` (Campaign.cs:55,90) — so earliest organic fuse is actually the day-10 close, and the staged fall (SimDirector.cs:446, day>=9 hour>=10) is the earliest possible. RunTheFall: `Now = new GameTime(Now.Day + 3, 8, 0);` (GC:1022) → landing day 12. Next SimDirector.Update: `int skipped = now.Day - _lastSeenDay - 1;` = 12-9-1 = 2, `_endDay += skipped` → 12 (SD:214-223), then same invocation line 489 `if (now.Day >= _endDay) Finish();` → 12>=12 fires Finish on the landing frame. The reclaimed days are never simulated; deleting the block gives identical behavior (12>=10). Since landing = fallDay+3 and reclaimed _endDay = fallDay+... always equals or precedes landing for every reachable fallDay>=9, the reclaim never extends any run, MaxReclaimedDays/the Falls==0-guarded second-fall case is dead code, and the workflow's 20->25 min sim timeout bump ("the run now reclaims the days the Fall skips") pays for time never used. Downgraded from high: no individual gate passes vacuously because of this (all staged gates fire before the fall; the fall's immediate effects do run), the run still covers ~8.4/9 days, and the unused timeout is a cap not a sleep — it is a silent coverage shortfall plus misleading comments, not a gate bypass.


---

## UNVERIFIED findings (verify wave in progress), by severity


## HIGH

### `ledger/Assets/Scripts/Game/GameController.cs:685` (acts)

**Claim:** A save made after the Table is called but before it is answered permanently softlocks the campaign out of Act III: the arm's head NPC is never respawned on load, and answering the Table is only possible by talking to that NPC.

**Failing input:** Arm reaches stage 4 -> CheckActTwo sets ActTwo.TableArmId="dockside" and calls SpawnHead (GameController.cs:690-691); player saves (tableArm persisted, ActTwo.cs:108) and restarts. TryLoad (GameController.cs:1727) restores acttwo but only respawns Ossei (line 1778); the PP7 block is guarded by `ActTwo.TableArmId == null` (line 685) so SpawnHead never runs again, and _headsSpawned is session-local. AnswerTable is reachable only via dialogue with a host whose Card.Name equals the arm's HeadName (DialogueUI.cs:563-567) — no such host exists — so TableFired stays false forever, and ActThree.ShouldOpen (ActThree.cs:143-145) requires tableAnswered, so the audit, all five endings, and the game's ending can never occur on that save. CI never sees this: SimDirector force-answers the table directly (SimDirector.cs:397-398) and the sim never loads saves (TryLoad line 1731).

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:38` (acts)

**Claim:** The Both ending is only reachable by taking Ossei's deflection deal, directly contradicting the approved player decision in act3-draft.md ("You CAN refuse Ossei and still reach 'Both' — but only through the information landscape"): OsseiCaseAnswerable's sole source is ActThree.Deflected.

**Failing input:** World at audit close: empire alive, BestDayLifeLoyalty 0.7, DayCircleRacketHeat 0.3, LedgerStrain 0.1, every mouth managed — but Deflected=false. Books() line 38 sets OsseiCaseAnswerable = ActThree.Deflected = false, so landscapeManaged (ActThree.cs:252-253) is false and Eligible() yields Kingdom, never Both. The design's alternatives ("her strongest lead discredited, bought, or contradicted" — act3-draft.md line 67, echoed in the Core comment at ActThree.cs:65) have no implementation; grep shows ActThreeHost.cs:38 is the only assignment. Worse, Deflect() requires OsseiSpawned && OsseiInterviews.Count > 0 (ActThreeHost.cs:445), so the cleanest campaign (Ossei never spawned, nobody talked) is structurally locked out of the best ending. The balance lab's own matrix corroborates: Both appears only in 'answered+deflect' rows.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:158` (acts)

**Claim:** Loading a save made after the inspector arrived leaves Reisz permanently absent from the world — the daily ask toast still fires, but the cooperate/stonewall verb is unreachable for the rest of the audit, freezing ScopeFactor and changing the ending.

**Failing input:** Audit opens day O; Reisz spawns day O+1 (InspectorArrived=true, persisted at ActThree.cs:554); player saves that evening and reloads. RestoreActThree sets InspectorArrived=true, so the spawn branch `!ActThree.InspectorArrived` (line 158) never runs and SpawnInspector (line 261) has no other caller. The ask block (line 168) needs only the flag, so each morning InspectorAskText announces "He will want it before he leaves" — but AnswerInspector is only reachable by talking to the InspectorName host (DialogueUI.cs:479-483), which no longer exists. A player who intended six cooperations keeps only the pre-save count: ScopeFactor stays at e.g. 1.0 instead of 0.775, SeenStrain 0.65 instead of 0.50 crosses BooksHoldThreshold 0.62, and Kingdom becomes BurnBoth.

### `ledger/Assets/Scripts/Game/GameController.cs:1680` (acts)

**Claim:** OsseiInterviews (and the _interviewed dedupe set) are not in ExtraFlags and vanish on every load, disabling Deflect, regressing Act III's osseiCanName opening condition, and changing which witness gets burned.

**Failing input:** Campaign where two witnesses gave statements (OsseiInterviews.Count=2, ActTwo.Pp6Fired=true persisted) and businesses+rackets=2; save/load. Count resets to 0, so: (a) osseiCanName at ActThreeHost.cs:114 (`Count >= 2`) is false and ShouldOpen's other disjunct (>=3 holdings) fails — the act that was about to open no longer does; (b) Deflect() returns false at ActThreeHost.cs:445 (`Count == 0`), locking out Both until Ossei re-interviews, which after a Fall (rumor wipe, GameController.cs:1029) or rumor aging may never happen; (c) FirstInformant (ActThreeHost.cs:486-490) reads the rebuilt list's [0], so the person burned by a post-load deflection is whoever happened to be re-interviewed first, not the one who actually talked first.

### `ledger/Assets/Scripts/Game/DirectorHost.cs:215` (clockjump)

**Claim:** A Director demand's DueDay is computed from its scheduled FireDay (`DueDay = p.FireDay + 2`), not the day it actually fired, so a demand whose FireDay falls inside the Fall's 3-day skipped window fires and expires in the same frame — the player is penalized -0.2 loyalty for ignoring a demand that never had an open window.

**Failing input:** Fall at the day-D close with Pressure{Kind=Demand, FireDay=D+1} pending: no closes run on D+1..D+3 (RunTheFall sets _lastClosedDay=D+3), so the first close is D+4. There FireDuePressures (GameController.cs:1408) fires it via DirectorBook.Due's `p.FireDay <= now.Day` (Director.cs:358), Fire() adds OpenDemand{DueDay=D+3}, and CheckDemands (GameController.cs:1409 -> DirectorHost.cs:277 `if (Now.Day <= d.DueDay) continue;`) removes it the same frame: the announce toast and the "stopped asking" grievance (-0.2 loyalty, DirectorHost.cs:281) land in one morning. Likewise any OpenDemand already outstanding at Fall time (DueDay D+1/D+2) expires at D+4 with the entire window consumed by prison. Violates the file's own "always a window, never a countdown" comment (DirectorHost.cs:216). Non-demand pressures merely fire 1-3 days late; only demands corrupt state.

### `ledger/Assets/Scripts/Game/GameController.cs:1680` (codec)

**Claim:** HarmBook (injuries, feuds, scars) is never saved or restored: Harm.Capture()/Restore() exist in Core (Harm.cs:310/337) and pass their CoreTests codec round-trip, but ExtraFlags() has no "harm" key and TryLoad() never calls Harm.Restore, so all violence consequences vanish on reload.

**Failing input:** Run a failed operation on day N (OperationHost.cs:162 inflicts Broken on a crew member, heals day N+25) and let a hit-and-run flare a feud (TrafficHost.cs:131); SaveNow; restart+TryLoad -> Harm.All is empty: Capability(crewId) returns 1.0 instead of 0.4, ScarsOf returns 0, FeudBetween returns null, so ReadySuccessor's feuding gate (ActThreeHost.cs:93) and WillWorkTogether all read a world where the violence never happened.

### `ledger/Assets/Scripts/Game/GameController.cs:91` (codec)

**Claim:** PurseBook is never saved or restored: Purses.Capture()/Restore() exist (Purses.cs:250/273, CoreTests-green at Program.cs:3559) but no Game code calls them — purse cash, Windfall (the carrying-unexplained-money evidence), TimesEmptied, LastBorrowedDay and the entire Favours list reset to authored/derived values on every load.

**Failing input:** Bribe Rocco $200 (DialogueUI.cs:1431 -> mill.Bribe -> purses.Credit sets Windfall=200, CarryingUnexplained true) and collect a partial debt that empties a purse (Debtor.Collect -> purses.Take), triggering NightBorrowing favours; save, reload -> BuildPurses() values stand: Rocco's Windfall is 0, the emptied purse is part-full again, favours are gone — collected money stays in the Wallet while the drawers it came from refill, and the bribe evidence is erased.

### `ledger/Assets/Scripts/Game/GameController.cs:1733` (codec)

**Claim:** TryLoad restores gossip agents before crowd gossipers exist in the mill, so SaveCodec.Restore's unknown-id skip (SaveCodec.cs:203-204 'g == null -> continue') silently discards the saved rumors, loyalty, suspicion, suppression and leash of every promoted crowd resident — the exact state GossipMill.Forget (Gossip.cs:140) refuses to drop during play.

**Failing input:** Empire.DailyTick picks crowd gossiper r123 as a racket witness (Empire.cs:602-608, pool is all mill agents) -> r123 carries a Hops=0 sensitive rumor; save (agent IS captured, LoadBearingIds kept them in the mill); reload -> at SaveCodec.Restore time the mill holds only bootstrap agents, mill.Get("r123")==null, entry skipped; later EnsureInMill (PopulationHost.cs:158) rebuilds r123 as a fresh Gossiper with no rumor — the witness evidence is erased by reloading.

### `ledger/Assets/Scripts/Game/GameController.cs:685` (codec)

**Claim:** Saving after the Table summit is called but before it is answered soft-locks Act III: ActTwo.TableArmId is persisted, but SpawnHead only runs inside the PP7 block guarded by 'ActTwo.TableArmId == null', so on load the arm's head is never respawned and AnswerTable is only reachable through dialogue with that head (DialogueUI.cs:563-567).

**Failing input:** An arm reaches Stage 4 -> TableArmId="dockside", head spawned, player saves without answering; reload -> CheckActTwo skips PP7 (TableArmId != null), _headsSpawned is empty but SpawnHead is never called, no walker named Sera exists -> TableAnswer stays null forever -> ActThreeState.ShouldOpen(tableAnswered=false,...) is false on every frame: the audit letter can never arrive.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:158` (codec)

**Claim:** The inspector is never respawned after a mid-audit load: RestoreActThree sets InspectorArrived=true, but SpawnInspector is only called inside the '!ActThree.InspectorArrived' branch, so Tobias Reisz does not exist in the reloaded world while the daily ask (line 168-175) keeps latching LastDealtDay.

**Failing input:** Save on any audit day after the inspector arrived; reload -> _inspectorWalker is null and no code path recreates him; the InspectorAskText toast still fires each morning and burns LastDealtDay, but AnswerInspector is only reachable by talking to the walker (DialogueUI.cs:479) -> zero further Cooperations/Stonewalls are possible, so ScopeFactor is frozen at its save-time value for the rest of the audit and the cooperate-your-way-to-narrow-scope mechanic is dead for that run.

### `ledger/CoreTests/Program.cs:2151` (coretests-economy)

**Claim:** The check "the takings factor never falls through its floor" cannot fail under any input perturbation or under deletion of the clamp it names — it asserts a tautology on a value that never approaches the floor.

**Failing input:** TakingsFactor is defined as Clamp(raw, MinTakingsFactor, MaxTakingsFactor) (Economy.cs:134-136), so `worst.TakingsFactor >= worst.MinTakingsFactor` is true by construction. Even with the clamp deleted it still passes: the worst fixture (racket 400, heat 1.0, 60 days) hits DailyTick's internal floors — prosperityTarget clamped to 0.05 (Economy.cs:175), priceTarget capped at 1+0.35+0.15 = 1.5 — so raw factor bottoms at (0.5+0.05)*(1-0.5*0.5) = 0.4125 > 0.35 for ALL possible racket/heat/wages inputs (in the actual fixture, suppliers are paid so it is 0.454). Perturb any input: the check's answer never changes. Its neighbor at 2153 (Prosperity > 0.0) is the only live check in the no-death-spiral block.

### `ledger/Assets/Scripts/Core/Empire.cs:522` (determinism)

**Claim:** Empire.DailyTick seeds its RNG from the day alone ('var rng = new Random(now.Day * 7919 + 17);'), so BalanceLab's Monte Carlo seed sweep never perturbs any empire roll — every run of a given plan replays the identical empire random stream, collapsing the lab's variance for its headline numbers.

**Failing input:** BalanceLab RunOpenLab (Program.cs:287-289) loops 'for (int seed = 0; seed < runs; seed++)' and calls RunOpenCampaign(plan, new Random(seed * 104729 + 7)); inside, line 349 calls empire.DailyTick(now, wallet, mill, ...), which ignores that per-run rng and builds its own from now.Day. Perturb the input (the seed) and the answer at Empire.cs:600 ('if (rng.NextDouble() < risk)') does not change: on day D the k-th empire draw is bit-identical in all N runs, so racket-witness generation (line 600/605), the NewCrew incident target pick (line 684), and the poach path all fire on exactly the same days in every 'independent' run. The reported reach%/falls/cutoff% distributions (Program.cs:299-301) and the ending matrix (RunEndingLab, line 461, same seeds) are averages over runs whose empire randomness is perfectly correlated — the lab's variance is understated and design gates tuned on those tables ('Both must be RARE', fall rates) are judged on a sweep that fails the project's own audit question (1) for this subsystem. (The day-seed is documented as intentional for the in-engine self-test replay — the defect is that the lab's seed parameter silently has no effect on the empire.)

### `ledger/Assets/Scripts/Game/GameController.cs:1369` (economy)

**Claim:** Decision 9's street coupling passes Economy.FactorFor(null) — the BAR's per-business factor (TakingsFactor x 0.45 when the bar's own drink supplier refuses) — into Empire.DailyTick, so every racket is coupled to the bar's cellar instead of the district-level TakingsFactor the approved decision specified ('couple it, at the district level rather than per-business', game-design/decisions-pending.md:174-175).

**Failing input:** Let Mirek (EconomySetup supplier with ServesBusinessId=null, 'the bar itself') hit Refusing=true — e.g. 4 unpaid days at -0.25 standing each from 0.25 — while district prosperity is ordinary (TakingsFactor=1.0). Economy.cs:143 makes FactorFor(null)=1.0*0.45=0.45, so Empire.cs:530 pays collection round(60*0.45)=27 instead of 60, protection 36 instead of 80 — a 55% cut to all racket income caused by an unpaid beer delivery, not by the street — and Empire.cs:591-596 fires the street<0.5 event 'There's nothing on that street to hold out with' about a street whose actual factor is 1.0. Perturbation test: pay Mirek $90 and racket income jumps 2.2x with zero change to district prosperity. Meanwhile the fencing racket run through the pawnshop front is NOT affected by its own front's supply state. CoreTests Program.cs:2181 itself glosses FactorFor(null) as 'the bar he supplied earns less' — a bar-specific number. BalanceLab/Program.cs:349 mirrors the same miscoupling, so the lab validates the wrong coupling.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:37` (fall)

**Claim:** An audit that closes after a Fall reads DayCircleRacketHeat = CurrentHeat = 0 because RunTheFall (GameController.cs:1029) deletes every player rumor that DayCircleHeat() is computed from while planting the guilt as Knowledge facts (did_time, GameController.cs:1026-1031) that no heat consumer reads — so Eligible()'s landscapeManaged leg (ActThree.cs:252-253, heat < FactThreshold 0.5) and the epilogue's hot/quiet read (ActThreeHost.cs:251 via EpilogueText) credit a 'managed' information landscape to a player the whole day circle just watched go to prison.

**Failing input:** Audit open with AuditClosesDay = N+2; heat >= 0.70 at the day N-1 and day N closes stages a Fall at the day-N close; RunTheFall lands the world on day N+3 8:00 having wiped all player rumors; at 9:00 CheckActThree runs CloseAudit -> Books() -> DayCircleRacketHeat = 0.0 < 0.5, so with ActThree.Deflected already true and books clean the run resolves Ending.Both ('Nobody in the day circle ever quite says what they think you do') — versus heat ~0.7+ and no Both/Kingdom-with-life one frame before the wipe. Perturbing the Fall on/off flips the landscape input from worst-possible to best-possible.

### `ledger/Assets/Scripts/Game/DirectorHost.cs:215` (fall)

**Claim:** A Director pressure whose FireDay falls inside the Fall's 3-day skipped window fires at the first post-Fall close with DueDay = FireDay + 2 already in the past, and CheckDemands — called one line later in the same close (GameController.cs:1408-1409) — immediately settles it as unanswered (-0.2 loyalty, DirectorHost.cs:281, 'The day came and went and I did not get it'), punishing the player for a window that never existed (independently verified; corroborates the clockjump finding in game-design/audit-findings-2026-07-27.md).

**Failing input:** Director schedules Pressure{Kind=Demand, Who=Rocco, FireDay=N+1} (MinLead=1..MaxLead=4, Director.cs:135-136, so this is routine); Fall at the day-N close sets _lastClosedDay=N+3, so the next close is day N+4: FireDuePressures pops it via FireDay <= now.Day (Director.cs:358), Fire() adds OpenDemand{DueDay=N+3}, then CheckDemands sees Now.Day (N+4) > DueDay (N+3) and removes it the same morning — announce toast and grievance land seconds apart.

### `ledger/Assets/Scripts/Game/SimDirector.cs:1034` (gates)

**Claim:** The forced-open lost-week path (the exact path this morning's coverage floor exists to keep testing) structurally fails the openModeOk and verdictSane gates whenever the week is lost at or before the day-6 close, so a legitimate lost week reds the build under two misleading gate names.

**Failing input:** Exposure fuse trips at the day-6 morning close (day-circle heat >= 0.70 on the day-5 and day-6 closes): Campaign.CloseDay sets LostExposed with DaysClosed=5; UpdateCampaign (GameController.cs:1331) then returns early every frame, so days 7-8 never close and `_lastClosedDay` jumps 6->8 when SimDirector forces open mode at day 8 (SimDirector.cs:252-267, which resets Verdict to Ongoing). Only the day-8 and day-9 closes remain before the staged day-9 fall jumps to day 12 and Finish runs, so DaysClosed=7 < 8 -> openModeOk (line 1034) is false; and jobs posted = nights 1-5 plus night 8 = 6 < SimMode.Days-2 = 7 -> verdictSane (lines 1011-1013) is false. Nothing is actually broken; the gates' baselines (DaysClosed >= 8, jobs >= 7) assume a won week whose closes and job posts never froze.

### `ledger/Assets/Scripts/Core/Gossip.cs:217` (gossip)

**Claim:** Tick's re-tell guard compares the incoming rumor only against Best(topicKey) — the highest-confidence rumor for the topic regardless of VALUE — so when two agents hold conflicting values for the same topic, each re-adds an identical copy of the other's version every round, growing Rumors and Memory unboundedly (CompareNotes lines 284-286 has the same hole).

**Failing input:** Player leaves messages at two phones asking for two different people: Phones.LeaveMessage gives Rocco player.left_word='lena'@0.55 and Sam player.left_word='viktor'@0.55 (Phones.cs:159-167); Rocco-Sam tie is 0.8 (GossipDirector.cs:58). Every 6-game-minute round they stand together: passed = 0.55*0.8*0.8 = 0.352 ≥ MinConfidenceToShare; listener.Best('player.left_word') is his OWN version with a different value, so line 217's 'existing.Content.Value == r.Content.Value' is false and line 225 appends another identical 0.352 copy — plus a Memory.Append (line 226) and, for file-backed cast memories, a full save-file rewrite — once per round for the ~2 game-days until Age decays the source below 0.3125, i.e. hundreds of duplicates; unbounded in any loop that doesn't call Age (CoreTests/BalanceLab-style). The test at CoreTests/Program.cs:306-309 only covers the same-value case.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:804` (legibility)

**Claim:** The player ledger (L panel) prints the gossip mill's raw belief-confidence scalar as a two-decimal figure in the LIABILITIES section: `$"<color=...><b>−{k.ConfidenceWhenLearned:0.00}</b></color>"` — the variable is literally named `figure` — while every sibling scalar on the same screen goes through a word ladder (HeatWord, StrainWord, ScopeWord, ProsperityWord).

**Failing input:** Any unhandled KnownLead — e.g. Lena witnesses the night drop (Witness call confidence 0.9, OperationHost.cs:94) — then press L: the liabilities section renders 'Lena — "..." −0.90'. A 0..1 belief confidence is exactly the class of internal odds the law's enforcement points (RiskWord/ScopeWord no-digit checks, CoreTests Program.cs:1667/4113) insist stay words.

### `ledger/Assets/Scripts/Game/GameController.cs:1446` (purity)

**Claim:** Sim mode (-simdays) silently overwrites the real player's autosave: TryLoad is sim-guarded but every SaveNow call site is not, so the self-test writes the bot's world over ledger-save.json in the player's persistentDataPath.

**Failing input:** Player with an existing ledger-save.json launches the shipping LEDGER.exe with '-simdays 9' (the exact flag CI documents and passes to the same shipping exe). Bootstrap.cs:32 drops straight into the self-test; GameController.cs:1731 skips loading the save ('the self-test always plays a fresh week'), but the morning-close autosave at GameController.cs:1446 (plus AnswerTable:838, ContinueToOpenMode:1005, AnswerPosture:~1050, RunTheFall:~1076, and SimDirector.cs:768 in Finish) all call SaveNow(quiet:true), which writes SavePath = Application.persistentDataPath/ledger-save.json (GameController.cs:1678,1712). Within ~2 real minutes (first in-sim morning close at 20 game-min/sec) the player's real progress is replaced by the bot's fresh week, unrecoverably — SaveSlots quarantines only corrupt files, never keeps a backup. This is also the concrete path by which a shipping build reaches Campaign.ForceOpenMode (SimDirector.cs:256) and ForcePendingFall (SimDirector.cs:450): the hooks are compiled into the release player and gated only on this runtime command-line check, with no build-config guard.

### `ledger/Assets/Scripts/Game/GameController.cs:1768` (reachability)

**Claim:** The summit head (Sera/Aldous/Danny) is never respawned on load, so a campaign reloaded while the Table is pending can never answer it — and since Act III opens only on TableFired, every Act III authored text (Pp1LetterText, inspector scenes, all five ending texts) becomes unreachable in that campaign.

**Failing input:** ActTwo PP7 fires (arm reaches Stage 4): TableArmId="dockside" is set and SpawnHead runs (line 691, guarded by TableArmId==null). Player saves (daily autosave) and relaunches. TryLoad restores ActTwo with TableArmId="dockside", TableAnswer=null; the PP7 block is skipped forever, SpawnHead has no other caller, no NpcWalker/ConversationHost named "Sera Kest" exists. RefreshEmpireButtons' table branch (HeadName == _current.Card.Name) can never match, AnswerTable is never callable, ActTwoState.TableOffer/TableResult never display, and ActThreeState.ShouldOpen(tableAnswered:false,...) is false for the rest of the game. TryLoad respawns Ossei at line 1778 but has no equivalent for the head.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:162` (reachability)

**Claim:** SpawnInspector is only reachable through the !InspectorArrived branch, and InspectorArrived is persisted — so after any save/load mid-audit, Tobias Reisz no longer exists: CooperateText, StonewallText and the InspectorCard persona become permanently undisplayable while InspectorAskText keeps toasting daily about a man who is not in the world.

**Failing input:** Audit open, day after the letter: InspectorArrived=true is saved (Capture key "inspector"). Player quits and relaunches. TryLoad restores ActThree (line 1768 of GameController.cs) but never calls SpawnInspector; _inspectorWalker is null and no host named "Tobias Reisz" is in _hosts. The daily ask block (lines 168-175) still fires InspectorAskText toasts and burns LastDealtDay each day, but ActThreeButtons(id=="Tobias Reisz") can never be reached, so AnswerInspector is uncallable — cooperations/stonewalls are frozen for the remainder of the audit.

### `ledger/Assets/Scripts/Game/AccessHost.cs:96` (reachability)

**Claim:** On every gate refusal, the authored doorman refusal line is overwritten in the same frame by the hint toast, so all four authored Gate.Refusal strings display for zero frames — despite the adjacent comment declaring the line-then-hint pairing IS the feature.

**Failing input:** Player walks within 3 units of any gate without holding a key, e.g. the back room with no introduction, standing <40 with dockside, <$60 and wearing the coat. Doors.Try returns Allowed=false, Line="\"Private tonight.\" He does not move...", Hint=nearest.Nearly (non-empty for every KeyKind). Lines 95-96 call _ui.Toast(result.Line, 8f) then immediately _ui.Toast(result.Hint, 10f); DialogueUI.Toast (line 1072) does _toastText.text = line with no queue, so the refusal string is replaced before it is ever rendered.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:1064` (ui)

**Claim:** Update() unconditionally recomputes InputLocked from only the dialogue and key panels, nullifying the Plan and Phone panels' input locks one frame after they are set.

**Failing input:** Open city, press J: TogglePlan (PlanUI.cs:36) sets InputLocked=true, but the next Update runs `_player.InputLocked = dialogueOpen || _keyPanel.activeSelf` with both false -> InputLocked=false. With the plan panel open the player can WASD away (PlayerController.cs:64 gates only on InputLocked), press E to open a dialogue on top of it (the Talk check at line 968 tests neither panel), or start driving (TrafficHost.cs:456 reads the now-false lock). Same for TogglePhone (PhoneUI.cs:64): the player can walk out of phone reach with the panel still live and ring rows still clickable. ForceDialogue (line 1195) also ignores both panels, so a confrontation can open over an open plan panel with both interactive.

### `ledger/Assets/Scripts/Game/UiSmokeTest.cs:84` (ui)

**Claim:** Two of the smoke test's four per-panel assertions are tautologies that can never fail: Check() writes `_player.InputLocked = false` (line 84) and immediately reads `!_player.InputLocked` as GaveBackControl (line 85), and reads `Closed = !panel.activeSelf` (line 78) immediately after its own `panel.SetActive(false)` (line 77).

**Failing input:** Perturb the input the check claims to guard (the file's own comment: 'the close path forgot to unlock input'): delete the unlock from TogglePlan/TogglePhone/TogglePause entirely. GaveBackControl is still true, because line 84 just forced InputLocked=false before line 85 reads it; Closed is still true because SetActive(false) always clears activeSelf. The CI ui gate (SimDirector.cs:977 `uiOk = _uiSmokeRun && panelsBad == 0 && panelsOk >= 5`) can only go red if a panel field is null or its parent canvas is inactive — the stranding bug the file says it exists to catch cannot fail it.

### `.github/workflows/ledger-build-windows.yml:114` (workflow)

**Claim:** The sim step's cap was raised 20->25 minutes for the ~4-minutes-longer post-Fall run, but the in-script Wait-Process timeout stayed at 1200 seconds (20 minutes), so the raise is dead: the effective sim budget is still 20 minutes and a slow-but-PASSING sim is force-killed.

**Failing input:** A fully passing 9-day sim that takes 20m30s of wall time (the header comment at lines 19-21 says the reclaimed Fall days add 'about four extra minutes', which is why timeout-minutes went to 25): Wait-Process -Timeout 1200 throws at 20:00, the script runs Stop-Process on the player, prints 'Simulation timed out after 20 minutes', and exits 1 -> red build with all 35 gates green; the 25-minute step cap is unreachable.


## MEDIUM

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:63` (acts)

**Claim:** Quiet's eligibility guard is a tautology once handed over — `s.HasReadySuccessor = ready != null || ActThree.SuccessorId != null` makes Eligible's `HandedOver && HasReadySuccessor` (ActThree.cs:247) collapse to HandedOver — so post-handover actions that remove the successor still resolve Quiet with self-contradicting text.

**Failing input:** Hand over to crew member X (SuccessorId set; Empire untouched), then either (a) go to Halvard and SellUp — the gate at ActThreeHost.cs:427 and the DialogueUI branch (DialogueUI.cs:414-415) never check SuccessorId, so Dissolve liquidates the businesses whose licence now bears X's name and marks X Departed ("Paid off and finished", Empire.cs:276-285) while the player pockets the proceeds; or (b) on the last day call X with "Tell them to go quiet" (LastDayOffer, ActThreeHost.cs:357, offers any non-departed crew including the successor) — X departs, "whatever you built with them is finished". Either way CloseAudit resolves Quiet (it outranks everything), prints "You sign it over to X and take the boat", and the epilogue reports X "behind the counter at seven" running the empire that was just sold out from under them / that they were just banished from.

### `ledger/Assets/Scripts/Game/GameController.cs:1296` (acts)

**Claim:** Act II's PP4 — which act2-draft.md line 47-48 specifies as "fires: any day-life loyalty >= 0.65 AND crew >= 1; the guaranteed collision" — actually fires only when the player physically walks to an attended evening beat, so a player who declines or misses every evening never sees it, and the documented firing condition exists nowhere in code.

**Failing input:** ActTwo open, crew of 3, Ada at loyalty 0.9: design says PP4 fires. In code FireCollision (line 702) is called solely from UpdateBeats' attend branch (line 1296) when the player stands within 2.5 units of the beat marker; invitations the player ignores resolve to skipped via ResolveLapsed (line 1259) with no fallback, so ActTwo.Pp4Fired stays false for the whole campaign. Additional threshold drift: evenings are offered at loyalty >= 0.5 (OfferEvening line 1236), not the design's 0.65, so the "collision" can also land on a host below the documented bar.

### `ledger/Assets/Scripts/Core/ActTwo.cs:22` (acts)

**Claim:** PP2's injunction counterplay is unimplemented: InjunctionAnswered has no setter anywhere in game code and InjunctionFee is never charged, so the on-screen letter text ("Pay the fees, have Halvard make it disappear, or wait it out") names two options that do not exist.

**Failing input:** Machine attention reaches 0.5: GameController.cs:645-649 fires PP2, sets InjunctionUntilDay = Now.Day+2, and shows Pp2LetterText. A player with $5000 who wants to pay, or who takes the letter to Halvard: no branch in DialogueUI or anywhere else references the injunction (repo-wide grep: InjunctionAnswered is set only in CoreTests/Program.cs:916; InjunctionFee appears only at its declaration). The only path is BarFrozen expiring by date (ActTwo.cs:24) — two days of zeroed takings (GameController.cs:1341) with no counterplay, versus act2-draft.md lines 34-38 which promise "pay the fee, or ask the Fixer to make it disappear, or eat the loss".

### `ledger/Assets/Scripts/Game/GameController.cs:1316` (clockjump)

**Claim:** TickWorldDay's guard `if (Now.Hour < 8 || Now.Day <= _lastWorldDay) return;` runs the world-day systems ONCE after the +3 jump, but two of its three consumers apply per-CALL increments, not per-elapsed-day arithmetic: every purse in the city gains one day's flow for three calendar days (Purses.cs:126-135, `p.Cash + gain` once per call), and every feud cools one 0.03 step instead of three (Harm.cs:229 `f.Heat - 0.03`); NightBorrowing likewise gets one night instead of three (Debts.cs:136).

**Failing input:** Fall on day D: TickWorldDay ran for D at 8:00, the jump lands D+3 8:00, next frame ticks once with day D+3 — a purse with Weekly=70 that was emptied on D holds ~10 (one day's gain) on the landing morning instead of ~30, so a Collect() against a willing debtor returns a third of what the calendar owes; a feud at Heat 0.52 sits at 0.49 instead of 0.43, keeping WillWorkTogether (Harm.cs:295, threshold 0.5) false when three simulated days would have made it true. Harm's own injury logic in the same tick proves the inconsistency: it uses absolute-day arithmetic (`day - i.DayTaken`, Harm.cs:214) and handles the jump correctly.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:207` (clockjump)

**Claim:** A Fall inside the audit window silently eats up to 3 of the 6 grace days (AuditClosesDay is an absolute date, ActThreeHost.cs:121), and when the jump lands on/past AuditClosesDay, PP3 (Ossei's "two days left" offer, line 179 `DaysLeftOnAudit <= 3`), PP5 ("The last day. You can reach a few people", line 199 `<= 1`) and CloseAudit (line 207) all execute in one CheckActThree pass — the last-day calls are announced and are already dead, because IsLastDay requires !AuditClosed (ActThree.cs:131), so LastDayOffer (ActThreeHost.cs:355) returns null immediately after.

**Failing input:** Audit opens day O (closes O+6); Fall at the O+3 close lands O+6 8:00. At the next 30-frame CheckActTree with Hour>=9: PP3 toast, PP5 toast, then CloseAudit fire back-to-back in the same invocation — the player is told they can move the ledgers/dismiss crew/confess the same instant the books close, days O+3..O+5 of inspector asks (LastDealtDay cadence, line 168) never happened, and the ending resolves off a state the player had zero of the advertised last-day agency over.

### `ledger/Assets/Scripts/Game/GameController.cs:193` (codec)

**Claim:** OsseiInterviews (and the _interviewed dedup set) are not in the save: ExtraFlags persists osseiSpawned but not the statement list, so on load Deflect() is gated shut and the burned-witness identity is recomputed wrongly.

**Failing input:** Ossei holds 3 statements (first from Sam); Act III open; save, reload -> OsseiInterviews.Count==0, so Deflect() returns false at ActThreeHost.cs:445 until interviews re-accrue — and re-accrual order depends on who Ossei happens to walk past, so FirstInformant() (ActThreeHost.cs:487, 'OsseiInterviews[0]') can name a different person than Sam: deflecting after a reload burns the wrong witness, and osseiCanName (Count>=2 at ActThreeHost.cs:114) also resets.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:323` (codec)

**Claim:** Saving between the inspector's daily ask and the player's answer permanently destroys that day's item: ActThree.LastDealtDay is latched and persisted at ask time (line 173), but _inspectorAskedDay (line 254) is transient, and AnswerInspector requires '_inspectorAskedDay == Now.Day'.

**Failing input:** Day D: ask fires -> LastDealtDay=D saved in the actthree dict; save, reload same day -> _inspectorAskedDay=-1 so AnswerInspector returns false, and the ask block won't re-fire because LastDealtDay==D -> one of the six cooperation opportunities is silently gone; losing one 0.045 cooperation step can push SeenStrain across the 0.62 BooksHoldThreshold and change the ending (independent of, and still present after fixing, the missing-respawn defect).

### `ledger/CoreTests/Program.cs:2111` (coretests-economy)

**Claim:** TestEconomy never asserts the heat input: deleting the heat coupling (and likewise SupplyRaisesPrices, DislikeRaisesPrice, SqueezeCostsSupplierStanding) leaves every one of its checks green.

**Failing input:** Set HeatCostsProsperity = 0 (Economy.cs:174): quiet (heat 0.1) moves 1.028 -> 1.047, still inside its (0.95, 1.15) band; squeezed/generous compare runs sharing heat 0.1 so relative inequalities hold; slow's one-day delta goes -0.054 -> -0.048, still < 0.06; worst's prosperity converges to 0.10 instead of 0.05, still > 0. No two fixtures differ only in heat. Same for HeatCostsSupplierStanding (Economy.cs:226 — 'lost' refuses via the unpaid -0.25/day alone, 'kept' survives on +0.28/week either way), SupplyRaisesPrices (Economy.cs:179 — every PriceLevel assertion uses fully-paid fixtures with strain 0), and DislikeRaisesPrice (Economy.cs:150 — no DeliveryPrice check ever runs with negative standing).

### `ledger/Assets/Scripts/Core/Empire.cs:583` (coretests-economy)

**Claim:** EmpireBook.TotalRacketIncome — the counter Act III's LedgerStrain reads as the dirty income the books must explain (ActThreeHost.cs:40) — has zero CoreTests coverage: neither its accumulation nor its codec round-trip is asserted.

**Failing input:** Mutate line 583 `TotalRacketIncome += income;` to double-count, or move it above the NewCrewTaxing/TributeShare/SharedRacket deductions (lines 578-581) so it counts gross instead of what actually entered the wallet: all 1395 checks stay green (every occurrence of 'TotalRacketIncome' in Program.cs — 2633, 2651-2663, 2874-2875, 2927-2990, 3048, 3126 — is the hand-set LedgerState struct, never an EmpireBook after a tick), and Act III's ending selection silently shifts because SeenStrain inflates.

### `ledger/CoreTests/Program.cs:2696` (coretests-endgame)

**Claim:** The did_nothing check is effectively unfailable: its fixture has TotalRacketIncome=0 (the exact no-racket-income shape from the 24-test incident), so LedgerStrain=0 and Resolve deterministically returns Kingdom, making the '|| BurnBoth' arm dead code and the comment's claim 'Doing NOTHING must produce Burn Both' unpinned.

**Failing input:** Fixture {BusinessesOwned=1, RacketsEstablished=1, loyalty=0.1, heat=0.9, income=0, washed=0}: with empire alive, OsseiCaseAnswerable=false, HandedOver=false, Eligible() (ActThree.cs:247-321) is structurally confined to {Kingdom, BurnBoth} — Both is blocked twice (heat>=0.5 and ossei false), StraightLife by empireSurvives, Quiet by HandedOver — so the disjunction 'Resolve==Kingdom || Resolve==BurnBoth' passes under ANY perturbation of any LedgerState number and any strain/threshold/scope constant, and under any single-conjunct regression to Eligible(). An established racket that produced zero income is also a world the game cannot produce (Empire.DailyTick pays established rackets daily), so the audit gate the comment describes never bites.

### `ledger/CoreTests/Program.cs:948` (coretests-social)

**Claim:** TestActTwo's codec roundtrip asserts only the 2 non-default fields of a 14-field Capture/Restore, so a restore regression in any of the other 12 ActTwoState fields ships green.

**Failing input:** Fixture `a` (lines 912-917) differs from a fresh ActTwoState only in InjunctionUntilDay=12 and InjunctionAnswered=true — exactly the two fields line 948 checks. Break Restore's parsing of any other key in Assets/Scripts/Core/ActTwo.cs:112-126 (e.g. make Pp4Fired read Flag(d,"pp5") instead of "pp4", or drop truceSpent/tableAnswer/lastEvening entirely): the restored default (false/-1/null) equals the fixture value, so the check still passes. Contrast TestPhones' full serialize-equality roundtrip at line 2618.

### `ledger/CoreTests/Program.cs:4013` (coretests-social)

**Claim:** "the yard opens to somebody the street talks about" passes via the shipped yard's After-21 key, not the Notorious key it names — the notoriety input is irrelevant to the outcome.

**Failing input:** famous = {Notoriety=0.9, Hour=22} against repair_yard, whose keys are Notorious(45), Crew(2), After(21) (AccessSetup.cs:85-93). Hour 22 >= 21 holds the After key, so perturbing Notoriety 0.9 -> 0.0 — or deleting the Notorious key from the shipped gate — leaves Doors.Try(...).Allowed true and the check green. The companion design claim in the comment ("No build holds both") is asserted nowhere, and is in fact false at this very fixture hour: `unknown` (Notoriety 0.05, Hour 22, line 4008) opens both the loft (Quiet) and the yard (After). A famous state at Hour < 21 would have isolated the Notorious key.

### `ledger/CoreTests/Program.cs:1026` (coretests-social)

**Claim:** "a leashed checker does not go asking" cannot fail: the fixture's partner is also leashed, so CompareNotes returns 0 events whether or not the checker-leash guard exists.

**Failing input:** rocco3 was leashed by UseHook at line 1023; with lena3.Leashed=true, delete the `checker.Leashed` early-return in GossipMill.CompareNotes (Core/Gossip.cs:269) and the call still yields Count==0 via the partner-leash break at Gossip.cs:280 — the check stays green. The only observable difference the guard makes — lena3 NOT gaining the "I asked Rocco straight out" memory written at Gossip.cs:271-272 before the loop — is never asserted. The §6.3 leashed-checkers-don't-check rule is therefore unverified.

### `ledger/CoreTests/Program.cs:4127` (coretests-social)

**Claim:** "a plan with too many people in it says so" asserts only Worry.Length > 0, which every WorryAbout return path satisfies — the assertion is unfalsifiable for any worry-selection logic.

**Failing input:** Operations.WorryAbout (Core/Operation.cs:233-253) returns a non-empty literal on every branch, including the fallback "Nothing about it is obviously wrong." at line 252. Delete the `plan.Crew.Count > 2` branch (Operation.cs:245-246): the 4-person fixture falls to the fallback, Length is still > 0, and the check passes. Worry can only be empty via Read's null/Done early-outs, which this fixture never takes. The two sibling checks (lines 4122, 4125) correctly use Contains("heard of you")/Contains("daylight"); this one pins nothing.

### `ledger/Assets/Scripts/Core/Empire.cs:583` (economy)

**Claim:** DailyTick racket income can go negative (flat -15 generous cut applied after street scaling, Empire.cs:538), and when it does the books diverge three ways: Wallet.EarnDirty silently drops it (Wallet.cs:22 guards amount>0) while TotalRacketIncome += income still subtracts it (Empire.cs:583) and the income event reports a negative dollar figure (Empire.cs:584-585).

**Failing input:** Prosperity driven to its 0.05 floor and PriceLevel to ~1.5 (both reachable by max squeeze + heat drift per Economy.cs:171-179), plus the bar's supplier refusing: FactorFor(null) = (0.5+0.05)*(1-0.5*0.5)*0.45 = 0.186. Collection round, runner on Cut="generous": income = round(60*0.186) - 15 = 11 - 15 = -4. Wallet gains nothing (the $4 owed to the runner is never actually paid by anything), but TotalRacketIncome drops by 4 — skewing ActThree.LedgerStrain (ActThree.cs:155-157) and the SimDirector's racketIncome telemetry (SimDirector.cs:1191) — the event prints 'Sam brings in $-4 off the collection round', GameController.cs:1371 sums -4 into racketToday, and ShowDaySummary (GameController.cs:1414-1415) displays negative rounds.

### `ledger/Assets/Scripts/Game/GameController.cs:1033` (fall)

**Claim:** RunTheFall appends a MemoryEvent to EVERY agent in the mill — including all crowd Gossipers promoted by PopulationHost — and GossipMill.Forget refuses any agent with a non-empty append-only Memory (Gossip.cs:140, MemoryStore has no pruning), so ApplyBand's Far branch (PopulationHost.cs:153) marks each one r.Known = true forever; after one Fall the entire Fall-time milled cohort (up to NearCap 22 + MidCap 110 = 132 residents) is permanently load-bearing, and SetBands sorts load-bearing residents ahead of everyone else regardless of distance (Population.cs:294-311), so the M9 attention-band rotation is dead for the rest of the run — fresh residents near the player can no longer claim Near/Mid slots and the walking crowd stops corresponding to where the player actually is.

**Failing input:** Open-city play with the mid band full (110 crowd members milled) when the fuse blows: RunTheFall's foreach gives all 110+ a 'They took the new owner in' memory; on the next re-band every one demoted to Far fails Forget (Memory.Events.Count > 0) and is pinned Known=true; with ~132 pinned, near(22)+mid(110) slots are consumed entirely by the pinned cohort in every subsequent SetBands call, so a resident standing next to the player is banded Far and never enters the mill or spawns a walker again.

### `ledger/Assets/Scripts/Game/SimDirector.cs:691` (gates)

**Claim:** The discredit gate is permanently vacuous in every 9-day CI run: Finish always executes on the frame the staged Fall lands, RunTheFall has just deleted every rumor whose Subject is "player" (GameController.cs:1029), and every `Sensitive = true` rumor in the codebase is a Fact("player", ...) — so the strongest-sensitive-story scan finds topic == null and discreditWorks defaults to true without ever calling Discredit.

**Failing input:** Any -simdays 9 run: staged fall (day 9) -> land day 12 -> Finish same frame; the scan at lines 693-699 iterates day-circle rumors for r.Sensitive and finds none (verified: all Sensitive=true creation sites — GossipDirector.cs:127/274, GameController.cs:660/718, Empire.cs:349/608/686, OperationHost.cs:93, TrafficHost.cs:144, ActThreeHost.cs:418, Gossip.cs:552 — use subject "player", which the wipe removes). Perturb GossipMill.Discredit to a no-op and the gate stays green in every CI run, even though secretReachedDay (latched) is true and the branch is entered.

### `ledger/Assets/Scripts/Core/Gossip.cs:159` (gossip)

**Claim:** Witness drops a repeat sighting of the same topic+value on the floor without raising the existing rumor's confidence, so a later CLEAR sighting cannot strengthen an earlier doubtful one — perturbing the input (confidence 0.6 → 1.0) does not change mill state.

**Failing input:** Same NPC witnesses two drops on day 5: first with the coat, GossipDirector.WitnessNightJob calls Witness(..., Fact('player','night_job_d5','seen'), conf 0.6); second without the coat, conf 1.0. Line 159's Holds('player.night_job_d5','seen') is true, so the block at 161-165 is skipped: the spreading rumor stays at 0.6 forever while line 167 appends a memory saying 'I saw it myself'. Heat, Leads, BribePrice and spread all keep pricing an eyewitness-certain event as a half-seen one (only Knowledge.Learn at line 158 registers the certainty).

### `ledger/Assets/Scripts/Core/SaveCodec.cs:220` (gossip)

**Claim:** Restore writes Rumor.Confidence (line 220) and Gossiper.Loyalty (line 205) straight from the save with no 0..1 clamp — the only rumor-confidence write path in the codebase that doesn't enforce the invariant (Witness clamps at Gossip.cs:157, SuspicionTracker.Restore clamps at Suspicion.cs:68).

**Failing input:** A save whose agents[].rumors[].conf is 1.6 (hand-edit, corruption, or a future migration bug): after load, DayCircleHeat's noisy-or (Gossip.cs:337) computes doubt *= (1-1.6) = -0.6 giving heat 1.6 > 1, so CurrentHeat-driven systems (Ossei spawn threshold, StreetWord, Empire NewCrewTick's heat>=0.45 check, ambient reach) all read impossible values, and Tick propagates passed = 1.6*tie*0.8 confidences above 1.0 through the network.

### `ledger/Assets/Scripts/Core/Gossip.cs:331` (gossip)

**Claim:** DayCircleHeat counts a leashed day-circle holder's sensitive rumors at full confidence, and its consumers model heat as circulating TALK — so a leashed NPC who can never speak still spawns Ossei and seeds brand-new 'somebody has been saying things' rumors into the crowd via ambient reach: a leak through a side channel the leash guards in Tick/Leads/CompareNotes were supposed to close.

**Failing input:** Exactly one day-circle NPC carries the night_job rumor at 0.9; player spends a strong hook (UseHook, Gossip.cs:485 sets Leashed). Leads returns nothing (line 354), Tick spreads nothing (line 210) — yet DayCircleHeat still returns 0.9 (loop at 329-341 never checks a.Leashed), so PopulationHost.TickPopulation (PopulationHost.cs:97-105) starts _talkStartedDay and Population.AmbientReach > 0, and EnsureInMill (lines 174-187) plants street_talk rumors in promoted crowd residents although no unleashed agent ever carried or spread the story. Contrast: a bribe (Contain, Gossip.cs:543 → 0.05) DOES cool heat, so the two damage-control verbs are inconsistent.

### `ledger/Assets/Scripts/Core/Gossip.cs:447` (gossip)

**Claim:** Discredit's once-per-story denial cap is keyed by topicKey only, but the method filters the actual confidence cut by VALUE — denying one version of a topic permanently burns the denial for every other version, so perturbing the value input no longer changes the outcome.

**Failing input:** Two witnesses hold conflicting values on player.location_d2_evening ('warehouse' and 'docks'). Discredit('player.location_d2_evening','docks') adds the bare topic to _discredited (line 447) and cuts only the docks tellings (line 454's value match). A later Discredit('player.location_d2_evening','warehouse') hits line 447-449 and returns AlreadyDenied with Affected=0: the warehouse story was never doubted, yet the denial is spent.

### `ledger/Assets/Scripts/Core/MemoryStore.cs:70` (gossip)

**Claim:** NPC memory is unbounded over a long campaign — Events is append-only (nothing ever prunes it; reflection only replaces Beliefs) and Append rewrites the ENTIRE markdown file on every call, so per-append cost grows linearly with lifetime memory.

**Failing input:** Open-mode play: every successful gossip hop appends a 'heard' event (Gossip.cs:226), every CompareNotes appends even when nothing is shared (Gossip.cs:271), the Fall appends to every agent (GameController.cs:1033), at up to 240 gossip rounds per game-day forever. For a file-backed cast member (CastSetup memories), Save() (MemoryStore.cs:124-130) rewrites the whole file each time: after N appends the total bytes written is O(N^2), and Events, ToMarkdown, and the LLM-context source all grow without cap for the life of the campaign.

### `ledger/Assets/Scripts/Game/PlanUI.cs:200` (legibility)

**Claim:** The operation-outcome toast interpolates the witness COUNT as a digit — `$"{outcome.Witnesses} people saw something."` — in the very system whose plan line is the legibility law's sole enforcement point; the ==1 branch one line above was carefully worded ('One person saw something'), the >=2 branch was not.

**Failing input:** Commit any plan where Operations.Run returns outcome.Witnesses = 3 (e.g. a loud Forced job at high heat): player-facing Toast reads '3 people saw something.' The file's own header (PlanUI.cs:16-18) says 'The read is words. Never a bar, never a percentage.'

### `ledger/Assets/Scripts/Core/Adjudicator.cs:97` (legibility)

**Claim:** A failed Checks.Crew novel action puts crew-count digits in the player's face: `Adjudication.Fail($"that needs {amount} people, and you have {state.Crew}")` flows through IntentBridge.NovelLine (IntentBridge.cs:286 `$"You start to — and stop. {Capitalize(verdict.Reason)}."`) into DialogueUI.Narrate (DialogueUI.cs:1330).

**Failing input:** Type a free-form intent the router maps to Check=Crew, CheckAmount=3 while Empire.ActiveCrew has 1 member: the dialogue window narrates 'You start to — and stop. That needs 3 people, and you have 1.' Contrast the same file's Standing/Heat failures, which are correctly worded ('you don't stand well enough with them for that').

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:281` (legibility)

**Claim:** The LLM channel — the game's largest player-visible text surface — has zero digit enforcement, and the game actively pumps digits into it: Reisz's ExtraContext returns 'The inspection closes on day {AuditClosesDay}; {left} day(s) remain... on {s.Cooperations} occasion(s) and refused on {s.Stonewalls}', and ResponseValidator.Validate/Humanize (ResponseValidator.cs:20-87) scrubs dashes, emoji, and fourth-wall breaks but contains no digit or number rule before the reply is shown verbatim; Director-authored p.Line is likewise toasted raw (DirectorHost.cs:174) after ConversationEngine.ValidateReply, which is the same digit-free-of-checks path.

**Failing input:** Talk to Reisz mid-audit: the model, told 'day 23; 4 day(s) remain', naturally replies 'I will be finished by day 23' — digits reach the dialogue box with no guard. Same for a Director Demand whose line names its own figure ('...asked for $200 by Friday'): Validate clamps p.Amount (Director.cs:301) but never inspects the line text that is the only part the player sees.

### `ledger/Assets/Scripts/Game/ConversationHost.cs:33` (purity)

**Claim:** NPC memory persistence has no sim guard in either direction: a -simdays run both loads the player's existing NPC memory markdown and appends the bot's events into it, so the 'fresh week' claim is false for NPC brains and player memory files get polluted.

**Failing input:** MemoryFilePath = Path.Combine(Application.persistentDataPath, "memories", $"{Card.Id}.md") (ConversationHost.cs:33) is passed to MemoryStore, whose constructor loads the existing file (MemoryStore.cs:67) and whose Append rewrites it on every event (MemoryStore.cs:70-74, 124-130) — none of it checks SimMode. Player machine with memories/lena.md holding 100 real-play events, launch '-simdays 9': (a) the sim run starts with the player's Lena memories, so its result differs from CI's clean-container run; (b) nine days of bot events and nightly reflections (GameController.cs:507-511 runs RunReflectionAsync in sim mode too) are written into the player's lena.md, so after the sim, normal play resumes with Lena 'remembering' the bot's drops — while the paired save file was clobbered separately (finding 1).

### `ledger/Assets/Scripts/Game/GameController.cs:1242` (reachability)

**Claim:** OfferEvening keys the generated evening beat by Gossiper.Id, but the beat-spot/marker lookup matches NpcWalker.DisplayName — for crowd residents Id ("r0123") never equals DisplayName (a human name), so the invitation toasts a scene that can never be attended, PP4's guaranteed collision is starved, and the lapse toast leaks the raw internal id to the player.

**Failing input:** Open mode; a crowd resident (PopulationHost.cs:162 creates Gossiper(r.Id, r.Name,...), Population.cs:186 rolls Loyalty 0.30-0.70, Circle "day") sits in the mill at loyalty 0.68 while every authored day-circle agent is at their 0.4-0.5 start. OfferEvening picks them: Beat.HostId="r0123". UpdateBeats' spot search (line 1276, npc.DisplayName == open.HostId) never matches any walker, no marker spawns, Attend is unreachable; at window end ResolveLapsed toasts "You never went. r0123 will remember that." (line 1260).

### `ledger/Assets/Scripts/Game/DialogueUI.cs:509` (reachability)

**Claim:** ActThreeState.LastDaySpentText ("There is not time for another...") is dead authored text: its only display site requires SpendLastDay to return false while LastDayOffer is non-null in the same frame, which is impossible.

**Failing input:** Last day of the audit, budget of 2 spent on Lena and a crew member: LastDayActions=2, LastDayLeft=0, so LastDayOffer returns null for everyone (ActThreeHost.cs:355), the ActThreeAct branch at line 507 is never entered and the button itself vanishes. When LastDayOffer(id) != null, SpendLastDay re-evaluates the identical LastDayOffer and every subsequent branch (Lena willing or not, crew, day-life friend — whose mill entry LastDayOffer already null-checked) returns true, so the Narrate at line 509 can never execute.

### `ledger/Assets/Scripts/Game/UiSmokeTest.cs:73` (ui)

**Claim:** The smoke walk opens panels with raw SetActive and never invokes any real open/close/refresh path, so the HadWords 'content' assertion is satisfied by build-time chrome and no live renderer is exercised.

**Failing input:** The ledger panel passes HadWords on its build-time title 'T H E   B O O K S' (DialogueUI.cs:727); RefreshLedger — the only code that renders live state and the only one with real failure modes — is never called by the walk (it runs only from the L-key path at line 988). The phone panel passes on rows built with label "-" (PhoneUI.cs:85) without RefreshPhone; the plan panel passes on static row labels without RefreshPlan. HasVisibleWords even counts inactive children (includeInactive:true, line 94). Concrete perturbation: make RefreshLedger throw or render an empty body — the panel gate stays green; the check asserts 'opens and contains any static text', not content.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:977` (ui)

**Claim:** The Escape/pause key chain does not know about the Plan, Phone, or day-summary panels, so with the default binding (Pause=Escape, GameSettings.cs:31) Escape opens the pause menu on top of an open plan/phone panel instead of closing it.

**Failing input:** Plan panel open, press Escape: the chain at 970-977 finds dialogue/ledger/key/debug all closed and calls TogglePause(); line 981 `if (_paused) return` then exits before the plan panel's dedicated Escape handler (lines 1009-1010) can run — pause menu now sits over the still-open plan panel. The handlers added at 1003-1010 (and the summary dismiss at 1021-1024, whose comment promises 'Esc ... dismisses') are only reachable on the same keydown that unpauses, so the second Escape closes pause AND the plan panel simultaneously. The comment at line 972, 'Escape closes whatever is open; with nothing open, it pauses', is false for plan, phone, and summary.

### `.github/workflows/ledger-build-windows.yml:22` (workflow)

**Claim:** The job-cap arithmetic in the comment ('30 + 15 + 25 is 70 in the worst case, so the job cap has to clear that') is wrong: per-step caps actually sum to 76 (it omits the Shape check's timeout-minutes: 6 at line 48), and checkout, lint, license activation, BOTH artifact uploads (a full Unity Windows player) and the Verdict step carry no cap at all, leaving as little as 4 minutes of headroom under 80 — so a run where every step passes its own cap can still be killed by the job cap, and the kill lands exactly on the always() upload/Verdict tail, losing the verdict on the runs where it matters.

**Failing input:** install 29m (the comment at lines 62-64 says the >15m slow tail is real — it went red twice in one morning at a 15m cap) + build 14m + sim 24m + shape check 5m (cold NuGet restore) = 72m, plus checkout + license activation + uploading a multi-hundred-MB LEDGER-Windows player + sim artifacts ~8m -> 80m breached with every individual step green; the job is cancelled during the post-sim steps.

### `ledger/ShapeCheck/Program.cs:69` (workflow)

**Claim:** The 'inherited MonoBehaviour members' whitelist contains 'rigidbody' and 'camera', which do not exist on Unity 6 (6000.0.58f1) Component/MonoBehaviour — those shortcut properties were removed in Unity 5 — so a genuine CS0103 on a bare 'camera' or 'rigidbody' reference is suppressed, the exact silent miss the comment at lines 63-65 claims is impossible ('a new one shows up as a false positive here, not as a silent miss'): a STALE entry is a silent miss.

**Failing input:** A Game script containing 'camera.transform.LookAt(target)' (author meant Camera.main or a _camera field): Roslyn raises CS0103 'The name camera does not exist...', line 96 finds 'camera' in the inherited set and discards it, ShapeCheck reports 0 shape errors, and the Unity build fails on CS0103 twenty minutes later.

### `ledger/lint-usings.py:66` (workflow)

**Claim:** The ambiguous-name lambda test only inspects the remainder of the SAME source line ('after = scrubbed[m.end():]' inside a per-line loop), so a lambda placed on the next line — normal formatting for long predicates — defeats the check for Count/First/Last/Min/Max/ToList etc.

**Failing input:** A file without 'using System.Linq;' containing:
    int alive = crowd.Count(
        p => p.Alive);
'after' is just '(' with no '=>', the match is skipped at line 66-67, lint prints '0 missing-using error(s)', and Unity fails the compile ~20 minutes later — the exact .Count(lambda) mistake from run 30218023272 that this linter was written to catch, one line-break away from its motivating case.


## LOW

### `ledger/Assets/Scripts/Game/DialogueUI.cs:567` (acts)

**Claim:** The Table compresses the design's three answers onto two buttons keyed on Standing, making "defy" unreachable for a player with standing >= 0.5 and "counter" unreachable below it — act2-draft.md PP7 says "Accept, defy, or counter with leverage", with defy unconditional.

**Failing input:** Player at the summit with dockside Standing 0.6 who wants to refuse Sera outright: button B reads "Name your own number" (canCounter=true, DialogueUI.cs:314-315) and EmpireAct maps leverage to `canCounter ? "counter" : "defy"` (line 567), so the only possible answers are accept or counter — the defy branch (standing -0.5, and its authored TableResult line) cannot be reached from any UI state when standing >= 0.5. Conversely at standing 0.4 counter is impossible even if the player "holds the right secrets", which is the condition the design named for counter.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:174` (acts)

**Claim:** Saving between the inspector's 10:00 ask and the player's answer permanently forfeits that day's cooperate/stonewall: LastDealtDay is persisted but _inspectorAskedDay is not, so on reload the ask is marked dealt yet nothing is answerable.

**Failing input:** Audit day N, 10:00: ask fires, LastDealtDay=N (persisted via "dealtDay", ActThree.cs:555) and _inspectorAskedDay=N (plain field, line 254, not captured). Player saves at 11:00 and reloads: _inspectorAskedDay=-1 so InspectorWaiting is false (line 345-346) and AnswerInspector fails its `_inspectorAskedDay != Now.Day` check (line 323), while the re-ask is blocked by `LastDealtDay != Now.Day` being false (line 168). One of the six scope-narrowing mornings is silently consumed with no player action.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:444` (acts)

**Claim:** Deflect remains offered after SellUp even though it can no longer help any eligible ending, and taking it can only hurt: it burns the first informant's loyalty by 0.5, which can single-handedly convert StraightLife into BurnBoth.

**Failing input:** Player sells up (EmpireDissolved=true) with exactly one day-life friend above trust — the same person who gave Ossei her first statement (loyalty 0.6). Ossei's "Give her the arm" button is still shown (DialogueUI.cs:430, gate is only Pp3Fired && !Deflected) and Deflect() passes all its checks (arm Attention survives Dissolve, which never touches Arms). OsseiCaseAnswerable now only affects booksHold paths, but StraightLife (ActThree.cs:305) ignores books entirely — zero benefit — while the burn (ActThreeHost.cs:465, loyalty 0.6 -> 0.1) drops BestDayLifeLoyalty below TrustThreshold 0.55, so lifeSurvives flips and Eligible falls through to BurnBoth: an offered verb whose only possible effect after selling up is to destroy the ending the sale was buying. The ledger meanwhile prints both "There is nothing left for them to find" and "They are looking somewhere else, and somebody paid for that" (ActThreeHost.cs:524-525).

### `ledger/Assets/Scripts/Game/GameController.cs:1024` (clockjump)

**Claim:** The Fall's `_jobPostedDay = Now.Day; // no ghost job from the lost nights` guards an impossible scenario and instead suppresses the landing night's legitimate drop: posting requires `inWindow && Now.Hour >= 22` at the moment of the check (GameController.cs:1453), so no "ghost" from a skipped night could ever post — the only effect of the reset is that the 22:00 drop on the landing day (a day the player has been free since 8:00) never appears.

**Failing input:** Fall lands day D+3 8:00 with _jobPostedDay=D+3; at D+3 22:00 the condition `_jobPostedDay != Now.Day` is false and no drop posts — the player silently loses one $90 job and its +0.10 patience gain; without the reset the same evening would have posted normally (the pre-Fall _jobPostedDay <= D-1 differs from D+3), and no earlier post was reachable because Hour>=22 fails from 8:00 to 21:59.

### `ledger/Assets/Scripts/Game/GameController.cs:648` (clockjump)

**Claim:** PP2's injunction window (`ActTwo.InjunctionUntilDay = Now.Day + 2`, enforced only at closes via `if (ActTwo.BarFrozen(Now)) takings = 0` at line 1341 with BarFrozen = `now.Day <= InjunctionUntilDay && !InjunctionAnswered`, ActTwo.cs:24) expires in calendar time while a Fall skips its enforcement points, so the nominal three frozen closes shrink to one and the pressure mostly vanishes.

**Failing input:** PP2 fires the evening of day X (InjunctionUntilDay = X+2); the Fall fires at the X+1 close — that close is frozen (CloseDay runs at line 1339, freeze applies at 1341, FallPending consumed the same frame), the jump lands X+4 with _lastClosedDay=X+4, and the X+2 close never happens: BarFrozen(X+5) is false at the next real close. The letter that says 'pay the fees, have Halvard make it disappear, or wait it out' is resolved by the calendar jump at the cost of a single morning, with InjunctionAnswered never set.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:247` (clockjump)

**Claim:** The Quiet-ending epilogue indexes mornings off absolute days (`int index = Now.Day - ActThree.EpilogueDay - 1; if (index < 0 || index >= ActThreeState.EpilogueDays) return;`), so a Fall during the 3-day epilogue jumps index past EpilogueDays and the remaining epilogue lines are silently never shown — and the campaign fuse still runs after AuditClosed (UpdateCampaign only checks Verdict, which stays Ongoing in open mode), so this is reachable.

**Failing input:** Quiet ending closes day E (EpilogueDay=E); the morning line for index 0 shows on E+1; two more hot closes set FallPending and the Fall fires at the E+2 close, landing E+5: index = 5-1 = 4 >= 3, TickEpilogue returns forever, and epilogue mornings 2 and 3 (the letter / no-letter payoff of the whole ending) never render.

### `ledger/Assets/Scripts/Game/GameController.cs:507` (clockjump)

**Claim:** Nightly reflection is keyed to `Now.Hour >= 23 && Now.Day > _lastReflectedDay` and reflects only the current day's events (ConversationHost.cs:113 `ReflectAsync(now.Day, now)` -> ConversationEngine.cs:156 `Memory.EventsOnDay(day)`), so the Fall day's 23:00 never occurs and every memory stamped on the Fall morning is never distilled into beliefs.

**Failing input:** Fall on day D at 8:00 (jump to D+3): Lena's close-time observation "Counted the till again..." (GameController.cs:1422, stamped Now=(D,8:xx) before the jump) and any NightBorrowing memories from that morning's TickWorldDay belong to day D; the next reflection runs at (D+3, 23:00) for day D+3 only, so day D's events are permanently skipped — the belief pipeline silently loses the arrest morning while the Fall's own memories (stamped D+3 at GameController.cs:1033, after the jump at 1022) are reflected normally.

### `ledger/Assets/Scripts/Core/SaveCodec.cs:185` (codec)

**Claim:** Runtime-generated open-city evening beats are captured but can never be restored: beat restore matches ids against the freshly-authored BeatBook only, and the 'evening_dN' beats created by OfferEvening (GameController.cs:1239-1245) are not re-authored at bootstrap, so a Pending evening vanishes on load and its Skip consequence never applies.

**Failing input:** Day 12 open city: Ada's 'evening_d12' beat is Pending at 20:00; save and reload -> beats.All.FirstOrDefault(id=="evening_d12") is null, entry skipped; the window passes with no beat to resolve, so Ada never takes the -0.15 loyalty hit or writes the stood-up memory — save/reload is a free way to skip any evening (ActTwo.LastEveningDay IS saved, so no replacement invite comes for EveryNDays either).

### `ledger/Assets/Scripts/Game/GameController.cs:1174` (codec)

**Claim:** The post-Fall calm's rumor half-life does not survive a reload: RunTheFall sets RumorHalfLifeHours=96 with _osseiCalmUntilDay (line 1043-1044); TryLoad restores osseiCalmUntil but then calls SpawnOssei, which unconditionally sets RumorHalfLifeHours to PresenceRumorHalfLifeHours (144).

**Failing input:** Fall on day 12 -> calm until day 16, half-life 96h; save on day 13, reload -> _osseiCalmUntilDay=16 is restored but half-life becomes 144h, so during the supposed calm rumors decay at presence speed (persist ~50% longer) — the same in-progress world ages talk differently before and after a reload.

### `ledger/Assets/Scripts/Core/Economy.cs:53` (codec)

**Claim:** Supplier.LastPrice exists on the class but appears in neither Capture (lines 319-325) nor Restore, so the price-change notice logic loses its baseline across a load.

**Failing input:** Supplier charging an elevated price (LastPrice=120) before save; reload -> LastPrice=0, and the next delivery's 'dearer' check at Economy.cs:195 ('price > s.LastPrice && s.LastPrice > 0') is false, so the first post-load price rise is never voiced — a price movement the design explicitly says must never be silent ('a price rise the player never hears about is a tax').

### `ledger/CoreTests/Program.cs:937` (coretests-economy)

**Claim:** "act2: signing Vane's cap throttles the fronts" asserts only the boolean FrontsCapped that ResolveTable set one line earlier — the throttle arithmetic exists solely in the Unity layer (GameController.cs:1346, x0.7, and MachineInspecting x0.75) which no test can reach, so the machine is the only Table doctrine whose monetary bite is unasserted.

**Failing input:** Delete `* (Empire.FrontsCapped ? 0.7 : 1.0)` from GameController.cs:1346: CoreTests stay green (dockside's tribute is arithmetic-checked at 933, 60 -> 53; newcrew's tax at 1826 via TakeFor; the machine's cap only via this flag) and a signed cap costs the player nothing.

### `ledger/Assets/Scripts/Core/Wallet.cs:41` (coretests-economy)

**Claim:** No money-conservation invariant is asserted anywhere in CoreTests — and none can be, because the design mints and burns money daily; the only both-sides transfer checks are Borrow, Take/Collect, and Credit, and nothing validates wallet state as an invariant.

**Failing input:** Racket income is minted (Empire.cs:582 wallet.EarnDirty with no purse debited), purse refills are minted (Purses.cs:131-133), supplier payments are burned (Economy.cs:193), so no test can sum 'total money in the world' — and none tries. Concretely in-Core: Wallet.Restore(clean, dirty, washed) applies values unchecked, so a corrupted save with Dirty = -500 restores, passes the round-trip equality check at Program.cs:570, and leaves Total negative with no invariant test objecting.

### `ledger/Assets/Scripts/Core/Empire.cs:523` (coretests-economy)

**Claim:** The street clamp `Math.Clamp(streetFactor, 0.1, 1.5)` never binds — the only real caller passes Economy.FactorFor(null), whose default-tuning range is [0.35*0.45, 1.35] = [0.1575, 1.35], and the tests only pass 0.4/1.0/1.3 — so the clamp's boundaries are both unreachable and untested.

**Failing input:** Mis-edit the floor from 0.1 to 0.5: the whole suite stays green (Program.cs:1877's TakeAtStreet(0.4) becomes clamp->0.5 -> take 50, still < plain 100), while in play a starved street (FactorFor = 0.35*0.45 = 0.1575) gets silently floored to 0.5 — roughly tripling racket pay exactly where the decision-9 coupling is supposed to hurt. Same pattern at Purses.cs:88: the Math.Max(0.15, ...) floor is unreachable (minimum value is 0.35), so the test `FlowAt(0.0) > 0` at Program.cs:3413 passes with or without it.

### `ledger/CoreTests/Program.cs:3030` (coretests-endgame)

**Claim:** The decision-10 stonewall term ('keeps its full 0.15', ActThree.cs:199) is pinned only from below (~0.117): inflating it passes the whole suite because the 1.6 clamp absorbs it.

**Failing input:** Set the stonewall term to 0.30 in ScopeFactor (ActThree.cs:201): ScopeFactor(0,3)=clamp(1.9)=1.6>1.35 passes line 3030, asymmetry 0.135<0.6 passes line 3027, ScopeFactor(0,99)<=1.6 passes line 3032, Marginal(0,2) seen=0.55*... still BurnBoth (line 3056), Reads('Stonewalls') 0.55*1.6=0.88 still flips (line 2886) — every check green while one stonewall now widens scope 1.30x instead of 1.15x in real play.

### `ledger/CoreTests/Program.cs:2736` (coretests-endgame)

**Claim:** CouldHold's succession thresholds (competence >= 0.55, loyalty >= 0.6, ActThree.cs:337-338) are pinned only within (0.3, 0.8]; the constants gate HasReadySuccessor and therefore the Quiet ending, but a large drift is invisible to all five checks.

**Failing input:** Change the competence floor 0.55 -> 0.75 (or the loyalty floor 0.6 -> 0.75): CouldHold(0.8,0.8,true,false) still true, !CouldHold(0.3,0.9,...) and !CouldHold(0.9,0.3,...) still true, feuding/independent cases unaffected — all five checks at lines 2736-2741 pass while most successors silently stop qualifying for the Quiet ending.

### `ledger/CoreTests/Program.cs:3134` (coretests-endgame)

**Claim:** The LedgersMoved 0.55 multiplier is pinned only from above (must be < ~0.886); the design comment 'the single largest movement any one action makes' (ActThree.cs:219-221) — i.e., stronger than the deflection's 0.7 — is asserted by no test.

**Failing input:** Set the LedgersMoved multiplier (ActThree.cs:222) to 0.75, making it WEAKER than the OsseiCaseAnswerable 0.7 relief: TestLastDay's Books pair gives kept=0.667>0.62, gone=0.667*0.75=0.50<0.62 — both checks at 3132/3134 pass — and Reads('LedgersMoved') still flips (0.7*0.75=0.525<0.62, line 2887); set it to 0.1 and everything passes too.

### `ledger/CoreTests/Program.cs:919` (coretests-social)

**Claim:** The Act II arm-voice checks hardcode one armId per text function instead of enumerating EmpireBook.Arms, so a new arm silently receives Danny's newcrew lines from all three functions with no test failing.

**Failing input:** Add a fourth RivalArm to EmpireBook.Arms (Core/Empire.cs:100-105): ActTwoState.FirstNotice/TableOffer/TableResult (Core/ActTwo.cs:48-53, 76-84, 86-99) are if/else chains whose trailing else is the newcrew text, so the new arm gets the grinning-fish/Danny-Ro voice everywhere. Lines 919-921 check only FirstNotice("machine"), TableOffer("dockside"), TableResult("newcrew","defy") and stay green. Contrast TestEveryKeyKindHasItsOwnWords (line 1698), which enumerates via Enum.GetValues and fails on a generic fallback.

### `ledger/CoreTests/Program.cs:4153` (coretests-social)

**Claim:** "a botched job is seen by more people than a clean one" asserts >=, so removing the failure-is-louder asymmetry entirely (equal multipliers) still passes; only an inversion is caught.

**Failing input:** The property lives in Operation.cs:310, `seen = vis * (Success ? 0.6 : Partial ? 1.0 : 1.3)`. Set the failure multiplier 1.3 equal to 0.6: seenWin and seenLoss both compute seen=0.48 and Witnesses=1 with the fixed Rolls fixtures, and 1 >= 1 passes. As green today it does distinguish (5 vs 1), but the check cannot detect the documented rule being deleted, only reversed.

### `ledger/CoreTests/Program.cs:338` (coretests-social)

**Claim:** "corroborated heat stays within 0..1" is a dead assertion: the previous line already pinned combined to 0.75 +/- 1e-9 in a throw-on-failure harness, so line 338 can never fail when reached.

**Failing input:** Line 337 throws unless |combined - 0.75| < 1e-9; therefore at line 338 `combined <= 1.0` is true by arithmetic for every execution that reaches it, under any change to DayCircleHeat. Any regression that would push heat above 1.0 (e.g. summing instead of noisy-or) is caught at 337, never at 338 — the check adds zero discriminating power.

### `ledger/CoreTests/Program.cs:2613` (coretests-social)

**Claim:** "the damping is the same in both directions" compares Damped(1.0) to FidelityOnTheLine, which are the same constant by construction — and no second 'direction' exists in the code to test.

**Failing input:** PhoneBook.Damped is `inPersonAmount * FidelityOnTheLine` (Core/Phones.cs:187), so Damped(1.0) IS FidelityOnTheLine: perturb the constant 0.45 -> 0.9 and the check still passes because both sides move together. Damped takes no direction parameter and has one call path, so the bidirectionality the message claims (player-to-NPC and NPC-to-player damped equally) is a property of call sites in the Unity layer that this suite never exercises. The two preceding checks (2609-2610) already bound the constant to (0,1).

### `ledger/CoreTests/CoreTests.csproj:15` (coretests-social)

**Claim:** There is no CoreTests coverage of Act One at all: ActOneState lives in the Unity layer and is not compiled into the test project, and no check in Program.cs references it.

**Failing input:** CoreTests.csproj compiles Core/** plus only AccessSetup.cs, EconomySetup.cs, OperationSetup.cs from Game (lines 15-17); Assets/Scripts/Game/ActOne.cs is excluded, and `grep ActOne|Posture|Noor` over CoreTests/Program.cs returns nothing. Break PostureSummary's winddown/takeover/refused mapping, the DayOneContext day==1&&Sam guard, or the Pp1/Pp2/Pp4/Noor-drawer flags' semantics and every one of the 1395 checks stays green — Act I is verified only by whatever SimDirector exercises in CI.

### `ledger/Assets/Scripts/Core/PlayerKnowledge.cs:73` (determinism)

**Claim:** StrongestFor breaks ties on equal ConfidenceWhenLearned by Dictionary insertion order, and a save/load round-trip reverses that order (SaveCodec captures knowledge via Entries, which is OrderByDescending(LearnedAt) — SaveCodec.cs:75 — and Restore re-inserts in that order, SaveCodec.cs:158-170), so the damage-control verb target can silently switch across a reload with no world change.

**Failing input:** Player holds two unhandled leads for holder 'Rocco', both with ConfidenceWhenLearned = 0.55 (the repeated coated-witness constant), learned D2 10:00 and D3 10:00. Live: _known insertion order is D2-then-D3, and the stable OrderByDescending in StrongestFor (PlayerKnowledge.cs:74-75) returns the D2 lead. Save then load: Capture wrote them LearnedAt-descending, Restore (PlayerKnowledge.cs:61-64) re-inserted D3 first, so StrongestFor now returns the D3 lead. DialogueUI.cs:1397 keys the damage-control verbs off this call — the same session state targets a different lead before vs after a reload, i.e. state read off iteration order that the codec does not preserve.

### `ledger/SimHarness/Program.cs:741` (determinism)

**Claim:** SimHarness writes floats into the committed sim-report.md using the current culture — '$"- Total estimated cost of this playtest: ${usd:0.0000} ..."' (line 741), Check detail strings like '$"value={lena.Suspicion.Value:0.00}"' (line 402) and 'lands.Magnitude.ToString("0.000")' (line 592), plus the embedded CostTracker block ('$"Estimated total: ${EstimateUsd():0.0000}"', CostTracker.cs:43) — so a de-DE machine regenerates the tracked report with comma decimals.

**Failing input:** Run SimHarness from the ledger/ directory on a machine with CurrentCulture de-DE: File.WriteAllText("sim-report.md", ...) (Program.cs:83) overwrites ledger/sim-report.md — which is git-tracked (git ls-files shows ledger/sim-report.md and sim-report.md; ledger/.gitignore:26 only excludes SimHarness/sim-report.md) — and the committed line 'Total estimated cost of this playtest: $0.0315' becomes '$0,0315', producing spurious diffs and making cross-machine report comparison meaningless. Contrast MemoryStore.cs:24 and SimDirector.cs:654-661, which use InvariantCulture for exactly this reason. Same current-culture formatting in BalanceLab's console tables (Program.cs:55, 299-301, 474-476). No CI verdict parses these strings, so impact is report reproducibility only.

### `ledger/BalanceLab/Program.cs:338` (economy)

**Claim:** BalanceLab's daily close omits the frontFactor the game applies to owned fronts — GameController.cs:1346 multiplies front income by 0.75 under MachineInspecting and 0.7 under FrontsCapped; the lab's takings line has neither term — so the Monte Carlo that balance decisions (including decision 9) lean on overstates clean income in exactly the worlds where the machine arm bites.

**Failing input:** A lab run where machine attention reaches 0.5 (three deed purchases at +0.12 each via NoteDeed, Empire.cs:467, plus poaching machine member Tibor at +0.2, Empire.cs:456/EmpireSetup.cs:62) sets Stage 2 => MachineInspecting: the game adds round(CleanIncomePerDay*0.75*FactorFor(id)*heatTerm) per front while the lab at line 338 adds round(CleanIncomePerDay*FactorFor(id)*heatTerm) — 33% more clean income per front per day than the shipped game would pay, for every remaining day of the 21-day run.

### `ledger/Assets/Scripts/Core/Economy.cs:193` (economy)

**Claim:** Weekly supplier deliveries and MakeAmends (Economy.cs:256) are paid with wallet.Spend(price, dirtyOk: true), letting unwashed cash pay day-world tradesmen — contradicting the wallet's own currency rule ('dirty money... only criminal counterparties take it', Wallet.cs:5-8) and the deliberate contrast the empire code draws (BuyClean uses dirtyOk:false at Empire.cs:298 while BuyDebt's dirtyOk:true is annotated 'criminal counterparties take dirty money for it — that is rather the point', Empire.cs:313-317).

**Failing input:** Wallet with Clean=0, Dirty=500 at a morning close on a delivery day: Mirek's $90 drink delivery is paid entirely from the dirty pile (Spend's clean-first split falls through to Dirty), converting $90 of unwashed cash into day-world goods with no launder-cap accounting — a hoarder can keep Dirty just under LaunderPerDay and still run all supply costs on night money, weakening the §6.7 evidence pressure (GameController.cs:1419 only checks Dirty > LaunderPerDay).

### `ledger/Assets/Scripts/Game/GameController.cs:1014` (fall)

**Claim:** RunTheFall's cleanup assumes it runs at the 8:00 morning-close frame, but the CI-staged Fall fires at hour >= 10 (SimDirector.cs:446-451 -> ForcePendingFall), by which time same-day in-flight state can exist that the Fall neither resolves nor cancels: a pending evening beat created by OfferEvening (hour >= 9, GameController.cs:1229) is skipped by ResolveLapsed in the very next lines of the same Update (524-525) with the full stood-up penalty (Beat.cs:53, -0.15 loyalty, 'They never showed. Noted.') from a host who was simultaneously given the memory that the player spent those days in custody; and an active courier shift (accepted 8:00-12:00, DayJob.cs:27-38) survives the jump because Lapse() is false at 8:00 (DayJob.cs:65), so the bot walks out of three days' custody still mid-round and completes it for pay — this also invalidates the 'no pending beat can exist at the Fall frame' clean claim in game-design/audit-findings-2026-07-27.md line 227, which only considered the organic 8:00 path.

**Failing input:** CI run: day 9, OfferEvening at ~9:00 creates evening_d9 (Pending, 21:00-24:00) and StageDayJobShift (SimDirector.cs:275-278) has a shift active; staged fall at 10:00 jumps to day 12 8:00 -> same frame UpdateBeats skips evening_d9 (-0.15 loyalty to the best-loyalty friend) while Job.ShiftActive remains true with WaypointIndex from day 9.

### `ledger/Assets/Scripts/Game/SimDirector.cs:1011` (gates)

**Claim:** verdictSane's `camp.Verdict != Verdict.LostCastOut` clause became unfalsifiable when the day-8 ForceOpenMode was added: any pre-open verdict (including LostCastOut) is rewritten to Ongoing at day 8 (Campaign.cs:85-91), and in open mode exhausted patience sets OutfitCutOff instead of LostCastOut (Campaign.cs:135), so at Finish of any >=8-day sim the clause is tautologically true.

**Failing input:** Bot cast out on night 5 (three missed drops, patience 1.0 - 3*0.34 <= 0): _weekLostVerdict records LostCastOut (report-only, ungated); ForceOpenMode at day 8 sets Verdict=Ongoing; at Finish the named cast-out check passes and the failure only surfaces indirectly through the jobs-count clause (4+1=5 < 7) under the same 'verdictSane' label — the check written to catch a broken job pipeline no longer answers that question.

### `ledger/Assets/Scripts/Game/SimDirector.cs:38` (gates)

**Claim:** ActTwoGraceSamples counts game-hours while beat firing runs on a 30-frame cadence, and in sim mode the clock advances min(realDelta, 2s) * 20 game-minutes per frame — so on a runner sustaining below ~10 fps one game-hour spans <= 30 frames, CheckActTwo may not run between two consecutive hourly samples, and a beat that would fire normally can accumulate the 2-sample grace and red the build with no game defect.

**Failing input:** Runner at 5 fps (step 0.2s -> 4 game-min/frame -> one hour = 15 frames, CheckActTwo every 30 frames = 2 hours) during day 9 with pp6 newly due at the 8:00 close (racket income first paid, Ossei interviews on file): ActTwoSample increments at hours 8 and 9 with no CheckActTwo pass between, count reaches ActTwoGraceSamples=2, then the 10:00 staged fall lands on day 12 and Finish reads act2Ok=false (lines 1102-1103) for a beat the game was never given a tick to fire — the exact race the grace was built to close, reopened by the frames-vs-hours unit mismatch (GameController.cs:471-481, 530-540).

### `ledger/Assets/Scripts/Core/Empire.cs:351` (gossip)

**Claim:** Two side-channel rumor writers bypass the Holds() dedup that Gossip.Backfire (Gossip.cs:550) and Debts (Debts.cs:93) use: Empire.Squeeze appends a fresh identical backfire rumor on every refused squeeze after the first, and Phones.LeaveMessage (Phones.cs:159) appends a new rumor on every repeated message.

**Failing input:** Player squeezes a high-nerve/low-loyalty owner on day 5 (refused, rumor player.squeezing_X='true'@0.85 added), again on day 6, day 7... — LastSqueezeDay (Empire.cs:328) only blocks same-day retries, so the owner accumulates one duplicate 0.85 sensitive rumor per attempt; likewise leaving the same phone message 10 times gives the taker 10 copies of player.left_word@0.55. List growth plus duplicate spread events; DayCircleHeat is unaffected only because it takes best-per-topic.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:933` (legibility)

**Claim:** The HUD campaign readout appends a raw stat counter — `(camp.Falls > 0 ? $"  ·  falls: {camp.Falls}" : "")` — under a comment (lines 921-922) that promises the readout is 'in words, not meters'; a fall-count is nobody's circumstance, it is a scoreboard.

**Failing input:** Get caught once (Campaign.Falls = 1): the always-on status line renders 'Day 5 of 9 · the street: quiet · the outfit: patient · falls: 1'. Every other value on that line (heat, patience) goes through HeatWord/PatienceWord.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:773` (legibility)

**Claim:** The morning summary card prints the open-liability COUNT as a bold digit: `$"Open liabilities you haven't dealt with: <color=...><b>{talkCount}</b></color> — press L for the books."` (fed from GameController.cs:1413-1415).

**Failing input:** Close a day with 3 unhandled Knowledge entries: the player-facing day-summary card (ShowDaySummary, guarded to never show in sim mode, so it is purely a player surface) reads 'Open liabilities you haven't dealt with: 3'.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:854` (legibility)

**Claim:** The ledger's street section shows the supplier arrears COUNT as a digit: `$"<b>{s.Name}</b> — owed for {s.Unpaid} {(s.Unpaid == 1 ? "delivery" : "deliveries")} of {s.Goods}"` — the singular case is worded, the plural prints the number.

**Failing input:** Skip paying Mirek twice (Supplier.Unpaid = 2), open the ledger: 'Mirek — owed for 2 deliveries of ale'. The parallel model-facing copy of this line (GameController.cs:750) is a lesser concern, but this one is on the player's screen.

### `ledger/Assets/Scripts/Core/Access.cs:295` (legibility)

**Claim:** The doorman fallback line generator DefaultNearly embeds raw numbers: `$"Not before {k.Amount}. Come back when it is dark enough."` prints a bare HOUR (Amount is compared to s.Hour, Access.cs:110-113), `$"You have left it too late. Before {k.Amount}, and not after."` (line 297), and `$"You would want {k.Amount} people behind you, and you have {s.Crew}."` (line 303) — currently LATENT: all four AccessSetup gates author their own Nearly strings in words, and nothing else constructs gates, so today these lines are unreachable; the first gate added without .Reads() puts 'Not before 21.' in a player toast (AccessHost.cs:96 shows result.Hint directly).

**Failing input:** Add any gate with `new AccessKey(KeyKind.After, 21)` and no .Reads(): refusal hint toasts 'Not before 21. Come back when it is dark enough.' — an hour as a bare integer, not even a clock time. The no-digit enforcement (ReadPlan) does not cover doorman lines, so nothing would catch it.

### `ledger/Assets/Scripts/Game/SimDirector.cs:22` (purity)

**Claim:** SimMode.Days returns the parsed -simdays value unclamped, and the codebase gates on it inconsistently ('> 0' vs '== 0'), so a negative value produces a normal-looking game with driving, traffic audio, footsteps, and the API-key prompt all silently disabled.

**Failing input:** Launch 'LEDGER.exe -simdays -1': int.TryParse succeeds, SimMode.Days == -1. Bootstrap.cs:32 tests '> 0' so the MainMenu and normal game come up, and GameController.cs:441 never attaches SimDirector — but the guards written as equality now fail: GameController.cs:520 'if (SimMode.Days == 0) CheckDriving()' disables driving entirely, TrafficHost.cs:78 'if (SimMode.Days == 0) HearTraffic()' kills traffic audio, PlayerController.cs:102 kills footsteps, and DialogueUI.cs:185 'Secrets.LoadAnthropicKey() == null && SimMode.Days == 0' suppresses the API-key prompt, so LLM conversations can never connect and the player is never told why. Perturbing the input from -1 to 0 restores all four systems, so the two comparison styles are genuinely divergent, not redundant.

### `ledger/Assets/Scripts/Game/SimDirector.cs:19` (purity)

**Claim:** SimMode.Days calls Environment.GetCommandLineArgs() — which allocates a fresh string[] copy — on every read, and it is read at least six times per frame on the normal-play hot path for a value that cannot change after process start.

**Failing input:** In a normal (non-sim) session at 60fps: GameController.Update reads it at lines 465, 483, 518, and 520 every frame, CheckBarDoor (GameController.cs:1188) is called every frame (per the comment at 527-529), PlayerController.Update reads it at line 102, and TrafficHost.TickTraffic at line 78 — roughly 7 calls/frame, i.e. ~420 array clones plus arg-string comparisons per second of steady GC garbage in MonoBehaviour Update paths, for a launch-time constant that a 'static readonly int' or lazy cache would read once. No behavioral bug in the positive/zero cases, purely hot-path cost.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:512` (reachability)

**Claim:** ActThreeLedgerLine() has no caller anywhere in the codebase, so its authored post-close lines — including the Quiet-ending-specific "-- it is not yours anymore --" — can never display; RefreshLedger's parallel audit block shows "The books were opened on day X" even after a handover.

**Failing input:** Player earns the Quiet ending (HandOver + audit closes) and opens the ledger panel (L). DialogueUI.RefreshLedger lines 888-909 render its own audit section whose AuditClosed branch is the single line "The books were opened on day {AuditClosesDay}" regardless of Result; grep for ActThreeLedgerLine finds only the definition, so the distinct it-is-not-yours-anymore state is never shown to anyone.

### `ledger/Assets/Scripts/Game/ActThreeHost.cs:254` (reachability)

**Claim:** _inspectorAskedDay is a non-persisted field while its partner ActThree.LastDealtDay is persisted, so saving after the morning ask and reloading the same day silently voids that day's cooperate/stonewall: the ask is not repeated and the answer buttons stay dead.

**Failing input:** Audit day N: at 10:00 the ask block sets ActThree.LastDealtDay=N (persisted) and _inspectorAskedDay=N (not persisted). Player saves via the pause menu and reloads. _inspectorAskedDay is -1, so InspectorWaiting (line 345) is false and AnswerInspector's guard (line 323, _inspectorAskedDay != Now.Day) rejects; the re-ask guard LastDealtDay != Now.Day (line 168) also fails — CooperateText/StonewallText are undisplayable for day N and one scope-narrowing opportunity is permanently lost.

### `ledger/Assets/Scripts/Game/GameController.cs:1296` (reachability)

**Claim:** When Act II's PP4 collision fires, the beat-attendance toast written one line earlier is overwritten in the same frame by Pp4CollisionText, so the "You stayed a while. X will remember this." acknowledgment for that evening is never visible.

**Failing input:** Act II open, one non-departed crew member exists, player steps onto an evening beat's marker for the first time since PP4 became armed: line 1295 toasts the attend line, line 1296 calls FireCollision which immediately calls ToastLine(ActTwoState.Pp4CollisionText, 14f) (line 711), replacing _toastText.text before the frame renders.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:536` (ui)

**Claim:** The empire button click path never re-validates the on-screen label against current state, so at an Act III state boundary a click executes a different verb than the one displayed — labels refresh only every 30 frames while the world keeps moving.

**Failing input:** Talking to Halvard during the audit, button A shows 'Sell up, pay everyone off' (ActThreeButtons, lines 414-426). The audit closes on its named morning (CloseAudit fires at Now.Day >= AuditClosesDay && Hour >= 9, ActThreeHost.cs:207) between two 30-frame refreshes (lines 1039-1044). Player clicks: EmpireAct -> ActThreeAct returns false at the `a3.AuditClosed` guard (line 475), execution falls through to the Act II Halvard branch (line 538) and silently spends $ReadPrice of the player's money on 'buy a read' they never chose. The typed/router path re-refreshes and re-checks Live() before executing (TryRouteAsync 1301-1321); the click path has no equivalent guard.

### `ledger/Assets/Scripts/Game/DialogueUI.cs:1530` (ui)

**Claim:** PlantDoubt does not handle the NoSuchRumor outcome, so a lead made stale by the Fall's rumor wipe can never be settled via the Plant-doubt verb — unlike PayOff and LeanOn, which route the same outcome through ResolveStale.

**Failing input:** Player learns a lead on day 5; the Fall (RunTheFall) wipes the mill's player rumors; day 7 the KnownLead snapshot still shows in the DC row (CurrentLead reads _game.Knowledge, not the mill). Clicking 'Plant doubt' -> Discredit finds 0 matching rumors and returns NoSuchRumor (Gossip.cs:457); line 1530 only marks handled on Contained/AlreadyDenied, so it narrates 'No such story to discredit.' forever and the liability stays open in the ledger, while PayOff/LeanOn on the identical state mark it settled via ResolveStale (lines 1411-1417).

### `.github/workflows/ledger-build-windows.yml:184` (workflow)

**Claim:** The Verdict step's key filter contains a dead alternative: 'dayJob=' matches no token in the done line, which emits 'dayJobStaged=' and 'dayJobOk=' (SimDirector.cs:1281), and the anchored '^dayJob=' cannot match either — so the day-job field never appears in the compact verdict this step exists to surface.

**Failing input:** Any completed run: split the done line on spaces and the tokens are 'dayJobStaged=True dayJobOk=False ...'; '^(...|dayJob|...)=' rejects both (the char after 'dayJob' is 'S'/'O', not '='), so on a run failing the dayJob gate the compact '$keys' line silently omits every day-job field while the other 10 alternatives all print.

### `ledger/ShapeCheck/Program.cs:96` (workflow)

**Claim:** The inherited-member whitelist is applied to every file in the tree, including Assets/Scripts/Core, which is engine-free and contains no MonoBehaviours — so a genuine typo'd bare reference to 'name', 'tag', or 'enabled' in a Core class (where the real field is '_name' etc.) is a real CS0103 that gets whitelisted away.

**Failing input:** A Core class with field '_name' whose method reads 'return name.Trim();': CS0103 'name' is raised, 'name' is in the inherited set, line 96 discards it, ShapeCheck passes; the Unity build (the only other compiler of this tree in CI — CoreTests does not run in this workflow) fails 20 minutes later.

### `ledger/ShapeCheck/Program.cs:95` (workflow)

**Claim:** The lower-case-initial CS0103 narrowing false-negatives on any mistyped BARE PascalCase name — a typo'd method call like 'Destory(obj)' for 'Destroy', or a typo'd own-class PascalCase method — and dotted member typos never surface as CS0103 at all (they are CS1061, which is neither in the 'interesting' set nor covered by the narrowing), so property-name typos slip through regardless of case.

**Failing input:** A MonoBehaviour calling 'Destory(gameObject)': Roslyn raises CS0103 'Destory'; char.IsLower('D') is false at line 95, the diagnostic is discarded, ShapeCheck reports clean, Unity fails ~20 minutes later. Same for '_game.Walet' (CS1061, discarded at line 97 since only CS0103 gets the missing-local path).

### `ledger/lint-usings.py:26` (workflow)

**Claim:** The LINQ-name regex omits several always-LINQ extension methods — TakeWhile, SkipWhile, Append, Prepend, Contains (on arrays/IEnumerable), ElementAt/ElementAtOrDefault, DefaultIfEmpty, ToLookup, MaxBy/MinBy, Chunk — so calls to them in a file without 'using System.Linq;' are invisible to the lint even with a lambda on the same line.

**Failing input:** 'var ready = queue.TakeWhile(j => j.Ready);' in a file with no System.Linq using: no alternative in the line-26 regex matches 'TakeWhile' (the 'Take' alternative fails because the next char is 'W', not '(' or '<'), lint prints 0 errors, Unity fails the compile on the runner.

### `ledger/lint-usings.py:64` (workflow)

**Claim:** Empty-call LINQ on names outside ALWAYS_LINQ is never flagged even though the module docstring says the trigger is 'a lambda or an empty call': '.First()', '.Min()', '.Max()', '.Reverse()' or '.ToArray()' on an array/IEnumerable receiver require System.Linq but contain no '=>', so line 64-67 skips them.

**Failing input:** 'int best = scores.Min();' (scores is int[]) in a file without 'using System.Linq;': 'Min' is not in ALWAYS_LINQ, 'after' has no '=>', the match is dropped, lint reports clean, and Unity raises CS1061 twenty minutes later.


---

## Checked and came back clean (as stated by the finders)

- gates: ActTwoOwed() (SimDirector.cs:499-516) matches the CheckActTwo firing sites (GameController.cs:634-694) exactly on all six sampled beats — pp1 (2 arms at attention >= 0.25), pp2 (machine >= 0.5), pp3 (newcrew >= 0.5 or Ruta crewed), pp5 (2 arms >= 0.5), pp6 (Ossei spawned + interviews + racket income), pp7 (arm at stage >= 4, with fired := TableArmId != null exactly mirroring the firing guard `!TableFired && TableArmId == null`); PP4's exclusion is correct since FireCollision keys off an attended beat, not standing state.
- gates: The Fall landing on the same hour value cannot swallow an hourly sample: the organic fall fires inside the same GameController.Update that first advances the clock into hour 8 (close at 1335-1339 -> RunTheFall at 524 run sequentially), so SimDirector never observes a pre-jump hour-8 world that would set _act2SampleHour/_vehicleScanHour/_lastSampledHour to 8; the staged fall fires at hour >= 10 and lands at 8:00. In every path the post-jump hour differs from the last sampled hour and the landing-frame sample runs.
- gates: errors==0 is genuinely asserted — gate ("noErrors", _errors.Count == 0) at SimDirector.cs:1245 — and the 30-entry cap in OnLog (line 106) cannot silently pass: it stops appends, not the count, so 30+ errors still hold the gate red and the first 30 appear verbatim in sim-report.json.
- gates: The vehicle-fact latch is race-free against the Fall's rumor wipe: vehicle facts are filed at drop completion (nights 22:00-02:00) under topic `player.vehicle_d{day}` (GossipDirector.cs:279, matching the latch's StartsWith at SimDirector.cs:151), the hourly scan latches them within one game-hour, and both fall paths fire only at morning hours (close hour 8 / staged hour >= 10), so the wipe can never outrun the next scan.
- gates: sawADropWithTheCar's baseline is sound: _witnessesWhenCarArrived snapshots NightWitnesses on the first day-5 frame before the car is teleported to the player (SimDirector.cs:134-138), and every subsequent witnessed drop has the car 2.6 m away — inside VehicleSeenAt's 12 m radius (TrafficHost.cs:438-444) — so a positive gate precondition always implies a vehicle fact was actually filed.
- gates: beatsResolved cannot be tripped by the 3-day time jump: UpdateBeats runs immediately after RunTheFall in the same GameController.Update (lines 524-525), so beats whose windows fell inside the skipped days (including open-mode evening_d* beats) are marked Skipped before SimDirector's Finish can read them Pending.
- gates: The one remaining `now.Day >= 9` (staged fall, SimDirector.cs:446) is genuinely safe as its comment claims: RunTheFall is the only writer that moves the clock, so with Falls == 0 day 9 arrives un-jumped; the hour >= 10 guard keeps day 9's 8:00 close (DaysClosed reaching 8 on the won path) ahead of the jump; and with OpenMode guaranteed by day 8 (organic or forced) plus Verdict pinned Ongoing post-force, ForcePendingFall always takes, so fallOk's Falls >= 1 precondition is reached in every 9-day run.
- gates: osseiOk cannot race its own sampling: ObservedPeakHeat is updated from the same `heat` local the spawn decision reads in the same CheckOssei pass, peak-update ordered before the spawn check (GameController.cs:1117-1119), so OsseiSpawned == (peak >= threshold) is comparing values captured on one cadence.
- gates: disguiseWorks reads MaxCoatedWitnessConf latched at rumor-creation time inside the drop-completion handler (GameController.cs:1506+), not from the end-of-run mill, so the Fall's wipe cannot erase its evidence — the witness-car lesson correctly applied.
- gates: harmOk's day-12 post-jump read holds: Sam's untreated cut turns at the day-6 tick (DaysBeforeItTurns=2) becoming Broken with HealsOnDay=14 > 12, Rocco's treated cut can never turn (DailyTick skips Treated), skipped days 10-11 are never ticked (TickWorldDay's single-tick guard), and the feud decays 5-6 ticks to heat 0.52-0.55, keeping !WillWorkTogether true — though note the margin over the 0.5 line is a single daily tick (0.02-0.05).
- clockjump: Harm injuries handle the jump correctly by construction: healing (`HealedBy(day) => day >= HealsOnDay`, Harm.cs:57) and worsening (`day - i.DayTaken < DaysBeforeItTurns` with the WentBad latch, Harm.cs:213-220) are absolute-day arithmetic, so one post-jump DailyTick applies every skipped day's turn exactly once — a Cut taken the day before a Fall turns Broken on landing, 2 days late but never twice, and a wound cannot both heal and turn.
- clockjump: Beats cannot straddle a Fall: every beat's window dies by midnight of its own day (WindowPassed, Beat.cs:31), ResolveLapsed runs every frame (GameController.cs:1259), authored beats exist only on week days 3 and 5 (GameController.cs:426-435) while Falls require open mode (day 8+), and generated evenings (line 1242) are always same-day — so no pending beat can exist at the 8:00 Fall frame, and the skip penalty latches State exactly once.
- clockjump: The landing-day close skip is deliberate and clean: `_lastClosedDay = Now.Day` (GameController.cs:1023) means CloseDay, Empire.DailyTick, Economy.DailyTick, FireDuePressures and the Director all skip the in-prison days wholesale and resume at landing+1 — no double close, no retroactive triple-banking, and Campaign.ConsumeFall resets ExposedStreak so the fuse cannot immediately re-fire.
- clockjump: Rumor aging is elapsed-time based, not per-call: Age() computes `hrs = (now.TotalMinutes - _lastAge.TotalMinutes) / 60.0` and decays by `0.5^(hrs/RumorHalfLifeHours)` (Gossip.cs:521-524), so the skipped 72 hours are decayed correctly in one step at the first post-jump hour tick; the Fall's player-rumor wipe (GameController.cs:1029) and half-life reset to street speed both happen before that, matching the stated intent.
- clockjump: Every once-per-day guard compares equality to Now.Day, so the jump re-arms rather than wedges them: _barkDay (GameController.cs:558), _lastWarnDay (1560), _confrontedDay (1207), _coatSeenDay (1550), AccessHost._gateSpokeDay (AccessHost.cs:80), TrafficHost._struckRecently (TrafficHost.cs:101), Debtor.LastAskedDay (Debts.cs:37), Business.LastSqueezeDay (Empire.cs:328), and all arms' LastActDay (Empire.cs:642/692/724).
- clockjump: Empire's modulo cadences survive the jump: `now.Day % 3` phases (machine fees Empire.cs:632, newcrew incidents 678, skim memory 545) are preserved by the exactly-+3 jump, and since they only execute inside DailyTick at a close, skipped days skip them wholesale with everything else — no double-fire, no phase drift.
- clockjump: Economy's weekly supplier deliveries use absolute-day arithmetic (`now.Day - s.LastPaidDay < 7`, Economy.cs:189): a delivery due inside the skipped window arrives at the first post-Fall close, is charged once and increments Unpaid once — no retroactive triple-billing, and standing drift only applies per close, consistent with the skip-wholesale rule.
- clockjump: SimDirector explicitly handles the jump for its own coverage arithmetic: `skipped = now.Day - _lastSeenDay - 1` extends _endDay by the skipped days, capped at MaxReclaimedDays so repeated Falls cannot make the run unbounded (SimDirector.cs:204-226).
- clockjump: Ossei's post-Fall calm is latched on absolute days and persisted: `_osseiCalmUntilDay = Now.Day + 4` uses the post-jump Now (GameController.cs:1043), restoration requires `Now.Day > _osseiCalmUntilDay && heat >= threshold` (1120-1121), and the field is captured/restored in the save (1698/1747) — perturbing either the day or the heat changes the outcome.
- clockjump: Debts carry no interest and Phones have no day fields (only OpenFrom/OpenTo hours, Phones.cs:55), so neither can be corrupted by the jump; the day-job shift cannot be active at an organic Fall (Falls consume at the 8:00 close frame, overnight shifts have already lapsed via Lapse()'s Hour>=18/<8 rule checked every 30 frames, and same-day accepts cannot precede the close), and the Fall destroys the night-job marker without invoking JobMissed (GameController.cs:1019), so no patience penalty leaks from the skipped nights.
- coretests-endgame: Decision 9 is genuinely pinned: with the street coupling reverted (flat r.IncomePerDay), TakeAtStreet(0.4) and TakeAtStreet(1.3) both return 100 == plain, failing Program.cs:1877 and 1880; the 'street' event at factor 0.4 is pinned at 1900; and the parameter is wired in real play — GameController.cs:1369 passes Economy.FactorFor(null) into Empire.DailyTick (BalanceLab/Program.cs:349 likewise).
- coretests-endgame: Decision 10's cooperation constant is jointly pinned to the interval (0.0375, 0.0625): reverting 0.045 -> 0.09 gives ScopeFactor(4,0)=0.64 and fails 'greater than 0.75' at Program.cs:3021; over-halving below 0.0375 fails Reads('Cooperations') at 2885 (needs 0.8*(1-6c) < 0.62). A revert cannot pass.
- coretests-endgame: The stonewall asymmetry is pinned: making stonewall symmetric at 0.045 fails Program.cs:3027 (0.135 < 0.135 is false) and 3030 (1.135 > 1.35 is false); reverting stonewall down to 0.09 fails 3030 (1.27).
- coretests-endgame: The decision-10 booksAreClean gate on Both is pinned: 'mitigated' (raw strain 1.0, seen 0.5425 < 0.62) would resolve Both without the raw-strain gate, failing Program.cs:2953; and 2951 (!= BurnBoth) simultaneously pins the Kingdom-does-not-require-the-life-gone fix — with a life-gone requirement the fixture (loyalty 0.8) would fall through to BurnBoth.
- coretests-endgame: All 14 Reads() perturbations in TestEveryInputIsRead (Program.cs:2855-2887) were verified numerically to flip Resolve (e.g. Cooperations: seen 0.8 -> 0.584 across the 0.62 threshold; Stonewalls: 0.55 -> 0.88; LedgersMoved: 0.7 -> 0.385), and the two declared exemptions (CrewCount, DayLifeDeparted) are genuinely unread by Eligible().
- coretests-endgame: Ending.None is unreachable when the audit closes: Eligible() always appends BurnBoth when none of Quiet/Both/StraightLife/Kingdom is present (ActThree.cs:319-321, guard includes Quiet), Resolve(null)==BurnBoth is pinned at Program.cs:2733, and ActThreeHost.CloseAudit (ActThreeHost.cs:218-220) resolves a freshly built LedgerState — SimDirector's gate additionally requires _actThreeEnding != Ending.None (SimDirector.cs:1117).
- coretests-endgame: Quiet's deliberate strain exemption and rank are pinned: Ruinous books + handover still resolve Quiet (Program.cs:3012 — would fail if Quiet were books-gated), Quiet outranks a live Both (2725-2726 pins list ordering), and HandedOver without a ready successor cannot reach it (2730).
- coretests-endgame: Both StraightLife doors are pinned and books-exempt for real: the sold-up door on Ruinous books (Program.cs:2976) and the never-built door whose fixture strain 0.66 exceeds BooksHoldThreshold (2992-2996), while the life gate still holds (neitherOne -> BurnBoth, 3001).
- coretests-endgame: The SeenStrain deflection multiplier 0.7 is tightly pinned to [0.62, 0.8): lowering it below 0.62 flips coldAndRuined (seen 1.0*mult) to Kingdom, failing Program.cs:2969; raising it to 0.8+ makes mitigated seen >= 0.62, failing 2948.
- coretests-endgame: Every one-way Act III latch survives its codec: SoldUp/Deflected/DeflectedOnto/BurnedWitnessId (Program.cs:2776-2786), the inspector's counts and LastDealtDay (3084-3092), and LastDayActions/LedgersMoved (3138-3145) are all round-tripped through Capture/Restore against a fresh instance — these are pure-state tests, not reads of a moving world.
- coretests-economy: streetFactor coupling (Program.cs:1854-1880) genuinely fails if Empire.DailyTick ignores the factor again: plain = 100, TakeAtStreet(0.4) must be 40 and TakeAtStreet(1.3) must be 130; ignoring the parameter makes both 100, failing the strict inequalities at 1877/1880, and TakeAtStreet(1.0) == plain pins the neutral default. The poor-street 'street' event at 1898-1900 also fails if the factor is ignored (street < 0.7 branch never fires).
- coretests-economy: Economy squeeze coupling can fail: quiet vs squeezed (Program.cs:2110-2126) differ only in racketIncomeToday (0 vs 170); if DailyTick ignored the input the two deterministic runs would be identical and all three strict-inequality checks fail. The wage coupling likewise (2133, strict >, would be exact equality if wagesPaidToday were ignored).
- coretests-economy: The takings-factor UPPER clamp is genuinely tested: the 'wild' fixture (Program.cs:1769-1774) restores prosperity 9.0 (clamped to 1.0 by Restore) and priceLevel 0.0 (clamped to 0.5), giving raw factor 1.875; deleting the Clamp in the TakingsFactor property fails the <= MaxTakingsFactor check.
- coretests-economy: Wallet laundering tests pin exact values (Program.cs:1135-1141): washed == 120 (the daily cap), remainder 30 next day, TotalWashed == 150, and Clean == 0 && Dirty == 150 pins clean-spends-first ordering; a refused overspend is verified to move nothing. Seize is pinned to exactly the dirty balance and to zero on a second call (437-438).
- coretests-economy: Every crew-cut and treaty term is pinned with exact arithmetic that fails if its term is dropped: generous 60-15=45 (775), skim lower-bounded at +15 (779), rotten-hook quarter-skim 60->45 (726), dockside tribute 60->53 (933), stage-2 rent exactly -40/day and only from the day after imposition (742), patron tribute exactly -50 (880), machine fee exactly -150 clean money (831).
- coretests-economy: Purse transfers are asserted on both sides: Borrow moves exactly 75 (debtor +75 at 3432, patron 380->305 at 3433) with the favour recorded; Take empties the drawer and never goes negative (3393, 3401); Collect-with-purses credits the wallet exactly 45 while the balance 75 stays on the page (3482-3483), and the next-day Begged outcome transitively proves the purse was debited.
- coretests-economy: Purse-prosperity coupling can fail: rich vs poor fixtures (Program.cs:3415-3422) differ only in the prosperity argument (0.8 vs 0.2), FlowAt(0.5) == 1.0 pins the neutral rate exactly (3409), and the 60-day ceiling check (3424, Cash == 200 exact) fails if the hoard cap is removed.
- coretests-economy: Dirty/clean segregation is exercised for real, not vacuously: the BuyClean refusal fixture (Program.cs:668-669) holds Clean 100 + Dirty 2000 — more than enough total to cover the 900 ask — so the check fails if Spend(dirtyOk:false) ever dips into dirty; BuyDebt asserts the exact dirty remainder (679); MachineTick fees are verified to come from clean only (831, wFee.Clean == 250).
- coretests-economy: The quit/rot breaking point asserts money, not just flags: the skimmed need-route quitter fixture (Program.cs:790-794) checks wQ.Dirty == 0 — income is suppressed on the quit day — alongside racket death and the departure flag, and the departed+cut state survives the codec (800-801).
- coretests-economy: Money state round-trips are all asserted against concrete mutated values: wallet Clean/Dirty/TotalWashed (570), a part-paid debt reloads at 75 not its original 120 (3556 — the 'steals back what was collected' regression), purses re-serialize byte-identically including patron and favours (3562-3564), and economy prosperity/prices/refusal/LastPaidDay survive (2232-2236). None of the CoreTests money checks reads a still-moving world — every fixture is synchronous and its state latched before the assertion.
- coretests-social: TestCampaign (Program.cs:371-440): every verdict transition is tested from both sides, post-verdict no-ops are pinned with before/after counters (JobsDone, JobsMissed, CloseDay returning 0), and the open-mode Fall is tested as a LATCHED flag — the fuse sets FallPending, only ConsumeFall clears it and increments Falls. Recomputed CloseDay arithmetic (220 -> 126 at heat 0.5) confirms every threshold check can fail on a one-input perturbation.
- coretests-social: TestEveryKeyKindHasItsOwnWords (Program.cs:1698-1745) is a correct open-vocabulary canary: it enumerates KeyKind via Enum.GetValues, so a NEW kind hits AccessKey.ShortfallFrom's default (returns 1, never held) and fails 'can actually open a door'; the generic-fallback set and the distinct-lines HashSet additionally catch a new kind that reuses the flat default or copies another key's voice.
- coretests-social: TestEveryApproachIsADifferentPlan (Program.cs:1646-1696) enumerates Approach via Enum.GetValues and demands pairwise-distinct risk AND visibility from live reads; a new Approach with no RiskOf/VisibilityOf case collides with Quiet's clamped 0.0 visibility in this fixture and fails the distinctness check. The cross-world checks (hot street hurts Social, low nerve hurts Quiet) verified against RiskOf's actual coefficients.
- coretests-social: TestClosedVocabulariesAreHandled (Program.cs:1903-2001): the Effects and Pressures canaries pin All.Length against the handled list, so ADDING a member fails the build until IntentBridge/DirectorHost gain a case — the hardcoded list cannot go silently stale because the length equality breaks first; and Checks.All is iterated from the source vocabulary in both the can-pass and can-refuse directions.
- coretests-social: TestGossip's anti-amplification block (Program.cs:305-312) is fully falsifiable: duplicate-rumor count, DayCircleHeat, and suspicion are all pinned with exact before/after equality after a third Tick, and all three fail if the bounce guard (Gossip.cs:216-218, existing.Confidence >= passed) is weakened. The best-per-topic dedup check at line 341 also genuinely bites (a sum-based heat would read 0.825, not 0.75).
- coretests-social: TestDamageControl (Program.cs:1171-1239) reaches every DcOutcome branch with trait-parameterized fixtures (greed 0.6/0.1, nerve 0.3/0.9, CantAfford via a real underpriced offer against price 200), and the once-per-story discredit cap is verified by exact confidence equality after the refused second denial — not just by the returned outcome code.
- coretests-social: TestHooks (Program.cs:1029-1088): the strong-hook leash is verified through actual Tick spread (warehouse rumor at confidence 0.68 would reach Lena without the Leashed guard), its subject scoping is verified (marek.debt still travels while leashed), and the §6.3 protection guarantee is checked against both Bribe and Intimidate backfire rumors; weak-hook one-shot, ContainedTopic reporting, and idle-favor-kept branches are all genuinely reached.
- coretests-social: TestHarm (Program.cs:3246-3380): the rot-timing guard is actually exercised inside the window (DailyTick(2) with day-DayTaken=1 < DaysBeforeItTurns=2), wound-cannot-rot-twice and bruise-never-turns are separately pinned, treatment's clean-money-only rule uses a wallet holding 900 dirty and 0 clean (so it fails only through the dirtyOk:false path), and the feud codec roundtrip is full serialize-equality.
- coretests-social: TestPhones (Program.cs:2537-2624): the order-matters check (ringing for Rocco and getting Lena) genuinely pins Regulars-order semantics; the message-as-gossip checks assert hops, confidence band, memory, and mill entry separately; and the codec roundtrip is full-fidelity Serialize(twin.Capture()) == snap plus a Restore(null) no-op check — the strong form the ActTwo roundtrip lacks.
- coretests-social: TestActTwo's mechanical-effects checks (Program.cs:923-943) all bite: the tribute check pins wT.Dirty == 53 against DailyTick's arithmetic (round(60 * (1-0.12)) = 53, deterministic because the fixture racket has BaseRisk 0), so removing ResolveTable's TributeShare assignment yields 60 and fails; FrontsCapped and the newcrew defy (Attention = 1.0, Standing -0.5) are each read off the exact state ResolveTable mutates.
- legibility: Scoping determination, verified against the project's own docs before excluding: dollar amounts and calendar day numbers are a deliberate, consistent diegetic convention, not violations — counterparty-purses-spec.md explicitly carves out 'The player's own money... that is the Wallet' while forbidding purse numbers; design-doc.md's own canonical example ('Mirek asking for more') is implemented WITH the $price (Economy.cs:202 'asks ${price} for it now. He doesn't explain the difference'); how-to-play.md advertises '$40 clean'; roadmap M7 declares legibility 'held' with these in place ('Nothing surfaces as a percentage'). Representative sanctioned sites: HUD wallet/clock (DialogueUI.cs:916-919), day-summary money (DialogueUI.cs:752-757), audit date (DialogueUI.cs:896 — ActThree.cs:102 'that day is named in the letter'), Zlata's '+${pay}' (GameController.cs:891), pay-off buttons (DialogueUI.cs:1353). If the parent reads the law literally, every one of these is a finding; the operative class the project enforces is internal scalars and stat counts.
- legibility: All Act III authored text is digit-free: OpenText, Pp1-Pp5, InspectorArrivesText ('ten past nine' in words), CooperateText/StonewallText, KingdomText, StraightLifeText, EndingText, EpilogueText (ActThree.cs:342-541); strain, scope, and loyalty pass through StrainWord/ScopeWord word ladders (Pp2LenaText, InspectorAskText).
- legibility: All Act II authored text is digit-free and exemplary — Sera Kest's offer and its acceptance spell out 'Twelve per cent' in words (ActTwo.cs:78, 89); TableOffer/TableResult/FirstNotice/all PP texts contain no digits.
- legibility: The plan read itself honors the law by construction: Operations.RiskWord and read.Line/Worry are asserted digit-free in CoreTests (Program.cs:1667, 3077, 4113) and SimDirector re-checks it live (SimDirector.cs:359); PlanUI renders hours as words via HourWord ('three in the morning', PlanUI.cs:184-186) and shows read.Line verbatim.
- legibility: Every internal scalar that reaches a player surface other than the two flagged goes through a word converter: StreetWord/OutfitWord (GameController.cs:152-166), HeatWord/PatienceWord in the HUD status line (DialogueUI.cs:931-932), ProsperityWord/PriceWord in the ledger street section (DialogueUI.cs:843) and supplier ExtraContext (GameController.cs:752), StrainWord/ScopeWord in the ledger audit section (DialogueUI.cs:897-901) and ActThreeLedgerLine (ActThreeHost.cs:523-524), rival/machine/New-crew stages rendered as escalation phrases not stage numbers (DialogueUI.cs:868-884).
- legibility: The 0.00-format scalar dumps are genuinely dev-only: GossipDirector.StatusLine, PurseStatusLine, PhoneStatusLine, and ConversationHost.DebugReport ('Suspicion: 0.42') feed exclusively the F1 _debugPanel (DialogueUI.cs:1028-1032); ActThreeHost.cs:231-233's F2-format verdict line and SimDirector's gate report go to Debug.Log; UiSmokeTest/Perf are log-only. Verified no player surface consumes any StatusLine.
- legibility: Suspicion.Reasons entries ('+0.35 reason', Suspicion.cs:75/81) are never rendered anywhere — the only references in the tree are inside Suspicion.cs itself.
- legibility: All REACHABLE doorman lines are worded: every key on all four AccessSetup gates authors both Opens and Nearly in circumstance language ('Sixty would do it. You do not have sixty.', 'a hundred and twenty', 'after nine', 'Two people behind you' — AccessSetup.cs:35-95), so the digit-bearing DefaultNearly fallbacks are dead today (flagged only as latent).
- legibility: Injury and harm never surface as numbers: outcomes use Look words ('came away {hurt.Look}' PlanUI.cs:207-212, TrafficHost.cs:147), and Harm's player-facing daily lines (Harm.cs:221) are worded.
- legibility: Phone lines, gossip-overheard toasts, beat invitations, coat toasts, epilogue toasts, and the Fall/verdict texts contain no interpolated numbers: Phones.cs:120-140 ('picks up on the fourth ring'), GossipDirector.cs:191, GameController evening/beat toasts (856-1006, digit content limited to sanctioned 'Day 8' framing), PhoneUI.cs:152-168.
- reachability: All ten KeyKind values have doorman lines in both Doors.DefaultOpens and Doors.DefaultNearly (Access.cs:254-307) — the historical After/Before gap is closed, and all four AccessSetup gates additionally author per-key Reads(opens, nearly) pairs, so no key kind falls to a missing line.
- reachability: All four Kingdom/StraightLife text variants are reachable in play: CloseAudit (ActThreeHost.cs:224-229) special-cases them with computed arguments (anybodyLeft from live BestDayLifeLoyalty, everBuiltIt from SoldUp||TotalRacketIncome), correctly bypassing EndingText's hardcoded KingdomText(false)/StraightLifeText(true) arms, which are exercised only by CoreTests.
- reachability: Inspector button identity holds in an unreloaded session: NpcWalker.Spawn(ActThreeState.InspectorName) makes CurrentHostId() return exactly "Tobias Reisz", matching ActThreeButtons' id check, so cooperate/stonewall verbs and their texts are reachable pre-reload.
- reachability: Summit-head identity holds pre-reload: CastTier1 card headers ("# Sera Kest", "# Aldous Vane", "# Danny Ro") equal Empire's Arm.HeadName strings exactly, so the Table's Take/Refuse/Counter buttons gate correctly, and TableOffer/TableResult cover all three arm ids and all three answers with no fallthrough gap.
- reachability: All six EpilogueText variants (day 0; day 1 hot/quiet; day 2 intact/no-letter) are displayable: TickEpilogue runs indexes 0..2 exactly once each on the mornings after a Quiet close, and CloseAudit sets EpilogueDay only for Quiet, matching the only-ending-with-an-epilogue design.
- reachability: Every Act I authored text has a live, satisfiable display site: Pp1CellarLine (day-1 09:30 toast), Pp2RunnerLine (first drop posting at 22:00), Pp4LedgerPage (lena_ledger becoming KnownToPlayer), PostureSceneText and TeaserText (won-week posture panel and end panel in DialogueUI.ShowPostureScene/ShowEndPanel).
- reachability: Act II's OpenText, FirstNotice (all three arm voices), Pp2LetterText, Pp3KidText, Pp5ShopText, Pp6CaseText and the PP7 summons all toast from CheckActTwo with perturbable arm-attention/crew conditions; FirstNotice's ternary covers dockside/machine/else so no arm id yields a missing line.
- reachability: Pp5CallsText's trigger (DaysLeftOnAudit <= 1) and ActThreeState.IsLastDay (day >= AuditClosesDay-1) open the same window, so the last-day announcement and the last-day verbs (LastDayLenaText both variants, LastDayCrewText, LastDayTruthText — all displayed from SpendLastDay) arrive together, in person or via the phone path (BeginPhoneConversation opens the same dialogue with the same empire buttons).
- reachability: Operation texts are fully wired: PlanUI shows PlanRead.Line (in the speaker's voice), read.Worry, and Toasts OperationOutcome.Line (PlanUI.cs:173-195); every RiskWord band and every WorryAbout branch is producible by plan choices, and both no-odds fallbacks are authored.
- reachability: All three campaign verdicts set a non-empty VerdictReason before the end panel reads it (Campaign.cs:139, 166, 176), and Doors.Try's cheapest-key-first ordering plus FirstInformant's " told you:" parsing of the OsseiInterviews format ("{name} told you: {summary}") both check out exactly.
- codec: ActThreeState.Capture/Restore (ActThree.cs:544-587) covers every field on the class, including all ten this-week additions — Cooperations, Stonewalls, InspectorArrived, LastDealtDay, LastDayActions, LedgersMoved, SoldUp, Deflected, DeflectedOnto, BurnedWitnessId — with correct null/empty-string handling for the three id fields; verified field-by-field against ActThree.cs:96-134, and CoreTests Program.cs:3084-3092 round-trips the new counters.
- codec: ActTwoState round-trips completely: Opened/OpenedDay, all six pp flags, TableArmId/TableAnswer (this week's TableArmId included), InjunctionUntilDay/InjunctionAnswered, TruceSpent/ReadsBought, and LastEveningDay with an explicit ContainsKey -1 default (ActTwo.cs:101-126).
- codec: EmpireBook.Capture (Empire.cs:814-846) is complete against the class: businesses (owned/via/debtHeld/lastSqueeze), crew including the Cut policy, rackets, all three arms including Members/Standing/IsPatron/TributePerDay, TotalRacketIncome, and the Table terms (TributeShare/FrontsCapped/SharedRacketId). Decision 9 (street coupling) added no new persisted Empire state — streetFactor is derived at call time from Economy.Prosperity, which is captured in Economy.Capture and passed in at GameController.cs:1369.
- codec: The per-agent gossip capture omits Greed/Nerve/Circle, and that is sound: a repo-wide grep shows they are only ever read, never assigned after construction — while every runtime-mutable Gossiper field (Loyalty, Leashed, Suspicion.Value, Suppressed, Rumors with all six Rumor fields, Knowledge.Facts) is captured and restored (SaveCodec.cs:106-121, 200-230).
- codec: Debtor.Amount is persisted and restored with an amount>=0 guard (SaveCodec.cs:196, Debts.cs:117-121), so part-payments survive a reload and pre-amount saves fall back to the authored figure instead of zero.
- codec: MiniJson has no culture dependency in the save path: Serialize uses InvariantCulture with "R" for doubles (MiniJson.cs:51-53) and ParseNumber uses InvariantCulture double.TryParse (line 194); GetInt's 'v is double' check is safe because every game Restore path runs on freshly-parsed JSON — I found no code outside tests (which serialize first) that passes an in-memory Capture dict straight to a Restore.
- codec: Wallet.LaunderPerDay is derived state and self-heals: recomputed at every daily close from 120 + Empire.OwnedLaunderCapacity (GameController.cs:1360), and the empire's owned businesses are restored, so laundering capacity is correct by the first close after load.
- codec: HarmBook's and PurseBook's Core codecs are themselves field-complete and correct (Injury incl. WentBad/Visible, Feud incl. Exchanges/LastFlaredDay, scars; Purse incl. Windfall/LastBorrowedDay, Favours incl. Settled) — the two high findings are purely missing Game-layer wiring, not codec bugs.
- codec: PhoneBook.Capture being unused loses nothing: phones are pure authored config rebuilt by BuildPhones, and left messages live as mill rumors/memories, which are captured through the agent path.
- codec: PopulationHost restore is safe against seed drift: a save carrying a different seed/count rebuilds the city from that seed with the same Districts/HomeShares/WorkShares constants (PopulationHost.cs:237-260), despawns stale crowd walkers, and RestoreKnown re-marks known residents — the seed-not-census invariant holds (save stores only count, seed, and known ids).
- determinism: No DateTime.Now/UtcNow, Guid.NewGuid, Environment.TickCount, or unseeded 'new Random()' anywhere under ledger/ — the only DateTime is the DateTime.MinValue sentinel in SaveSlots.NewestPath (SaveSlots.cs:35), which compares file mtimes to pick the newest save, which is the intended behavior of 'Continue'.
- determinism: Save files are culture-proof end to end: MiniJson serializes doubles as ToString("R", InvariantCulture) (MiniJson.cs:53) and parses with NumberStyles.Float + InvariantCulture (MiniJson.cs:194); every SaveCodec/Capture number flows through MiniJson doubles (SaveCodec Num() converts values MiniJson already parsed as double), so a de-DE machine writes and reads byte-identical saves.
- determinism: NPC memory markdown round-trips invariantly: MemoryEvent.ToLine writes Importance with "0.00" + InvariantCulture (MemoryStore.cs:24) and FromLine parses with InvariantCulture (MemoryStore.cs:45-46); GameTime's D/H/M format is integer-only (GameTime.cs:51-64).
- determinism: Population is fully seed-driven and platform-stable: Generate takes an explicit seed (Population.cs:153), PopulationHost pins PopulationSeed = 20260726, saves it, and regenerates on restore if it differs (PopulationHost.cs:59, 244-248); HeardIt deliberately uses an FNV-1a StableFraction (Population.cs:363-375) instead of string.GetHashCode, so ambient-rumor membership never reshuffles between sessions or platforms.
- determinism: Population.SetBands imposes a total ordering (load-bearing flag, then cached distance, then Index tiebreak — Population.cs:293-299) precisely because List.Sort is unstable; equal-distance residents cannot swap bands between calls.
- determinism: TrafficSim carries its own 64-bit LCG seeded from a constant (Traffic.cs:252-257; TrafficHost.cs:45 seeds it with PopulationSeed) and its adjacency dictionary uses StringComparer.Ordinal (Traffic.cs:762); CoreTests pins same-seed run identity (Program.cs:3716-3726) and frame-stutter invariance (drift < 2.5, Program.cs:3728-3735).
- determinism: UnityEngine.Random appears exactly once in the Game layer — footstep pitch jitter (Audio.cs:102) — pure audio cosmetics; all procedural audio beds use fixed-seed System.Random (Audio.cs:144-232) and WorldBuilder decor uses new System.Random(9001 + bi * 131) (WorldBuilder.cs:185), visual only.
- determinism: GossipMill's spread is RNG-free and order-safe: Tick snapshots each agent's rumor list before propagating (Gossip.cs:193-206) so spread is one hop per round regardless of iteration order, and the only randomness enters through the caller's 'together' closure — which both BalanceLab (Program.cs:145, 329) and the game supply from their own seeded sources.
- determinism: Operations.Run takes randomness solely via the caller's roll delegate (Operation.cs:260-261 — 'the caller's RNG so the balance lab can sweep it'), and Access gate key selection carries an explicit tiebreaker (OrderBy(CostRank).ThenBy((int)k.Kind), Access.cs:217).
- determinism: SimDirector's CI verdict cannot be flipped by culture or parsing: every gate at SimDirector.cs:1243-1257 is computed from in-process numerics (never re-parsed from formatted strings), the render-fingerprint gate values are explicitly InvariantCulture (SimDirector.cs:654-661), and the workflow's pass/fail is the player process exit code (ledger-build-windows.yml:132), not a grep of numbers.
- fall: Wipe coverage is complete: every rumor-creation site was enumerated (GossipDirector.cs:274/279, GameController.cs:660/718, Empire.cs:347/607/685, Debts.cs:96, PopulationHost.cs:178, OperationHost.cs:91, TrafficHost.cs:142, ActThreeHost.cs:417/469, DirectorHost.cs:192, IntentBridge.cs:273, Gossip.cs:548 backfires) and all use subject "player" (Fact's constructor lowercases), so a.Rumors.RemoveAll(r => r.Content.Subject == "player") at GameController.cs:1029 catches vehicle facts and backfire rumors too — nothing about the player survives in rumor form.
- fall: The ledger's known leads do not dangle after the wipe: RunTheFall's MarkHandled loop (GameController.cs:1037) safely sets a bool on existing entries (no collection mutation during enumeration), and every consumer filters Handled — DialogueUI chips (DialogueUI.cs:672), StrongestFor for the damage-control verbs (PlayerKnowledge.cs:73-75), the day-summary liability count (GameController.cs:1413), the Director snapshot's unhandled count (DirectorHost.cs:88) — while RefreshLedger deliberately renders wiped entries as "settled" (DialogueUI.cs:802-804).
- fall: Hooks and leverage degrade correctly post-Fall: a weak hook is NOT consumed when the target carries nothing (Gossip.cs:495-498 returns NoSuchRumor before SpendWeak), Bribe/Intimidate return NoSuchRumor rather than acting on ghosts (Gossip.cs:397/425), and the strong-hook leash surviving the Fall matches the §6.3 'for good' contract (leashed guards in Tick/CompareNotes/Leads all still hold).
- fall: NightWitnesses and MaxCoatedWitnessConf are latched at drop-completion time (GameController.cs:1505 and 1516 read the rumor back from the mill in the same frame it was created), so the Fall's wipe cannot erase their evidence; the SimDirector gates that consume them (SimDirector.cs:720, 727-728, 925) read only these latched values.
- fall: Act II PP6 and Act III's opener condition (osseiCanName, ActThreeHost.cs:114) consume OsseiInterviews — an append-only list latched at interview time — plus monotonic TotalRacketIncome, so a Fall cannot un-satisfy a beat condition that was true; the _interviewed dedup keys (name|topicKey, GameController.cs:606) cannot collide post-Fall because new witness topics are day-stamped.
- fall: ORGANIC Falls cannot straddle beats or day-job shifts: the fuse only stages FallPending inside CloseDay at the 8:00 close frame and RunTheFall runs in the same Update (GameController.cs:523-524); generated evenings are always same-day (OfferEvening creates Day=Now.Day at hour>=9 and blocks while any future beat is pending, GameController.cs:1228-1245) and lapse by midnight, and courier shifts lapse overnight (DayJob.cs:65, hour<8) — the straddle defect reported above is reachable only through the hour>=10 staged path.
- fall: Rumor aging across the 3-day jump is correct: Age() is elapsed-time based (Gossip.cs:521-524), so the skipped 72 hours decay in one accurate step at the first post-jump hour tick, after the wipe and the calm half-life reset have already applied; and the Ossei calm-window restore (GameController.cs:1120-1127) correctly re-applies PresenceRumorHalfLifeHours only when heat re-crosses the spawn threshold, as its comment intends.
- fall: The night-job board resets are verified against their consumers: _lastClosedDay = Now.Day (GameController.cs:1023) means the skipped mornings and the release morning never close (no triple close, no heat-tax on prison days), and _jobPostedDay = Now.Day (1024) means no ghost drop and — because Campaign.JobMissed only fires when a marker exists (1466-1472) — no missed-drop patience penalty for the nights in custody.
- fall: OsseiCaseAnswerable is wired to ActThree.Deflected (ActThreeHost.cs:38), a latched one-way player action rather than a live mill read, so the Fall cannot flip it in either direction; and FirstInformant's parse (ActThreeHost.cs:487-490, IndexOf " told you:") exactly matches the latched interview format written at GameController.cs:607, so the deflection's burned-witness cost still lands on the right person post-Fall.
- fall: Stale Suppressed sets and Noor's drawer topics left behind by the wipe cannot strand anything: Leads(), CompareNotes and Tick filter by topic key only, post-Fall witness topics are day-stamped fresh keys, and NoorDrawerTopics/Suppressed merely hold silence on topics that no longer have rumors — un-suppressing them later (drawer break, GameController.cs:988) is a harmless no-op.
- purity: (a) All 36 files in ledger/Assets/Scripts/Core scanned for UnityEngine contamination: no 'using UnityEngine', and no MonoBehaviour, GameObject, Transform, Vector2/3, Quaternion, Mathf, Debug., Application., PlayerPrefs, Color, Rect, KeyCode, Input., AudioSource, Texture, Camera, Physics, Coroutine, or UnityEngine.Random anywhere. The only 'Time.'/'Vector'-shaped grep hits are the project's own Ledger.Core.GameTime and MemoryEvent.Time (e.g. MemoryRetrieval.cs:44). Every Core file imports only System.* namespaces.
- purity: (b) One-way dependency holds: no Core file references Ledger.Game, GameController, SimDirector, DialogueUI, any *Host, or any *Setup type (grep clean). The boundary is CI-enforced despite there being no .asmdef: CoreTests.csproj, SimHarness.csproj, and BalanceLab.csproj each compile Core/**/*.cs under net8.0 with no Unity reference, and ledger-core-tests.yml runs the suite, so a UnityEngine or Game-type reference in Core breaks a green build.
- purity: (c) Campaign.ForceOpenMode (Campaign.cs:85): exactly one caller in the entire repo — SimDirector.cs:256 — and SimDirector is only ever instantiated at GameController.cs:441-442 behind 'if (SimMode.Days > 0)' (Bootstrap.cs:32 likewise). The real door, EnterOpenMode (Campaign.cs:49-56), independently requires Verdict == WonWeek, so no UI/player code path can force the city open without the -simdays flag.
- purity: (c) Campaign.ForcePendingFall (Campaign.cs:68): callers are SimDirector.cs:450 and CoreTests/Program.cs:422 only, and the hook self-guards on 'OpenMode && Verdict == Ongoing', so even if invoked pre-open-mode it is a no-op.
- purity: (c) GameController.StageDayJobShift (GameController.cs:916): sole caller SimDirector.cs:277; it self-guards on Campaign.OpenMode and routes through the real Job.Accept(Now) path — it stages only the accept, and no UI or player path calls it.
- purity: (c) DirectorHost.StagePressure (DirectorHost.cs:261): sole callers SimDirector.cs:322 and 328; it validates the pressure (p.IsSomething) and runs through the real Fire(p) primitive; no player-facing caller exists.
- purity: (c) DialogueUI.DismissEndScreen (DialogueUI.cs ~1093): sole caller SimDirector.cs:263; a real player who loses the week keeps the frozen end panel and restarts via the R path, as documented.
- purity: (c) ForceDialogue (DialogueUI.cs:1193) is not a test hook despite the name: it is the NPC-confrontation mechanic called from GameController.cs:1216 in real play, and it refuses to interrupt an open dialogue, the key prompt, the end screen, or the posture panel.
- purity: (c) ReadySuccessor is legitimate shared game logic, not a sim-only hook: real player dialogue uses the same public query (DialogueUI.cs:443 to offer 'Sign it over to them' and DialogueUI.cs:503 to execute HandOver), so SimDirector.cs:423 exercising it goes through the genuine Act III path.
- purity: (c) The sim-mode read guards that exist are correctly placed: TryLoad skips loading the save under sim (GameController.cs:1731), the DialogueUI posture bypass (DialogueUI.cs:1116) and pause/key-panel/day-summary suppressions (DialogueUI.cs:74, 185, 748) are all gated on SimMode.Days > 0, and SmokeTestPanels/CapturePopulationForSim are called only from SimDirector (SimDirector.cs:162, 818).
- economy: Wallet.Spend conservation (ledger/Assets/Scripts/Core/Wallet.cs:26-36): the availability check runs before any mutation, fromClean=min(Clean,amount) and the dirty remainder is covered by the check, so neither purse can go negative and clean-before-dirty is exact; partial spends are impossible.
- economy: Wallet.Seize (Wallet.cs:46-51) takes exactly Dirty and zeroes it — cannot create money, cannot double-seize (pinned by CoreTests Program.cs:437-438); Launder (Wallet.cs:54-61) moves min(Dirty, LaunderPerDay) 1:1 from Dirty to Clean and logs it in TotalWashed — conservation holds across Earn/Spend/Wash/Seize.
- economy: EarnClean/EarnDirty (Wallet.cs:21-22) reject non-positive amounts, so the negative-income defect cannot drain the wallet itself — only the side books diverge.
- economy: Empire.Dissolve (Empire.cs:252-289): AskPrice/2 integer division is exact for every shipped AskPrice (900, 550, 500 in EmpireSetup/BalanceLab; 400 in tests — all even), proceeds land as EarnClean once, and the buy-debt-cheap/squeeze/sell-at-half loop is not exploitable because SellUp is one-shot (ActThreeHost.cs:427 gates on !ActThree.SoldUp and sets it).
- economy: Purse drains can never go negative: Take clamps to min(Cash, wanted) (Purses.cs:143-144), Borrow leaves the patron at least Weekly/7 and moves money 1:1 debtor<-patron with a recorded Favour (Purses.cs:213-224), DailyTick refill caps at Ceiling with min gain 1 (Purses.cs:131-134), Credit rejects amount<=0 (Purses.cs:181).
- economy: Debt collection conserves money across systems (Debts.cs:47-76): exactly payment.Paid leaves the debtor's purse and exactly the same figure enters the wallet via EarnClean, with Amount reduced by paid on part-payment — nobody owes the void, nothing is minted.
- economy: The empire's drains all clamp to what the wallet holds: patron tribute and dockside protection tax use Spend(min(tax, wallet.Total), dirtyOk:true) (Empire.cs:739, 749) and the machine's legal fee uses min(150, wallet.Clean) with dirtyOk:false (Empire.cs:634-637) — a broke player is never driven negative, and lawyers genuinely refuse dirty cash.
- economy: The DailyTick street clamp [0.1, 1.5] (Empire.cs:523) fully contains everything FactorFor can produce — TakingsFactor is clamped to [0.35, 1.35] (Economy.cs:134-136) and the starved minimum 0.35*0.45=0.1575 stays above the 0.1 floor — so no double-clamp distortion exists (the separate 'clamp never binds and is untested' observation is already logged in game-design/audit-findings-2026-07-27.md:147).
- economy: The income-modifier chain's four decision levers are each genuinely pinned by a perturbation test: NewCrewTaxing, TributeShare, SharedRacketId, and both cut policies all move the take in CoreTests Program.cs:1826-1840, and TakeAtStreet(0.4)/TakeAtStreet(1.3) pin the street coupling itself at Program.cs:1876-1880.
- economy: Bribes and hush money are conserved into the world rather than destroyed: Gossip pay-to-quiet credits the recipient's purse with the exact price (Gossip.cs:405), Purses.Credit marks it Windfall so CarryingUnexplained can surface it as evidence (Purses.cs:179-196, pinned by tests Program.cs:3521-3534).
- acts: Ending.None is impossible once AuditClosed: Eligible() (ledger/Assets/Scripts/Core/ActThree.cs:319-321) adds BurnBoth whenever none of Both/StraightLife/Quiet/Kingdom made the list, Resolve (line 327-331) returns BurnBoth for an empty list (null LedgerState), and CloseAudit (ActThreeHost.cs:215-237) only ever assigns Result from Resolve — perturbing any input moves between the five real endings, never to None.
- acts: The judge-to-handover race is handled: HandOver (ActThreeHost.cs:496-498) re-runs ReadySuccessor() at the moment of signing and requires ready.Id == crewId; ReadySuccessor skips Departed crew (line 83-84), so a candidate who departed (poached at Empire.cs:779, quit at 556) between PP4's announcement and the conversation correctly blocks the verb, and DialogueUI (line 443-444) hides the button the same way.
- acts: The audit clock itself survives save/load: AuditClosesDay is an absolute calendar day set once at open (ActThreeHost.cs:121), captured/restored as "closesDay" (ActThree.cs:549, 566) alongside Now in the main save, so a plain mid-audit save/load neither shifts nor resets the deadline, and DaysLeftOnAudit recomputes correctly from restored state.
- acts: The live (non-loaded) Table conversation path has no name drift: DialogueUI matches ArmOf(TableArmId).HeadName against the head's Card.Name (DialogueUI.cs:307-308, 563-564); head cards are titled with full names ("# Sera Kest", CastTier1.cs:38) parsed into Card.Name (CharacterCard.cs:64-66), which equals HeadName "Sera Kest" (Empire.cs:102-104) — the label logic and act logic use identical conditions so button and action cannot diverge.
- acts: ActTwo.ShouldOpen is fed live, failable inputs: GameController.cs:625-626 passes freshly-counted owned businesses, established rackets, and non-departed crew each check; the 2-of-3 conjunction (ActTwo.cs:40-41) is reachable by an ordinary open-city campaign (one business + one racket) and genuinely fails when the empire isn't real (sell the business or lose the racket and the count drops below 2 before Opened latches).
- acts: Act I's pressure points are each satisfiable, non-overlapping, latched, and persisted: PP1 (day 1, 09:30, GameController.cs:931), PP2 (first 22:00 job post, line 1459), PP4 (lena_ledger KnownToPlayer via any channel, line 941-951), PP7 posture (WonWeek end panel, DialogueUI.cs:1112-1151) — distinct triggers, each guarded by its own once-flag, all four flags in ExtraFlags (lines 1699-1700) and restored (1748-1752).
- acts: The Both-ending rebalance matches its documentation: Eligible requires both SeenStrain < BooksHoldThreshold and raw LedgerStrain < BooksHoldThreshold (ActThree.cs:267-268, 287-290), so the multiplicative mitigations (deflection x0.7, moved ledgers x0.55, cooperation scope) can save Kingdom but cannot buy Both — exactly the fix balance-findings-endings.md describes, and ScopeFactor's clamp [0.55, 1.6] and asymmetric 0.045/0.15 constants match the decision-10 comment.
- acts: The stage-4 summit that gates the whole third act is reachable: arm stage escalates to 4 at attention >= 0.9 (Empire.cs:629, 691), attention rises from observed operations, and PP7 fires on `Stage >= 4` (GameController.cs:687) matching act2-draft.md's "fires: any arm reaches stage 4 / attention 0.9" — SimDirector's due-list uses the identical condition (SimDirector.cs:515).
- acts: FireCollision cannot misfire outside its act: it is guarded on ActTwo.Opened and a live (non-departed) crew member (GameController.cs:704-706), so week-one beats and crew-less campaigns never trigger the collision, and the once-flag latches it on first attendance.
- acts: CloseAudit resolves off a single fresh snapshot and pure functions only: Books() is built once (ActThreeHost.cs:217), Resolve/Eligible/LedgerStrain are deterministic pure functions of that state with no randomness and no LLM input, the result is latched into ActThree.Result before any text renders, and the StraightLife/Kingdom text variants (lines 224-229) read the same latched snapshot rather than re-querying a moving world.
- ui: Router typed-verb staleness handling is correct (audit question 2 done right): TryRouteAsync refreshes the action rows before building the catalogue AND again after the await, re-checks Live(ButtonFor(verbId)) before firing, and bails if `_current != host` after the model thought (DialogueUI.cs:1294-1325) — an expired verb becomes speech, never a fire.
- ui: ActThreeButtons/ActThreeAct wiring is branch-for-branch consistent: same five branches (Reisz, Halvard sell-up, Ossei deflect, successor, last day) in the same order with identical guards, and every verb id in ButtonFor/ExecuteVerb (8 ids, IntentBridge.cs:148-182) maps to a button whose click listener was wired in BuildDialoguePanel to the same handler.
- ui: Act III verbs are self-guarding in Core, so a stale disabled button cannot corrupt state: AnswerInspector re-checks `_inspectorAskedDay == Now.Day` (ActThreeHost.cs:322-323), Deflect re-checks OsseiInterviews.Count and worst-arm attention (442-452), HandOver re-checks ReadySuccessor().Id (494-498), SpendLastDay re-checks LastDayOffer (374).
- ui: RefreshLedger's arm dereferences are null-safe: Empire.Arms is field-initialized with dockside/machine/newcrew (Empire.cs:100-105) and Restore updates arms in place by id without ever removing one (Empire.cs:893-908), so `e.ArmOf("machine").Stage` at DialogueUI.cs:876-881 cannot NRE, including after loading an old save.
- ui: ActThreeLedgerLine (ActThreeHost.cs:512) has zero callers anywhere in the repo — the ledger panel renders its own audit section and guards the Reisz scope line on ActThree.InspectorArrived (DialogueUI.cs:901), and Books() guards hosts/mill with null checks and forces SuccessorName non-null via `?? ActThree.SuccessorId` — so a no-inspector world cannot crash the ledger panel.
- ui: DismissEndScreen's unconditional unlock cannot fire during a scene that must stay locked: during the posture scene _endPanel is null so it returns false at line 1095 without touching InputLocked; in sim (its only caller, SimDirector.cs:263) the pause menu is unreachable (SimMode guard, DialogueUI.cs:74) and the key panel never auto-opens (line 185); in real play it has no callers.
- ui: The damage-control row survives the Fall wipe without crashing: Bribe, Intimidate, and UseHook all return DcOutcome.NoSuchRumor rather than throwing when the gossiper or rumor is gone (Gossip.cs:397, 425, 480), BribePriceFor falls back to snapshot pricing when the live price is 0 (DialogueUI.cs:1404-1408), and PayOff only moves money on Contained (line 1434-1439).
- ui: The ui smoke CI gate fails closed on exception: if SmokeTestPanels threw mid-walk, _uiPanels would remain null while _uiSmokeRun is true, and `uiOk = _uiSmokeRun && panelsBad == 0 && panelsOk >= 5` (SimDirector.cs:977) fails on panelsOk=0 — a crashing panel build fails the build rather than passing silently.
- ui: ShowOdds is applied live on the Plan panel — RefreshPlan reads GameSettings.Current.ShowOdds at every refresh (PlanUI.cs:168) and shows an honest 'Odds are off in options' line when off; the text-size option's build-time-only application is explicitly disclosed on the options screen (OptionsScreen.cs:111), so neither is a silent staleness.
- ui: End-screen and pause lock persistence is correct: Update returns before the per-frame lock recompute while the end panel or posture panel is up (DialogueUI.cs:951/953) so ShowEnd's InputLocked=true holds, the paused path re-asserts the lock every frame (line 981), and Escape on the open ledger closes it through the else-chain (line 974) without also toggling pause.
- workflow: Verdict step '$done -split " "' (workflow line 183): safe for both shapes Where-Object can return — on a single String it splits that string; on Object[] the -split operator splits each element and flattens — so the String-vs-Object[] concern is NOT a bug; and only one 'SimDirector: done.' line exists per run (SimDirector.cs:1261 is inside a _finished-guarded Finish()).
- workflow: GITHUB_STEP_SUMMARY block (workflow lines 201-206): quoting is correct — the '```' fences are single-quoted literals so pwsh does not interpret the backticks, $lines pipes line-per-line into the fenced block, and the fallback at line 173 fires correctly because both a missing player.log and a no-match Select-String leave $lines empty/$null, making '-not $lines' true.
- workflow: Artifact paths match where the sim actually writes: Start-Process uses -WorkingDirectory sim-run, SimDirector writes relative paths 'sim-out/sim-report.json' (line 1234), 'sim-out/shot_*.png' (line 554) after Directory.CreateDirectory("sim-out") (line 97), and '-logFile player.log' is relative to the same CWD — so 'sim-run/sim-out/**' and 'sim-run/player.log' in the upload step both resolve to real outputs.
- workflow: The CI pass/fail is latched to a real signal: SimDirector.cs:1309 calls Application.Quit(pass ? 0 : 1) with pass computed from all 35 named gates, and the workflow fails on nonzero $p.ExitCode (line 132) — the 'FAILING GATES' text is informational only, so gate failures cannot be lost to log truncation; Finish() is guarded (_finished, lines 666-670) so the report/quit happens exactly once despite Application.Quit being asynchronous.
- workflow: The Verdict key regex (line 184): 10 of the 11 alternatives correspond to real space-delimited tokens in the done line — coverageOk=, openModeForced=, endScreen=, daysSkipped=, actThree=, actTwoOk=, opened=, ending=, verdict=, pass= all verified against SimDirector.cs:1261-1305; only dayJob= is dead (reported as a finding).
- workflow: The in-script wait itself is the right primitive and fail-loud: Wait-Process honours -Timeout (seconds) on a Start-Process object where WaitForExit(ms) did not (the run-30217466971 bug), and the timeout branch tails 80 log lines, Stop-Process-es the player, and exits 1; additionally, even if $p.ExitCode were unavailable ($null) at line 132, '$null -ne 0' is $true in pwsh, so the failure mode is a loud red build, never a silent pass.
- workflow: lint-usings' qualified-call scrub works: QUALIFIED.sub replaces 'System.Linq.Enumerable.' with 'QUALIFIED_', removing the dot before the method name, so 'System.Linq.Enumerable.Count(list, ...)' cannot re-match the extension-form regex (which requires a literal '.'); and the exemption for files importing System.Linq uses a correctly anchored MULTILINE '^\s*using\s+System\.Linq\s*;'.
- workflow: The LINQ regex's alternation ordering does not mis-truncate names that ARE listed: for '.FirstOrDefault(' the 'First' alternative fails its required [(<] (next char 'O') and backtracking matches 'FirstOrDefault' — same for OrderBy/OrderByDescending, ThenBy/ThenByDescending, Single/SingleOrDefault — so no false positives or wrong-name reports from prefix overlap.
- workflow: The forward-slash-only '/obj/' and '/bin/' filters in lint-usings.py (line 77) and ShapeCheck (line 36) would not match Windows '\'-separated paths on the runner, but no obj/ or bin/ directory exists anywhere under ledger/Assets/Scripts (verified by find), so nothing wrong is currently scanned — no impact today.
- workflow: The Verdict step's placement contract holds: it is the last step, if: always(), reads only sim-run/player.log (workspace-relative, correct for a default-working-dir step), and contains no exit-code manipulation — it cannot turn a red job green, and it degrades to 'no verdict — the run did not reach the simulation step' when the sim never ran.
- gossip: Cycle amplification is impossible in the confidence VALUE: SocialGraph.Put clamps ties to 0..1 (Gossip.cs:24), so Tick's passed = conf*tie*HopDecay (line 211) and CompareNotes' tie = Max(tie,0.5) <= 1 (line 274) are strictly below the source confidence at HopDecay 0.8; an A-tells-B-tells-A bounce of the SAME value is additionally blocked by the Best>=passed check (lines 216-218) and covered by CoreTests/Program.cs:303-311 (heat and suspicion provably don't re-trigger).
- gossip: Witness clamps incoming confidence to 0..1 (Gossip.cs:157) and only >=0.95 becomes hard knowledge; every in-engine Rumor construction stays in range (Backfire 0.9, Empire.Squeeze 0.85, Debts 0.7, Phones 0.55, PopulationHost street_talk 0.3) — SaveCodec restore is the sole unclamped write path.
- gossip: Leashed is honored at every SPREADING reader I traced: Tick speaker guard (Gossip.cs:210), CompareNotes checker and partner (269, 280), Leads (354), Bribe/Intimidate/UseHook early returns (394, 422, 484), GossipDirector.RunChecking skips leashed checkers (GossipDirector.cs:207), Ossei interviews skip leashed witnesses (GameController.cs:600), Empire's witness pools exclude leashed (Empire.cs:602, 681), the leashed bark reveals no rumor content (GameController.cs:1085), and eavesdropping/Noor's OnEvents pickup only ever see events Tick/CompareNotes already filtered.
- gossip: Suppressed is honored at Tick (Gossip.cs:209), CompareNotes (279), Leads (356), Ossei interviews (GameController.cs:605), and weak-hook target selection (Gossip.cs:495); Contain additionally floors the topic's confidence at 0.05 (line 543), below the 0.2 share/lead/KnowsSecret threshold, so bought silence holds against every confidence-gated reader.
- gossip: Decay units are consistent with the accelerated clock: Age computes elapsed GAME hours from GameTime.TotalMinutes (Gossip.cs:521-524), is driven once per game-hour off the world clock (GameController.cs:498-502), RumorHalfLifeHours values (96 default, 144 under Ossei) are game-hours, and the GossipDirector cadence is 6 GAME minutes with a MaxCatchUpRounds=8 cap computed via game-time MinutesBetween (GossipDirector.cs:29-33, 141-160) — no Time.deltaTime/frame-rate dependence remains in the mill's timing.
- gossip: Age is monotone and self-consistent: multiplier Pow(0.5, hrs/halfLife) < 1 for hrs > 0, negative elapsed time is ignored via the hrs > 0 guard, spent rumors prune at <0.03, and the first call only sets the baseline (Gossip.cs:517-534).
- gossip: Forget refuses to drop any agent carrying state (rumors, memory events, suppressions, or a leash — Gossip.cs:137-144), and PopulationHost respects the refusal by re-pinning the resident to the Mid band as load-bearing (PopulationHost.cs:150-154, LoadBearingIds at 75-87), so the crowd LOD cannot erase gossip state.
- gossip: DayCircleHeat's noisy-or stays within 0..1 for in-range confidences and takes best-per-topic so retellings of the SAME story never stack — verified at CoreTests/Program.cs:325-341 (0.5+0.5 corroborate to exactly 0.75; a weaker duplicate changes nothing).
- gossip: SuspicionTracker clamps on Raise, Lower, and Restore (Suspicion.cs:66-82), and every Loyalty mutation I found in Gossip.cs/Empire.cs/Debts.cs/GameController.cs goes through Math.Clamp(...,0,1).
- gossip: Fact normalizes Subject/Predicate/Value to lower-invariant in its constructor (Suspicion.cs:16-21), so the case-sensitive comparisons in Leads (subject.ToLowerInvariant vs r.Content.Subject), the Leashed 'player' guard, TopicKey matching, and Witness's Holds dedup cannot miss on casing.