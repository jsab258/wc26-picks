line: production (the channel to Jafar)
spec: found 2026-09-06 by the agent building the notification consumer, while
  answering whether the served page can be requested at all.
acceptance: one publish-glance run reaching its steps and printing
  pageResult=OK, and the served map URL answering 200 with this branch's
  commit in its stamp
max_sessions: 1
status: DONE 2026-09-07. Jafar allowed the branch to deploy and a re-run
  landed it: publish run 12 attempt 2 succeeded on 85b5222a, and run 13 on
  284cfb76. The glance, the map and the gallery are served. Eleven of eleven
  runs had failed in seconds with zero steps executed under an environment
  protection rule, which no code change here could ever have fixed.

## The finding, confirmed twice

All 11 publish-glance runs have FAILED, every one since the workflow landed on
2026-09-05T17:19. Each completes in a few seconds with ZERO STEPS EXECUTED.
Run 11 was created at 16:08:10 and finished at 16:08:13.

    Branch "claude/game-dev-ai-automation-2h67ix" is not allowed to deploy to
    github-pages due to environment protection rules.

Confirmed by the builder from the Actions API and then again by the resident
independently, because a claim this consequential should not rest on one read.

## What it means, and it is worse than a missing page

`https://jsab258.github.io/wc26-picks/map.html` has never been served from this
branch. Every link this studio has sent Jafar today, in this conversation and
in the message waiting in `production/outbox/`, leads to a 404 or to the
repository's old index.

THE GLANCE, THE MAP AND THE GALLERY ARE ALL AFFECTED. The register's link
allowlist names exactly those three pages, so every compliant message this
studio can write links to something that does not exist.

## What has to happen, and only Jafar can do it

GitHub repository Settings, Environments, `github-pages`, deployment branches:
allow `claude/game-dev-ai-automation-2h67ix`. Or a ruling to publish from a
branch that is already allowed, which the studio can then implement.

## Two things this explains

Queue 097's acceptance, "done when the run prints pageResult=OK", HAS NEVER
BEEN REACHABLE. No publish job has reached a step that could print it, so an
item has been sitting at WAITS on a condition that could not occur.

And the notification consumer built today is `needs: publish`, so it correctly
does nothing while this holds. That is the design working. It also means the
whole notification path stays unproven end to end until this is lifted, and
nobody may report it as working before then.

## The rule this is an instance of

A page that is generated is not a page that is served, and a workflow that runs
is not a workflow that reaches its steps. This project already knows to verify
a job's EFFECTS rather than its exit code; here the effect was never even
attempted, and eleven runs went red in a lane nobody was reading.
