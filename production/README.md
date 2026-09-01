# production/ (the studio's working state, per ledger-v2/studio-v2/)

- queue/            task files, one deliverable each. Folder is the state
                    machine: queue/ then active/ then done/ or blocked/.
- briefs/           weekly and nightly briefs; latest.md is always current.
- specs/            assembly-line specs (station 1 of every pipeline).
- scratch/<agent>/  per-agent namespaced scratch. No shared scratch files
                    (waste lesson 4: a filename collision corrupted a commit
                    message). An agent writes only under its own name.
- token-ledger.md   per-department spend estimates and recorded escalations.
- throughput.md     verified pieces per week, the planning unit.
- logs/             runner logs, gitignored, one dir per night.
- STOP              the kill switch. If this file exists the runner exits
                    between iterations. Create it to stop a night; delete it
                    to allow the next one.
