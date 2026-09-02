# Organization: departments, roles, models

Structure: three tiers, adapted from the donchitos taxonomy, run under our constitution. Roles are agent definition files with standing constraints baked in (never retyped in briefs). Handoffs are files in known locations, publish-subscribe style; agents never chat with each other directly (MetaGPT lesson: shared artifact pool beats direct calls).

| Department | Roles (tier) | Model class |
|---|---|---|
| Direction | Director agent (1), plus Jafar | Top |
| Production | Producer/roadmap keeper (1), watchdogs (3) | Top for audits, cheap for watchdogs |
| Engineering | Core, engine, tools, build/CI (2 to 3) | Mid; top for architecture |
| Design | Systems, economy, level (2) | Mid |
| Narrative | Lead writer (2), dialogue writers (3), brand bible keeper (3) | Mid; cheap for bulk barks |
| World | Environment, props, set dressing, interiors (3) | Mid |
| Characters | Casting (bios), rigs, voices, faces (3) | Mid |
| Audio | Radio, ambience, foley sourcing (3) | Mid; cheap for batch runs |
| Verification | Instrument runner, judges, license gate, canon gate, playtest bots (2 to 3) | Cheap first pass, mid for judges, top for audits |
| Tools/Research | Pipeline builder, external tool evaluation (3) | Mid |

Model routing law: top models only for direction, architecture, audits and hard debugging. Authoring runs mid. Mechanical transforms, first-pass verification and watchdogs run cheap. Route up only on failure, and record the escalation in the token ledger.

Escalation path: specialist to lead to director to Jafar's decision queue. Only genuinely non-technical calls reach Jafar.

---

## Carried from CLAUDE.md (2026-09-01, task 013)

The studio split in full, moved intact when CLAUDE.md was cut to standing
rules plus pointers. The one-line version stays in CLAUDE.md; this is the
reasoning, the incidents and the enforcement mechanism.

The director-cadence gate described below is live in ledger/verify.py, and the
scope correction dated 1 Sep is the operative one: the constants are
DIRECTOR_WORK and DIRECTOR_EVIDENCE in that file, and they are tested, so read
them rather than any copied list including this one.

<!-- moved verbatim from CLAUDE.md lines 1074-1231 on 2026-09-01, task 013 -->

## THE STUDIO SPLIT — WHO DOES WHAT (24 Aug, Jafar)

Decided the day the studio structure was adopted, after a day of the main
session doing builder work inline on the director's model and burning
Jafar's usage doing it. His words: *"Tier 1 should be fable, not opus.
Tier 2 and 3 should be opus"* and, on catching the non-conformance:
*"everything on fable doesn't conform to what we agreed and consumes too
much."*

- **The main session is the DIRECTOR (tier 1).** It decides, reviews agent
  diffs and reports, reads landings and stills, commits after review,
  dispatches builds, and talks to Jafar. It does NOT implement features,
  write instruments, or grind files — spawning is the default, not the
  exception. The director may hand-apply only genuinely one-line
  corrections where briefing an agent costs more than the fix.
- **Tier 2 (Opus, read-only)** — the verifiers in `.claude/agents/`
  (measurement-auditor, claim-auditor, artifact-reader, guard-tester,
  reach-auditor). Their first two sweeps found 21 confirmed findings in one
  day; run them as standing work, not on ceremony.
- **Tier 3 (Opus)** — the builders (systems-builder, instrument-builder,
  engine-specialist, content-wrangler). All implementation goes here, with
  the finding/spec in the brief and "do not commit" standing: the director
  reviews and commits.
- Agents' uncommitted work-in-progress is NOT committed under them by a
  stop-hook's nagging; the tree goes clean in one reviewed commit per
  builder report.

**THE HYBRID RESIDENT (24 Aug, Jafar: "hybrid is ok for me but we need
to be 100% sure it works"):** the resident session runs on Opus; Fable is
the on-demand `studio-director` agent. Escalation is MECHANICAL, never
judged — the director MUST be spawned at: builder-batch review before
commit, queue reordering/refill, a landing that changes a conclusion or
closes/opens an item, any verifier-vs-builder disagreement, any close-out,
anything touching premise/roadmap/CLAUDE.md. The watchdog forces a dailies
review if the agent log shows none in 12h. Enforcement has teeth:
`director_cadence` in verify goes RED — blocking the commit — when a
substantial code change (>100 changed lines under ledger/Assets/Scripts)
has no `studio-director` row in `.claude/agent-log.tsv` newer than **the
last commit that TOUCHED `ledger/Assets/Scripts`**. The spawn log is the
instrument; the verify footer carries the count into every commit message,
so the commit feed shows the cadence.

**CORRECTED 1 Sep by director ruling (game-design/decision-2026-09-01-cadence-widening-and-propview-batch.md): the scope in the sentence above is stale and is kept so it cannot be re-derived.** Since 1 Sep the gate counts pending lines across a NAMED SET of work prefixes minus a NAMED EVIDENCE LIST, and the reference instant is the newest commit that touched that set. On 1 Sep the old scope printed `0 changed line(s) ... review not required` through a full day of tools, workflow, C++ and hook work with no director review, and its freshness test was comparing against a commit 6.7 days old. The 100-line bound is inherited from the old scope and every printed line says so until a series under the new scope has been read and ruled on. The list itself lives in `DIRECTOR_WORK` and `DIRECTOR_EVIDENCE` in `ledger/verify.py`; read those, not this paragraph, because a copied list decays and the constants are tested.

**This paragraph used to end "newer than HEAD's commit", and that was
wrong** — quoted rather than deleted so the error cannot be re-derived by
the next reader who finds it plausible, which it was to everyone who read
it. Comparing against HEAD meant a docs commit, a `git commit --amend` of
a message, or CI committing its own stills invalidated a review that had
actually happened, and forced a fresh Fable spawn to re-do it. It fired
three times in one night before it was fixed on 25 Aug.

**AND A HOLE THAT IS STILL OPEN, recorded because a gate nobody distrusts
is worse than no gate: `director_cadence` is satisfied by a SPAWN, not by
a COMPLETED REVIEW.** A `studio-director` killed mid-ruling by a usage
limit — which happened on 25 Aug — still writes its row, still clears the
gate, and still leaves the batch unreviewed. Verify printed `cadence ok
... REVIEWED` over a review that reached no decision. An unattended loop
following the rules would have committed on that green. The spawn log is
an attendance register, not a review record. Two candidate fixes, neither
built: pair the row with a SubagentStop completion, or require the
director's decision record itself to be newer than the reference commit —
the second is stronger, because it tests the ARTIFACT rather than the
process and cannot be satisfied by a director that ran and said nothing.

**CLOSED THE SAME NIGHT, AND THE PARAGRAPH ABOVE IS KEPT AS WRITTEN
BECAUSE THE HOLE FIRED A SECOND TIME WHILE IT WAS BEING READ.** At
17:01Z a `studio-director` was killed by a session limit before ruling,
its row landed, and `director_cadence` went green over an unreviewed
1,800-line batch carrying eleven confirmed audit findings. The
unattended loop this paragraph predicts is the one that nearly
committed it.

**The stronger fix is built and live.** The gate now requires a decision
RECORD — `<!--RULING spawn=<ISO8601>-->` inside a
`game-design/decision-*.md`, where the stamp names a real
`studio-director` row NEWER than the reference commit, quoted verbatim
from the log. The row changes ROLE rather than losing one: still
necessary (a hand-typed date matches nothing), no longer sufficient. A
machine writes the row at spawn; the director writes the stamp as the
closing act of a ruling, and a killed director never reaches that write.
Selftest 38 -> 53 fixtures, and the refusal message names the exact
stamp to use and says **RESUME the killed director rather than restart
it** — which turned the repair from a fresh Fable spawn into one cheap
turn. Exit 3 means spawned-but-never-ruled.

**Both outcomes were watched on live data, not fixtures** — it refused
the director's own unstamped ruling, then went `REVIEWED` once stamped.
On the same tree in the same minute, HEAD's pre-change gate returned
GREEN over that same unreviewed batch. That pair is the finding.

**TWO RESIDUAL HOLES, MEASURED RATHER THAN REASONED, so nobody records
this as airtight.** A stamp naming the DEAD 17:01Z spawn clears the gate
exactly as a real one does — nothing here attests authorship. And the
resident could author a decision file outright. **Both need a person to
write a false sentence; the hole they replace needed nobody to do
anything**, which is the whole distance travelled. The rule that keeps
it honest is procedural and was followed the first night: **a resident
never stamps the director's ruling — that is the spawn-row hole with
better manners.**

**AND THE WATCHDOG STILL HAS THE ORIGINAL HOLE.** Its DAILIES CHECK
reads *"if no `studio-director` row in the last 12 hours, spawn"* — a
ROW, which is attendance. Director-ruled 25 Aug: it moves to the same
artifact test, implemented by CALLING the commit gate's parse rather
than growing a second copy of it. One idea, one implementation.

**WHAT COUNTS AS ONE BATCH — AND MINIMISING FABLE (25 Aug, Jafar:
"have we actually been minimizing fable usage now (no more than
necessary)? fable has its own usage limit and counts double against the
full weekly limit").** Measured before answering: **9 `studio-director`
spawns out of 36 agents in one night, ~25%**, roughly 0.9M Fable tokens
and ~1.8M at double weighting. The honest answer was no. The triggers
were not the problem — trigger 1 says "builder-batch review before any
commit of builder work" and **nobody had ever defined how big a BATCH
is**, so each agent's output was treated as its own. Director ruling,
same day:

- **A batch is all builder work landing in ONE reviewed commit**,
  accumulated to a natural boundary and capped at one dispatch cycle.
  **Red fixes never wait for a batch.**
- **Every commit containing builder work still needs a director row**, so
  splitting a batch cannot dodge review. `director_cadence` comparing
  against the last commit that TOUCHED `ledger/Assets/Scripts` (not HEAD)
  is ratified as the mechanism — before that fix, a docs commit or CI
  committing its own stills invalidated a valid review and forced a fresh
  Fable spawn.

  (Since 1 Sep the reference is the last commit that touched the REVIEWED SCOPE, a named set wider than `ledger/Assets/Scripts`. The mechanism is unchanged; the set moved. See the correction above.)
- **Verifier first, director second.** Anything whose content is
  claim-checking goes to a tier-2 Opus verifier; the director is spawned
  with the verified position and spot-checks the verifier's citations.
  Fable is for DECISIONS — premise, tier conflicts, scope, the
  quality-ladder call. The review that produced this rule named itself as
  the counter-example: its own A-D were tier-2 work sent to tier 1.
- **One decision, one spawn.** Fold pending questions into the next
  mandatory spawn. **A killed spawn is RESUMED, never restarted** — one
  review cost two spawns on 25 Aug when a usage limit killed it mid-ruling.

The six mandatory triggers are unchanged and are not relaxed by any of
this. `director_cadence` prints the spawn count and the Fable share into
the verify footer, which rides into every commit message, so the drift is
visible in the commit feed without anyone remembering to look. It is
DELIBERATELY NOT GATED: there is no landed series yet, a bound set from
one night would be invented, and a gate here would block reviews that
were legitimately needed.

**REPORTING — HIGH LEVEL AND JUDGMENT, 24 Aug, his words: "don't need
details, but high level info and judgment".** Not a status dump: what
changed at the level a person cares about, and THE ASSESSMENT — is it
closer, is it working, what do I think. Facts he can check are welcome;
lists of what was done are not. When Jafar asks for an update — any wording —
he gets the compact shape: one plain line each for Visual, Voice, Rest of
roadmap (what changed, what is next, anything needing him), plus a current
frame when the street looks different. Simple terms, no shas, no metric
names. Between his asks: nothing on a clock (the 22 Aug rule stands), and
his independent heartbeat is the branch's commit feed — if pushes are
flowing, work is flowing.
