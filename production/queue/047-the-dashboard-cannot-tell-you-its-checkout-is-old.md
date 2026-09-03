line: production (the reporting channel Jafar reads)
spec: this file
acceptance: (1) the registered scheduled task brings the checkout current and rebuilds, with `git pull --ff-only` and GIT_EDITOR=true set in the same edit per tools/lint-bat-editor.py, so Jafar clicks NOTHING and the page he opens is built from current files; (2) a fast-forward that is refused, a fetch that fails and a missing network each leave the working tree untouched and are rendered on the page as a checkout-age Reading, MEASURED as "N commit(s) behind origin/<branch>" or UNAVAILABLE with the reason, NEVER as a bare 0; (3) build-dashboard.py --selftest gains an accepting fixture (checkout level with origin) and a rejecting one (checkout deliberately behind), both run
max_sessions: 1
status: LANDED 2026-09-02, commit c1311ea7. Fast-forward-only pull before each scheduled rebuild, a checkout-age Reading that is MEASURED or UNAVAILABLE and never a bare zero, and a gate that holds entirely while a build runs on that PC. Was: READY 2026-09-02.

## The finding

The dashboard says how old THE PAGE is. It cannot say how old THE CHECKOUT
is, and those are different facts. Measured today:

    open-dashboard.bat        rebuilds the page, runs no git at all, by an
                              explicit choice in its own header comment
    UPDATE FROM CLAUDE.bat    fetches and pulls, and never rebuilds the page

Neither does the other, so the reader is the integration step. A page
regenerated thirty seconds ago from a six-hour-old pull reads as current. If
the fifteen-minute scheduled refresh is registered it repaints that staleness
every quarter hour, so the page looks MORE alive the further behind it falls.

Today's instance: a decision card was written, committed and pushed, and the
resident told Jafar it was on the dashboard. It was on the dashboard the
build container generates. His copy had never seen the commit, and nothing on
his screen could have told him which of the two was true.

## Why the "no git" rule does not forbid the fix, and what replaces it

The header's reasoning is sound and it is about ONE COMMAND. A bare `git pull`
every fifteen minutes can make a merge commit behind the build agent's back,
and on 26 August one opened vim in Jafar's window and blocked every pull after
it. That is a real incident and the rule earned its place.

`git pull --ff-only` is not that command. It advances the branch pointer or it
refuses; it can never create a merge commit, never opens an editor, and on a
refusal changes nothing at all. The rule worth keeping is NEVER MERGE
UNATTENDED. "Never speak to the remote" was the blunt version of it, and the
cost of the blunt version is that the reader does the integration by hand,
which is what Jafar has just refused.

Keep GIT_EDITOR=true and GIT_MERGE_AUTOEDIT=no set in the same edit anyway:
belt and braces cost nothing and tools/lint-bat-editor.py asks for it.

## The one thing to verify before writing the pull, not after

`ledger-pc` is Jafar's PC and it is also the self-hosted runner. Establish
WHERE the runner checks out (its own `_work` tree, or the same clone the
dashboard reads) and quote the evidence. If a scheduled pull could change
files under a running job, gate it: no pull while a job is running, and the
page says "held: a build is running" as a Reading rather than going quiet.
Do not assume the two directories are separate because they usually are.

## The shape of the number, because this project has paid for the other shape

Checkout age is a Reading like every other number on that page. Zero commits
behind is MEASURED and means level with origin. A failed fetch is UNAVAILABLE
with its reason and must not render as zero: "I could not find out" printing
as "fine" is the exact fault the dashboard exists to refuse, and it would be
arriving inside the dashboard's own honesty machinery.

## Not in scope

Do not make it merge. A refused fast-forward is reported, never resolved
unattended. The reader decides what to do about it; this item only makes the
machine stop needing the reader to remember.
