<!--RULING spawn=2026-09-10T15:21:09Z-->
# Ruling: model routing, four tiers, 2026-09-10

> **STATUS: LIVE, verified 2026-09-10.** The routing table in section 2 is the
> standing reference every `.claude/agents/*.md` must match; wrong is a bug.
> Jafar's ruling and amendment of 2026-09-10 are quoted verbatim in section 1.
> Director spawned 2026-09-10T15:21:09Z, `.claude/agent-log.tsv` line 529, the
> newest `studio-director` row; the last commit in `.git/logs/HEAD` (line 617)
> is epoch 1789052372, which is 14:59:32Z the same day, so the row is newer.

## 0. What was read, what was not run

No shell in this seat: read, grep and search only. Nothing below came from
running `spawn-cost.py`, `verify.py` or `git`. Every number is the brief's or
a hand tally off a file read whole this session, and section 8 makes the
resident print each one before commit.

Read whole: the 15 agent definitions and the README; `.claude/agent-log.tsv`
(529 lines); `.claude/agent-turns.tsv` (189 rows); `tools/spawn-cost.py`; both
spawn hooks; `production/token-ledger.md`; organization.md 1 to 60; CLAUDE.md
166 to 195; verify.py 3255 to 3287, 3693 to 3708, 1612 to 1649; docs-check.py
112 to 190. Documented subagent model resolution (code.claude.com/docs/en/sub-agents):
frontmatter `model:`, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model;
aliases `sonnet`, `opus`, `haiku`, `fable`, a full ID, or `inherit`; a
per-invocation parameter exists.

**Premise check.** A process ruling; nothing touches Meridian, the era, the
moat or the visual bar. Section 0 of CLAUDE.md moves intact. **Correction
confirmed by grep:** twelve of fifteen definitions carry `model: opus`, not
thirteen (`^model:` over `.claude/agents/`: 15 hits, 12 opus, 2 fable, 1 sonnet).

## 1. The ruling being applied, verbatim

Jafar, 2026-09-10: "Model routing is enforced, not advisory. Every role carries
its model in its definition and a spawn cannot override it upward without a
written reason. Fable: the resident, the studio director, the Producer,
reviews, and simulation changes to the Core or the port. Sonnet: builders of
code, content and art, research, and the world designer. Haiku: mechanical
work, archive moves, greps and sweeps, formatting and docs checks, selftest
runs, gathering for the brief, queue bookkeeping, and the thirty-minute
trigger's idle check. Escalation: a lower-tier agent that fails a task twice
escalates one tier with the failure attached, never straight to Fable."

Amendment, same day: "Four tiers, not three; Opus was my omission. Fable: the
resident, the studio director, the Producer, reviews, and simulation changes
to the Core or the port. Opus: engine and Core builders, the Unreal C++, the
port, the engine instruments. Sonnet: content, art, research, the world
designer, ordinary tools and gates. Haiku: mechanical work, archive moves,
greps and sweeps, formatting and docs checks, selftest runs, gathering for the
brief, queue bookkeeping, and the idle check of the recurring trigger once it
exists on ledger. Enforcement: verify refuses any agent definition whose model
is not one of the four; the spawn log gains a model column; an upward override
carries a written reason in that row or is refused. Measurement: turns and
spawns per tier in every brief, the two meters side by side on Sunday; points
are mine and are not estimated. The test is unchanged: the Fable meter below
the total meter within a week."

Tier order, for "upward" and "one tier": haiku < sonnet < opus < fable. The
amendment settles the engine-specialist, the points question and the spawn-log
column; those are applied, not re-argued.

## 2. The table

Cost column: stop rows in `.claude/agent-turns.tsv`, hand-tallied; the median
is of per-stop readings and is biased upward for resumed agents (section 7).
"nothing measured" is a role with no stop row since the hook was registered on
2026-09-03. Spawn counts are rows in `.claude/agent-log.tsv` by grep.

| agent | today | ruled | measured (stop rows / median turns) | reason |
|---|---|---|---|---|
| producer | fable | **fable** | 21 rows: 18 fable median 8, 3 ran opus | named: the Producer |
| studio-director | fable | **fable** | 48 rows: 30 fable median 13, 18 ran opus median 20 | named: the studio director |
| systems-builder | opus | **opus** | 7 rows, median 78 | "Core builders". A brief whose deliverable changes simulation behaviour in Core goes UP to fable for that spawn (section 4) |
| engine-specialist | opus | **opus** | 53 rows, median 63 | "engine builders, the Unreal C++, the port". A port simulation change goes UP to fable for that spawn |
| instrument-builder | opus | **opus** | 35 rows, median 79 | "the engine instruments": probes compiled into a build that does not compile locally, the silent-failure class. An ordinary python tool or verify gate routes DOWN to sonnet per spawn, no reason needed. The default is the side whose forgotten override is silent |
| content-wrangler | opus | **sonnet** | 5 rows, median 49; 29 spawns | content and art fetch; the fetch pipelines are ordinary tools |
| world-designer | opus | **sonnet** | 9 rows, median 138; 10 spawns | named. The 09-08 ruling (`decision-2026-09-08-the-lookup-that-lied-and-the-art-line-in-house.md` line 239) already dictated sonnet; line 5 of the file still reads opus, so a ruled edit to a model line went unapplied and nothing could see it |
| dialogue-writer | sonnet | **sonnet** | 1 row, 12 turns; 2 spawns | content |
| planner | opus | **sonnet** | 2 rows, 36 and 19 | authors briefs, which is authoring (organization.md line 18: authoring runs mid). The premise check on its output is the director's, at review. Not queue bookkeeping, which is moving cards |
| integrator | opus | **haiku** | 0 spawns in 528 rows | applies gates and merges or rejects with the gate's own text; never fixes (its definition, lines 10 to 15) |
| reach-auditor | opus | **haiku** | 0 spawns in 528 rows | "greps and sweeps" are his words; the four sweeps are greps against a documented trap list; ranking by value returns to the director |
| guard-tester | opus | **haiku** | 0 spawns in 528 rows | "selftest runs" are his words; the output is five evidence lines a reader checks, and a missing line is the finding |
| artifact-reader | opus | **sonnet** | 8 spawns, 0 stop rows: nothing measured | judges a frame against a gate and proposes the measurement: judgement, neither a sweep nor a review of a diff |
| claim-auditor | opus | **sonnet** | 0 spawns in 528 rows | judges whether code falsifies a sentence; sweep 2 (negative claims) is a pure grep and is the named rung down (section 9) |
| measurement-auditor | opus | **sonnet** | 12 spawns, 0 stop rows: nothing measured | judges whether a number is the statistic its name claims. The arguable case; ruled in section 3 |

Nine definitions change (content-wrangler, world-designer, planner,
integrator, reach-auditor, guard-tester, artifact-reader, claim-auditor,
measurement-auditor); six stand. Result: fable 2, opus 3, sonnet 7, haiku 3.
The cadence gate's fable set (`_cadence_fable_agents`, verify.py 3255) stays
{producer, studio-director}; its spend reading does not move.

**Three routing surfaces outside the 15, ruled so they are not invented later:**

- **`general-purpose`**, the harness's built-in: 18 spawns, 8 stop rows, 723
  turns (6 on sonnet 2026-09-07, 2 on opus 2026-09-10). No definition, so it
  inherits the main model or the environment. Ruled: its declared model is
  "none", every spawn of it is upward and needs a section 4 reason, and the
  resident does not spawn it for work a defined role covers.
- **Jafar's Haiku list has no home.** Archive moves, greps, docs checks,
  selftest runs and queue bookkeeping are done INLINE by the resident, on
  Fable: the largest lever on his test, and no file in the table moves it.
  Queue item, section 9: mint `clerk` at haiku carrying his Haiku list as its
  scope. "Gathering for the brief" is `tools/producer-day.py`, no model call;
  the recurring trigger's idle check does not exist on ledger yet (grep idle,
  thirty, "30 min" over `.claude/hooks`, `tools`, `.github`: no trigger) and
  is haiku when it does.
- **Direct `--model` flags outside agent files:** `.github/workflows/tier2-generate.yml`
  lines 71 and 147, both `claude-sonnet-5`, both content generation. On the
  Sonnet line. Any new one is a routing surface and gets a ledger row.

## 3. Question 2: the word "reviews"

Two readings. (A) Every verification is a review, so the five tier-2 roles
are Fable. (B) A review is the Fable-tier reading of a builder's work before
it is committed or reported: the resident reviewing diffs, the director's
batch review, the verdict on a verifier-builder disagreement.

**Ruled: (B).** The evidence is textual, because the question is what a word
means in this studio:

1. CLAUDE.md line 171 gives the director "reviews builder diffs"; line 174
   calls tier 2 "the verifiers". The word he reads daily for the five roles
   is "verifier", and he did not use it.
2. His Haiku line names the verifiers' own tasks, "greps and sweeps" and
   "selftest runs", the reach-auditor's and guard-tester's definitions in
   four words. Those tasks on Haiku and the roles doing them on Fable would
   contradict each other; (B) does not.
3. organization.md line 18, approved and not revoked: first-pass verification
   cheap, judges mid, audits top. (B) is that law in his vocabulary; (A)
   deletes its first two rungs.

So the verifiers route by what they do: sweeps and runs to haiku
(reach-auditor, guard-tester), judgement to sonnet (artifact-reader,
claim-auditor, measurement-auditor). None is fable by role. A verification
whose result gates a conclusion put to Jafar may be spawned up as a `review`
under section 4, reason written.

**The resident's recommendation, route down and let escalation carry failures
up, is taken for the assignments and corrected in its reasoning.** Escalation
catches a LOUD failure: a builder whose tests go red twice. A verifier's
characteristic failure is a false clean, which does not fail twice; it is
never seen. Tier does not change that: the verifiers ran on Opus and the three
visual faults in the artifact-reader's own definition were each found by a
person. What makes a verifier's failure visible is the denominator on every
report and CLAUDE.md's rule that every finding gets the director's cheapest
decisive measurement, both of which already bind. The safeguard added here is
a series, not a tier (section 7).

**measurement-auditor, the arguable case.** For opus: instruments are the
quietest fault class and it audits their arithmetic. For sonnet: its output is
accusations anchored to a file:line with the command that settles them
(definition lines 16 to 19), the director adjudicates with that command, and
organization.md puts Verification at cheap first pass and mid for judges.
Ruled sonnet: the instrument of correctness is the director's measurement of
each accusation, not the auditor's tier, and a top-tier verifier at a 35-turn
ceiling is exactly the long spawn his test wants off the top meters. If the
section 7 series shows confirmed findings per spawn fall against the Aug 25
to 26 baseline (12 spawns; "21 confirmed findings in one day", organization.md
line 54), the first escalation is to opus with the series attached, by
section 4, not by re-arguing this page.

## 4. Question 3: how a role and a task coexist, and what a reason is

**The definition carries the role's default. A spawn may deviate per task.
Downward is free and recorded; upward is recorded with a reason or refused.**
The legitimate upward reasons are exactly the task classes Jafar named, plus
his escalation rule. Nothing else is a reason. The reason is one token, no
spaces, in the spawn-log row:

    up:<class>:<evidence>

| class | target | evidence that resolves |
|---|---|---|
| `simulation-core` | fable | a path under `ledger/Assets/Scripts/Core/` in the diff or tree |
| `simulation-port` | fable | a path under `ue-probe/` in the diff or tree |
| `review` | fable | a queue item `queue/NNN` or a `game-design/decision-*.md` path that exists |
| `core-builder` | opus | a path under `ledger/Assets/Scripts/Core/` |
| `unreal-cpp` | opus | a path under `ue-probe/` |
| `engine-instrument` | opus | the probe's path under `ledger/Assets/` or `ue-probe/` |
| `engine` | opus | a path under `ledger/Assets/` or a workflow under `.github/workflows/` |
| `escalation` | exactly one tier above the failed spawns | two `when` values of rows in `.claude/agent-log.tsv` with the same agent and a model one tier below the target |

**Sufficient means all of:** the class is in this table; the class permits the
target tier (`review` cannot justify opus, `engine-instrument` cannot justify
fable); the evidence resolves (the path exists at HEAD or in the uncommitted
diff, the queue item or record exists, the two spawn rows exist). "Never
straight to Fable" is the escalation row: fable is reached only from two
failed opus spawns. **Refused by name:** an empty reason, a full stop, prose
("hard task", "see brief"), a class with no evidence, evidence that does not
resolve, a class not permitted for the target, an escalation skipping a tier.

**"A simulation change to the Core or the port"**, for the two opus builders
whose default is opus while this class is fable: a change that alters
behaviour the CoreTests or the port's golden table assert (who perceives,
remembers, says or suspects what), as against an instrument, a comment, a
wiring or call-site change, a test, or rendering, import and build work. When
the resident cannot tell, it is a simulation change: a wrong up-route costs
turns on a meter; a wrong down-route on the moat is invisible.

**Where else the reason lives.** `production/token-ledger.md` already exists
for this ("escalations (task, from, to, why)", one row, 2026-W36, "none yet"),
named by organization.md line 18 and operations.md line 41, parsed by no tool
(grep `token-ledger` over py, sh, yml, json: 3 dashboard readers of the path).
It stays the weekly human roll-up; the spawn-log row is the record of fact,
because the ledger stayed empty through 27 measured deviations (section 7).

## 5. Enforcement, precise enough to implement

Today nothing validates the value: `ledger/verify.py` 3282 to 3286 reads the
first `model:` line in the first 20 lines and asks one question, equality with
`fable`. Every other string, including `opus`, a typo and a missing line, is
"not fable". Measured consequence: declared and ran models disagree in 27 of
181 definition-bearing stop rows (section 7), recorded and explained by nothing.

**E1. The definition lint**, in verify.py beside `_cadence_fable_agents` (one
reader of `model:`, not two). For every `*.md` under `.claude/agents/` whose
first line is `---` (frontmatter present; the README has none and is counted
as `nonAgent=1`, never refused and never silently skipped):

- exactly one line matching `^model:` inside the frontmatter; zero is refused
  ("no model line", which the harness treats as inherit, the invisible
  override); two or more is refused ("duplicate model line");
- the value is the text after `model:` with leading and trailing whitespace
  removed, compared BYTE-EXACT to one of `fable`, `opus`, `sonnet`, `haiku`.
  `Opus`, `claude-opus-5`, `inherit`, `haiiku` and the empty string are each
  refused by name: the harness's alias matching is not known to be
  case-insensitive, and a value it does not recognise falls through silently;
- the footer prints `agentFiles=15 onList=15 offList=0 noModel=0 dupModel=0 nonAgent=1`.

Rule 5b: the live tree after the nine edits is the accepting case; the
rejecting fixtures are synthetic files carrying `model: opus ` with a trailing
space (accepted: whitespace is stripped), `model: Opus`, `model: inherit`,
`model: claude-opus-5`, no model line, two model lines, each refused with its
filename in the message.

**E2. The spawn-log column.** `.claude/agent-log.tsv` line 1 becomes
`when	agent	model	reason	agentId`; the 528 existing two-column rows are never
rewritten (append-only, rule 5) and every reader counts them as
`preRuling=528`, their own bucket, never padded. `agentId` is my addition to
his column: the join key to `.claude/agent-turns.tsv`, without which the
declared-versus-ran comparison is by time window, which the 09-08 ruling had
to do by hand. The SubagentStart hook (`log-agent.sh`) writes:

- `model`: the per-invocation model if the SubagentStart payload carries one
  (MEASURED FIRST, off `/opt/claude-code/bin/claude` the way `spawn-cost.py`
  established the Stop payload; a field the hook cannot see is not invented);
  else the model named in `.claude/spawn-intent` when that file names this
  `agent_type`; else the declared model read from `.claude/agents/<agent_type>.md`;
  `none` for a built-in with no definition;
- `reason`: `default` when model equals declared; `down` when below; the
  `up:` token from `.claude/spawn-intent` when above. The intent file is one
  line, `agent=<type> model=<tier> reason=<token>`, written by the resident
  immediately before the spawn and deleted by the hook that consumes it. An
  `up` with no intent file writes `up:MISSING`, never nothing.

Readers checked: verify.py 3701 to 3708 takes columns 0 and 1 only, so the
cadence census is unaffected; `spawn-cost._spawn_rows` counts lines;
`.claude/hooks/selftest.sh` line 148 writes the old header into a fixture and
is updated in the same change.

**E3. Where the refusal happens.** Certain: the commit gate. verify goes red
on any row whose model is above declared and whose reason fails section 4,
quoting the row. Measured, not assumed: whether this harness honours a
blocking exit from a SubagentStart hook; if it does, the hook refuses
`up:MISSING` before the spend, and if not, the row is the evidence of an
unreasoned spend and the commit is what is refused.

**E4. The routing reader**, `spawn-cost.py --routing`: per agent, declared
(the file), intended (agent-log model column), ran (turns-log tier), and each
disagreement with its denominator: `intendedUpNoReason=0/N`,
`ranNotIntended=0/N` (a harness deviation: environment variable, fallback or
the main model), `preRuling=528`. Rows before the landing commit compare
against the "today" column of section 2, which this record preserves for it.

**E5. When the word "enforced" may be used.** Until E1 prints its footer and
E2 to E4 print theirs on a real spawn, the Producer says "routing ruled and
applied; enforcement queued", never "enforced". Rule 6: built is not running.

## 6. Question 5: CLAUDE.md, the studio split

Tier and model are now different axes, so the parentheticals on lines 173 to
176 are wrong rather than stale. Dictated text for the resident; this seat has
no Edit tool and will not rewrite a file the goal-block check reads
byte-exact. Replace lines 171 to 176 with:

> The main session is the DIRECTOR (tier 1): it decides, reviews builder diffs,
> commits, dispatches and writes the record. It does not implement or address
> Jafar: it talks to files and the Producer. Tier 2 (read-only) are the
> verifiers, tier 3 the builders: all implementation happens there, the finding
> in the brief, a standing instruction not to commit. Each `.claude/agents/`
> definition carries its model; a spawn above it needs a written reason
> (2026-09-10).

and replace lines 190 to 191 with:

> Reasoning and incidents: `ledger-v2/studio-v2/organization.md`.

Arithmetic, hand count with `len(text.split())` semantics: the paragraph was
67 words and becomes 73; the pointer was 8 and becomes 4. Net +2 on a file the
brief reads at 1996 of 2000; expected footer `CLAUDE.md 1998/2000 words`. If
the one-rules-file fold (ruled earlier today) lands first, the same two edits
apply to the same paragraph, which that ruling leaves unchanged.

## 7. Measurement: what the brief reports, and two instrument faults

**Every brief carries**, per tier, from `spawn-cost.py`: spawns as DISTINCT
agents, turns as last-wins per agent, median and total, coverage (stop rows
over spawn rows), and E4's two disagreement counts. **On Sunday** the Producer
sets Jafar's two meter readings beside the week's turns per tier. The readings
are his, typed by him into the inbox; the studio never derives, estimates or
projects a point, and a Sunday without his readings prints "meters: not
supplied". This is already the register's law: `tools/producer-check.py` 744
to 751 requires "sessions, not points, measured" (ruled 2026-09-05).

**Fault 1, found reading the series: stop rows are cumulative.** The same
`agentId` appears in several rows with monotonically growing turns:
`a604e4c5cec99a16b` (world-designer) at 156, 164, 175, 181;
`a60a32b7822c76c23` (general-purpose) at 45, 68, 83, 105, 122, 162;
`a1b7c0a31a52f329f` (engine-specialist) at 47, 60, 63, 69, 78. Seventeen ids
repeat, 44 rows for 17 agents. `read_transcript` counts distinct message ids
over the WHOLE transcript at each stop, so a resumed agent is counted once per
stop, and `tier_line` sums every row. Hand tally of the re-counted turns: 2000
of 10,407 summed (fable 561 + opus 8667 + sonnet 1179), about 19 percent;
distinct agents 162, not 189. My fable (561) and sonnet (1179) tallies match
the tool's printed totals exactly, which validates the reading. Fix, queue
item: dedupe per agentId last-wins, print `stopRows=189 distinctAgents=162
resumed=17`.

**Fault 2: `KNOWN_TIERS` (spawn-cost.py line 78) is `opus, fable, sonnet`.** A
haiku tier with no rows therefore prints nothing rather than "nothing
measured", the case the constant exists for. Becomes the four.

**The 27 deviations, hand-tallied** (declared from today's files, ran from the
tier column): 18 `studio-director` and 3 `producer` rows ran opus against
`fable` between 2026-09-08T23:22Z and 2026-09-10T09:54Z (544 turns); 6
builder rows ran sonnet against `opus` on 2026-09-07 between 10:34Z and 21:48Z
(582 turns). No `+mixed` marks, so each ran one model throughout. No record
under `game-design/` or `production/NOW.md` explains either window (grep "on
opus", "tier=opus", "fallback": the one hit is the 09-08 reading of a
content-wrangler row), and the token ledger has no row. The documented
resolution order offers two mechanical causes, `CLAUDE_CODE_SUBAGENT_MODEL`
in the session environment or a per-invocation parameter, and the record
cannot tell them apart. E2 and E4 are what would have.

**The verifier series.** Per verifier, per month: spawns, findings filed,
findings confirmed by the director's measurement, findings refuted. Baseline:
2026-08-25 to 26 on opus, 12 measurement-auditor and 8 artifact-reader spawns.
Printed before any tier is moved back up, per rule 2.

## 8. Conditions the resident prints before the commit

1. `grep -n '^model:' .claude/agents/*.md` after the nine edits: 15 lines,
   2 fable, 3 opus, 7 sonnet, 3 haiku, matching section 2 by name.
2. E1's footer on the live tree, then the six rejecting fixtures each refused
   with the filename, then the live tree green again.
3. The SubagentStart payload's field list, read off the binary, pasted: does
   it carry a model or an agent id. E2's hook shape follows from it.
4. One real spawn after E2 lands: its row pasted, five columns, and the
   matching turns-log row by agentId.
5. E4's first report on the live logs: `preRuling=528`, the 27 deviations
   listed under `ranNotIntended` (pre-ruling, history, not red),
   `intendedUpNoReason=0/N`.
6. `spawn-cost.py --report` after the dedupe: `distinctAgents`, `resumed`,
   per-tier `turnsTotal` before and after, side by side.
7. The CLAUDE.md footer with N under 2000; `tools/goal-block-check.py` green;
   `tools/docs-check.py` green, this file LIVE and under 400 lines.
8. Formatting law on this file and the edited agent files: em-dash count 0
   beside the line count.
9. Cadence numbers: rulingStamps, rulingFresh, rulingStale, rulingUnmatched.
   This stamp lands FRESH.
10. `production/token-ledger.md` gains a 2026-W37 row carrying condition 5's
    counts.

## 9. Quality ladder at close

The first working result. The rungs above it, named:

- **`clerk`, haiku.** A role carrying Jafar's Haiku list verbatim as scope,
  spawned by the resident for archive moves, greps and sweeps, docs and
  formatting checks, selftest runs and queue bookkeeping. The resident's
  inline mechanical work is the largest Fable spend no file in section 2
  touches; the series is the resident's own turns before and after.
- **Split `instrument-builder`** into the engine-probe half (opus) and a
  `tool-builder` (sonnet) once E4 prints how many of its spawns touched only
  `tools/` or `ledger/verify.py`. A role overridden on most spawns has the
  wrong default; the number decides.
- **claim-auditor sweep 2** (negative claims, pure grep) to haiku as its own
  sweep, once the verifier series exists.
- **Hook-time refusal** (E3), if the harness honours it: one spawn measures it.
- **The rule-held test**, still blank from the 09-02 ladder: a session shown
  to have read a rule and broken it. Research task.

## 10. Landing

Filled by the resident with printed numbers, one line per condition 1 to 10,
then Jafar's Sunday readings in his words. Empty until then.
