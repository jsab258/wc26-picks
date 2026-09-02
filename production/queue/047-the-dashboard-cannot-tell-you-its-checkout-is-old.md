line: production (the reporting channel Jafar reads)
spec: this file
acceptance: open-dashboard.bat performs a FETCH-ONLY (never pull, never merge) before rebuilding, with GIT_EDITOR=true set in the same edit per tools/lint-bat-editor.py; the page carries a checkout-age reading rendered by the same Reading machinery as every other number, MEASURED as "N commit(s) behind origin/<branch>, newest N/A" or UNAVAILABLE with the reason (no network, no git, fetch failed) and NEVER as a bare 0; a rejecting fixture (a checkout deliberately behind) and an accepting fixture (a checkout level with origin) both run in build-dashboard.py --selftest
max_sessions: 1
status: READY 2026-09-02. engine-specialist or systems-builder. Found 2026-09-02 when Jafar could not see a card that had been pushed.

## The finding

The dashboard says how old THE PAGE is. It cannot say how old THE CHECKOUT
is, and those are different facts. Measured today:

    open-dashboard.bat   rebuilds, runs no git at all, by an explicit choice
                         in its own header comment
    UPDATE FROM CLAUDE.bat   fetches and pulls, and never rebuilds the page

So a page regenerated thirty seconds ago from a checkout six hours behind
reads as current and is not. If the fifteen-minute scheduled task is
registered, it repaints that same staleness every quarter of an hour, which
makes the page look MORE alive the further behind it falls.

Today's instance: a decision card was written, committed and pushed, and the
resident told Jafar it was on the dashboard. It was on the dashboard this
container generates. His copy had never seen the commit, and nothing on his
screen could have told him which of the two was true.

## Why the "no git" rule does not forbid the fix

The header's reasoning is sound and is about PULL: a pull every fifteen
minutes makes merge commits behind the build agent's back, which is a way to
lose work. FETCH is not that. It writes only remote-tracking refs, creates no
merge, touches no working file, and cannot lose anything. The rule to keep is
"never merge unattended", not "never speak to the remote".

## The shape of the number, because this project has paid for the other shape

Checkout age is a Reading like every other number on that page. Behind by
zero commits is MEASURED and means level with origin. Fetch failed is
UNAVAILABLE with the reason, and must not render as zero: "I could not find
out" printing as "fine" is the exact fault the dashboard exists to refuse,
and it would be arriving inside the dashboard's own honesty machinery.

## Not in scope

Do not make the bat pull. Do not make the scheduled task pull. The reader
decides when to take new files; this item only makes the page tell them
whether there are any.
