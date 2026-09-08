line: narrative (the overheard consequence)
spec: Twelve `clause` values on the witness_summary rows of
  content/dialogue/crime-witness-v1.json, THIRD PERSON, lowercase, no interior full
  stop. BankPick reads it; CrimeProbe.cpp 1184 files the clause as the rumour
  Summary and keeps the sentence as the spoken witness line;
  production/specs/dialogue-crime-witness-v1.md 23 to 27 corrected to say the summary
  is SPLICED in both roles and that one string cannot be both.
acceptance: the composed telling reads as English, the selftest prints all twelve
  spliced memory forms so a reader can judge person agreement, and the committed
  memory markdown no longer reads "I heard from the shopkeeper that He looked..."
max_sessions: 1
status: READY 2026-09-08, and it BLOCKS THE CRIME DISPATCH. Amendment A3 of the
  director ruling game-design/decision-2026-09-08-queue-147-the-composed-telling-and-the-clause-the-bank-never-had.md.
  THE DEFECT, measured rather than argued: StreetVoice.cs 752 to 771 states that a
  Rumor.Summary is a LOWERCASE CLAUSE written to be spliced, and all twelve
  witness_summary rows are finished first-person sentences with capital first letters
  and interior full stops. The composed telling therefore comes out as "You hear all
  sorts. He looked straight at me before he ran. Couldn't tell you his name, but I've
  got his face now, apparently." The caption tool renders it worse still, with a
  doubled stop: "...his face now., apparently."
  THE SECOND CONSUMER ALREADY SHIPPED A CORRUPT ARTIFACT and it predates queue 147:
  Gossip.h 586 appends "I heard from " + DisplayName + " that " + Summary, and
  production/d1-probe/ue-crime-memory-n2.md line 6 is committed reading "I heard from
  the shopkeeper that He looked straight at me before he ran."
  THE TWELVE CLAUSES ARE WRITTEN, NOT DERIVED. A rule that lowercases the first letter
  and strips the final stop produces "he looked straight at me before he ran" in the
  first person, which is the wrong person for a third party's memory.
