line: infrastructure
spec: this file
acceptance: one implementation of the self-hosted PATH bootstrap called by both workflows; both dispatched once and green; the duplicated blocks gone
max_sessions: 2

The self-hosted PATH bootstrap (find bash, find pwsh, put both on
GITHUB_PATH, exit 0 explicitly) now exists TWICE: in
ledger-build-windows.yml and in ledger-probe-unreal.yml.

It drifted the first day it was duplicated. The probe's copy dropped the
pwsh half and the explicit exit, and run 1 died on "pwsh: command not
found" with nothing else to say. That is one idea in two implementations
and the second one missing a line, which is a shape this project has a
standing rule about.

Extract it to tools/runner/bootstrap-paths.cmd, called by both as
`shell: cmd` `run: tools\runner\bootstrap-paths.cmd`. Keep the diagnostic
messages verbatim: they name the .bat to run on the machine when a tool is
genuinely absent, and that is the part a person acts on.

DISPATCH BOTH AFTERWARDS. The Unity workflow is the proven one and this
task touches it; a green probe alone does not show the Unity job survived
the change, and the whole point is that the shared copy behaves for both.
