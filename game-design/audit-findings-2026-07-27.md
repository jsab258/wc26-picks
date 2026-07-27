# Audit findings — 2026-07-27 (Fable session, IN PROGRESS)

**Status: PARTIAL and UNVERIFIED.** The audit workflow hit the session usage
limit mid-run. Five of fifteen dimensions completed; the adversarial verify
wave and the completeness critic never ran. Resume is scheduled for 15:31 UTC
(limit resets 15:30) with run id `wf_a5b50969-f05` — completed dimensions
replay from cache, the eleven missing ones run live.

**Dimensions COMPLETED (findings below):** gates, clockjump,
coretests-endgame, coretests-economy, coretests-social.

**Dimensions NOT YET RUN:** legibility, reachability, codec, determinism,
fall, purity, economy, acts, ui, workflow, gossip — plus ALL verification and
the critic.

**Nothing here is fixed yet** — per the session plan, no fixes while the audit
is incomplete, and none of these findings has survived an adversarial
verifier. Treat every entry as a claim with a traced failure path, not a
confirmed bug.

---

## Findings (unverified), most severe first

### [HIGH] `ledger/Assets/Scripts/Game/DirectorHost.cs:215` (clockjump)

**Claim:** A Director demand's DueDay is computed from its scheduled FireDay (`DueDay = p.FireDay + 2`), not the day it actually fired, so a demand whose FireDay falls inside the Fall's 3-day skipped window fires and expires in the same frame — the player is penalized -0.2 loyalty for ignoring a demand that never had an open window.

**Failing input:** Fall at the day-D close with Pressure{Kind=Demand, FireDay=D+1} pending: no closes run on D+1..D+3 (RunTheFall sets _lastClosedDay=D+3), so the first close is D+4. There FireDuePressures (GameController.cs:1408) fires it via DirectorBook.Due's `p.FireDay <= now.Day` (Director.cs:358), Fire() adds OpenDemand{DueDay=D+3}, and CheckDemands (GameController.cs:1409 -> DirectorHost.cs:277 `if (Now.Day <= d.DueDay) continue;`) removes it the same frame: the announce toast and the "stopped asking" grievance (-0.2 loyalty, DirectorHost.cs:281) land in one morning. Likewise any OpenDemand already outstanding at Fall time (DueDay D+1/D+2) expires at D+4 with the entire window consumed by prison. Violates the file's own "always a window, never a countdown" comment (DirectorHost.cs:216). Non-demand pressures merely fire 1-3 days late; only demands corrupt state.

### [HIGH] `ledger/CoreTests/Program.cs:2151` (coretests-economy)

**Claim:** The check "the takings factor never falls through its floor" cannot fail under any input perturbation or under deletion of the clamp it names — it asserts a tautology on a value that never approaches the floor.

**Failing input:** TakingsFactor is defined as Clamp(raw, MinTakingsFactor, MaxTakingsFactor) (Economy.cs:134-136), so `worst.TakingsFactor >= worst.MinTakingsFactor` is true by construction. Even with the clamp deleted it still passes: the worst fixture (racket 400, heat 1.0, 60 days) hits DailyTick's internal floors — prosperityTarget clamped to 0.05 (Economy.cs:175), priceTarget capped at 1+0.35+0.15 = 1.5 — so raw factor bottoms at (0.5+0.05)*(1-0.5*0.5) = 0.4125 > 0.35 for ALL possible racket/heat/wages inputs (in the actual fixture, suppliers are paid so it is 0.454). Perturb any input: the check's answer never changes. Its neighbor at 2153 (Prosperity > 0.0) is the only live check in the no-death-spiral block.

### [HIGH] `ledger/Assets/Scripts/Game/SimDirector.cs:1034` (gates)

**Claim:** The forced-open lost-week path (the exact path this morning's coverage floor exists to keep testing) structurally fails the openModeOk and verdictSane gates whenever the week is lost at or before the day-6 close, so a legitimate lost week reds the build under two misleading gate names.

**Failing input:** Exposure fuse trips at the day-6 morning close (day-circle heat >= 0.70 on the day-5 and day-6 closes): Campaign.CloseDay sets LostExposed with DaysClosed=5; UpdateCampaign (GameController.cs:1331) then returns early every frame, so days 7-8 never close and `_lastClosedDay` jumps 6->8 when SimDirector forces open mode at day 8 (SimDirector.cs:252-267, which resets Verdict to Ongoing). Only the day-8 and day-9 closes remain before the staged day-9 fall jumps to day 12 and Finish runs, so DaysClosed=7 < 8 -> openModeOk (line 1034) is false; and jobs posted = nights 1-5 plus night 8 = 6 < SimMode.Days-2 = 7 -> verdictSane (lines 1011-1013) is false. Nothing is actually broken; the gates' baselines (DaysClosed >= 8, jobs >= 7) assume a won week whose closes and job posts never froze.

### [HIGH] `ledger/Assets/Scripts/Game/SimDirector.cs:219` (gates)

**Claim:** The _endDay reclaim can never actually reclaim a day in any reachable run: every reachable Fall fires on day >= 9 and lands on fallDay+3, the reclaim adds exactly landing-fallDay-1 = 2 days making _endDay equal the landing day, and `now.Day >= _endDay` (line 489) fires Finish on the landing frame — so the two 'reclaimed' days are never simulated, the post-Fall world gets zero sim time, and MaxReclaimedDays is dead code.

**Failing input:** Standard won-week CI run: _endDay = 1+9 = 10; staged fall at day 9 hour 10 (line 446) -> RunTheFall sets Now = (12, 8:00) (GameController.cs:1022); next SimDirector.Update computes skipped = 12-9-1 = 2, _endDay = 12, then line 489: 12 >= 12 -> Finish() same frame. Perturbation proof: delete the whole reclaim block and behavior is identical (12 >= 10 also finishes at landing). The last lived moment is day 9 10:00 (~8.4 of the promised 9 days), and .github/workflows/ledger-build-windows.yml line 20 raised the sim timeout 20->25 min because 'the run now reclaims the days the Fall skips... about four extra minutes' — time that is never used. Open-mode falls before day 9 are unreachable (open mode starts day 8 and EnterOpenMode/ForceOpenMode reset ExposedStreak, so the earliest organic fuse is the day-9 close), so the reclaim never extends any run.

### [MEDIUM] `ledger/Assets/Scripts/Game/GameController.cs:1316` (clockjump)

**Claim:** TickWorldDay's guard `if (Now.Hour < 8 || Now.Day <= _lastWorldDay) return;` runs the world-day systems ONCE after the +3 jump, but two of its three consumers apply per-CALL increments, not per-elapsed-day arithmetic: every purse in the city gains one day's flow for three calendar days (Purses.cs:126-135, `p.Cash + gain` once per call), and every feud cools one 0.03 step instead of three (Harm.cs:229 `f.Heat - 0.03`); NightBorrowing likewise gets one night instead of three (Debts.cs:136).

**Failing input:** Fall on day D: TickWorldDay ran for D at 8:00, the jump lands D+3 8:00, next frame ticks once with day D+3 — a purse with Weekly=70 that was emptied on D holds ~10 (one day's gain) on the landing morning instead of ~30, so a Collect() against a willing debtor returns a third of what the calendar owes; a feud at Heat 0.52 sits at 0.49 instead of 0.43, keeping WillWorkTogether (Harm.cs:295, threshold 0.5) false when three simulated days would have made it true. Harm's own injury logic in the same tick proves the inconsistency: it uses absolute-day arithmetic (`day - i.DayTaken`, Harm.cs:214) and handles the jump correctly.

### [MEDIUM] `ledger/Assets/Scripts/Game/ActThreeHost.cs:207` (clockjump)

**Claim:** A Fall inside the audit window silently eats up to 3 of the 6 grace days (AuditClosesDay is an absolute date, ActThreeHost.cs:121), and when the jump lands on/past AuditClosesDay, PP3 (Ossei's "two days left" offer, line 179 `DaysLeftOnAudit <= 3`), PP5 ("The last day. You can reach a few people", line 199 `<= 1`) and CloseAudit (line 207) all execute in one CheckActThree pass — the last-day calls are announced and are already dead, because IsLastDay requires !AuditClosed (ActThree.cs:131), so LastDayOffer (ActThreeHost.cs:355) returns null immediately after.

**Failing input:** Audit opens day O (closes O+6); Fall at the O+3 close lands O+6 8:00. At the next 30-frame CheckActTree with Hour>=9: PP3 toast, PP5 toast, then CloseAudit fire back-to-back in the same invocation — the player is told they can move the ledgers/dismiss crew/confess the same instant the books close, days O+3..O+5 of inspector asks (LastDealtDay cadence, line 168) never happened, and the ending resolves off a state the player had zero of the advertised last-day agency over.

### [MEDIUM] `ledger/CoreTests/Program.cs:2111` (coretests-economy)

**Claim:** TestEconomy never asserts the heat input: deleting the heat coupling (and likewise SupplyRaisesPrices, DislikeRaisesPrice, SqueezeCostsSupplierStanding) leaves every one of its checks green.

**Failing input:** Set HeatCostsProsperity = 0 (Economy.cs:174): quiet (heat 0.1) moves 1.028 -> 1.047, still inside its (0.95, 1.15) band; squeezed/generous compare runs sharing heat 0.1 so relative inequalities hold; slow's one-day delta goes -0.054 -> -0.048, still < 0.06; worst's prosperity converges to 0.10 instead of 0.05, still > 0. No two fixtures differ only in heat. Same for HeatCostsSupplierStanding (Economy.cs:226 — 'lost' refuses via the unpaid -0.25/day alone, 'kept' survives on +0.28/week either way), SupplyRaisesPrices (Economy.cs:179 — every PriceLevel assertion uses fully-paid fixtures with strain 0), and DislikeRaisesPrice (Economy.cs:150 — no DeliveryPrice check ever runs with negative standing).

### [MEDIUM] `ledger/Assets/Scripts/Core/Empire.cs:583` (coretests-economy)

**Claim:** EmpireBook.TotalRacketIncome — the counter Act III's LedgerStrain reads as the dirty income the books must explain (ActThreeHost.cs:40) — has zero CoreTests coverage: neither its accumulation nor its codec round-trip is asserted.

**Failing input:** Mutate line 583 `TotalRacketIncome += income;` to double-count, or move it above the NewCrewTaxing/TributeShare/SharedRacket deductions (lines 578-581) so it counts gross instead of what actually entered the wallet: all 1395 checks stay green (every occurrence of 'TotalRacketIncome' in Program.cs — 2633, 2651-2663, 2874-2875, 2927-2990, 3048, 3126 — is the hand-set LedgerState struct, never an EmpireBook after a tick), and Act III's ending selection silently shifts because SeenStrain inflates.

### [MEDIUM] `ledger/CoreTests/Program.cs:2696` (coretests-endgame)

**Claim:** The did_nothing check is effectively unfailable: its fixture has TotalRacketIncome=0 (the exact no-racket-income shape from the 24-test incident), so LedgerStrain=0 and Resolve deterministically returns Kingdom, making the '|| BurnBoth' arm dead code and the comment's claim 'Doing NOTHING must produce Burn Both' unpinned.

**Failing input:** Fixture {BusinessesOwned=1, RacketsEstablished=1, loyalty=0.1, heat=0.9, income=0, washed=0}: with empire alive, OsseiCaseAnswerable=false, HandedOver=false, Eligible() (ActThree.cs:247-321) is structurally confined to {Kingdom, BurnBoth} — Both is blocked twice (heat>=0.5 and ossei false), StraightLife by empireSurvives, Quiet by HandedOver — so the disjunction 'Resolve==Kingdom || Resolve==BurnBoth' passes under ANY perturbation of any LedgerState number and any strain/threshold/scope constant, and under any single-conjunct regression to Eligible(). An established racket that produced zero income is also a world the game cannot produce (Empire.DailyTick pays established rackets daily), so the audit gate the comment describes never bites.

### [MEDIUM] `ledger/CoreTests/Program.cs:948` (coretests-social)

**Claim:** TestActTwo's codec roundtrip asserts only the 2 non-default fields of a 14-field Capture/Restore, so a restore regression in any of the other 12 ActTwoState fields ships green.

**Failing input:** Fixture `a` (lines 912-917) differs from a fresh ActTwoState only in InjunctionUntilDay=12 and InjunctionAnswered=true — exactly the two fields line 948 checks. Break Restore's parsing of any other key in Assets/Scripts/Core/ActTwo.cs:112-126 (e.g. make Pp4Fired read Flag(d,"pp5") instead of "pp4", or drop truceSpent/tableAnswer/lastEvening entirely): the restored default (false/-1/null) equals the fixture value, so the check still passes. Contrast TestPhones' full serialize-equality roundtrip at line 2618.

### [MEDIUM] `ledger/CoreTests/Program.cs:4013` (coretests-social)

**Claim:** "the yard opens to somebody the street talks about" passes via the shipped yard's After-21 key, not the Notorious key it names — the notoriety input is irrelevant to the outcome.

**Failing input:** famous = {Notoriety=0.9, Hour=22} against repair_yard, whose keys are Notorious(45), Crew(2), After(21) (AccessSetup.cs:85-93). Hour 22 >= 21 holds the After key, so perturbing Notoriety 0.9 -> 0.0 — or deleting the Notorious key from the shipped gate — leaves Doors.Try(...).Allowed true and the check green. The companion design claim in the comment ("No build holds both") is asserted nowhere, and is in fact false at this very fixture hour: `unknown` (Notoriety 0.05, Hour 22, line 4008) opens both the loft (Quiet) and the yard (After). A famous state at Hour < 21 would have isolated the Notorious key.

### [MEDIUM] `ledger/CoreTests/Program.cs:1026` (coretests-social)

**Claim:** "a leashed checker does not go asking" cannot fail: the fixture's partner is also leashed, so CompareNotes returns 0 events whether or not the checker-leash guard exists.

**Failing input:** rocco3 was leashed by UseHook at line 1023; with lena3.Leashed=true, delete the `checker.Leashed` early-return in GossipMill.CompareNotes (Core/Gossip.cs:269) and the call still yields Count==0 via the partner-leash break at Gossip.cs:280 — the check stays green. The only observable difference the guard makes — lena3 NOT gaining the "I asked Rocco straight out" memory written at Gossip.cs:271-272 before the loop — is never asserted. The §6.3 leashed-checkers-don't-check rule is therefore unverified.

### [MEDIUM] `ledger/CoreTests/Program.cs:4127` (coretests-social)

**Claim:** "a plan with too many people in it says so" asserts only Worry.Length > 0, which every WorryAbout return path satisfies — the assertion is unfalsifiable for any worry-selection logic.

**Failing input:** Operations.WorryAbout (Core/Operation.cs:233-253) returns a non-empty literal on every branch, including the fallback "Nothing about it is obviously wrong." at line 252. Delete the `plan.Crew.Count > 2` branch (Operation.cs:245-246): the 4-person fixture falls to the fallback, Length is still > 0, and the check passes. Worry can only be empty via Read's null/Done early-outs, which this fixture never takes. The two sibling checks (lines 4122, 4125) correctly use Contains("heard of you")/Contains("daylight"); this one pins nothing.

### [MEDIUM] `ledger/Assets/Scripts/Game/SimDirector.cs:691` (gates)

**Claim:** The discredit gate is permanently vacuous in every 9-day CI run: Finish always executes on the frame the staged Fall lands, RunTheFall has just deleted every rumor whose Subject is "player" (GameController.cs:1029), and every `Sensitive = true` rumor in the codebase is a Fact("player", ...) — so the strongest-sensitive-story scan finds topic == null and discreditWorks defaults to true without ever calling Discredit.

**Failing input:** Any -simdays 9 run: staged fall (day 9) -> land day 12 -> Finish same frame; the scan at lines 693-699 iterates day-circle rumors for r.Sensitive and finds none (verified: all Sensitive=true creation sites — GossipDirector.cs:127/274, GameController.cs:660/718, Empire.cs:349/608/686, OperationHost.cs:93, TrafficHost.cs:144, ActThreeHost.cs:418, Gossip.cs:552 — use subject "player", which the wipe removes). Perturb GossipMill.Discredit to a no-op and the gate stays green in every CI run, even though secretReachedDay (latched) is true and the branch is entered.

### [LOW] `ledger/Assets/Scripts/Game/GameController.cs:1024` (clockjump)

**Claim:** The Fall's `_jobPostedDay = Now.Day; // no ghost job from the lost nights` guards an impossible scenario and instead suppresses the landing night's legitimate drop: posting requires `inWindow && Now.Hour >= 22` at the moment of the check (GameController.cs:1453), so no "ghost" from a skipped night could ever post — the only effect of the reset is that the 22:00 drop on the landing day (a day the player has been free since 8:00) never appears.

**Failing input:** Fall lands day D+3 8:00 with _jobPostedDay=D+3; at D+3 22:00 the condition `_jobPostedDay != Now.Day` is false and no drop posts — the player silently loses one $90 job and its +0.10 patience gain; without the reset the same evening would have posted normally (the pre-Fall _jobPostedDay <= D-1 differs from D+3), and no earlier post was reachable because Hour>=22 fails from 8:00 to 21:59.

### [LOW] `ledger/Assets/Scripts/Game/GameController.cs:648` (clockjump)

**Claim:** PP2's injunction window (`ActTwo.InjunctionUntilDay = Now.Day + 2`, enforced only at closes via `if (ActTwo.BarFrozen(Now)) takings = 0` at line 1341 with BarFrozen = `now.Day <= InjunctionUntilDay && !InjunctionAnswered`, ActTwo.cs:24) expires in calendar time while a Fall skips its enforcement points, so the nominal three frozen closes shrink to one and the pressure mostly vanishes.

**Failing input:** PP2 fires the evening of day X (InjunctionUntilDay = X+2); the Fall fires at the X+1 close — that close is frozen (CloseDay runs at line 1339, freeze applies at 1341, FallPending consumed the same frame), the jump lands X+4 with _lastClosedDay=X+4, and the X+2 close never happens: BarFrozen(X+5) is false at the next real close. The letter that says 'pay the fees, have Halvard make it disappear, or wait it out' is resolved by the calendar jump at the cost of a single morning, with InjunctionAnswered never set.

### [LOW] `ledger/Assets/Scripts/Game/ActThreeHost.cs:247` (clockjump)

**Claim:** The Quiet-ending epilogue indexes mornings off absolute days (`int index = Now.Day - ActThree.EpilogueDay - 1; if (index < 0 || index >= ActThreeState.EpilogueDays) return;`), so a Fall during the 3-day epilogue jumps index past EpilogueDays and the remaining epilogue lines are silently never shown — and the campaign fuse still runs after AuditClosed (UpdateCampaign only checks Verdict, which stays Ongoing in open mode), so this is reachable.

**Failing input:** Quiet ending closes day E (EpilogueDay=E); the morning line for index 0 shows on E+1; two more hot closes set FallPending and the Fall fires at the E+2 close, landing E+5: index = 5-1 = 4 >= 3, TickEpilogue returns forever, and epilogue mornings 2 and 3 (the letter / no-letter payoff of the whole ending) never render.

### [LOW] `ledger/Assets/Scripts/Game/GameController.cs:507` (clockjump)

**Claim:** Nightly reflection is keyed to `Now.Hour >= 23 && Now.Day > _lastReflectedDay` and reflects only the current day's events (ConversationHost.cs:113 `ReflectAsync(now.Day, now)` -> ConversationEngine.cs:156 `Memory.EventsOnDay(day)`), so the Fall day's 23:00 never occurs and every memory stamped on the Fall morning is never distilled into beliefs.

**Failing input:** Fall on day D at 8:00 (jump to D+3): Lena's close-time observation "Counted the till again..." (GameController.cs:1422, stamped Now=(D,8:xx) before the jump) and any NightBorrowing memories from that morning's TickWorldDay belong to day D; the next reflection runs at (D+3, 23:00) for day D+3 only, so day D's events are permanently skipped — the belief pipeline silently loses the arrest morning while the Fall's own memories (stamped D+3 at GameController.cs:1033, after the jump at 1022) are reflected normally.

### [LOW] `ledger/CoreTests/Program.cs:937` (coretests-economy)

**Claim:** "act2: signing Vane's cap throttles the fronts" asserts only the boolean FrontsCapped that ResolveTable set one line earlier — the throttle arithmetic exists solely in the Unity layer (GameController.cs:1346, x0.7, and MachineInspecting x0.75) which no test can reach, so the machine is the only Table doctrine whose monetary bite is unasserted.

**Failing input:** Delete `* (Empire.FrontsCapped ? 0.7 : 1.0)` from GameController.cs:1346: CoreTests stay green (dockside's tribute is arithmetic-checked at 933, 60 -> 53; newcrew's tax at 1826 via TakeFor; the machine's cap only via this flag) and a signed cap costs the player nothing.

### [LOW] `ledger/Assets/Scripts/Core/Wallet.cs:41` (coretests-economy)

**Claim:** No money-conservation invariant is asserted anywhere in CoreTests — and none can be, because the design mints and burns money daily; the only both-sides transfer checks are Borrow, Take/Collect, and Credit, and nothing validates wallet state as an invariant.

**Failing input:** Racket income is minted (Empire.cs:582 wallet.EarnDirty with no purse debited), purse refills are minted (Purses.cs:131-133), supplier payments are burned (Economy.cs:193), so no test can sum 'total money in the world' — and none tries. Concretely in-Core: Wallet.Restore(clean, dirty, washed) applies values unchecked, so a corrupted save with Dirty = -500 restores, passes the round-trip equality check at Program.cs:570, and leaves Total negative with no invariant test objecting.

### [LOW] `ledger/Assets/Scripts/Core/Empire.cs:523` (coretests-economy)

**Claim:** The street clamp `Math.Clamp(streetFactor, 0.1, 1.5)` never binds — the only real caller passes Economy.FactorFor(null), whose default-tuning range is [0.35*0.45, 1.35] = [0.1575, 1.35], and the tests only pass 0.4/1.0/1.3 — so the clamp's boundaries are both unreachable and untested.

**Failing input:** Mis-edit the floor from 0.1 to 0.5: the whole suite stays green (Program.cs:1877's TakeAtStreet(0.4) becomes clamp->0.5 -> take 50, still < plain 100), while in play a starved street (FactorFor = 0.35*0.45 = 0.1575) gets silently floored to 0.5 — roughly tripling racket pay exactly where the decision-9 coupling is supposed to hurt. Same pattern at Purses.cs:88: the Math.Max(0.15, ...) floor is unreachable (minimum value is 0.35), so the test `FlowAt(0.0) > 0` at Program.cs:3413 passes with or without it.

### [LOW] `ledger/CoreTests/Program.cs:3030` (coretests-endgame)

**Claim:** The decision-10 stonewall term ('keeps its full 0.15', ActThree.cs:199) is pinned only from below (~0.117): inflating it passes the whole suite because the 1.6 clamp absorbs it.

**Failing input:** Set the stonewall term to 0.30 in ScopeFactor (ActThree.cs:201): ScopeFactor(0,3)=clamp(1.9)=1.6>1.35 passes line 3030, asymmetry 0.135<0.6 passes line 3027, ScopeFactor(0,99)<=1.6 passes line 3032, Marginal(0,2) seen=0.55*... still BurnBoth (line 3056), Reads('Stonewalls') 0.55*1.6=0.88 still flips (line 2886) — every check green while one stonewall now widens scope 1.30x instead of 1.15x in real play.

### [LOW] `ledger/CoreTests/Program.cs:2736` (coretests-endgame)

**Claim:** CouldHold's succession thresholds (competence >= 0.55, loyalty >= 0.6, ActThree.cs:337-338) are pinned only within (0.3, 0.8]; the constants gate HasReadySuccessor and therefore the Quiet ending, but a large drift is invisible to all five checks.

**Failing input:** Change the competence floor 0.55 -> 0.75 (or the loyalty floor 0.6 -> 0.75): CouldHold(0.8,0.8,true,false) still true, !CouldHold(0.3,0.9,...) and !CouldHold(0.9,0.3,...) still true, feuding/independent cases unaffected — all five checks at lines 2736-2741 pass while most successors silently stop qualifying for the Quiet ending.

### [LOW] `ledger/CoreTests/Program.cs:3134` (coretests-endgame)

**Claim:** The LedgersMoved 0.55 multiplier is pinned only from above (must be < ~0.886); the design comment 'the single largest movement any one action makes' (ActThree.cs:219-221) — i.e., stronger than the deflection's 0.7 — is asserted by no test.

**Failing input:** Set the LedgersMoved multiplier (ActThree.cs:222) to 0.75, making it WEAKER than the OsseiCaseAnswerable 0.7 relief: TestLastDay's Books pair gives kept=0.667>0.62, gone=0.667*0.75=0.50<0.62 — both checks at 3132/3134 pass — and Reads('LedgersMoved') still flips (0.7*0.75=0.525<0.62, line 2887); set it to 0.1 and everything passes too.

### [LOW] `ledger/CoreTests/Program.cs:919` (coretests-social)

**Claim:** The Act II arm-voice checks hardcode one armId per text function instead of enumerating EmpireBook.Arms, so a new arm silently receives Danny's newcrew lines from all three functions with no test failing.

**Failing input:** Add a fourth RivalArm to EmpireBook.Arms (Core/Empire.cs:100-105): ActTwoState.FirstNotice/TableOffer/TableResult (Core/ActTwo.cs:48-53, 76-84, 86-99) are if/else chains whose trailing else is the newcrew text, so the new arm gets the grinning-fish/Danny-Ro voice everywhere. Lines 919-921 check only FirstNotice("machine"), TableOffer("dockside"), TableResult("newcrew","defy") and stay green. Contrast TestEveryKeyKindHasItsOwnWords (line 1698), which enumerates via Enum.GetValues and fails on a generic fallback.

### [LOW] `ledger/CoreTests/Program.cs:4153` (coretests-social)

**Claim:** "a botched job is seen by more people than a clean one" asserts >=, so removing the failure-is-louder asymmetry entirely (equal multipliers) still passes; only an inversion is caught.

**Failing input:** The property lives in Operation.cs:310, `seen = vis * (Success ? 0.6 : Partial ? 1.0 : 1.3)`. Set the failure multiplier 1.3 equal to 0.6: seenWin and seenLoss both compute seen=0.48 and Witnesses=1 with the fixed Rolls fixtures, and 1 >= 1 passes. As green today it does distinguish (5 vs 1), but the check cannot detect the documented rule being deleted, only reversed.

### [LOW] `ledger/CoreTests/Program.cs:338` (coretests-social)

**Claim:** "corroborated heat stays within 0..1" is a dead assertion: the previous line already pinned combined to 0.75 +/- 1e-9 in a throw-on-failure harness, so line 338 can never fail when reached.

**Failing input:** Line 337 throws unless |combined - 0.75| < 1e-9; therefore at line 338 `combined <= 1.0` is true by arithmetic for every execution that reaches it, under any change to DayCircleHeat. Any regression that would push heat above 1.0 (e.g. summing instead of noisy-or) is caught at 337, never at 338 — the check adds zero discriminating power.

### [LOW] `ledger/CoreTests/Program.cs:2613` (coretests-social)

**Claim:** "the damping is the same in both directions" compares Damped(1.0) to FidelityOnTheLine, which are the same constant by construction — and no second 'direction' exists in the code to test.

**Failing input:** PhoneBook.Damped is `inPersonAmount * FidelityOnTheLine` (Core/Phones.cs:187), so Damped(1.0) IS FidelityOnTheLine: perturb the constant 0.45 -> 0.9 and the check still passes because both sides move together. Damped takes no direction parameter and has one call path, so the bidirectionality the message claims (player-to-NPC and NPC-to-player damped equally) is a property of call sites in the Unity layer that this suite never exercises. The two preceding checks (2609-2610) already bound the constant to (0,1).

### [LOW] `ledger/CoreTests/CoreTests.csproj:15` (coretests-social)

**Claim:** There is no CoreTests coverage of Act One at all: ActOneState lives in the Unity layer and is not compiled into the test project, and no check in Program.cs references it.

**Failing input:** CoreTests.csproj compiles Core/** plus only AccessSetup.cs, EconomySetup.cs, OperationSetup.cs from Game (lines 15-17); Assets/Scripts/Game/ActOne.cs is excluded, and `grep ActOne|Posture|Noor` over CoreTests/Program.cs returns nothing. Break PostureSummary's winddown/takeover/refused mapping, the DayOneContext day==1&&Sam guard, or the Pp1/Pp2/Pp4/Noor-drawer flags' semantics and every one of the 1395 checks stays green — Act I is verified only by whatever SimDirector exercises in CI.

### [LOW] `ledger/Assets/Scripts/Game/SimDirector.cs:1011` (gates)

**Claim:** verdictSane's `camp.Verdict != Verdict.LostCastOut` clause became unfalsifiable when the day-8 ForceOpenMode was added: any pre-open verdict (including LostCastOut) is rewritten to Ongoing at day 8 (Campaign.cs:85-91), and in open mode exhausted patience sets OutfitCutOff instead of LostCastOut (Campaign.cs:135), so at Finish of any >=8-day sim the clause is tautologically true.

**Failing input:** Bot cast out on night 5 (three missed drops, patience 1.0 - 3*0.34 <= 0): _weekLostVerdict records LostCastOut (report-only, ungated); ForceOpenMode at day 8 sets Verdict=Ongoing; at Finish the named cast-out check passes and the failure only surfaces indirectly through the jobs-count clause (4+1=5 < 7) under the same 'verdictSane' label — the check written to catch a broken job pipeline no longer answers that question.

### [LOW] `ledger/Assets/Scripts/Game/SimDirector.cs:38` (gates)

**Claim:** ActTwoGraceSamples counts game-hours while beat firing runs on a 30-frame cadence, and in sim mode the clock advances min(realDelta, 2s) * 20 game-minutes per frame — so on a runner sustaining below ~10 fps one game-hour spans <= 30 frames, CheckActTwo may not run between two consecutive hourly samples, and a beat that would fire normally can accumulate the 2-sample grace and red the build with no game defect.

**Failing input:** Runner at 5 fps (step 0.2s -> 4 game-min/frame -> one hour = 15 frames, CheckActTwo every 30 frames = 2 hours) during day 9 with pp6 newly due at the 8:00 close (racket income first paid, Ossei interviews on file): ActTwoSample increments at hours 8 and 9 with no CheckActTwo pass between, count reaches ActTwoGraceSamples=2, then the 10:00 staged fall lands on day 12 and Finish reads act2Ok=false (lines 1102-1103) for a beat the game was never given a tick to fire — the exact race the grace was built to close, reopened by the frames-vs-hours unit mismatch (GameController.cs:471-481, 530-540).


---

## Checked and came back clean (also unverified, but stated)

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