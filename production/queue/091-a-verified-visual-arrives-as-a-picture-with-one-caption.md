line: infrastructure (the Producer loop, images)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 1, images clause
acceptance: a frame chosen by `python3 tools/report-frame.py` arrives on his phone AS AN IMAGE with exactly one caption line naming what it shows and the commit it came from, proven by one real send on the PC and by the file arriving as a photo rather than a link; when report-frame withholds (the last build measured nothing) NO image is sent and the message carries the words "nothing measured"; a file that is missing or over the platform's photo limit is reported by name and not silently skipped; the sender prints imagesSent=N/M candidates and announces the caption cap when it bites; the receipt carries the photo descriptor the platform returned (its sizes), which is the artifact for arrived-as-a-photo
max_sessions: 1
status: WAITS 2026-09-05 behind the first real photo send, which is run 21's frames. Built and selftested.

## The picker already exists and it already refuses

`tools/report-frame.py` is the standing answer to which picture goes with an
update, and its refusal is the important half: it walks back to the last commit
whose own verdict says a sim actually ran, because on 4 August a build
committed six stills it could not have drawn. CLAUDE.md carries the rule that
every report to Jafar rides with a picture that this tool withholds when the
last build measured nothing.

So this task does not choose pictures. It carries the tool's answer to his
phone, including the answer "there is nothing honest to show", which must
arrive as those words rather than as an old frame reused.

## Why an image and not a path

He is on a phone. A repository path is not a picture, and the last month of
this project has three separate incidents of a green number standing in for a
frame nobody opened. The deliverable is the photo in the chat.

The bot is standard library only and stays that way: a photo upload is a
multipart POST built by hand with urllib, which is why this is its own task and
not a line in another one. Nothing new enters the licence allowlist.

## One caption line, and the cap announces itself

One line. It names what the picture shows and the short sha it came from, and
it links the evidence per constitution law 12, which puts the link behind the
sentence for Jafar rather than beside it. If the platform's caption limit bites,
the message says `(+N more character(s) not shown)` in the shape every other
cap in this tree uses.

## Both halves, accepting first

Accepting: one real send on the PC. The image opens on his phone, the caption
is one line, and the sha in the caption matches the commit report-frame named.
Read the arrived image, do not infer it from a 200.

Rejecting, three cases: with the newest frame's verdict carrying NO PLAYER LOG,
the sender sends no image and says "nothing measured"; a named candidate whose
file is absent is reported by name; and an oversized file is refused with its
measured size rather than truncated or silently dropped.

Denominator on the done line: `imagesSent=N/M` where M is the candidate count
report-frame offered, so a zero can be told apart from a run that never looked.

## Depends on, and what it blocks

Depends on queue 088 only for the receipt route if the send is recorded in the
repo; the send itself needs nothing but the bot. Independent of 089 and 090, so
it can run in parallel with either. Blocks nothing. Related: item 6 of the
standing order, where the first textured frames come to him as images, which is
the first real use of this path.
