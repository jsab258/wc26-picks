# The Director's Console: Overseeing an Autonomous Agent Studio Building a Game

## TL;DR
1. The fix for "decisions buried in walls of technical chat" is not a better dashboard; it is a set of role-separated communication surfaces modeled on how film and game studios already work: review the artifact, not the report (Pixar dailies), decide from a filtered queue (the producer/Braintrust model), and demo playable builds on a fixed rhythm (Valve's weekly Friday playtest). Pair that with an SRE-style severity ladder so only genuinely blocking items reach you live.
2. Build six surfaces plus one channel: a State glance, a Needs-You decision queue (the single most important surface), a "Since you last looked" delta feed, a Show-Moment forecast, an Evidence gallery of artifacts, and a Process-Health scorecard; escalations flow through an interrupt classifier (Blocking / Decision / Review / FYI) that decides push-now vs daily-brief vs weekly-review vs never.
3. Enforce the register in Claude Code with a dedicated director-facing agent role and output styles that lead with the ask, ban technical narration, cap length hard, and link artifacts instead of describing them. The documented risk is real and quantified: more escalation is not safer, because human attention is a finite, fatiguing resource. Per arXiv:2606.08919 ("Oversight Has a Capacity"), "realized safety becomes an inverted-U in the escalation rate."

## Key Findings

1. Creative studios review artifacts, not status text. Pixar's dailies put unfinished work on screen every morning; the Braintrust gives notes on the work with no authority over the director. This is "show, don't tell" institutionalized.
2. Game studios run on a fixed demo cadence and always-playable builds. Valve playtests every Friday and lets the playtest drive the next week's work; the milestone ladder (first playable, vertical slice, alpha, beta, gold) exists precisely so a non-technical stakeholder can understand the state of the game by looking at it.
3. Production tracking tools that directors actually use (ShotGrid / Flow Production Tracking) are built around thumbnails, versions, notes and playlists, with a producer acting as the filter between the ticket swamp and the creative director.
4. Flat, producer-less structures (Naughty Dog) have documented costs: without a filter/escalation router, communication blunders, duplicative work and sign-off gridlock appear, and crunch becomes the release valve.
5. AI agent vendors have independently converged on the same answers: Devin escalates "only when blocked," uses emoji "body language" instead of chatter, gives a status chip (working/blocked/done), and delivers a PR as the unit of work. LangGraph makes human approval a first-class interrupt. MetaGPT enforces structured handoffs to kill "idle chatter between LLMs."
6. Oversight has a capacity. arXiv:2606.08919 (2026) shows that a policy that escalates more can be less safe, because a fatigued reviewer rubber-stamps; on its 125 hand-labeled adversarial actions, reviewers showed only moderate agreement (Fleiss' kappa = 0.52). Notification-batching research (Fitz et al., 2019) shows the same effect at the individual level. This is the scientific backing for pushing less, not more.

## Details

### Part 1: Real studio practice

#### Dailies and the Braintrust (Pixar, VFX)
Ed Catmull's account in Creativity, Inc. describes dailies as morning sessions where work is shown "in an incomplete state to the whole crew" for constant, constructive feedback, and where inexperienced staff receive "daily and meticulous feedback from senior directors." The defining move is that people review the actual work in progress, not a written summary of it. The Braintrust meets periodically; the director shows work-in-progress and invites candid feedback, but "the room has no authority" and the director does not have to take any suggestion. Two design lessons transfer directly:
- The unit of review is the artifact (a shot, a sequence), not a report.
- Advice and authority are separated: reviewers critique; the director decides.

The VFX/animation industry productized this in ShotGrid (now Autodesk Flow Production Tracking): review pages organized around media playback, versions, notes, annotations and playlists, with "a rich history of production information, with previous notes, versions, statuses." Directors review in a player with compare modes (Hold, Ghost, Compare) and frame-accurate notes; they do not read engineering logs. Autodesk's own materials describe burndown charts and status history as the data visualization layer, and a separate "Screening Room" for reviewing cuts.

#### Milestones and always-playable builds (game studios)
The standard milestone ladder is first playable, vertical slice, alpha, beta, gold. Practitioner sources stress that each milestone should be "something you can put in front of a publisher, investor, or even just a fresh playtest group and have them understand the state of the game without you explaining it." The vertical slice is a fully polished standalone segment representing final-quality gameplay (often a 10-15 minute segment), used as both a go/no-go gate with publishers and a proof of concept.

Valve's weekly playtest is the strongest cadence precedent. Level designers playtest every Friday; per level designer Phil Co, "Everything we do during the week is focused on that Friday playtest," and Monday meetings set the goals and owners for that test. Valve's stated philosophy from the Half-Life 2 process: "Create 15 minutes of gameplay in rough form. Playtest. Use playtest to prioritize work for next week. Repeat until complete," and "We felt done as soon as playtesting was no longer painful to watch." They deliberately use 1-2 week increments because shorter "results in not enough time to make changes" and longer "results in churn and flail." Valve's cabal is the small multi-disciplinary team owning a chunk of the game; during Half-Life 2's alpha a "Cabal Cabal" (one member from each of six teams) met daily to critique the game chapter by chapter and feed notes back, but each design cabal retained final decision authority over its own levels, another instance of separating advice from authority.

Supergiant Games shows the tiny-team version. The studio formed in 2009 with seven people and has grown to 25 today (all seven originals still on staff), and states on its own site: "We now have more than 20 people on our team ... We work on one main new game project at a time." It uses a transparent Early Access model where continuous player feedback refines story, balance and even the ending; Hades II scored 95 on Metacritic for PC, "the single highest-rated game of this year on the aggregate site" (released v1.0 September 25, 2025). Supergiant famously bans out-of-hours email, an explicit norm against always-on interruption.

#### The producer as filter and the cost of removing them
Naughty Dog historically ran without dedicated producers; leads served as both individual contributors and quasi-managers, and leadership viewed producers/managers as a "crutch" and "bureaucratic red tape." The documented cost, per a former engineering manager's analysis, is that flat hierarchies without a production filter produce "communication blunders, duplicative work, and sign off gridlock," with crunch as the recurring release valve. Naughty Dog began adding producer-style managers after The Last of Us Part II specifically to alleviate these problems. The lesson for a solo director: you must build the filter/escalation-router function into the system, because you cannot personally be both the creative director and the producer triaging every ticket.

#### Written status norms
Where studios do write for leadership, the dominant form is the one-page report: RAG (red/amber/green) status by dimension, a 2-3 sentence executive summary, accomplishments, upcoming milestones, top risks, and "decisions needed." Guidance is explicit: "Lead with the headline. RAG status first, decisions needed second, risks third." Risk registers are reviewed on a standing (typically monthly) cadence and versioned (v1.0, v1.1) to preserve an audit trail. RAG's value is that "executives do not typically read burndown charts. They read status reports."

### Part 2: AI agent oversight interfaces (2025-2026)

#### Devin (Cognition)
Devin's design is the closest existing analog to what the director wants. Its documented behaviors:
- Escalate only when blocked. When test failures are unrelated, Devin "logs them and proceeds"; only if failures "genuinely block the task" does it "surface this to you with a clear explanation."
- Status as a chip, not a transcript: a "code channel" shows "a status chip showing whether Devin is working / blocked / done," a link to the session, PR tabs, and a collapsible worklog behind each message.
- Body language over chatter: after an over-eager first version spawned a dozen redundant sessions, Cognition added a long-running triage agent per channel and made "silence an acceptable exit condition." Devin uses a 👀 emoji reaction to signal it picked something up instead of posting "on it."
- The unit of delivery is a PR, with a "PR Preview" to inspect before creation; "Hand off async work to Devin while you focus on your primary task. Review when convenient."
- Scope discipline: sessions classed L/XL are flagged "unhealthy"; docs recommend "one vertical slice per session." Devin can schedule messages to itself to check back on long-running child sessions, and a coordinator session "scopes the work, monitors progress, resolves conflicts, and compiles results" for parallel managed Devins.

Independent guidance is blunt about the review trap: a six-hour session "produces a PR sized like a week of human work, and it arrives all at once... the tests pass, the description is articulate, and the reviewer skims." The recommended countermeasure is to read the commit sequence, which reveals mid-session detours the final diff hides.

#### Claude Code (the studio's own runtime)
Relevant primitives, from Anthropic's docs and the practitioner community:
- Hooks fire on lifecycle events. SessionStart can inject context ("loads git status, recent issues, and context files"); Stop/SubagentStop can force continuation or gate completion (exit code 2 on a Stop hook "forces Claude to keep working"); PreCompact can back up transcripts. As of August 2026 the reference documents 31 hook events; nearly every production setup uses five (PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, Stop). A Notification hook can route to Slack or trigger text-to-speech.
- Headless mode (`claude -p`) with `--output-format json`, `--max-turns` and a dollar-budget cap makes Claude Code scriptable for cron jobs and unattended runs; hooks still fire in headless mode, so hook-based guardrails still apply.
- Subagents run in isolated context windows and return summaries to the parent, the mechanism for a director-facing summarizer that never surfaces raw narration.
- CLAUDE.md is durable memory read at session start.
- The Ralph loop (Geoffrey Huntley, July 2025) is the canonical overnight pattern: a bash loop spawns a fresh headless Claude Code process each iteration with a clean context window, rebuilding state from disk (task queue, progress file, git history) to defeat "context rot." Anthropic packaged an official plugin in December 2025, and built-in /loop, /goal and /batch commands now offer supported equivalents. Reported overnight results (entire features shipped, one $50,000 contract for under $300 of API cost) are anecdotal from the technique's creator, not independently benchmarked.

Note on output styles: Claude Code deprecated its built-in output-style feature; the community pattern is now to encode the equivalent director-facing register via SessionStart hooks (and migrator tooling exists for this). Verify the current mechanism at implementation time.

#### Other coding agents and the "don't read the reasoning" stance
Across OpenAI Codex, GitHub Copilot coding agent, Cursor background agents, Google Jules, Replit Agent and similar, the unit of delivery is consistently a pull request or a preview deployment for human review, and the vendor framing is "Copilot, not autopilot," suggestions "meant for review." Codex "clones your GitHub repository into a sandboxed environment, writes code across multiple files, runs your tests, and opens a pull request." The consistent supervision strategy is to review the output artifact (PR, preview, screenshot), not the intermediate token stream. Independent 2026 testing found large gaps between vendor claims and reality (one Answer.AI analysis reported a 15% success rate across 20 real-world tasks against a vendor-reported 67% PR merge rate), which argues for gating on tests and demos rather than trusting narration.

#### Multi-agent "organization" frameworks
- MetaGPT encodes standard operating procedures and role-play (Product Manager, Architect, Engineer, QA) with structured document handoffs. Its explicit design goal is to reduce "the risk of hallucinations caused by idle chatter between LLMs" by forcing structured intermediate outputs (PRDs, designs) rather than free conversation. Core philosophy: "Code = SOP(Team)."
- ChatDev simulates a full virtual software company including CEO/CTO roles.
- LangGraph is the human-in-the-loop reference: interrupt at a node, collect human input, resume from checkpoint; "you can add a human approval step between Analyze and Write with one line," and state "can persist for hours or days." CrewAI and AutoGen support human input but as a less-native pattern (CrewAI task-level input; AutoGen's human_input_mode).
- Production reliability is poor enough that oversight is the main event, not an edge case: Foundra's 2026 production reliability analysis measured a 56.6% task success rate across 6,259 deployed agents and 4.5 million runs.

#### Documented autonomous game builds
- Outpost Ulu (buildaloud.ai, ~3 weeks, started 2026-05-21): built milestone by milestone (M0-M10), "each one a thing you could actually run before the next started." The decision loop that worked: agents "come back with options. 'Here's candidate A, B, C, D. Here's the tradeoff on each. Chad picks.' That kept the human in the loop on every call that mattered without making him write the analysis himself." Work was split across narrow domain sub-agents (combat, economy, towers, enemies, idle mechanic, research), including a monetization guard whose "entire job is to veto pay-to-win... It has veto. It uses it." Everything is gated by BDD/Gherkin: frozen at "240 shipped specs hard-gating CI," grown to "93 .feature files, 698 scenarios," all run by a single command "pnpm check... One gate. Green or you don't merge," including a headless simulation matrix that runs the game forward to catch "tower X is now mathematically unkillable" before a player does. The director's stated rationale for gating instead of reading: "the model is fast and confident, and confident-but-wrong is the failure mode. A balance change that looks reasonable can quietly break a win condition three systems away." The honest failure section documents an O(N squared) per-frame render pass that had to be batched to O(N).
- Spell Cascade (dev.to/yurukusa, 5-agent Claude Code Teams studio): roles were team-lead, builder, designer, researcher, grower, shipper (6 agents on Claude Opus, completing 9 of 17 tasks in one session). Agents self-assign from a task list with blockedBy dependencies ("No human needed to coordinate"). The documented coordination failure, raised by a commenter and confirmed by the human Yurukusa, is that "one agent's output invalidates another agent's work and nobody catches it until the end"; his answer: "yes, it does happen, and we haven't fully solved it," mitigated by running only tasks with no shared outputs in parallel and by blocking on a specific "UI-stable" commit rather than "builder done." The human explicitly retains taste decisions: "I'm honestly not at the point where I'd fully trust an AI designer for game feel, UI, or UX decisions."

#### Notification, interrupt and escalation research
- Batching works. The randomized field study is Fitz, Kushlev, Jagannathan, Lewis, Paliwal and Ariely (2019), "Batching smartphone notifications can improve well-being," Computers in Human Behavior vol. 101, pp. 84-94 (n = 237); participants batched 3x/day showed lower inattention (d = -0.65) and higher concentration (d = 0.54) versus controls. Their 14-day design batched notifications at 9am/3pm/9pm and participants "felt happier, more productive and less stressed." Across the literature, alert fatigue and attention disruption, not raw frequency, are the strongest predictors of harm.
- SRE severity/paging model. Google SRE classifies events into page (P1), ticket (P2) and logging categories, triages incidents into severities 1-3 with a finite, explicit criteria set for Sev 1, and warns that frequent alerts cause responders to "second-guess, skim, or ignore alerts," including the important ones. Playbooks accompany every alert. The design principle: proportional response, alert suppression to avoid noise, and paging only for what needs immediate human action; page frequency is reviewed quarterly with management.
- Oversight has a capacity. arXiv:2606.08919 ("Oversight Has a Capacity: Calibrating Agent Guards to a Subjective, Fatiguing Human") formalizes the counterintuitive result that a guard escalating 500 actions a day can be less safe than one escalating five: "By the three-hundredth approval of a routine, benign action, a human is fatigued and primed to keep clicking Approve, so a malicious action buried deep in Guard B's stream is rubber-stamped ... Guard B has more oversight and the worse outcome." The safety-optimal escalation rate sits below "escalate everything." This is the strongest single argument for aggressive filtering.

### Part 3: Synthesis, the Director's Console

#### 3.1 The information surfaces
Build these as read-oriented surfaces generated from repo state, plus one action channel. Each maps to a documented precedent.

| Surface | What it answers | Studio / AI precedent |
|---|---|---|
| State glance | What is the studio working on right now; roadmap position; RAG health | ShotGrid status; one-page RAG report; Devin working/blocked/done chip |
| Needs-You queue | Decisions and blocks that require the director, ranked, with options | Braintrust (advice vs authority); producer escalation; "candidate A/B/C/D, you pick" |
| Deltas since last visit | What changed in the plan and why, what shipped, what broke, since you last looked | Change log with reasons; SRE "since last shift"; delta feeds |
| Show-Moment forecast | When there will be something concrete to see, with target date and confidence | Milestone ladder; vertical slice go/no-go; release calendar |
| Evidence gallery | The artifacts themselves: renders, generated assets, voice clips, playable build links | Pixar dailies; ShotGrid review playlists; "show don't tell" |
| Process-Health scorecard | Is the studio following its own constitution/process; issues and learnings | Post-mortems; SRE playbook adherence; MetaGPT SOP conformance |

The Needs-You queue is the antidote to the user's actual complaint. Decisions must live in a durable, ranked queue with a default and a deadline, never in chat scrollback. Precedent: LangGraph approval interrupts, Devin's "offers to wait for your confirmation," and the producer's job of surfacing only what needs the creative director.

The Evidence gallery is how you serve a director who will not read narration. During visually quiet phases (core simulation, save systems, refactors) the gallery would otherwise go dark, so run standing local asset and voice generation jobs whose only purpose is to keep producing gallery content (concept renders, environment shots, candidate voice lines, a headless sim replay). Precedent: Pixar shows unfinished work daily; Outpost Ulu's headless simulation matrix produced runnable evidence continuously.

#### 3.2 Interrupt classification and routing
Four classes, routed by an SRE-style policy. The classifier is a hook plus the director-facing agent; the router decides the channel.

| Class | Definition | Route | Precedent |
|---|---|---|---|
| Blocking (Sev 1) | Studio is stopped or about to do something irreversible/out-of-constitution; cannot proceed without you | Push now (phone/Slack), single message, one clear ask | SRE P1 page; LangGraph irreversible-action interrupt; Devin escalate-only-when-blocked |
| Decision (Sev 2) | A real fork with product/creative consequences; agents have a recommendation and a safe default | Batched to the daily morning brief, unless the safe default expires sooner | Braintrust; producer escalation; "Chad picks" |
| Review (Sev 3) | Something to look at and react to, no hard blocker | Weekly show-and-tell | Valve Friday playtest; dailies |
| FYI (Sev 4) | Progress, learnings, minor changes | Never pushed; lives in delta feed and scorecard, pulled on demand | SRE ticket/log tier; batched notifications |

Two hard rules from the research: (1) deny-by-default on timeout for anything irreversible (agents wait, they do not guess); (2) a strict budget on Sev 1/Sev 2 volume, because escalating more lowers the quality of every decision you make. If Blocking interrupts exceed a small threshold per week, that is itself a process-health red flag (the environment or the constitution needs fixing), exactly as SRE reviews page frequency quarterly.

#### 3.3 Cadence
- Daily glance (2-3 minutes): read the morning brief = State glance + Needs-You queue + overnight deltas + new gallery items. This is the Pixar daily, compressed to a pull-based page.
- Weekly show-and-tell (30-60 minutes, fixed day): playable build or artifact reel, the week's learnings, the process scorecard, and the plan changes with reasons. This is Valve's Friday.
- Per-milestone demo and go/no-go: at first playable, vertical slice, alpha, beta, the studio produces a demo and an explicit go/no-go recommendation; you approve continuation, redirect, or cut scope.
- Ad hoc blocking only: nothing else interrupts you live.

#### 3.4 Show moments as first-class schedule items
Treat each "first" as a scheduled deliverable with an owner, a target date and a confidence level, tracked on the Show-Moment forecast like a milestone:
- First render / first generated street / first character turnaround
- First generated ambient track / first voiced line / first full voiced conversation
- First interactive prototype / first playable loop / first playable build

Each show moment gets a definition of done that a non-technical viewer can judge by looking, mirroring the milestone rule that a stakeholder should understand the state "without you explaining it." Confidence should be reported honestly (green/amber/red), and the forecast should show what is coming in the next 1, 2 and 4 weeks. During quiet phases, the forecast explicitly lists the standing generation runs as the interim show content so the calendar never looks empty.

#### 3.5 Register for director-facing communication and enforcement
The register (the house style for everything that reaches you):
1. Lead with the ask or the headline. Decision first, then the recommended option and default.
2. No technical detail. No file names, stack traces, code, or step-by-step narration.
3. Hard length cap. A decision item fits in a few lines; the daily brief fits on one screen.
4. Artifacts over descriptions. Link the render/build/clip; never describe what a screenshot would show.
5. Options with a default. Where a decision is needed, present 2-4 options, a recommendation, and what happens if you do nothing.

Enforcement in Claude Code (framed as communication design, implemented as configuration):
- A dedicated director-facing agent (a subagent role, e.g. "Chief of Staff") is the only role permitted to write to your surfaces. Working agents report to it in whatever technical detail they like; it translates to the register. This is the producer/summarizer function made into an org role, and it mirrors MetaGPT's structured-handoff principle and Devin's per-channel triage agent.
- An output-style equivalent (a SessionStart-injected style block for that role) encodes the register (lead with the ask, banned content, length cap, artifact-link requirement).
- Hooks do the deterministic enforcement: a SessionStart hook injects the constitution, roadmap and open decision queue; a Stop/SubagentStop hook rejects any director-facing output that exceeds the length cap or contains banned technical tokens, forcing a rewrite; a Notification hook routes only Sev 1 to push. The read-only dashboard and the brief are generated from repo files (task queue, canon file, decision records, capped roadmap), so the surfaces are always a projection of real state, never hand-written spin.
- The decision queue is a file (append-only decision records), so choices are durable and auditable, never lost in scrollback, the direct fix for the user's core complaint.

#### 3.6 Anti-patterns to avoid
1. Dashboard-only. A state dashboard with no Needs-You queue and no push for blockers is what already failed the user; state without attention-routing does not answer "what needs me."
2. Escalate-everything. Contradicted by the "Oversight Has a Capacity" inverted-U result and SRE alert-fatigue findings; more pushes make you a rubber stamp.
3. Reading the transcript. The "articulate PR that passes tests" skim-trap; trust the gate and the demo, not the narration.
4. Chat as the system of record. Decisions and requests in chat scrollback get buried; this is the failure the user reported. Put decisions in a queue, artifacts in a gallery, changes in a delta log.
5. Notification flooding / no batching. Contradicted by batching research (Fitz et al., 2019); default everything below Sev 1 to pull.
6. No producer/filter role. The Naughty Dog flat-structure cost: gridlock, duplicated work, crunch. The director-facing agent is the filter.
7. Silent drift. Long autonomous runs drift from the constitution unnoticed; the process-health scorecard and a periodic self-audit are the countermeasure, and unreviewed cross-agent invalidation (the Spell Cascade failure) must be caught by the gate, not discovered at the end.
8. Empty calendar during quiet phases. If show moments are not scheduled and standing generation runs are not producing gallery content, the director loses the sense of progress; schedule interim evidence deliberately.

#### 3.7 Prioritized implementation order
1. Constitution + decision queue as files. Write the constitution/canon and start an append-only decision-records file. Everything else references these.
2. Director-facing agent + register style. Create the one role that writes to your surfaces in the register; forbid all other agents from addressing you directly.
3. Interrupt classifier + Sev 1 push. Implement the four-class routing; wire only Blocking to push (Notification hook), everything else to the brief/feed.
4. Morning brief (daily glance). Generate State + Needs-You + deltas + new gallery items from repo state at a fixed time.
5. Evidence gallery + standing generation runs. Make artifacts the primary output; keep the gallery fed during quiet phases.
6. Weekly show-and-tell + Show-Moment forecast. Fix the day; schedule the "firsts" with dates and confidence.
7. Process-health scorecard + self-audit. Constitution adherence, cross-agent invalidation checks, Sev 1 frequency, gate pass rate.
8. Per-milestone go/no-go. Formal demo + recommendation at first playable, vertical slice, alpha, beta.

## Recommendations
1. Start this week by moving decisions out of chat into an append-only decision-records file and standing up the director-facing agent with a register style that leads with the ask and bans technical detail. This alone addresses the primary complaint.
2. Implement the four-class interrupt router next and wire only Sev 1 (Blocking) to phone/Slack push. Benchmark: if you receive more than a couple of live pushes per week, treat it as a red flag and fix the environment or constitution, do not raise your tolerance.
3. Set a fixed weekly show-and-tell day and a daily 2-3 minute brief. If the daily brief cannot be read in three minutes, the register is being violated; tighten the length cap.
4. Schedule show moments as dated, confidence-rated deliverables and keep standing local asset/voice generation runs feeding the gallery so quiet phases still produce something to see.
5. Gate everything on an always-green check (tests + headless simulation) and review the demo, not the diff. Benchmark to change course: if a milestone go/no-go demo cannot be understood without explanation, the milestone is not really met.
6. Add the process-health scorecard once the daily/weekly rhythm is stable; track constitution adherence, Sev 1 frequency, gate pass rate, and cross-agent invalidation catches.

## Caveats
- Vendor claims vs reality: Devin's escalation and status design and the Ralph overnight results are vendor/practitioner claims; independent 2026 testing found large gaps between advertised and real success rates (e.g. 15% observed vs 67% reported PR merge rate), so gate on tests and demos rather than trusting reported completion.
- The autonomous game-build accounts (Outpost Ulu, Spell Cascade) are small-n, self-published, and in at least one case authored by an AI agent rather than the human; treat the specific figures as illustrative of technique, not as benchmarks. The buildaloud.ai post's "Chad" is strongly implied to be the human director but is not explicitly confirmed as such (the site brands itself as an AI-agent "build in public" project).
- Some cited numbers come from secondary summaries of primary sources (for example the Valve GDC 2009 talk quoted via level-design and postmortem write-ups rather than the original video); the substance is well corroborated across multiple accounts.
- Claude Code's hook and command surface is changing rapidly (31 hook events as of August 2026; built-in output styles were deprecated and the community migrated the capability to SessionStart hooks); verify exact event names and mechanisms against current docs at implementation time.
- The synthesis (the six surfaces, four interrupt classes, cadence and enforcement) is my recommendation built on these precedents, not itself a documented deployed system.