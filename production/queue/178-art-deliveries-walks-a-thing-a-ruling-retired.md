line: instrument (the art line's own reader)
spec: Reconcile tools/art-deliveries.py with the in-house clause. Either it also reads
  deliveries that land in the studio checkout under production/art/<commission>/, or it
  says in its own output that branch deliveries are the OUTSIDE case and names where the
  in-house ones are, so a zero cannot read as an idle art line.
acceptance: on a morning when a delivery landed in the studio checkout, the tool's
  output names it rather than printing 0 of 0, and game-design/art-collaboration.md no
  longer holds two sentences that contradict each other about where a delivery lives
max_sessions: 1
status: READY 2026-09-09. Found by running the tool the daily wake names, which is the
  first time it has been run since the ruling that retired its input.
  MEASURED: branchesWalked=0 deliveriesFound=0/0-branches, and the tool says plainly
  that this is NO ART BRANCHES AT ALL rather than art branches with nothing on them.
  `git branch -r` agrees: five remote refs, no art/*.
  THE CAUSE IS A RULING, NOT A FAULT. The in-house clause of 2026-09-08 says a spawned
  designer has no separate checkout and writes only under production/art/<commission>/
  in the studio checkout. atlas-02 landed exactly that way, correctly, and no art branch
  was made.
  TWO SENTENCES IN ONE DOCUMENT NOW DISAGREE. art-collaboration.md section 5 tables
  art/atlas-01 and art/atlas-02 with full pins, and section 4 says "Deliveries live on
  the art branch; reviews live here. Neither line writes on the other's branch." The
  in-house clause, added to the same file the same day, says the opposite for a spawn.
  WHY IT MATTERS EVERY MORNING: the daily wake calls this tool, so it will answer 0 of 0
  every day, and a reader who does not know the ruling concludes the art line is idle on
  the morning after it delivered 1368 cited lines. That is the reach-decay class: a tool
  whose input source was retired keeps running, keeps passing, and keeps reporting zero.
  ONE THING THIS ITEM DOES NOT DECIDE: whether art branches should come back for an
  OUTSIDE delivery. That is Jafar's taste about how an outside line arrives, and it goes
  to him as a card if the work reaches it.
