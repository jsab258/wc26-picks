# Director's Console, step 1 report

STATUS: LOG, 2026-09-03. Read-only survey. Nothing was built, no builder or
director was spawned, and nothing changes until Jafar approves.

COST OF THIS REPORT: one resident session, no spawns, roughly half a point
against the 20 remaining to the ceiling. Stated because the brief asked for
the number rather than for reassurance.

## a. The ten items against what is actually here

**1. Role split: PARTIAL, and CONTRADICTED.** The studio-director agent exists
and is the binding decision-maker between agents, as the brief says. The
Producer does not exist. The contradiction is in CLAUDE.md line 169: the
resident is defined as the role that "commits, dispatches builds and TALKS TO
JAFAR". The brief reassigns that last clause to a role that does not exist
yet, so this is a CLAUDE.md change, which is itself a director trigger. Naming
it, not resolving it.

**2. Evidence layering law: MISSING.** The constitution has eleven laws. Law 1
is "a claim without an instrument decays". There is no beside-versus-behind
distinction anywhere; every surface built here puts evidence inline by
default, which is exactly the diagnosis the brief makes.

**3. Producer register: MISSING, with the machinery to check it already
present.** No register, no word cap, no banned-token list for Jafar-facing
text. But `tools/slopcheck.py` already runs 19 patterns over 4967 strings and
the formatting law is mechanically enforced, so a register check has a working
precedent to copy rather than a new mechanism to invent.

CONTRADICTION WORTH SETTLING BEFORE BUILDING: item 3 caps a message at 120
words and item 2 puts evidence one tap away. In chat THERE IS NO TAP. A
Producer message in this window can only link out or say less. Either the
Producer's chat messages carry a link to the console, or the register's
promise of layered evidence does not apply in the channel Jafar uses most.

**4. Interrupt classes: MISSING as classes, present as instinct.** NOW.md has
"what waits on Jafar" and the dashboard counts a decision inbox, but nothing
classifies by blocking, decision, review or FYI, and nothing routes by class.
The "more than two Blocking pushes a week is a process fault" rule has no
counter to read.

**5. Telegram: ABSENT ENTIRELY, and it cannot be tested here.** No Telegram
anywhere in the repo. `tools/pc-request.py` and `tools/pc-watcher.py` are the
existing PC channel and are the nearest working thing. Two facts the brief
should absorb: every external host is blocked from this container, so the bot
runs on the PC and its first real run on Jafar's machine is its accepting case,
exactly like every .bat here. And the brief says "no n8n" while n8n appears in
`ledger-v2/studio-v2/runner.md`; naming that, not resolving it.

**6. Decision queue: PARTIAL, and the brief names one of two systems.**
`game-design/decisions-pending.md` is the inbox the dashboard already reads.
But decisions also live in `ledger-v2/respec/decision-register/` as D1 to D13,
which is where D13 landed this morning. Replacing the inbox without saying how
it relates to the register would leave two homes for one idea.

**7. Dashboard glance: PARTIAL.** The audit view exists and has Decision inbox,
Phases, Queue, In flight, Budget, Gates, Verification and a full derivations
table. The five-second glance does not exist. Demoting the audit view is
cheap; the glance is new.

**8. Health panel: PARTIAL, and better supplied than the brief assumes.** The
weekly process audit is `production/queue/900-process-audit.md`. Lessons and
terminations live in `learning.md`. And the studio-versus-game split is ALREADY
MEASURED: the verification footer prints `gameShareDay=4/7`, how many spawns
built the game rather than measuring or reviewing it. Blocking pushes is the
only input with no source.

**9. Show moments: MISSING as rows.** roadmap-v2 has phase rows with gates, not
dated confidence-rated show moments. "First textured Unreal street" is one
unconnected pin away and would be the first row. The standing local generation
line exists as queue 039 and the free lane, so that half is real.

**10. Cadence: PARTIAL, and one piece of it is already a queue item.**
budget.md carries the ceiling, the Monday 14:00 CEST reset and four stop
conditions. "Land clean at the ceiling, park with state, sleep to Monday" is
not written. CONTRADICTION: the watchdog fires hourly and would keep waking a
sleeping studio; that is already queue 026, "watchdog backs off during a stop".

## a2. What the research changes, read after the survey

The report arrived mid-survey and it moves one of my answers.

**IT RANKS THE PRODUCER ROLE SECOND AND I RANKED IT EIGHTH.** Its
recommendation 1 is to move decisions into a file AND stand up the
director-facing agent, and it says "this alone addresses the primary
complaint". I ranked the role low because it needs a CLAUDE.md change, which
is a governance cost, not because it lacks value. The research is right that
the register cannot be enforced while the role that must obey it is the same
role that wants to explain itself. My revised order below moves it to second.

**IT NAMES THE THING I BUILT YESTERDAY AS ITS FIRST ANTI-PATTERN.**
"Dashboard-only. A state dashboard with no Needs-You queue and no push for
blockers is what already failed the user." I published a live dashboard
yesterday and it has a decision inbox that counts but never pushes. Building a
better dashboard was the wrong instinct and the report says so plainly.

**IT SUPPLIES THE EVIDENCE FOR PUSHING LESS, which I would otherwise have
argued as taste.** arXiv:2606.08919 finds realized safety is an inverted-U in
the escalation rate: a guard escalating five hundred actions a day can be less
safe than one escalating five, because by the three-hundredth approval the
human is a rubber stamp. Its reviewers agreed only moderately with each other
(Fleiss kappa 0.52). Plus the batching field study, Fitz et al. 2019, n=237,
where three-times-daily batching lowered inattention (d=-0.65). So item 4's
"more than two Blocking pushes a week is a process fault" is not a
conservative guess; it is the shape the evidence predicts.

**IT INDEPENDENTLY REACHES MY REGISTER POINT.** Its register rule 4 is
"artifacts over descriptions, link the render, never describe what a
screenshot would show". I wrote the same objection before reading it: cap the
words and REQUIRE the link, or the cap teaches vagueness. Two routes to one
conclusion is the strongest form this gets.

**ONE IMPLEMENTATION FACT THAT CHANGES HOW ITEM 3 IS BUILT.** Claude Code
deprecated built-in output styles; the register now goes in a SessionStart
hook, and the mechanical check goes in a Stop or SubagentStop hook that
rejects over-length or banned-token output and forces a rewrite. This project
already runs five hook events, so the machinery is present rather than new.

**AND A CAVEAT IT IS HONEST ABOUT, which I will carry:** the autonomous
game-build accounts are small-n and self-published, one of them written by an
agent rather than a human, and vendor completion claims diverged sharply from
independent testing (15 percent observed against 67 percent reported). So the
technique transfers; the numbers do not.

## b. What I would do differently, and why

**The register cap should be a floor on evidence, not only a ceiling on
words.** 120 words is easy to satisfy by saying less rather than by layering.
The check that would actually change my behaviour is: every claim in a
Producer message resolves to an artifact the console can open. Cap the words
and require the link, or the cap teaches vagueness.

**Silence needs a heartbeat somewhere Jafar does not have to read.** Item 3
makes silence an acceptable exit, which is right. But this morning's failure
was a run that never started, and I explained its slowness for an hour. Under
the Producer register that hour is silent. The console needs a liveness row
that Jafar never has to look at and that goes amber on its own.

**Blocking pushes should count themselves from the start.** Item 4 sets a
threshold of two a week with nothing counting. Ship the counter before the
threshold, which is this project's own rule 2.

**One thing I would not change:** the decision to keep evidence inline on
agent-facing surfaces. Today's diagnosis of the grey street came from reading
nine keys in a row. Thinning that surface would cost more than it saves.

## c. Proposed order, with points

Estimates are calibrated from the measured cost of a builder spawn plus its
review, 3 to 4 points, and this session's own overhead. 20 points remain to the
ceiling and 97 hours to the Monday reset, so the whole console does not fit
before Monday and the order matters more than the total.

    1  item 6, decision queue, one file the bot and dashboard both read   2
    2  item 1, the Producer role and the CLAUDE.md change                  2
    3  item 3, register plus its Stop-hook check                           3
    4  item 4, interrupt classes and the Blocking counter                  2
    5  item 2, constitution amendment (director ruling, not a build)       1
    6  item 7, the five-second glance over the existing model              3
    7  item 8, health panel                                                2
    8  item 9, show-moment rows                                            1
    9  item 10, cadence and the sleep rule (folds queue 026)               2
    10 item 5, Telegram bot on the PC                                      4

REVISED after reading the research, which ranks the role second and argues the
file plus the role alone fix the complaint. Items 1 to 4 now total 9 points.

Item 5 is last on purpose: it is the only one that cannot be tested here, and
everything above it improves the existing channel whether or not the bot is
ever built. Items 1 to 4 total 7 points and would change what Jafar reads
tomorrow morning.

## d. Dry run: today, in the Producer register

**Message 1, sent 09:05, class Decision.**

> Unreal renders the street from our own data, and it is one wire from
> textured. The material pipeline works with no human touching the editor,
> which is the measurement the engine choice turns on. 563 of 593 objects
> carry textures and all four frames are still grey: the texture coordinates
> are unconnected, so every surface reads one colour.
>
> NEEDS YOU: next builder on the Unreal wire, or on the Ledger?
> A: the wire. One session, and the street stops being grey.
> B: the Ledger. Starts the thing the game is actually for.
> Recommendation A, because it finishes something. Default A at 18:00.
>
> NEXT VISIBLE: textured street, unknown, one build after the fix.
> BUDGET: 60 percent, 20 points to the ceiling.

98 words.

**Message 2, sent 10:30, class FYI, NOT PUSHED.**

> Held at your word. Two rules agree: your wait, and our own stop rule, which
> fired because the connection count did not move across two runs.

25 words, and under item 4 this never reaches his phone.

**What today would NOT have sent:** the dispatch that never fired, the hour
explaining a run that did not exist, the gate that could not fail, the two
staged-empty files, and the session limit. One line of that reaches him in the
morning brief: "One process fault, logged and fixed: a run I reported as
started had not started."

## e. Questions only Jafar can answer

1. Does the Producer speak in THIS chat window, or only through the console and
   the bot? Item 1 says the session he opens defaults to the Producer, and the
   Claude app stays the channel for conversation. Those two can both be true
   only if the Producer is allowed to be conversational here while the console
   carries the evidence, which is a different thing from a 120-word cap.
2. When the Producer and the resident disagree about what is worth telling him,
   who wins? Today they are the same session and the conflict is invisible.
3. Is the morning brief a push, or something he opens? Item 4 routes Decision
   items to it, which only works if it arrives.
4. The console's glance needs one sentence of overall state. Who writes it,
   and does he want it to be able to say "worse than yesterday"?
5. Item 5 says the budget quick-reply is asked at most twice a day and only
   when the next batch would approach the ceiling. Today he was asked twice and
   volunteered once. Is that the intended rate, or the maximum he will tolerate?
