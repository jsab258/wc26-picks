# 253. The E4 remainder: intendedUpNoReason and ranNotIntended

STATUS: READY, 2026-09-10. Named by the builder that landed the routing
enforcement, as the part of its brief it did NOT reach. Filed so it is not
mistaken for finished work.

## What was built and what was not

BUILT: `routing_drift()` in `tools/spawn-cost.py` joins what a definition
DECLARES against what a spawn RAN, keyed on `agentId`, last-wins per id, with
pre-ruling rows excluded and direction deciding whether a disagreement is a
silent demotion or a violation.

NOT BUILT: the two readings that use the log's own `reason` column rather than
the definition.

- `intendedUpNoReason`: a spawn whose recorded model is ABOVE its definition
  and whose `reason` field is `up:MISSING` or does not resolve. The verify
  check `agent_model_overrides()` refuses these at the commit gate. What is
  missing is the SERIES: how often it happens, so a rising count is visible
  before somebody starts writing a reason that parses and means nothing.
- `ranNotIntended`: the spawn log records what was ASKED FOR and the turns log
  records what RAN. Where they differ, the intent itself was not honoured. This
  is a different fault from a mis-declared definition and today it has no name
  and no count.

## Why the second one is the sharper half

The model column cannot see what ran. The harness supplies no model on the
`SubagentStart` payload, so the hook falls back to the definition's own line,
and `log-agent.sh` says so in its own header comment with the worked example:
a row reading `instrument-builder opus` written while that spawn ran on sonnet.

So there are THREE facts and today only two are compared:

    what the definition declares      .claude/agents/<type>.md
    what the spawn asked for          agent-log.tsv, model + reason
    what actually ran                 agent-turns.tsv, tier

`routing_drift` compares the first and the third. `ranNotIntended` is the
second against the third, and it is the one that catches a spawn whose
override was written down and then not honoured by the harness.

## Done looks like

Both readings printed with denominators, both with a planted fixture proving
they fire, and the accepting case run over the live tree. A zero prints its
denominator; a never-run case prints "nothing measured".

## Dependencies and risk

Depends on the spawn-intent sidecar being used at all: until a resident writes
one, every row's model comes from the definition and `ranNotIntended` reduces
to `routing_drift`. Say that in the tool rather than printing a zero that reads
as clean.
