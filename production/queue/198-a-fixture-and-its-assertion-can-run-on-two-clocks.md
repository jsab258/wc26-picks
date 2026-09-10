line: instrument
spec: Sweep the selftests for a fixture armed on one clock and asserted against
  another. Five tools carry both a frozen datetime literal and a real-clock call in the
  same file, of 69 tools that have a selftest at all: tools/gallery.py, tools/map.py,
  tools/morning-brief.py, tools/producer-check.py, tools/wake-queue.py. Being on that
  list is NOT a fault, it is the shape a fault of this kind has. Open each, say which
  clock every fixture and every assertion uses, and fix only the pairs that disagree.
acceptance: each of the five names the clock its fixtures run on, in a comment or a
  variable name, and any pair that disagreed is fixed with the disagreement recorded.
  The count of pairs examined ships with the count of pairs changed.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. FOUND BY A GREEN SUITE TURNING RED WITH NOTHING CHANGED.
  tools/wake-queue.py went from 63 passed to 62 passed at one o'clock in the afternoon,
  on a working tree whose wake-queue.py was byte-identical to the last commit that
  touched it. Its `loop` fixture is armed at `past`, which is REAL now minus an hour,
  and the case asserting something is due read `noon`, frozen at 12:00Z. The two agree
  only while the real clock is before 13:00Z. It was green at 12:25 and red at 13:00.
  THE COMMENT ABOVE THE FIXTURE ALREADY RECORDS THE MIRROR OF THIS FAULT: "The first
  version of this suite planted 11:00 and ran at 08:03, and the case that should have
  blocked quietly permitted." The repair for that made the fixture real and left the
  assertion frozen, which is how the same file acquired the opposite fault in the same
  section. That is the transferable half and it is why this is a sweep and not a fix:
  ONE CLOCK PER FIXTURE, NAMED, and a repair that moves a fixture's clock moves every
  assertion that reads it.
  The one-line repair to wake-queue.py landed with this item and was proven both ways:
  63 of 63 accepting, and with the record planted two hours in the FUTURE the case fails
  along with four others, so it is not a ratchet.
