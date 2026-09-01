line: code feature (D1 probe)
spec: production/d1-probe/plan.md, week 1 item 2
acceptance: ported perception tests pass in UE5; cycles.tsv rows written for every edit; no hand-edited binary assets
max_sessions: 3
status: DONE 2026-09-01. The transliterated perception core runs inside a real
        Unreal build on ledger-pc and agrees with the shipped C# on 1221 rows,
        0 mismatches, to 1e-9 (probe run 11). Cycle rows written for every edit,
        each endpoint traced to a landed CI commit rather than recalled.
        The golden table is emitted from the REAL Core by ledger/PerceptionGolden,
        so there is one source of truth and no second implementation of the
        expectations. No binary asset was hand-edited.

Transliterate the perception core (seven slots, five-rung ladder) and its
tests from ledger/Assets/Scripts/Core to UE5 C++. Transliteration, not
redesign: the C# suite is the behavioral definition. Blocked until queue
task 000 (UE5 install, Jafar) is done; if UE5 is absent, move this to
blocked/ naming that dependency.

TOOLCHAIN: DONE. Build Tools 17.14.37614.0 at C:\Program Files (x86)\
Microsoft Visual Studio\2022\BuildTools, installed and verified by
ledger-setup-msvc.yml in 2.9 minutes. Logged as setup, not as an edit cycle,
so it cannot poison measurement a.

SCOPE THIS SMALL. The Core is 98 files and 32,554 lines and porting it whole
is not one session's work and not what measurement a needs. The smallest
thing that yields a REAL cycle number is: a minimal UE C++ project that
compiles in CI, ONE ported Core type, and ONE test that passes on both
sides. That produces a build time, a cycle time, and proof the toolchain
works end to end. Everything after it is repetition, and repetition is what
the cycle number is meant to price.

NOTE ON THE VERSION: 5.8.2, newer than the plan assumed. Check the C++ API
against the version actually installed rather than against remembered
signatures; a transliteration written to the wrong API version is the kind
of failure that reads as "UE is hard to work in" and contaminates
measurement a.
