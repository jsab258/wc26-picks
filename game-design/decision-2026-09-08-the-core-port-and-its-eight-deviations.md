# Ruling: the Core port and its eight deviations. LAND WITH AMENDMENTS

> **STATUS: LIVE, verified 2026-09-08.** Director ruling at spawn
> 2026-09-08T07:08:34Z (`.claude/agent-log.tsv` line 358) on the uncommitted
> tree after `d6411af6`: 4518 changed lines (1956 tracked, 2562 untracked in
> 8 new files) against the 100 threshold,
> `workByScope=scripts:2/ledger:597/ueprobe:3919`. The specification is
> section 1 of
> `decision-2026-09-08-the-crime-the-witness-and-the-overheard-consequence.md`.
> The reading copy for the resident until the amended batch lands and the
> golden job on it is read; then the record of why.

VERDICT: LAND WITH AMENDMENTS. Six of the eight deviations are accepted as
written, one is accepted as a finding and refused as a proof, one is refused
outright. Three amendments block the commit, all three ride one regenerate of
the golden table:

- A1. The four-witness fixture is owed and is added as a scenario. Section 2,
  deviation 7.
- A2. Two golden rows one ulp below a half decide whether `FormatTwoDecimals`
  reproduces .NET or only the six values it was measured on. Section 2,
  deviation 5.
- A3. Six of the seven uncovered members get a failing-capable reading on the
  same regenerate; the seventh was covered already. Section 4.

Everything else in the batch stands, including the one-character change to
`Gossip.cs`, the empty shim, and the six unrun bridging lines, each on the
condition named in its section.

## 0. What was read, what was not run

No shell in this seat: the task text says Bash is available and this seat has
no Bash tool, so NOTHING WAS RUN. Read whole: the crime ruling; the six port
headers and `Perception.cpp`; `CoreGolden.h`; `core-port-test.cpp`; the shim;
`ledger/PerceptionGolden/Program.cs`; the C# it compiles (`Observation.cs` 20
to 355, `MemoryStore.cs`, `Suspicion.cs` 1 to 70, `Gossip.cs` 1 to 435,
`GameTime.cs` 1 to 60, `Perception.cs` 218 to 367); the golden table by grep
and by row for every function this ruling names; the Unreal dispatch block
(`LedgerProbe.cpp` 608 to 733); the workflow's golden step (455 to 535); the
cadence parser; the CoreTests four-witness case (16019 to 16103).

The numbers `2614 checks over 3 of 3 binaries`, `2418 rows`, `0 mismatches`,
`0 unknown` are THE RESIDENT'S, quoted, not mine. What this seat can see:
`ledger/.ue-test/core-port-test` exists on disk, which proves the binary
compiled at least once and nothing about whether it passed;
`perception-golden.txt` has 2418 rows whose first token is one of the twenty
function names (grep count, this session); `ledger/.verify-footer` is absent,
which is what a red cadence check leaves behind and is consistent with the
refusal quoted in the task. Section 8 requires the resident to paste the
test line FROM A FRESH RUN after the amendments.

Rule 1 applies to the one external fact this ruling leans on: that .NET
renders a double to fifteen significant digits before applying a custom
format string. The constant `DoublePrecisionCustomFormat = 15` in
`Number.Formatting.cs` was confirmed by search against `dotnet/runtime` this
session. What follows from it is REASONED, not measured, which is why A2
orders the measurement instead of ruling on the reasoning.

## 1. The one test every deviation is judged by

`Perception.h` lines 3 to 8: the C# suite is the behavioural definition, and
a port that improved something would make the two engines incomparable. So
the question for each deviation is never "is the C++ better" but: IS THERE AN
INPUT THE C# DEFINES ON WHICH THE TWO ENGINES NOW ANSWER DIFFERENTLY, and if
so, does a golden row exist that would go red on it. A deviation with no such
input is a transliteration by another spelling. A deviation with such an
input and no row is a hole.

## 2. The eight deviations

**Deviation 1, the two renames. ACCEPTED.** `Observation::AwarenessState`
and `GossipEvent::RumorRef` are member names; the types keep the C# names,
which is what other code says out loud. No golden row reads either member by
name across engines (`RumorRef` is reached as `R2[0].RumorRef->Confidence`
and the C# reads `r2[0].Rumor.Confidence`; the two readings agree at row
2362). Both sites carry the comment naming the C# name (`Observation.h` 110
to 115, `Gossip.h` 293 to 295). No input the C# defines is answered
differently.

**Deviation 2, `Fact` held by value. ACCEPTED.** Every ported line that
touches a `Fact` was read: the constructor writes the three fields;
`SameTopic`, `ToString`, `TopicKey` read them; `Learn` stores; `CheckClaim`
compares `Value`; `Witness` stores into a `Rumor`; `Tick` copies `R->Content`
into `Heard`. No ported line writes a field after construction, so aliasing
is the only thing a reference would add and no ported line depends on
aliasing. `Rumor`, `Gossiper`, `MemoryStore`, `KnowledgeBase` are mutated
through handles (`Witness` raises `Already->Confidence` in place; `Tick`
appends to a listener fetched by id) and are `shared_ptr`, correctly. The
header names the deviation at `Gossip.h` 36 to 45.

**Deviation 3, `Prune` by index. ACCEPTED, tie caveat recorded.**
`MemoryStore.cs` 97 builds `HashSet<MemoryEvent>` and `MemoryEvent` overrides
neither `Equals` nor `GetHashCode` (read, lines 8 to 50), so the C# set is
reference identity: it removes exactly those instances, and two field-equal
events are two instances. Marking indices is the faithful reading of that.
For distinct importances the two removals are the same set. For equal
importances the C# is engine-defined (`List.Sort` is an unstable introsort)
and so is the port's choice, so making the C++ side deterministic with
`std::stable_sort` cannot make the engines disagree on any input where the
C# is defined. The golden scenario uses `i / 1000.0` for `i` in 0 to 700,
all distinct, and the crime run's two stores hold one and two events against
a cap of 600, so `Prune` is exercised only by the table. Nothing to add.

**Deviation 4, ASCII-only `Trim`, `ToLowerInvariant`, `IsLetterOrDigit`, and
`"\n"` for `AppendLine`. ACCEPTED, measured.** Non-ASCII bytes this session:
0 in `content/dialogue/crime-witness-v1.json` (1 file examined), 0 in
`perception-golden.txt` (1 file examined). Every string the run can put
through these helpers comes from the bank, from ids, or from the literals in
`Gossip.cs`, so on every input the run can produce the two engines agree.
The day a non-ASCII summary enters the bank, `IsWordChar` beside "player"
and `ToLowerInvariantAscii` on an id become the two places the engines can
part; a queue name is filed in section 7 rather than a Unicode port bought
now for a run that cannot reach it. The line ending: `Environment.NewLine` is
a platform fact, the golden `Escape` drops `\r` on both sides, and the
memory file from the PC is compared line for line. A reader who diffs it
byte for byte against a Windows C# run will see every line differ and must
not read that as a model difference.

**Deviation 5, `FormatTwoDecimals`. THE FINDING IS ACCEPTED; THE RULE IS NOT
YET PROVEN; A2 decides it.** The finding stands on its own evidence: six
values where C# `"0.00"` and `printf("%.2f")` disagree, in the table at rows
2293 to 2298, and a rejecting check that `printf` really does print `0.12`
for `0.125` (`core-port-test.cpp` 159 to 161), which is rule 5b in both
halves. A `%.2f` port would have written a different importance into the
committed memory file for every value on a binary-exact or below-half
boundary, invisible until two engines' files were diffed. The builder was
right to reimplement rather than to switch the comparison to a tolerance,
because the comparison is of a committed string and a tolerance on a string
is a comparison that cannot fail.

The rule as stated is the problem. `MemoryStore.h` 95 to 118 says C# renders
"the shortest decimal that reads back as the double" and then rounds it half
away from zero, and `ShortestRoundTrip` implements exactly that. The .NET
source says something else: a custom format string renders the double to
`DoublePrecisionCustomFormat = 15` significant digits FIRST, then rounds that
digit buffer half away from zero. The two rules agree on every value whose
shortest round-trip has at most fifteen significant digits, which is every
value in the table (the longest is `0.36096`, five digits). They can
disagree on a 16- or 17-digit double sitting one ulp below a half: for the
double just under `0.125`, fifteen digits gives `0.125000000000000` and then
`0.13`; the shortest round-trip gives `0.12499999999999999` and then `0.12`.
Products of three and four factors, which is what the mill's importances
are, routinely need 16 or 17 digits to round-trip. Whether this run's do is
not in the table, and that is the point: the rule was set from a series that
did not contain the case the rule was written about (rule 2).

A2, ordered: two `TwoDecimals` rows emitted by the C# from
`Math.BitDecrement(0.125)` and `Math.BitDecrement(0.135)`, so nobody types
seventeen digits and the value is the neighbour double by construction.
Read the C# answer before touching the port. If it prints `0.13` and `0.14`,
`FormatTwoDecimals` replaces its `ShortestRoundTrip` first step with a
fifteen-significant-digit render (`%.15g`, correctly rounded in glibc) and
the comment names the .NET constant. If it prints `0.12` and `0.13`, the
port stands and the comment gains the two rows as the proof that the rule
survives seventeen digits. Either way the rows stay, and either way the
port's rule is then a thing the table checked rather than a thing a comment
described. Should the divergence have been surfaced differently? No: a
measured table in the comment, six rows, a rejecting check and a line in the
eight-item list is the right shape. What was missing was the second
measurement, not the first.

**Deviation 6, `Beliefs` kept and always empty. ACCEPTED.** Row 2337
(`Scenario|mem_basic|markdown`) pins `##~Beliefs^^##~Events`, so the field is
covered in the only state this port can put it in, and dropping it would
change a committed artefact for no reason a reader could see. Both writers
(`ReplaceBeliefs`, `LoadFrom`) are out of scope by the ruling. This is not
one of the uncovered seven; see section 4.

**Deviation 7, the four-witness case not reproduced. REFUSED; A1.** The
crime ruling section 8 item 3 names "Observation.cs's four-witness case" as
the port's own proof, and a binding ruling's named fixture is not a
suggestion. The fixture is `CoreTests/Program.cs` 16019 to 16103: one deed
(loudness 62, drawn, fled, leaves a body, had a precursor, no cry) and four
vantages, and its first claim is that four positions produce FOUR DISTINCT
slot sets, with the far witness producing `act, no actor` because the victim
is in the market light at 9 m and the shooter in a doorway at 24 m under
0.08. That label is the reason `Sight` was split off `Vantage` at all
(`Observation.cs` 114 to 126).

The thirteen emitted cases were walked one by one. `act, no actor` needs
`seesVictim` true with `seesActor` false or rung 0. The only cases with the
victim in sight (`crimeA`, `rungFloor`) also have the actor in sight at rung
3 or 4 and label `full`; `glance` fails `NoticeSeconds` for both; `cryOnly`
puts the victim at 70 degrees, outside the 60-degree field, so the victim
is not seen; `night`, `calmAt20`, `alertAt20` are under 0.12 light at 5 m
and 20 m against a 4.8 m range; the rest blind the victim. So the one branch
the named fixture exists for is reached by no `Resolve` row. The 128 `Label`
rows pin the STRING for slot set 12; they do not pin that `Resolve` can
produce it from two sightlines. That is the hole.

A1, ordered: a scenario `observation_four` on both sides, built exactly as
CoreTests builds it: the deed above; `close` (4 m, light 1.0, familiarity
0.9), `wall` (6 m, occluded both sightlines), `later` (1 m, arrived later),
`across` (victim `Sight::At(9, 1.0)`, actor `Sight::At(24, 0.08)`,
familiarity 0.9, floor 58, face toward, 3 s), `litShooter` (`across` with
the actor at `Sight::At(24, 1.0)`), `wallLoud` (`wall` with loudness 100).
Readings per vantage: `slots`, `rung`, `certainty`, `label`, `accused`,
`namesSomebody`; plus `distinctSets`, the count of distinct slot values over
close, across, wall, later, which the C# asserts is 4. The three `Both`-shaped
vantages are built through `Vantage::Both` and an `At` helper of the
CoreTests shape on the C++ side, which is what covers `Vantage::Both` (section
4). About forty lines each side; it rides A2's regenerate.

**Deviation 8, `D2` versus `%02d`. ACCEPTED.** They differ only on a negative
hour or minute (`-05` against `-5`), no producer supplies one, and the five
golden rows include hour 0 and minute 0 and a two-digit day. Nothing to add.

## 3. The one character in `Gossip.cs`. ACCEPTED IN THIS BATCH

Checked this session, not taken from the builder: `couldn't swear` has
exactly one hit under `ledger/Assets/Scripts/` (`Gossip.cs` 324, comma form)
and the other four hits under `ledger/` are different sentences
(`CoreTests/Program.cs` 563, `Informing.cs` 208, `DialogueUI.cs` 1081 and
1685), so no test asserts the string. The three em-dash shapes of the
sentence return 0 hits across the repository. The golden table was
regenerated AFTER the edit: rows 2355 and 2405 carry the comma. Those are
also the only two rows that contain the sentence, which matches "exactly two
mismatches" on the first run to the row.

Whether a change to the behavioural definition belongs in the port's batch:
yes, for three reasons each sufficient. The crime ruling ordered it in the
same batch, explicitly, lines 92 to 98. The string is one the run writes into
a committed memory file, which is the exact case the formatting law's
opportunistic clause exists for. And the port WAS compared against the
original definition: it went red on the em-dash, on exactly the two rows the
sentence sits in, and green on the comma. That red is the rejecting half of
rule 5b for every string row in the table, the proof that a one-character
difference in a committed line is a thing this instrument sees. It goes in
the commit message by row number (section 8). Condition inherited from the
crime ruling section 8 item 6: `CoreTests` green on CI by ancestry for the
landed sha.

## 4. The seven members with no failing-capable case. A3

Rule 6: a member nothing calls and no row can fail is built, not running.
Taken one at a time, against what a row would cost:

- `MemoryStore::Beliefs`: COVERED already, section 2 deviation 6. Off the
  list.
- `Vantage::Both`: covered by A1's `At` helper. Off the list once A1 lands.
- `Awareness` / `AwarenessState` and `Observation::Retellings`: the
  constructor is their only writer. Two more fields in the `Resolve` row
  list on both sides (`awareness` as its integer, `retellings`), so the
  defaults are pinned. Two lines each side.
- `Sight::Blind()`: one C# caller, `Witnesses.cs` 86, the eye that does not
  exist, which is the shape the crime probe will feed for an out-of-world
  target. In `observation_four`, one more vantage `blindVictim` (`close`
  with `ToVictim = Sight::Blind()`) read as the others, plus three readings
  of `Blind()` itself (`blindMetres`, `blindLight`, `blindOccluded`).
- `Gossiper::Holds` and `Gossiper::Best`: in `gossip_crime` after round 2,
  `n2Holds` (topic and value held, expect 1), `n2HoldsOther` (same topic,
  value `east_parade_glass1`, expect 0), `w1BestConf` (0.94), `n2BestConf`
  (0.4512). `Best` has one subtlety, stability among equal confidences, and
  it gets its own case: in `witness_upgrade`, two more sightings on one new
  topic with DIFFERENT values at equal confidence 0.5, then `bestValueTie`,
  which must read the first-added value, because `OrderByDescending` is
  stable and the port's strict `>` claims to reproduce that.

All of it rides the one regenerate A1 and A2 already require. If any single
item above costs more than the lines named here, it drops to the queue under
its own name rather than blocking; none should.

## 5. The empty shim. ACCEPTED

`ue-probe/tests/unreal-shim/CoreMinimal.h` declares nothing, so any Unreal
type reached for in the port fails to compile in the container instead of
being satisfied by a stub. Checked: `Perception.h` is the only port header
that includes `CoreMinimal.h`; the five new headers include only each other
and standard headers. The shim lives under `tests/`, off the module's include
path, so the engine build gets the engine's own header. It is the right shape.
What it cannot do is stand in for MSVC or for Unreal's compile flags, which
is section 6.

## 6. What cannot be checked here, and what a green run must not mean

Unrun until the golden job runs on his PC:

1. The six bridging lines, `LedgerProbe.cpp` 684 to 703, and the compile of
   six new headers inside an Unreal translation unit.
2. NOT ON THE BUILDER'S LIST: exceptions. `Suspicion.h` 85 to 87 throws
   `std::invalid_argument`; `CoreGolden.h` 687 to 695 is a `try`/`catch`,
   and `Evaluate` is called from `LedgerProbe.cpp` 689, so both are compiled
   into the module. Neither `LedgerProbe.Build.cs` nor `LedgerProbe.Target.cs`
   enables exceptions, and nothing else under `ue-probe/Source` uses `try`,
   `catch` or `throw` (grep: the three sites above and one comment). g++ in
   the container has exceptions on. Whether Unreal's MSVC configuration
   accepts a `try` block in a module that does not enable them is a fact
   about Jafar's PC that this seat cannot read. PRE-RULED, so the failure
   costs one round trip and not a spawn: if the build refuses, the
   `FactNull` branch of `Evaluate` is compiled out under a macro the module
   defines, the four rows count as Unknown, and the verdict prints
   `perceptionUnknownFns=4/FactNull-needs-exceptions`. NOT
   `bEnableExceptions = true`: that changes every translation unit's flags
   for the sake of a test path and moves the build number D1 exists to
   measure. The container keeps proving the four rows either way.

What a green container run must NOT be read as:

- That the module compiles. It says the port answers the C# where g++ can
  run it, and nothing about MSVC, Unreal headers, or the two items above.
- That `probeTest=PASS` means every row was answered. On the PC `probeTest`
  is `Bad == 0` (`LedgerProbe.cpp` 731) and an unknown row does not fail it.
  The reader reads FOUR keys from `production/d1-probe/ue-verdict.txt`, which
  the workflow does collect (line 535): `perceptionRows` equal to the
  container's row count after the regenerate, `perceptionMismatches=0`,
  `perceptionUnknownFns=0`, `probeTest=PASS`. A PASS at 1221 rows is a stale
  table answered from one of `FindGoldenTable`'s four candidate paths, not a
  pass.
- That the crime run's memory file will match a C# file byte for byte. Line
  for line, `\n`; section 2 deviation 4.
- That the probe feeds `Resolve` the right geometry, or that a trace hits a
  terrace. The table proves the two engines answer the same numbers the same
  way; the crime run's verdict proves the numbers were the right ones.
- That the mill's consequences fire. `SuspicionTracker` is absent at
  `Gossip.cs` 402 and 412 by the ruling and the verdict prints it.

Two silent caps, named, not blocking: `Detail.size() < 10`
(`core-port-test.cpp` 91, 99) and `Bad <= 10` (`LedgerProbe.cpp` 695, 708)
truncate the mismatch listing without saying so. The done line carries the
whole-run totals, so nothing is hidden, but `instruments.md` says a cap
announces when it bites. One line each; queue-named in section 7.

## 7. What is filed, by name, not done here

- Unicode `IsWordChar` and `ToLowerInvariant` in the port, opened the day
  `dialogue-verify.py` admits a non-ASCII line to any bank the mill reads.
- The two silent caps above, `(+N more not shown)`.
- The scenario fixture is written twice (`CoreGolden.h` 31 to 37 names the
  cost). A research task: one fixture description both emitters interpret,
  so a drift between the two builders is impossible rather than merely
  detectable.
- `Perception.Attention` ported so `RungFloor` stops being fed 0: already
  filed by the crime ruling; restated because A1's `rungFloor` case is the
  row that will change when it lands.

## 8. Before the commit the resident prints

1. `dotnet run` of `ledger/PerceptionGolden` after A1 to A3, its stderr line
   `golden rows emitted: N`, and N equal to the grep count of non-comment
   lines in `ue-probe/perception-golden.txt`.
2. `python3 -c "import verify; verify.ue_probe_tests()"` from `ledger/`,
   pasted from THAT run: `ue-probe instruments ok (M checks over 3 of 3
   binaries)` with M above 2614 by at least the rows added, and the
   per-function lines showing `observation_four` present and
   `unknown=0` on every line.
3. The two A2 rows quoted from the table with the C# answer visible, and
   the sentence "the port was changed" or "the port stands" beside them.
4. `grep -rn "couldn't swear" ledger/Assets/Scripts`: one hit, comma form.
5. `python3 ledger/verify.py` green, footer FROM `ledger/.verify-footer`; the
   cadence line names this record and row `2026-09-08T07:08:34Z`.
6. Commit message names rows 2355 and 2405 as the rule-5b red on the
   em-dash, and this record.
7. The sha captured BEFORE dispatch; the golden job dispatched on it and
   watched by ancestry; `production/d1-probe/ue-verdict.txt` opened and the
   four keys of section 6 read beside their numbers before any message is
   written. If the build refuses `try`, section 6 item 2 applies without a
   new spawn.

## 9. The ladder at close

Best available, or first working? For the method, best available: the
expectations are emitted by the original engine and neither engine's author
typed one, which is the strongest comparison this project has run between
two implementations of anything. For the coverage, first working until A1
to A3 land: a port whose named fixture is absent and whose formatter was
measured on the easy half of its domain is a first working one. The next
rung after this batch is the single-fixture generator in section 7; the rung
after that is `Attention`.

<!--RULING spawn=2026-09-08T07:08:34Z-->
