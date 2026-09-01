line: code feature (D1 probe)
spec: production/d1-probe/plan.md, week 1 item 2
acceptance: ported perception tests pass in UE5; cycles.tsv rows written for every edit; no hand-edited binary assets
max_sessions: 3
status: UNBLOCKED 2026-09-01, UE 5.8.2 installing

Transliterate the perception core (seven slots, five-rung ladder) and its
tests from ledger/Assets/Scripts/Core to UE5 C++. Transliteration, not
redesign: the C# suite is the behavioral definition. Blocked until queue
task 000 (UE5 install, Jafar) is done; if UE5 is absent, move this to
blocked/ naming that dependency.

NOTE ON THE TOOLCHAIN, so this does not become a second blocked task: UE
cannot compile a C++ project without a C++ toolchain. On Windows that is
Visual Studio 2022 Community with the single workload "Game development with
C++". If it is absent when this task starts, install it rather than blocking,
and record the install in cycles.tsv as setup rather than as an edit cycle.

NOTE ON THE VERSION: 5.8.2, newer than the plan assumed. Check the C++ API
against the version actually installed rather than against remembered
signatures; a transliteration written to the wrong API version is the kind
of failure that reads as "UE is hard to work in" and contaminates
measurement a.
