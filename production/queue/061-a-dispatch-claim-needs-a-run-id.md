line: infrastructure (the dispatch discipline)
spec: this file
acceptance: a tool that takes a commit sha and a workflow name and answers "did a run start on THIS sha", returning the run number and status or the words NO RUN STARTED, with an accepting fixture (a sha that did start a run) and a rejecting one (a sha that did not); plus a line in .claude/rules/ci.md making the claim "this push is run N" unsayable without it
max_sessions: 1
status: READY 2026-09-03. instrument-builder, small. Found by making the mistake.

## The finding

This project has careful rules for reading a run: verify effects not exit
codes, watch by ancestry, a run that measured nothing says NO RUN. It has NO
RULE FOR CONFIRMING A RUN STARTED, and that is the gap that cost an hour on 3
September.

Commit e6676ec6 carried Phase C, the light probe and the clipping counts. The
Unreal workflow triggers on a push touching `production/d1-probe/DISPATCH`.
That file was not in the commit. Nothing started. The resident told Jafar
"this push is Unreal run 18", and it was false when written.

THE EXPENSIVE PART WAS NOT THE MISS. Jafar asked why a render was taking
thirty minutes. Rather than checking whether the run existed, the resident
explained the slowness: a cold Unreal editor module build that nobody had
timed. Plausible, specific, and about a thing that was not happening. The
newest run was still 17 and one API call said so.

An absence got a theory instead of an investigation. That is the same family
as suspecting the instrument last, and it is worse here because the theory was
good enough to be believed.

## Why a tool and not a resolution to be careful

The existing rules are all about a run that HAPPENED. Every one of them
assumes the run exists, so none of them fire when it does not. A resolution to
check would decay exactly like the comments this project has a rule about;
the ancestry check exists as a command for the same reason.

The tool is small: given a sha and a workflow, ask the run list whether any
run carries that head sha. The rejecting fixture is the interesting one and it
already exists in history, e6676ec6, a sha that started nothing.

## The cheap half, worth doing in the same session

The sentinel-triggered workflows are the ones this bites, and there are five
of them. A push that touches files a workflow watches, WITHOUT touching its
sentinel, is the exact shape of the miss. The commit-time check could say
"this commit touches ue-probe/ but not DISPATCH, so no Unreal run will start"
as a NOTICE rather than a block, because sometimes that is deliberate and was
deliberate twice last night.
