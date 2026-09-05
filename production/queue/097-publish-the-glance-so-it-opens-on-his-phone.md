line: infrastructure (the console, publication)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 3b
acceptance: a request to the published URL from the container returns HTTP 200 with a text/html content type and a body containing the dated sentence from the newest generated page, printed as `pageHttp=200 pageType=text/html pageAgeMin=<n>`; a run where the page was not published, or where the served body carries an older date than the newest commit's page, FAILS the check naming which of the two it was rather than reporting green; the served body is searched for the token pattern and for the string config.local and the check fails if either appears; and if Pages cannot be enabled the deliverable is a recorded refusal naming the exact error, with NO green claim and no file left that he cannot read; a request that does not complete (proxy refusal, timeout) prints the words "nothing measured" with the error, and is never reported as 404
max_sessions: 1
status: READY 2026-09-05. Immediately after queue 096. instrument-builder.

## The order's own condition

"IF PAGES IS REFUSED FOR ANY REASON, SAY SO rather than leaving a file he
cannot read." So this task has two legitimate endings and only one of them is a
published page. The refusal ending is a decision card in
`production/decision-queue.md` carrying the exact error text and the routes
left, not a quiet retry next week.

## What has to be settled before any code

Enabling Pages is a repository setting, not a commit. Find out, in this order,
and write down what each answer was: whether Pages is already enabled; whether
the account running the check can enable it; and which source it would build
from, given that the work lands on `claude/game-dev-ai-automation-2h67ix` and
Pages builds one configured branch and folder. If enabling needs Jafar, that is
a card with a one-line ask, not a blocked week.

## Two traps to check rather than assume

- A RAW FILE HOST IS NOT A FALLBACK UNTIL IT IS MEASURED. Before offering
  raw.githubusercontent.com or any similar route, request it and print the
  content type: a host that serves HTML as text/plain gives him source code on
  a phone screen, which is a file he cannot read by another name.
- A CDN CACHE MAKES "not published" AND "published but stale" LOOK IDENTICAL.
  The check tells them apart by the dated sentence in the body and prints the
  age in minutes, and any retry announces its wait rather than looping quietly.

The container reaches the network through the agent proxy. If the request comes
back 403 or 407 from the proxy, read `/root/.ccr/README.md` and the status
endpoint. Never disable TLS verification and never unset the proxy.

## Nothing on that page is a secret, and the check proves it

The page is generated from committed files in a repository that is already
public, and it must stay that way. The published body is searched for the
credential shapes before the URL is given to him, because a gitignore stops a
commit and does not stop a render.

## Both halves, accepting first

Accepting: the URL, requested from the container, returns 200 and text/html and
carries today's sentence. Then open it and read it.

Rejecting, three cases: request a URL that was never published and show the
check failing with `pageHttp=404`; serve a body one day old and show it failing
on age rather than passing on status; and plant a credential-shaped string in a
fixture body and show the search catching it.

## Depends on, and what it blocks

Depends on queue 096 for the page to publish. Blocks nothing, but item 3 is not
done until this lands: a glance he cannot open is a file, not a glance.
Related: the hosted artifact dashboard recorded in NOW.md, which stays as it is
and is not what this replaces.

## THE UNRUN CHECK, RUN BY THE RESIDENT 2026-09-05

`jsab258/wc26-picks` is PUBLIC (`visibility: public`, read from the repository
listing, not inferred). So GitHub Pages is available without a paid plan and
this item is not blocked. Jafar's instruction was to SAY SO if Pages were
refused; it is not refused, and that is the answer to the question he asked.

ONE CONSEQUENCE HE SHOULD RULE ON RATHER THAN INHERIT. A Pages site on a public
repository is WORLD READABLE at a guessable URL. The glance carries his budget
percentages on both meters, the needs-you count and the top item. The
repository is already public so nothing new is exposed by publishing, but
"already public" is a reason it is not a new leak, not a reason it is fine.
Put it to him before the first publish: publish as designed, or hold back the
budget bar, or accept it. Do not decide this in a builder pass.
