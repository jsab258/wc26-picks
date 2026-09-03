line: production (the reporting channel Jafar reads)
spec: this file
acceptance: the live status document is written to the store on every landing without the resident remembering, by a mechanism that is itself observable; the page's own age line is the check, and a deliberate skipped write must show as a stopped feed within its stale window rather than as calm numbers; the mechanism names what it could NOT write and why, and a run that wrote nothing says so in those words
max_sessions: 1
status: READY 2026-09-02. instrument-builder. Filed at the moment the hosted page went up, because the fault it replaces is the fault it can grow back into.

## The finding, filed before it happens rather than after

The hosted dashboard is live and correct:

    https://claude.ai/code/artifact/2c3da7c0-8b8e-4626-8e73-2498acbe6ed8

It contains no numbers of its own by construction, subscribes to
`status/current`, and turns red when its numbers age past the stale window.
Every part of that is right. And all of it depends on one unautomated act: a
resident running `--emit-json` and writing the document to the store.

THAT IS THE SAME SHAPE AS THE THING IT JUST REPLACED. The .bat dashboard was
current only if Jafar remembered two clicks. The hosted page is current only
if a session remembers one write. Moving a manual step from the reader to the
writer is an improvement in who pays, not a fix to the mechanism.

## Why the red feed is not sufficient on its own

The page ageing honestly is the difference between this and the snapshot
fault, and it is worth keeping whatever else changes. But a reader who opens
the page and learns "these numbers are four hours old" has still learned
nothing about the project. Honest silence is better than a false number and
worse than a fact.

## The work

Make the write happen on every landing, and make the mechanism observable in
the same breath. A writer that silently stops is the failure mode, and it
looks exactly like a quiet week. Whatever carries it must be able to say "I
wrote nothing, and here is why", in those words, per the standing rule that a
run which measured nothing says so.

## What not to do

Do not solve it by widening the stale window. Do not let the page fall back
to numbers baked in at publish time; render_live_page() takes no model
precisely so that cannot happen by accident, and that property is load
bearing. Do not republish the page on a schedule: the page changes only when
the renderer changes, and a republish is not a data update.
