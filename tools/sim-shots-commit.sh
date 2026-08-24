#!/usr/bin/env bash
# The body of the Windows job's "Commit the review stills" step, moved out
# verbatim on 22 Aug because the step had grown to 23k characters — 416
# under the hard expression ceiling that fails a workflow AT DISPATCH, so
# every comment edit in there was a coin flip against getting any build at
# all. Same move as sim-shots-stage.sh, for the same reason: a file has no
# ceiling, and this whole block is executable history nobody should trim
# to fit a limit.
#
# Runs on the Windows runner under bash. Needs from the step:
#   GH_TOKEN        - the push credential (checkout is persist-credentials:false)
#   LICENSE_FIRST   - steps.unity_license.outcome
#   LICENSE_RETRY   - steps.unity_license_retry.outcome, or "not needed"
# Everything else ($GITHUB_STEP_SUMMARY, $GITHUB_REF_NAME, $GITHUB_SHA) is
# ambient runner environment.
set -u

# AND IT SAYS WHAT HAPPENED SOMEWHERE READABLE. This step failed six
# times and reported success, and the reason was undiagnosable from
# outside: `continue-on-error` hides the exit code, and this step's log
# sits above the fixed ~4KB tail the log API returns, which post-job
# cleanup fills entirely. The step summary is the one channel out of a
# job here that survives — it is how the sim verdict already gets home.
say() { echo "$1"; echo "$1" >> "$GITHUB_STEP_SUMMARY"; }
echo "## Review stills" >> "$GITHUB_STEP_SUMMARY"

shopt -s nullglob
mkdir -p game-design/sim-shots
# `hunt_*` TOO — the pair taken while the manhunt is live.
# `sim-shots-stage.sh` learnt about them and this glob did not, so
# `huntStills=2/2` came back with no `hunt_*.jpg` committed:
# rendered, never copied, and only the verdict key said so.
shots=(sim-run/sim-out/review_*.jpg sim-run/sim-out/hunt_*.jpg sim-run/sim-out/district_*.jpg)
if [ ${#shots[@]} -eq 0 ]; then
  # NOT `exit 0`, AND THE DIFFERENCE IS THE WHOLE POINT OF THE STEP.
  # Bailing here left the PREVIOUS run's verdict.txt sitting in the
  # repository, so the one thing a catastrophically broken run
  # produces is a stale verdict that reads exactly like a fresh one.
  # The header carries the SHA, which is the only reason that has not
  # yet cost anything. A run with no stills still has a log worth
  # grepping and a ledger worth committing, so carry on.
  say "no review stills — the sim did not reach a screenshot"
else
  say "${#shots[@]} still(s) rendered"
  cp "${shots[@]}" game-design/sim-shots/
  STILLS_MINE=1
fi

# THE CLIP SHEET, ON ITS OWN FLAG, and `[ -f ]` NOT AN ARRAY: the
# first version copied the glob idiom above and missed that
# `nullglob` only empties a WILDCARD, so `cp` always ran and the
# first build that rendered nothing died here under `-e`, taking the
# verdict with it. Account in `game-design/clip-findings.txt`.
if [ -f sim-run/sim-out/clips.jpg ]; then
  cp sim-run/sim-out/clips.jpg game-design/sim-shots/ || true
  [ -f sim-run/sim-out/clips.tsv ] \
    && { cp sim-run/sim-out/clips.tsv game-design/sim-shots/ || true; }
  CLIPS_MINE=1
  say "clip sheet rendered ($(du -k sim-run/sim-out/clips.jpg | cut -f1) KB)"
else
  # NAME WHAT IS THERE INSTEAD. Run 3c6d160 printed this line while the
  # sim's own verdict said sheetTiles=64 — drawn but never landed here —
  # so a miss now lists the directory it looked in, which separates
  # "the pass never ran" from "it wrote somewhere else" and from "the
  # encode died after drawing" (rule 3b: a zero needs a denominator).
  say "no clip sheet — sim-run/sim-out holds: $(ls sim-run/sim-out 2>/dev/null | head -8 | tr '\n' ' ' || echo 'nothing — no such directory')"
fi
ls -la game-design/sim-shots/

# AND THE VERDICT, AS A FILE IN THE REPOSITORY — the one channel out
# of this job that has ever worked. The log API returns a fixed ~4KB
# BYTE tail, not a line count, so nothing mid-log is reachable and
# post-job cleanup fills that window every time. The step summary
# comes back EMPTY through the check-run API, and artifacts live on a
# host this project's review environment is denied outright.
#
# So every diagnostic the sim prints was unreadable unless it landed
# in the last four kilobytes, and three faults in one night had to be
# inferred from a step's DURATION. A file in the repository can
# simply be read. Grepped rather than copied whole — player.log is
# megabytes and the point is the few lines that answer a question.
# THE HEADER IS WRITTEN UNCONDITIONALLY, and it used to be written
# only when there was a player.log to grep. That meant the single
# worst kind of run — one that never reached the sim at all — left
# the PREVIOUS run's verdict.txt sitting in the repository, freshly
# committed by this very step, indistinguishable from a real result
# except for a SHA on line one that a reader has to think to check.
# Truncating here means a broken run produces a verdict that says so.
{
  # THE COMMIT'S OWN TIMESTAMP, ON LINE ONE, because the only other
  # way to ask "is this run newer than that one" needs history and
  # there is none — `actions/checkout` clones at depth 1.
  #
  # The first version of the ordering rule used `git merge-base
  # --is-ancestor`, which on a shallow clone cannot resolve the other
  # run's commit at all, fails, and takes the "theirs is newer" branch
  # every single time. So the run carrying the fix for the upside-down
  # player contributed its numbers and NO STILLS, and the pictures on
  # the branch stayed the ones from before the fix — a feedback channel
  # closed by the change meant to protect it.
  #
  # An epoch second compares without history and is present on a
  # shallow clone, because the commit itself is always there.
  echo "# Sim verdict — ${GITHUB_SHA:0:7} @$(git show -s --format=%ct ${GITHUB_SHA})"
  echo
  echo "Written by the Windows build. Overwritten every run — but"
  echo "also kept per-commit under sim-shots/runs/, so two builds"
  echo "dispatched together are two answers rather than one."
  echo "Read this instead of trying to tail the job log."
  echo
} > game-design/sim-shots/verdict.txt

# THE SPEECH RUNTIME'S OUTCOME, IN THE ONE CHANNEL THIS ENVIRONMENT CAN
# READ (rule 12). `speechLive` has been 0 across 301 builds with
# `speechNoModel=29`, and the reason lived only in a `continue-on-error`
# step's echo, in a job log that cannot be tailed from here. So "the fetch
# 404s", "the runtime loaded but no voice model shipped" and "the backend
# is off by design" were indistinguishable, and they have completely
# different next actions.
#
# OUTSIDE THE player.log BRANCH ON PURPOSE: a build that never reaches the
# sim should still say whether the runtime arrived, and that is exactly the
# run where the question is hardest to answer any other way.
#
# Spaces become underscores because a verdict value may not contain one --
# the reader splits on whitespace and would return the first word silently.
if [ -f speech-fetch.txt ]; then
  echo "speechRuntime=[$(tail -3 speech-fetch.txt | tr -d '\r' \
        | tr '\n' ';' | tr ' ' '_' | tr -s '_' | cut -c1-150)]" \
    >> game-design/sim-shots/verdict.txt
else
  echo "speechRuntime=[no_fetch_record]" >> game-design/sim-shots/verdict.txt
fi

if [ -f sim-run/player.log ]; then
  {
    # ASCII ONLY IN THE PATTERN, and matched on distinctive
    # substrings rather than prefixes. The places line starts with a
    # section sign, and a non-ASCII byte in a grep pattern under Git
    # bash on Windows is a coin flip about encoding that silently
    # matches nothing and looks like "the sim never printed it".
    # `brandished a cosh` carries the HAND TIER, which otherwise
    # appears only in the threat gate's label — printed when the gate
    # FAILS. Backwards for a diagnostic: `hand=hand bone` on a GREEN
    # run is what proves the bought skeleton holds the object.
    # AN ALLOWLIST THAT HAS SILENTLY EATEN THREE PIECES OF WORK:
    # windowWarmth, ringGrowth, and — to the commit repairing this
    # very channel — ALL GATES. Each built, ran, went green, never
    # arrived. `[series]` is matched as a FAMILY so the next probe
    # needs nobody to remember this file; anything else must be
    # named. tools/verdict-reach.py reads this pattern and lists what
    # the sim prints that never lands. Full account in its docstring:
    # this step has a hard size limit and a longer version of this
    # paragraph broke dispatch outright (422, max expression length).
    grep -E "FAILING GATES|SimDirector: ALL GATES|SimDirector: done\.|SimDirector: sky |SimDirector: glyphs |alley eyes=|Traffic: wheels |brandished a cosh|SimDirector: windowGlow|\[series\]|\[panel\]|SceneAudit: " \
      sim-run/player.log || echo "(no SimDirector lines matched)"
    # A filter that drops a line in silence is what made that cost a
    # round trip. This says it in the verdict, on the run it happens.
    grep -q "SimDirector: ALL GATES" sim-run/player.log \
      || echo "NOTE: no ALL GATES line — build predates it, or the sim died before the summary."

    # WHERE IT STOPPED, WHEN IT DID NOT FINISH — the channel fix, rule 12.
    #
    # Three runs in a row were killed by the sim step's 24-minute
    # `Wait-Process` timeout (24m03s against a 1440s wait; complete runs take
    # about twelve minutes). Each left a verdict assembled from greps, so what
    # arrived was a SET OF SECTIONS with the done line absent — and nothing in
    # it said where the run had got to. One reached day 6, one day 2, one took
    # no shots at all, and I read that variance backwards twice: first as a
    # deterministic code fault, then as a busy machine, because the only
    # evidence was which greps happened to match.
    #
    # The last lines of the log are the one thing that says what it was DOING.
    # Emitted only when there is no done line, so a healthy run is unchanged,
    # and capped because this file is read whole. `hangTail` is greppable and
    # the count is stated so a truncated tail cannot look like a short log
    # (rule 3b).
    if ! grep -q "SimDirector: done\." sim-run/player.log; then
      echo "hangTail=[the sim produced no done line; the last 30 log lines follow]"
      echo "hangTailLines=$(wc -l < sim-run/player.log | tr -d ' ')"
      tail -30 sim-run/player.log | tr -d '\r' | sed 's/^/hangTail| /'
    fi
  } >> game-design/sim-shots/verdict.txt
  # AND THE EDITOR-SIDE LINES, IN A SCRIPT, BECAUSE THIS STEP IS FULL.
  # `verify.py` refused the inline version at 1,234 characters over the
  # dispatch limit, and a step that cannot be dispatched is a build
  # that cannot run. The reasoning lives in the script.
  bash tools/verdict-characters.sh build-log/unity.log \
    >> game-design/sim-shots/verdict.txt
  say "verdict.txt written ($(wc -l < game-design/sim-shots/verdict.txt) lines)"
else
  say "no player.log — the sim did not run"
  echo "NO PLAYER LOG — the sim did not run on this commit." \
    >> game-design/sim-shots/verdict.txt
  # AND WHY, WHICH IS THE WHOLE DIAGNOSIS.
  #
  # "The sim did not run" has two completely different causes and the
  # line above cannot tell them apart: a Game-layer compile error,
  # which is mine and cannot be caught locally, or a licence
  # activation failure, which is contention between my own parallel
  # dispatches and is nothing to do with the code. Reading the second
  # as the first cost several minutes of staring at correct C#.
  #
  # Both attempts are named, because "failed then recovered" is worth
  # knowing too — it is the measurement that says how close the
  # dispatch rate is running to the limit.
  {
    echo "  first licence attempt : ${LICENSE_FIRST:-unknown}"
    echo "  second licence attempt: ${LICENSE_RETRY:-unknown}"
    echo "  IF EITHER SAYS failure, THIS IS NOT A COMPILE ERROR — it is"
    echo "  contention for a Personal licence seat between concurrent builds."
    echo "  Dispatch fewer at once; do not go looking in the Game layer."
  } >> game-design/sim-shots/verdict.txt

  # AND IF IT WAS THE COMPILER, PUT THE ERRORS WHERE THEY CAN BE READ.
  #
  # THIS IS RULE 12, AND IT HAD BEEN HALF-DONE FOR MONTHS. The build
  # step already extracts `error CS` lines — into the step log, which
  # is a fixed ~4KB tail and evicts them, and into
  # GITHUB_STEP_SUMMARY, which comes back EMPTY through the API this
  # environment has. Two channels, both carefully populated, neither
  # readable from the container that needs them.
  #
  # So a Game-layer compile error — the ONE class of fault that
  # cannot be caught locally, because only Core compiles here — was
  # costing a blind 25-minute round trip and a guess. On 4 August it
  # cost one, and I spent the wait inspecting correct code while the
  # answer sat in a log nobody could open.
  #
  # `verdict.txt` is a file in the repository. It is committed by the
  # step below, which runs on failure, and `git pull` reads it in a
  # second. That is the whole fix and it is fifteen lines.
  if [ -f build-log/unity.log ]; then
    {
      echo
      echo "COMPILE ERRORS (from build-log/unity.log):"
      grep -E "error CS|Compilation failed" build-log/unity.log \
        | head -25 | sed 's/^/  /' \
        || echo "  none matched — the build failed for another reason"
    } >> game-design/sim-shots/verdict.txt
  fi
fi

# LAYER 3, PIXELS: what moved in the render since the last build.
#
# The comparison happens HERE and not in the sim, because this is the
# only place both ledgers exist at once — the checkout carries the
# previous run's committed copy and sim-out carries the new one. It
# has to run BEFORE the copy below, or it would compare the new
# ledger against itself and report, with total confidence, that
# nothing had changed.
#
# Reports, does not gate. The run-to-run noise floor of a mean
# luminance on a software rasteriser is not known yet, and rule 2 is
# explicit that inventing it is how `nightNotDarker` came to fail at
# 0.136 against 0.135.
# STAMP FIRST, THEN COMPARE, and the order is the whole of it.
#
# The sim cannot know its own SHA; this step can. Without the stamp a
# drift block cannot tell "the same commit built twice" (which IS the
# noise floor) from "two different commits" (which is the change plus
# the noise, readable as neither) — a distinction already got wrong
# once, when a delta that was mostly a white capsule leaving every
# frame got described as run-to-run variance.
#
# The first version of this stamped the file on the way into the
# repository, i.e. AFTER the comparison had already read the unstamped
# original — so the new side never carried a stamp and the block said
# "commits unstamped" every run, for ever, which is exactly the
# silent-no-op shape this project keeps producing. Stamped into a temp
# first, compared, then moved.
if [ -f sim-run/sim-out/frames.tsv ]; then
  { echo "# commit ${GITHUB_SHA}"; cat sim-run/sim-out/frames.tsv; } \
    > "$RUNNER_TEMP/frames-stamped.tsv"
fi
{
  echo
  python3 tools/frame-drift.py \
    game-design/sim-shots/frames.tsv \
    "$RUNNER_TEMP/frames-stamped.tsv" \
    || echo "FrameDrift: the drift tool itself failed"
} >> game-design/sim-shots/verdict.txt
if [ -f "$RUNNER_TEMP/frames-stamped.tsv" ]; then
  cp "$RUNNER_TEMP/frames-stamped.tsv" game-design/sim-shots/frames.tsv
  FRAMES_MINE=1
  # COUNTED, NOT SUBTRACTED. This said `wc -l ... - 4` for the four
  # non-data lines, and adding the commit stamp above made it five —
  # a magic number falsified by the commit that changed the file it
  # counts, which is the whole shape of the stale-comment problem.
  say "frame ledger: $(grep -cv '^#\|^shot' game-design/sim-shots/frames.tsv) shot(s)"
else
  say "NO FRAME LEDGER — the sim wrote no frames.tsv"
fi

# A PER-RUN COPY, SO TWO BUILDS IN FLIGHT ARE TWO ANSWERS.
#
# This job has no concurrency group and is dispatch-only, so N builds
# can already run at once — nothing queues them. What made that
# useless is right below: every run writes the SAME verdict.txt and
# the SAME four JPEGs, so a second run landing after the first
# overwrites the answer I dispatched it for, and I get one result for
# two round trips without being told.
#
# That is the whole reason five hypotheses about the upside-down
# player cost five serial half-hours instead of two waves. The
# verdict is a few kilobytes of text; keeping one per commit costs
# nothing and can never collide, because the filename carries the SHA.
# `verdict.txt` stays exactly as it was — the latest run, where every
# reader already looks.
mkdir -p game-design/sim-shots/runs
cp game-design/sim-shots/verdict.txt \
   "game-design/sim-shots/runs/${GITHUB_SHA:0:7}.txt"
# Keep the last twenty. Unbounded, this grows a file per build for
# ever; twenty is about a day of parallel waves, which is as far back
# as anything has ever been read.
ls -1t game-design/sim-shots/runs/*.txt 2>/dev/null | tail -n +21 \
  | xargs -r rm -f

git config user.name  "Claude"
git config user.email "noreply@anthropic.com"

# WHAT THIS RUN PRODUCED, AND NOTHING ELSE — the reasoning, and the
# build that reverted six stills it never rendered, are in the script.
mapfile -t ours < <(bash tools/sim-shots-stage.sh "${GITHUB_SHA:0:7}" \
                    "${STILLS_MINE:-0}" "${FRAMES_MINE:-0}" "$RUNNER_TEMP/ours" \
                    "${CLIPS_MINE:-0}")
say "committing ${#ours[@]} file(s) this run produced (stills=${STILLS_MINE:-0} frames=${FRAMES_MINE:-0} clips=${CLIPS_MINE:-0})"

# The script also stocks $RUNNER_TEMP/ours, which the retry loop puts
# back on top of whatever another run pushed meanwhile.
git add "${ours[@]}"
if git diff --cached --quiet; then
  say "stills identical to the committed ones — nothing to commit"
  exit 0
fi
git commit -m "Sim stills from ${GITHUB_SHA:0:7}

What the street actually looks like, at the size it is played at.
Committed because the artifact host is unreachable from the review
environment, so an ASCII luminance grid was standing in for the
picture."
# REBASE BEFORE EACH ATTEMPT, because the branch moves under a
# twenty-eight-minute build. This job checks out a commit, spends half
# an hour rendering, and by the time it pushes there may well be newer
# work on the branch — in which case a plain push is rejected, and
# retrying the identical push six times just fails six times and drops
# the stills on the floor. The retry loop was written for flaky
# networks and reads every rejection as one.
# THE CREDENTIAL, FOR THIS STEP ONLY — see the checkout step above.
origin="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"

# REDIRECTED, NOT PIPED. `git push | sed` reports SED's exit status,
# which is zero whatever git did — a retry loop that can never observe
# a failure, bolted onto a step whose entire problem was failing
# invisibly. The log is filtered afterwards so the token cannot reach
# a public log.
for i in 1 2 3 4 5 6; do
  if git push "$origin" HEAD:${GITHUB_REF_NAME} > "$RUNNER_TEMP/push.log" 2>&1; then
    say "pushed ${#shots[@]} still(s) to ${GITHUB_REF_NAME}"
    exit 0
  fi
  sed "s|${GH_TOKEN}|***|g" "$RUNNER_TEMP/push.log" || true
  echo "push failed, attempt $i — refetching and reapplying our outputs"
  # REAPPLIED, NOT REBASED, AND THE DIFFERENCE ONLY SHOWS UP WHEN TWO
  # BUILDS RUN AT ONCE.
  #
  # `git rebase FETCH_HEAD` replays our stills commit onto whatever
  # arrived. Against ordinary source commits that is fine, and it is
  # what this loop did for weeks. Against ANOTHER BUILD'S stills it
  # is a binary conflict on four JPEGs — rebase stops, the `|| abort`
  # below it puts the branch back, and the next five attempts push
  # the identical rejected commit and fail identically. A whole run's
  # results land nowhere, and the step's own retry logging makes it
  # read like a flaky network.
  #
  # These files are RENDERED OUTPUT, not content anybody merged, so
  # there is nothing to reconcile: the newest render of a frame is
  # the right one. Reset to what is on the branch, lay our outputs
  # back over the top, commit that. It cannot conflict. The other
  # run's per-run verdict survives untouched, because `cp` overlays
  # and its filename carries a different SHA — which is the point of
  # writing it in the first place.
  # AND "NEWEST RENDER" IS NOT "LAST TO FINISH", which is the half of
  # that reasoning the first version got wrong.
  #
  # Two builds ran together on 3 Aug. The one on the NEWER commit
  # finished first and pushed its verdict; the one on the OLDER commit
  # finished second, hit this path, and laid its own older output over
  # the top. `verdict.txt` ended up naming the earlier commit — so the
  # file every reader treats as "the latest" was the stale answer, and
  # only the SHA on line one said so. Runners vary by twenty minutes
  # here, so dispatch order tells you nothing about landing order.
  #
  # So: if what is already on the branch was rendered from a commit we
  # are a descendant of, we are newer and ours wins. Otherwise theirs
  # is newer or unrelated, and we take ONLY our per-run file — which
  # cannot collide, and is the whole reason it exists.
  if git fetch "$origin" ${GITHUB_REF_NAME} > /dev/null 2>&1; then
    git reset --hard FETCH_HEAD > /dev/null
    theirs=$(head -1 game-design/sim-shots/verdict.txt 2>/dev/null \
             | sed -n 's/.*@\([0-9]\{6,\}\).*/\1/p')
    mine=$(git show -s --format=%ct ${GITHUB_SHA})
    # DEFAULTS TO OURS WINNING, and that direction is deliberate.
    # The first version defaulted the other way and, because the
    # ancestry test it used can never succeed on a shallow clone, the
    # newest run stopped updating the stills entirely — silently, and
    # in the one direction that costs a feedback channel. Never
    # landing is worse than landing out of order: an unreadable
    # verdict is a build wasted, a stale one at least carries its own
    # timestamp on line one.
    mine_wins=1
    if [ -n "$theirs" ] && [ -n "$mine" ] && [ "$theirs" -gt "$mine" ] 2>/dev/null; then
      mine_wins=0
    fi
    if [ "$mine_wins" = "1" ]; then
      # `ours` now holds only what this run produced, so this copy can
      # no longer reinstate the checkout's stills over a newer run's.
      cp -r "$RUNNER_TEMP/ours/." game-design/sim-shots/
      say "ours is newer than ${theirs:-nothing} — updating the latest verdict and stills"
    else
      mkdir -p game-design/sim-shots/runs
      cp "$RUNNER_TEMP/ours/runs/${GITHUB_SHA:0:7}.txt" \
         game-design/sim-shots/runs/ 2>/dev/null || true
      say "a NEWER run ($theirs) already landed — keeping its stills, adding only our per-run verdict"
    fi
    git add game-design/sim-shots ':(exclude)game-design/sim-shots/verdict-keys.json'
    git diff --cached --quiet \
      || git commit -q -m "Sim stills from ${GITHUB_SHA:0:7}"
  else
    echo "fetch failed too — retrying the push unchanged"
  fi
  sleep $((2 ** i))
done
say "PUSH FAILED after 6 attempts — the stills did not land"
exit 1
