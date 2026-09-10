# Cleanup batch: the four named dashboards are not orphans, the census gains 22 tiles, and my own sweep was wrong twice

> **STATUS: LIVE, verified 2026-09-10.** The resident's record of the grep half of
> Jafar's cleanup ruling of 2026-09-10, and of the systems-census additions
> under the same ruling. Supersedes nothing. Two of my own instrument faults
> are recorded here because both changed an answer.

## 1. The ruling this answers

Jafar, 2026-09-10, cleanup batch, work order item: "delete orphan tools and
superseded dashboards after a grep proves nothing calls them; map, gallery,
cards page remain." The four he named were `STATUS.md`, `glance.html`,
`dashboard.html` and `open-dashboard.bat`.

THE CONDITION WAS NOT MET FOR ANY OF THE FOUR. The grep proves the opposite of
what it was asked to prove, so nothing was deleted and nothing was archived.
The readers, by file and line:

- `STATUS.md`: `ledger/verify.py:3024` registers it in the cadence scope table,
  `:4419` ASSERTS `_cadence_scope("STATUS.md") == ("evidence", "status")` as
  part of verify's own selftest, and `:4681` uses `("STATUS.md", 200)` in the
  evidence ratchet guard. `.claude/hooks/session-start.sh:46` prints lines 7 to
  12 of it at the start of every session, which is where this session read its
  own phase.
- `glance.html`: `tools/producer-check.py:302` to `:322` carries it in
  `SITE_PAGES`, the Producer's link allowlist, under A2 of the batch ruling of
  2026-09-09, and `:1799` to `:1803` checks that `tools/publish-glance.py`
  publishes that exact filename. Deleting the file breaks the Producer's link
  discipline, which is a ruled mechanism.
- `dashboard.html`: written by `tools/dashboard/build-dashboard.py`, and
  `.claude/hooks/session-start.sh:39` names it as one of the two files that
  build writes at every session start.
- `open-dashboard.bat`: no CODE calls it, and that is not evidence of death. It
  is a Windows batch file: a human double-clicks it, and `START EVERYTHING.bat`
  line 39 describes it to that human. A grep cannot see a double-click, so
  absence of a caller means nothing for this class of file.

Deletion is still possible and it is REHOMING WORK, not a delete. It costs, in
order: the Producer's link allowlist loses the glance and gains whichever page
replaces it, which is a change to a ruled mechanism and so needs Jafar;
verify's cadence scope entry, ratchet entry and selftest assertion for
`STATUS.md` all come out together; and the session-start hook loses the only
status it prints, which is rule 12 territory. None of that is cleanup.

## 2. The real orphan sweep, and the two faults in it

147 tools examined, all tracked `.py` and `.sh` under `tools/`.

Result: orphan=1, docsOnly=11, reachedByCode=135. The one orphan is
`tools/voice-fetch/standalone_page.py`, 78 lines, last touched 31 July.

PASS 1 OF THIS SWEEP WAS WRONG AND SAID orphan=2. It grepped each tool's
basename WITH the `.py` extension, and a Python import never writes the
extension, so every module reached by `from <stem> import` read as unreached.
The fault surfaced because a bare-token check found
`tools/shape-check.py:29: from mp3probe import probe` for a file pass 1 had
just called an orphan. Three tools moved from dead to live when the import form
was added: `mp3probe.py`, `mp3trim.py`, `botconfig.py`.

THE SECOND FAULT, in the census sweep in section 3: five of twenty-one search
tokens were truncated stems passed to `grep -w`. A word-boundary match on
`Injur`, `Heal`, `Burglar`, `Intimidat` or `Localis` CANNOT MATCH `Injury`,
`Healing`, `Burglary`, `Intimidate` or `Localisation`. Those five tokens were
structurally incapable of hitting anything, and all five read as zero. Redone
without `-w`, two of the five had live code behind them.

Both faults are the same shape and it is the shape rule 3 names: the ruler was
wrong and the reading looked clean. A zero from a grep is only a zero if the
pattern could have matched.

## 3. The census additions, and where they contradict the instruction

`production/systems-inventory.json` goes from 69 systems to 91. 18 absent, 4
partial. Validator: `accepted problems=0/checks=2594`, `refs=214
resolved=214/214`, `missingWhere=0/66-not-absent`.

THE INSTRUCTION SAID ADD THEM AS ABSENT. FOUR OF THEM ARE NOT ABSENT, and they
are in as partial with their evidence instead, because the inventory's own
`howToRead` names the inverse of this fault as the one the project keeps
repeating:

- injury and healing: `Core/Harm.cs` declares an `InjuryKind` enum and an
  `Injury` class; `Game/OperationHost.cs:131` holds `LastInjury`.
- bribes and intimidation: `Core/Gossip.cs:706 Bribe` and `:738 Intimidate`
  both return a `DcResult`, and `Game/DialogueUI.cs:2214` calls one from the
  dialogue surface, so they are reached and not only written.
- foley: `Game/Audio.cs:830` declares `Foley(string kind, float volume)` and
  `Game/DialogueUI.cs:1546` calls it on a coat verb.
- ambient beds: `Game/RoomTone.cs` holds a room-tone authority and
  `Game/Audio.cs:335` gains it through `Core.Acoustics.OutsideBleed`. Indoors
  has a tone; `ambientBed`, `ambientLoop` and `BackgroundLoop` all return zero
  in 218 files, so outdoors has none.

Four more of the named items are FALSE FRIENDS whose only hits are unrelated,
and those went in as absent with the false friend named in the note, so nobody
re-greps and reaches the opposite conclusion: `Thread.Sleep(50)` at
`Game/Audio.cs:1291` is not sleep, Court in `Core/StreetMap.cs:243` is a street
name, `BurialCellRead` in the Unreal vignette spec is not a police cell, and
`Letter(...)` in `Game/WorldBuilder.cs` is a fascia lettering call and not post.

Not added, with the reason on the record:

- drunkenness, pub games and gambling: D17 and D18 forbid them.
- controller: `gamepad` and `controls` are already tiles.
- stamina as its own tile: `Core/Combat.cs` carries `StrikeStamina`,
  `ShoveStamina`, `StaminaRecovery` and `StaminaCost`. A blow costs wind. It is
  RUNNING that has no stamina, so the tile is sprinting and the existing
  combat stamina is named in its note.

## 4. Five gate-class tools are wired to nothing, and CLAUDE.md says one of them proves something

Found by the sweep, not looked for. Each of these has zero readers in any `.py`,
`.sh`, `.yml` or `.ps1`, and zero hits in `ledger/verify.py`:

`tools/goal-block-check.py`, `tools/brand-verify.py`,
`tools/dialogue-verify.py`, `tools/blocking-count.py`, `tools/brief-sheet.py`.

The sharp one is the first. `CLAUDE.md:227` reads "`tools/goal-block-check.py`
proves the goal block still matches", and nothing runs it, so the sentence
describes a guard that never fires. That is rule 6 exactly: built is not
running.

NOT FIXED IN THIS BATCH, and the reason is Jafar's own instruction for it: "no
studio building until it lands." Wiring five gates into verify is studio
building. The right moment is when the D18 content gate is wired, because D18
requires its word-list gate to be ENFORCED and a gate nothing runs is not
enforcement, so that edit opens the same registration site in `verify.py` and
the other five cost nothing extra there. Held to that moment, named here so it
is not lost.
