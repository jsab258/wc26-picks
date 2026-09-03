# What the playbook repo is owed — the 25 Aug sync payload

> **STATUS: LOG, 2026-08-25. NOT CURRENT** once synced and re-stamped.
> Approved by Jafar 25 Aug ("recommendations are fine, go with them") on
> the recommendation: ONE batched pass AFTER the current build lands, not
> a trickle, because the lessons were still arriving and a mid-flight sync
> would need redoing.

`jsab258/game-studio` last moved 24 Aug (`37f50fd`). `tools/template-sync.py`
holds a DEFER marker naming `template-sync-batch-definition-and-turn-ceilings`
and goes RED again on the next process-section edit, so this debt cannot rot
silently — it already blocked a commit tonight, which is how it was noticed.

**Everything below is GENERAL, not LEDGER-specific. That is the test for
inclusion: would it help a project that shares none of this code?**

**(a) The batch definition and verifier-first rule.** Just written into
CLAUDE.md's HYBRID RESIDENT section. Trigger 1 said "builder-batch review
before any commit of builder work" and never defined how big a batch is —
that ambiguity alone produced 9 tier-1 spawns from one night's work, ~25%
of all agents, on a model that counts double. A batch is now all builder
work landing in ONE reviewed commit; claim-checking goes to a tier-2
verifier first; one decision is one spawn; a killed spawn is RESUMED, never
restarted.

**(b) The turn ceilings were low by about 2x.** Seven agents stalled one
step from finishing, each on a sentence announcing the work it was about to
do. The counter-intuitive part, and the reason it belongs in a template: a
capped agent spends its full context, delivers nothing, and then needs a
resume that reloads it — so the cap turned one agent into two, seven times.
Raising the ceiling is the CHEAPER setting. Ceilings are not targets and
remain unvalidated upward.

**(c) A review-cadence gate must compare against the last commit that
TOUCHED CODE, not against HEAD.** Otherwise a docs commit — or CI
committing its own output — invalidates a still-valid review and forces a
fresh top-tier spawn. This fired three times in one night before it was
fixed.

**(d) The same gate is satisfied by a SPAWN, not by a completed review.**
A director killed mid-ruling still clears it. That is the gate certifying
the exact thing it exists to prevent, and an unattended loop would have
committed unreviewed work on a green signal. Log completion, or require the
decision record itself to be newer than the last code commit. STILL OPEN
here; carry the finding, not a fix.

**(e) A docs checker must recurse and print what it examined.** Ours globbed
one directory level and had never looked at fifteen files. The tell was a
denominator that did not move when a file was added.

**(f) The commit gate assumes ONE writer.** With four builders editing, the
tree is rarely stable long enough for a whole-tree footer to describe it,
and the gate blocks constantly. Unresolved; a template should say so rather
than ship a gate that fights concurrency silently.

**(g) The session scratchpad is shared with every spawned agent**, so a
fixed filename is a collision. One commit landed carrying a different
commit's message entirely. Name scratch files uniquely; read back anything
written before a delay.

**(h) Measurement arithmetic and formatting live in the TESTED layer.** Now
a standing rule in `.claude/rules/instruments.md` after the third instance.
Where the top layer does not compile locally, a formatter written there
ships unrun, and an unrun formatter printing a plausible string is the
silent-instrument failure.

**(i) "Quote the corpse."** A retracted comment quotes its own false
sentence verbatim before correcting it, so the error cannot be re-derived
by the next reader who finds it plausible — it was plausible to everyone
who read it the first time.

**(j) An accepting fixture can ENSHRINE the bug.** The space-in-values check
had `places=[alley=3 market=53]` in its own SELFTEST_GOOD, asserted as
required behaviour. Not an accepting case that went unrun — one that
certified the fault. This is 5b's deepest form and the template's 5b
section should carry it.
