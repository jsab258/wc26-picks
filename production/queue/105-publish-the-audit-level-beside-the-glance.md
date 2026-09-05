line: infrastructure (the console)
spec: game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md, section 3 and section 11 item A
acceptance: dashboard.html built fresh by the publish step and STATUS.md rendered as HTML, both named in SITE_FILES and both requested after deploy with their own pageResult; the glance's AUDIT taps come back and a served tap on each returns 200 with the expected body, proven against a local server; and a missing audit file is REFUSED by the publisher rather than shipped as a dead link
max_sessions: 1
status: READY 2026-09-05. NOT STARTED THIS WEEK by Jafar's rule that after item 4 the studio stops building studio.

## The fault, measured rather than argued

Jafar's item 3 says of the glance: "Everything else one tap down." Two of
those taps are dead on the published site. Measured against a local server
built from the real publisher output:

    tap dashboard.html http=404
    tap STATUS.md      http=404
    tap map.html       http=200

`dashboard.html` and `STATUS.md` are repository-root files the publisher never
ships, so the links resolved locally and 404 on the site.

## What was done instead, and why this item exists

The ruling WITHHELD the two taps rather than shipping them: `AUDIT = ()` and
the glance's footer now says the audit level "is in the repository and not yet
one tap down". A 404 tap is a lie; a footer saying so is true. That is a
holding position, not a fix, and this item is the fix.

## The trap

`dashboard.html` is BUILT, not committed, so publishing a stale copy is worse
than not publishing it: a dashboard that silently describes yesterday is the
decayed-evidence fault. The publish step builds it fresh or refuses.

`STATUS.md` is markdown and the site serves HTML. Rendering it needs a
converter; adding a dependency for that needs a decision record naming its
licence, so prefer a minimal in-repo renderer or serve it as plain text with
its content type set honestly.

## Both halves

Accepting: four files become six, every one requested after deploy, each
printing its own `pageResult=OK`, and the two restored taps return 200.
Rejecting: with one audit file missing the publisher REFUSES and names it,
rather than shipping a site whose links 404. A fix that ships the link without
the file has recreated the fault it closes.
