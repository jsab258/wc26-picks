# Ruling: the crime, the witness and the overheard consequence. AMEND THE PROPOSAL, THEN BUILD

> **STATUS: LIVE, verified 2026-09-08.** A reference, not a plan: a
> specification the builder works from clause by clause, so the scannability
> cap on a live plan does not apply, and `tools/docs-check.py` is told so
> here rather than by a list it keeps. Director ruling at spawn
> 2026-09-08T02:21:36Z (`.claude/agent-log.tsv` line 349) on items two and
> three of Jafar's order of 2026-09-07 section 6, after the walk landed on
> `de4ad4d`. The reading copy for builder and resident until the crime run
> lands on his PC; then the record of why.

VERDICT: AMEND. The proposal's shape is kept: a CrimeProbe on `-LedgerCrime`
modelled on WalkProbe, real geometry into the transliterated perception, one
crime committed twice as a rule-5b pair, a second NPC out of sight by trace,
transmission by the ported gossip rule, a line at the achieved rung. Six
amendments, each reasoned in the section named:

- A1. The witness decision is `Observe.Resolve`, not bare `InSight`+`IdRung`:
  bare calls yield a rung and no certainty, so the rumour's confidence would
  be a number this record typed. Section 1.
- A2. The occluded case needs a floor: every opaque piece at eye height here
  is a terrace carcass and no ground exists behind any of them. Section 2.
- A3. Two windows, not one window twice. Section 2.
- A4. The transmission pair is planted on `together`, not earshot. Section 3.
- A5. The line and the witness's own telling both come from a bank. Section 3.
- A6. The ladder gets a `done` array; the street step moves into it on the
  evidence named. Section 7.

## 0. What was read, what was not run

No shell, no git, no Windows in this seat. Read whole: the walk probe, the UE
`Perception` port, `MemoryStore.cs`, `Gossip.cs`, `Observation.cs`,
`VignetteShot.h`, `LedgerCharacter.h`, `next-three.json`, queue 138, both
2026-09-07 rulings, the ladder file, the walk verdict on `de4ad4d`. Every
other file is cited by line where used. NOT RUN: anything. Every coordinate
below is hand arithmetic from `vignette-pieces.json` in street metres (x
along, z across, y up; UE cm are x100 with UE Y equal to street z, as the
walk verdict's 400/400/98 for cam_A (4, 4) shows). Rule 2: the instrument
prints every one; none is trusted from this page. A builder may move a
placement within its stated constraint and prints what it did.

## 1. Question 1: the C# slice, by type and by line

THE ONE RULE THAT DECIDES WHETHER ONE CHARACTER PASSES A RUMOUR TO ANOTHER
is `GossipMill.Tick`, `Gossip.cs` 356 to 383; its heart is 371 to 372:
`passed = r.Confidence * tie * HopDecay; if (passed < MinConfidenceToShare)
continue;`. Around it, in order: `together` (356), `tie > 0` (358 to 359),
the share floor (363), suppression (366), the leash (367), the re-tell guard
against the listener's best OF THIS VALUE (381 to 383). Nothing else in 976
lines decides a hop.

IN SCOPE, transliterated line for line under `LedgerCore`, each with a g++
test in the tested layer reproducing the C# worked cases (D1: the engines
must agree, not resemble):

1. `Perception.cs`, the hearing half `Resolve` reads, added to the existing
   `Perception.h/.cpp`: `NoticeSeconds` (65), `AmbientNight3am` (227),
   `AmbientDaytimeStreet` (228), `LoudShout` (243), `LoudBottleSmash` (244),
   `WallAttenuation` (252), `LoudRemark` (274), `AudibleBaseMetres`,
   `AudibleDivisor`, `AudibleCapMetres` (276 to 278), `AudibleRadius` (290
   to 297), `AlertFloorDrop` (357), `EffectiveFloor` (359 to 360), `Heard`
   (362 to 364).
2. `Observation.cs`: `Slot` (23 to 42), `Awareness` (44 to 59), `Observation`
   with `Label` (62 to 111), `Sight` (127 to 141), `Vantage` (147 to 200,
   `RungFloor` kept and fed 0), `Deed` (202 to 215), `Observe.Resolve` (257
   to 327), `Observe.CertaintyFor` (334 to 349). `Feel.Clamp` is
   `LedgerCore::Clamp`, already in `Perception.h`. `Resolve` is where slots,
   rung and certainty are one decision (293 to 325) and `CertaintyFor` the
   only confidence measured against the mill's 0.95 promotion (342 to 348).
3. `GameTime.cs` 9 to 22 and 51: `Day`, `Hour`, `Minute`, `TotalMinutes`,
   `ToString`. No parsing, no slots.
4. `MemoryStore.cs`: `MemoryEvent` 8 to 24; `MemoryStore` 55 to 99 in-memory
   only (`MaxEvents`, `PruneTo`, `Append`, `Prune`), `EventsOnDay` (124 to
   125), `ToMarkdown` (148 to 159): the markdown IS the artefact of
   "permanently remember" and the run commits it. `_filePath` is always
   null: no load, save, append-to-file, `FromLine`, beliefs.
5. `Suspicion.cs`: `Fact` (10 to 43, null refusals included), `ClaimResult`
   (45), `KnowledgeBase` (49 to 66): eighteen lines that let `Witness` 290
   and `Tick` 400 stay verbatim.
6. `Gossip.cs`: `SocialGraph` (9 to 32); `Rumor` (37 to 59); `Gossiper` (64
   to 118) less `Suspicion`; `GossipEvent` (122 to 128); `GossipMill`:
   `_agents`, `_graph`, the four tunables (141 to 144), constructor (146),
   `Tie` (152), `Add` (154), `Get` (178 to 179), `WitnessesOffered/Dropped`
   (194 to 195), `SummariesSaying`, `SaysWord`, `IsWordChar` (225 to 256,
   the "player" leak guard), `Witness` (262 to 325), `Tick` (341 to 430)
   with `together` as a function argument.

THE ONE OMISSION INSIDE PORTED FUNCTIONS, named in the port at each site:
`SuspicionTracker` is not ported, so `Tick` 402 and 412 (`Suspicion.Raise`)
are absent while `ev.Contradiction` and `ev.Exposure` are set exactly as 406
and 413 set them; the verdict prints
`gossipSuspicionPorted=no/SuspicionTracker-out-of-scope`. One exception under
the formatting law: `Witness` line 324 has an em-dash inside a string this
run WILL write to a committed file (certainty caps at 0.94, so the doubtful
branch fires). The port writes a comma there and `Gossip.cs` 324 is corrected
to the same comma in the same batch, the one-character opportunistic
correction the law allows; the resident greps `CoreTests` for the old string
first and CI's core tests are the proof.

OUT OF SCOPE; a builder reaching for any of these has drifted:
`Perception.Attention`, `IdentifySeconds`, `RingDraw`, `HeardAs`,
`BelievedAt`, `Traces`; `Observe.DeedFor` (needs `Arsenal`), `Willingness`,
`AwarenessOf`, `GhostAllowed`, `Misattribute`, `Retell`, `Combine`,
`AssemblesMore`, `Delivery`; `SuspicionTracker`; every other `GossipMill`
member (`Forget`, `PlayerClaims`, `CompareNotes`, `KnowsSecret`,
`DayCircleHeat`, `Leads`, `ExposureOf`, `Bribe`, `Intimidate`, `Discredit`,
`UseHook`, `Age`, `HoldsIndelible`, `Contain`, `Backfire`,
`RestoreDiscredited`, `StrongestSurvivingPlayerLead`) and their types;
`StreetVoice`, `SpeechDirector`, `VoiceBank`; any save format; any JSON
beyond the bank file; `Empire`, `Homicide`, `OperationSetup`, `Operations`.

## 2. Question 2: the crime, exactly

THE STREET HAS SIX GROUND-FLOOR WINDOWS AND NOTHING ELSE TO BREAK. From the
JSON: `C7_shop_glazing` is `east_parade_glass0..5` (3.562 x 1.8 x 0.04 m,
centre y 1.6, z 4.985, x 6.869 + 6n) plus six toplights; the kiosk has four
glass panels; the west terraces are brick houses. Refused: the kiosk (small
panels, poor at 480x270, operator mark owed by canon, queue 030); dustbins
and the sign (no crime anyone tells); assault (no second body exists).

RULED: A HALF-BRICK THROUGH A SHOP WINDOW, at two windows (A3): crime A is
`east_parade_glass0`, crime B `east_parade_glass1`. A window broken once
cannot be broken again without the probe restoring it, a trick nobody
watching should be told about; the two are the same piece kind at the same
height off the same footway line, so only who can see differs. The act: the
glass actor hidden and its collision off, both READ BACK after the call;
eight shard boxes (0.15 x 0.01 x 0.10 m) on the footway within 1 m of the
window foot; one brick box (0.215 x 0.065 x 0.1 m) inside the window line.
No projectile, no animation: a sequence frame is forced immediately before
and after each deed so the break reads as a cut, the honest form at 0.4 s
sampling. The `Deed`: `Loudness = Perception::LoudBottleSmash` (70, the
nearest named sound to breaking glass, no new number),
`VictimCriesOut=false`, `WeaponDrawn=false`, `ActorFled=true` (the script
walks the pawn away), `LeavesBody=false`, `HadPrecursor=false`,
`IsAccident=false`, `VictimId` the window's name. All printed as inputs.

ONE PROBE HELPER, NOT FIVE. `VignetteShot.h` gains `SpawnProbePiece(World,
Name, CentreM, SizeM, Shape, Surface)`, a thin export over the existing
`SpawnPiece` with `bInteractive=true`, registered in a SEPARATE map so
`GByName`, `FindStreetPiece`, `piecesEmitted=593/593` and every vignette
counter are untouched. It spawns the shards, the bricks, the two NPC
stand-ins (cylinders 0.4 m by 1.75 m, the shape-from-code discipline
`LedgerCharacter.h` states; no Mixamo body exists in ue-probe and the
verdict says so), and the yard floor.

THE YARD FLOOR (A2). `ground_plot_2` spans x 3 to 21, `ground_plot_3` x 24
to 42, both z -13.125 to -5.125; between them, behind the dropped kerb
(`kerb_west_kerb022..026`), x 21 to 24 has no ground plane. That gap is the
only place a person can stand with a terrace between them and a shop window:
the west footway ends at z -5.125 and every sightline from it to the parade
clears `west_south_bay2` by construction. The probe spawns
`probe_yard_floor`, a box 3.0 x 0.3 x 8.0 m at (22.5, -0.05, -9.125), surface
`concrete`, printed `probeFloor=1/1
probeFloorNote=not-a-street-piece/the-street-owes-a-yard-behind-the-crossover`;
a queue item is filed for the street to own that yard.

THE PLACEMENTS, street metres, all printed:

- Pawn start S (1.0, 4.0), yaw +x, teleported as the walk teleports. Crime
  point C_A (6.87, 3.9), then yaw to +z to face the window. C_B (12.87, 3.9),
  same. The footway x 4 to 10.18 at z about 4.0 is the line the walk verdict
  proved open.
- W1 at P1 (9.0, 4.7), the next doorstep along, facing C_A. Constraint:
  inside 8 m so a stranger can reach rung 3; inside the pawn's face arc when
  the pawn faces the window (`Witnesses.cs` 152, `Angle(actor.forward, eye -
  actor) < FaceArcDegrees`, 90 at line 43; here about 69 degrees); clear of
  the pawn's later line at z 3.9.
- W1 at P2 (22.5, -7.5) on the yard floor for crime B, facing C_B.
  Constraint: the trace from its eye to the actor's head hits a
  `C1_terrace_carcass` by name; by arithmetic `west_south_bay2` at about x
  20.5 on the z -5.125 face.
- N2 at PN (22.5, -8.9), facing +z. Constraint: occluded by trace from both
  C_A and C_B (`west_south_bay2` at about x 17.9 and 19.7); within 6 m of P2
  (1.4 m) and of the overhearing point.
- Overhearing point Y (22.5, -3.3), on the west footway between the cones (x
  21.3 and 23.7, z -3.35) and short of the skip (z -2.85 to -0.85), pawn
  facing -z into the yard: about 4.2 m to P2, 5.6 m to PN, both under 6.

THE INPUTS THAT ARE NOT GEOMETRY, each the game's own value, named so:
`GameTime` D1 12:00; light 1.0, which is `Perceivers.LevelAt` (`Perceivers.cs`
69 to 71) at night amount 0, lanterns off, the `overcast_day` condition this
build runs; ambient floor 45.0 (`AmbientDaytimeStreet`, the noon default
`AmbientFloorAt` lerps from); familiarity 0.0 for both (`Witnesses.cs` 142,
the value when nothing supplies one: strangers); no mark; tie `w1`-`n2` 0.6,
an existing neighbour weight (`GossipDirector.cs` 127 to 128); `together` is
distance at or under 6 m (34, 660 to 666); earshot 6 m to BOTH speakers (247,
577 to 578). `SecondsWatching` is MEASURED: the ticker accumulates seconds
during which `InSight` to the actor holds for that witness (`Witnesses.cs`
178 to 192 says that is what belongs there), printed against `NoticeSeconds`
0.35. `FaceToward` is computed as line 152 does. Occlusion is a UE line trace
against the street's collision from the eye (1.6 m) to the actor's head and,
separately, to the window centre, target ignored, the first blocking actor's
NAME printed.

THE PREDICTION, so the first run is read against one: W1 at P1 for A, 2.3 m,
0 degrees, clear, face toward, light 1.0: `InSight` true, rung 3, heard
(radius 13.1 m), slots act/victim/actor/flight, `full`, certainty 0.94,
filed. W1 at P2 and N2 at PN for either crime: occluded, and the occluded
hearing radius at floor 45 is 1.95 m against 14 to 21 m, so no slot, nothing
filed. A disagreement between prediction and print is the finding.

## 3. Question 3: the second NPC's line, and where it comes from

RULED: A BANK, `content/dialogue/crime-witness-v1.json`, spec
`production/specs/dialogue-crime-witness-v1.md`, written by the
dialogue-writer, gated by `tools/dialogue-verify.py` and `canon-gate.py`,
found at runtime as `vignette-pieces.json` is (`VignetteShot.cpp` 320 to 324,
the same four candidates). Not a C++ literal, for three reasons each
sufficient: the same text must reach the verdict, the caption and, next rung,
a voice clip whose FILENAME is a hash of speaker and text (`VoiceBank.cs`),
so the text has one home; the rung discipline is a tool that reads banks and
cannot read C++; the D7 judge reads banks. Not `StreetVoice.Exchange` (what
`ReportOverheard` calls at 587): a composition system, out of scope, and the
rung above a bank pick on the ladder.

THE BANK (A5). Two contexts, `witness_summary` and `overheard`, at `idRung` 1
to 4, three variants per cell, twenty-four lines. Each line carries `rung`
for the address checker (`stranger` for idRung 1 to 3, `novak` for 4, never
`tom`) and `idRung` for selection. The summary is what `Witness` files and
what the "heard" memory line repeats (`Gossip.cs` 394), so it is in the
witness's mouth at her rung: a shape at 1, a mark at 2, a face she would know
again at 3, the new owner at 4. The overheard line is the second NPC's reply
at the same rung and never claims more than the summary carried. Selection
is deterministic, seed `Day * 31 + Hour` as `GossipDirector.cs` 586. Display
names are archetypes, not cast (`w1` "the shopkeeper", `n2` "the lad in the
yard"): canon's cast baseline is pending OPEN 2 and a probe does not mint it.
One window, on the Parade (the pub bank's own word). No line contains
"player"; `summariesSayingPlayer=0/N` is printed by the ported guard. In the
clip the exchange is two beats as the game stages it (`SayAfter` at `i * 2.1`
s): her summary, then his reply.

## 4. Question 4: the verdict keys

File `ue-crime-verdict.txt`: line 1 `# UE crime probe <sha> @<epoch>`, header
comments naming each judgment as the walk's do, breadcrumbs
`crimePhaseReached=` and `crimeReached=end`, `launchStatus=` added by the
workflow from outside. No spaces in values; `/`, `,` and `..` for structure;
the statistic named beside each key; every zero with its count.

1. `sceneStatus ...`, the walk's line read back; `probeFloor=1/1
   probeBodies=2/2 probeShards=16/16 probeBricks=2/2
   probePiecesNote=not-street-pieces/never-in-GByName` (spawned over asked).
2. Inputs, once, each value beside a `*Source=` key naming the C# line it
   came from (section 2): `crimeGameTime=D1/12:00 crimeLightLevel=1.00
   crimeAmbientFloor=45.0 crimeLoudness=70.0 castTie=0.60
   castFamiliarityW1=0.00 castFamiliarityN2=0.00
   castBodies=cylinder-stand-in/no-mixamo-body-in-ue-probe`.
3. Per crime: `crime=A piece=east_parade_glass0 actorAtXYZcm=.. actorYawDeg=..
   glassHiddenBefore=no glassHiddenAfter=yes glassCollisionAfter=off
   shards=8/8 brick=1/1 crimeStatus=COMMITTED` (read back from the actor; a
   hide that did not take prints `NOT-COMMITTED` with the flag it read).
4. Per witness per crime, the per-sample moment: `witness=w1 event=A
   witnessAtXYZcm=.. witnessYawDeg=.. actorMetres=.. actorOffAxisDeg=..
   actorOccluded=no actorBlocker=none actorTraceLenCm=.. victimMetres=..
   victimOffAxisDeg=.. victimOccluded=no victimBlocker=none faceToward=yes
   faceAngleDeg=.. faceArcDeg=90 secondsWatching=.. noticeSeconds=0.35
   inSightActor=yes inSightVictim=yes heardAct=yes audibleRadiusM=13.1
   idRung=3 slots=act,victim,actor,flight label=full certainty=0.94
   filed=yes filedReason=none`; the rejecting shape carries
   `actorOccluded=yes actorBlocker=west_south_bay2 .. inSightActor=no
   idRung=0 slots=none label=nothing certainty=0.00 filed=no
   filedReason=slots-none`. Four lines per run. What the probe does with an
   empty `Observation` is whatever `Witnesses.cs` does after line 207; the
   builder reads it and prints which branch ran.
5. The mill, whole-run: `witnessesOffered=1 witnessesDropped=0/1
   summariesSayingPlayer=0/1-rumours gossipSuspicionPorted=no/..`.
6. Per gossip round: `gossipRound=1 speaker=w1 listener=n2 pairMetres=19.1
   talkRangeM=6.0 together=no rumoursHeld=1 passed=0/1
   passedStatus=NOT-TOGETHER`; `gossipRound=2 .. pairMetres=1.4 together=yes
   tie=0.60 hopDecay=0.80 minShare=0.20 confidenceIn=0.94
   confidencePassed=0.45 passed=1/1 hops=1 heardMemoryImportance=0.36
   contradiction=no exposure=no passedStatus=PASSED`.
7. Overheard, once: `overheardEvents=1/1 overheardPlayerToW1M=..
   overheardPlayerToN2M=.. earshotM=6.0 overheardStatus=HEARD
   overheardSpeakers=w1,n2 overheardIdRung=3
   overheardLineIds=cw-ws-r3-02,cw-ov-r3-01
   overheardBank=content/dialogue/crime-witness-v1.json
   overheardLineSource=bank/StreetVoice.Exchange-not-ported`.
8. Memory, whole-run: `memoryW1Events=1 memoryN2Events=1 memoryFiles=2/2
   memoryFilePrefix=ue-crime-memory-`; `ue-crime-memory-w1.md` and `-n2.md`
   written by `ToMarkdown`, staged by name.
9. Three combined readings, each needing both halves (rule 5b):
   `witnessStatus=REAL|NOT-PROVEN|NOTHING-MEASURED` (W1 filed on A with idRung
   at least 1, AND W1 filed nothing on B with `actorOccluded=yes`, AND N2
   filed nothing on either); `gossipStatus` (round 1 passed 0 with
   together=no AND round 2 passed 1 with together=yes); `overheardStatus` as
   above. No new numeric bound: every word is a conjunction of the model's
   own outputs, with the raw numbers beside it.
10. Frames: six milestones `ue-crime_NN_<name>.png` (`start`, `before_crime_a`,
    `after_crime_a`, `before_crime_b`, `after_crime_b`, `overheard`) each
    with the walk's pixel line, `crimeFramesRequested=6/6
    crimeFramesWrote=6/6`; the sequence `ue-crimeseq_NNN.png` with
    `crimeSeqFramesRequested=N/32 crimeSeqFramesWrote=N/32
    crimeSeqIntervalSeconds=0.4 crimeSeqForcedAtDeeds=4/4
    crimeSeqKeysFile=ue-crimeseq-keys.txt`; 32 is a clock cap and announces
    itself as 16 does now.

## 5. Question 5: what the clip shows

A person watching `production/d1-probe/ue-crime.gif` with no numbers sees:
the parade ahead and a figure on a doorstep; the approach; the window whole
in one frame and gone in the next, glass on the pavement, the figure right
there; walking on and putting the next window in with nobody in frame; then
the yard, two figures behind the barrier, and words along the bottom, hers
first (a window on the Parade, a face she would know again), then his reply.
That is: I did it in front of someone, and later two people were talking
about it. The second window's consequence is that nobody speaks of it, which
is the true consequence and can be shown no other way.

MECHANICS. The probe writes `ue-crimeseq-keys.txt`, one line per sequence
frame: `frame=ue-crimeseq_012.png beat=overheard speaker=w1
lineId=cw-ws-r3-02 heard=yes`; approach and deed frames carry `heard=no`.
`tools/clip-from-frames.py` gains `--frame-keys` and `--bank`, burns a
caption strip on frames whose line says `heard=yes` from the bank's text for
that id, and prints `clipCaptionedFrames=N/M clipCaptionTextPx=..
clipCaptionFont=..`. The caption is formatting and lives in the tested Python
layer (`instruments.md`); its selftest is a synthetic keys file, accepting
case first: a `heard=yes` frame's strip changes, a `heard=no` frame's does
not, an id the bank lacks refuses with the id named. The overheard hold is
about three seconds, so seven frames carry words. The walk's fifteen frames
were 1.64 MB; thirty at the same scale is about 3.3 MB against the 8 MiB
refusal, and the stitcher prints the bytes. The milestones stay untouched.

## 6. Question 6: what is NOT in this change

No third NPC, no second crime kind, no night, no rain. No Mixamo body (the
ladder row stays: stand-ins; next rung a held body with an idle). No voice
and no sound in the clip (a GIF is silent; a sound clip is MP4 is ffmpeg is a
decision record). No `StreetVoice` composition. No `Attention`:
`SecondsWatching` is the probe's count and `RungFloor` is 0, both printed. No
suspicion, contradiction or exposure consequences. No `Delivery`. No save
file, no memory loading. No general engine bridge: the bank and the pieces
file are the only JSON read. No `Weapon` row for a half-brick: the `Deed` is
hand-built with its fields printed and the `Arsenal` row is filed. No change
to `ALedgerGameMode`, `ALedgerCharacter`, the three existing switches,
`BuildScene` or the vignette gates; `-LedgerCrime` is checked only in
`LedgerProbe.cpp`'s switch block beside `-LedgerWalk`, and a plain launch is
bit-for-bit unaffected. No yard in the street's JSON. No new threshold.

## 7. The ladder: a done step must be showable; the street step is done

THE CHAIN, CHECKED. `next_three` (`map.py` 1310 to 1353) reads only `next`;
`ladder_rungs` (1390 to 1434) marks the first non-refused item `current` and
the rest `next`; `next-three.json` says "An item leaves the list by being
deleted from it"; the docstring (34 to 39) and the done line (2582 to 2593,
`ladderDoneCount` never a number) concede no rung below the goal can be shown
done. Deleting the street step moves the page from STEP 1 OF 4 to STEP 1 OF
3; "step 2 of 10" cannot print. The selftest (3366 to 3378) pins `named ==
NEXT_ASKED` and the three titles in `next`, so the move also breaks it
unless taught the new shape.

RULED: A `done` ARRAY; the candidate shape is right, with one addition that
keeps the tick measured.

- Field `done`, ordered, before `next`, entries `{title, why, queue, doneOn,
  evidence}`, where `evidence` is a list of `{file, key}` pairs: `file` a
  committed path, `key` an exact `key=value` token that must appear on a
  line of it. A done entry is a CLAIM plus the instrument that proves it;
  map.py checks the instrument, never the claim.
- Governance, appended to `howItChanges`: "A finished step MOVES from `next`
  to the end of `done`, carrying the date and the evidence files whose named
  keys prove it. It is never deleted. A human or a ruling makes the move,
  and the ladder counts done, then next, then the goal."
- map.py: `next_three` reads `done` (absent means empty, printed
  `doneNamed=0/absent`) and searches each evidence file for its key on a
  line; `ladder_rungs` numbers done rungs first, state `done`, then `next`
  as now, then the goal; `total = len(done) + stepsShown + 1`, `currentNum =
  len(done) + i`; `NEXT_ASKED` caps `next` only; `ladder_html` renders a
  done rung with the word DONE and its date, never a glyph; the done line
  prints `ladderDoneCount=N/M-claimed ladderDoneProven=N/M`.
- Disagreement: a title in both arrays, a missing evidence file, or a key not
  found refuses the WHOLE ladder with the stale banner and the reason
  (`title-in-both-done-and-next`, `done-step-1-evidence-missing/<file>`,
  `done-step-1-key-absent/<key>`): a step count on his phone rests on every
  done rung being real, and a half-proven ladder is the invented progress
  ruling 3 forbids. A done entry whose queue file is still READY is fine:
  queue 138 covers all three steps; a step is not a queue item.
- Selftest: the live repository is the accepting fixture (one done, two next,
  STEP 2 OF 4 on the page); rejecting fixtures are synthetic (an evidence
  path that exists nowhere; a title in both arrays); the order assertion at
  3375 to 3378 runs over done then next, still control, crime, gossip;
  `check_ladder_done_not_invented` keeps the zero-glyph rule and requires
  the "nothing measured" wording only when `done` is empty.

IS THE STREET STEP FINISHED? ON THE MACHINE, YES. The verdict on `de4ad4d`:
`launchStatus=LAUNCHED launchExitCode=0`, `sceneStatus=WHOLE
piecesEmitted=593/593`, `walkCameraStatus=MOVED` at 618.2 cm,
`testCardsSpawned=0/3`, `collisionStatus=REAL` with the planted wall
`STOPPED` at 100.0 of 150.0 cm, `clipStatus=WROTE` 15 of 15 frames at 1642282
bytes: every judgment ruling 1 named, with denominators and the rule-5b pair.
Jafar's sentence ends "a clip on my phone and a green step on the ladder", in
that order, so the move needs one key this seat cannot read: a receipt under
`production/outbound/` reading `receipt: sent-with-clip` for the walk clip.
The resident greps for it before editing. If present, the street step moves
to `done` in this batch with `evidence` naming the verdict
(`launchStatus=LAUNCHED`, `collisionStatus=REAL`) and the receipt. If absent,
the step stays in `next` and its `why` becomes "verified by the machine on
de4ad4d; the clip is not yet on his phone", because a false sentence on his
phone cannot stand for a batch. Either way item 1's `why` is replaced now.

## 8. Before the commit the resident prints; and what is filed

1. `grep -rn "LedgerCrime" ue-probe/Source`: one site, in `LedgerProbe.cpp`.
2. `grep -rn "SpawnProbePiece" ue-probe/Source` and `grep -n "GByName.Add"`
   in `VignetteShot.cpp`: the export's call sites; still one `Add` site.
3. The g++ selftest for the port: the six radii of `Perception.cs` 283 to 289
   and `Observation.cs`'s four-witness case, count and exit 0.
4. `tools/dialogue-verify.py` and `canon-gate.py` on the bank: lines read,
   pairs compared, worst overlap, 0 rung violations, exit 0.
5. `tools/clip-from-frames.py --selftest` and `tools/map.py --selftest`: count
   lines, one case more per rejecting fixture named above, exit 0; the map's
   done line `ladderDoneProven=1/1-claimed` or `0/0-absent`.
6. `grep -rn "couldn't swear" ledger/`: the comma form only; `CoreTests` green
   on CI by ancestry.
7. `tools/docs-check.py` clean on this record.
8. `ls production/outbound/ | grep -i walk` and the receipt line, quoted.
9. `python3 ledger/verify.py`, footer FROM `ledger/.verify-footer`; the
   cadence line names this record and row `2026-09-08T02:21:36Z`.
10. The sha captured BEFORE dispatch; the crime run watched by ancestry; its
    verdict opened and every `*Status` word read beside its numbers before
    any message is written.

FILED, NAMES NOT WORK: the yard behind the west crossover as a street piece;
`StreetVoice.Exchange` ported so the reply is composed, not picked;
`Perception.Attention` ported so `SecondsWatching` and `RungFloor` come from
the accumulator; `SuspicionTracker` and consequences 1 and 2; a held body for
the stand-ins (ladder row, queue 028); a crowd voice for the two lines by
`VoiceBank` hash and a clip format that carries sound; an `Arsenal` row for a
half-brick so `DeedFor` replaces the hand-built `Deed`. Quality-ladder rows
the builder adds: Crime (hidden piece plus shards; next rung a projectile and
a sound), Witness (`Resolve` on real traces; next rung `Attention`),
Overheard line (bank pick with caption; next rung composed and voiced), NPC
body (cylinder; next rung a held Mixamo body).

<!--RULING spawn=2026-09-08T02:21:36Z-->
