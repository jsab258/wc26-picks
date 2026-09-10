line: narrative (the overheard consequence)
spec: StreetVoice.Exchange composes the HEARER'S ANSWER as well as the telling, in
  ledger/Assets/Scripts/Core/StreetVoice.cs FIRST, with its C# tests and golden rows,
  and only then in the ported StreetVoice.h.
acceptance: overheardBeatsComposed reads 2/2 rather than 1/2, and the two engines
  still agree line for line
max_sessions: 2
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-08. The next rung for the overheard beat, filed by the director
  ruling game-design/decision-2026-09-08-queue-147-the-composed-telling-and-the-clause-the-bank-never-had.md
  section 2. NOT A DEFECT IN QUEUE 147: StreetVoice.cs 285 to 295 marks only the
  TELLING as Composed and says in the same comment why marking both would put a false
  renderable hole in the structural bucket, so Exchange has never composed the answer
  and a faithful port could not.
  WHY THE C# FIRST AND NOT THE PORT: the C# suite is the behavioural definition. A
  port that improved something would make the two engines incomparable, which is the
  one thing the transliteration method exists to prevent.
  ITS OWN SIMULATION CHANGE AND ITS OWN ESCALATION.
