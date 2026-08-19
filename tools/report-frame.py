#!/usr/bin/env python3
"""WHICH PICTURE GOES WITH THE UPDATE, and which one it should sit beside.

    python3 tools/report-frame.py            # the current noon frame + its before
    python3 tools/report-frame.py --night    # the night pair instead

WHY THIS EXISTS. Jafar asked on 4 August why twenty-four hours looked like
almost nothing, about a day whose single biggest change — the street going from
featureless dummies to people with skin and a walk — was sitting in this
repository as a JPEG the whole time. The rule that came out of it is his:
**every report carries a picture.**

A rule that depends on me remembering to go and find the right file is a rule
that decays, and this project's notes are mostly a list of things that decayed.
So the lookup is mechanical.

TWO FRAMES, NOT ONE. A single still says what the game looks like; a pair says
what CHANGED, which is the question actually being asked. The "before" is the
previous version of the same file — git already tracks it, so there is nothing
to store and nothing to keep in sync.

AND IT REFUSES TO OFFER A FRAME FROM A BUILD THAT RENDERED NOTHING. A run whose
licence activation failed, or whose Game layer would not compile, still commits
a verdict — and on 4 August one of them also committed six stills it could not
have made, from its own checkout, indexed under its own sha. So the newest
commit that touched a frame is not necessarily a commit that DREW one. This
walks back to the last one whose verdict says a sim actually ran, and says so.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "game-design" / "sim-shots"


def git(*args):
    p = subprocess.run(["git", "-C", str(ROOT), *args],
                       capture_output=True, text=True)
    return p.stdout.strip()


def ran(sha):
    """Did the run that produced this commit actually measure anything?

    Reads the per-run verdict rather than the commit message: a commit that
    says "Sim stills from X" is a claim, and `NO PLAYER LOG` in X's own verdict
    is the evidence. Missing verdict means it was not a build commit at all,
    which is also not a frame worth offering.
    """
    f = SHOTS / "runs" / f"{sha[:7]}.txt"
    if not f.exists():
        return False, "no verdict for this commit"
    body = f.read_text(encoding="utf-8", errors="replace")
    if "NO PLAYER LOG" in body:
        return False, "the sim did not run on this commit"
    return True, body.split("\n")[0]


def main():
    # ANY OF THE SIX, BECAUSE THE CHANGE IS NOT ALWAYS IN DAY ONE AT NOON.
    #
    # This offered `day1_noon`, or `day1_night` with a flag, and the build
    # commits six frames. On 5 August the night's most visible change — the
    # name labels going from seven per cent of screen height to under four —
    # was only legible in `day5_night`, where a dozen of them are in shot, and
    # the tool that exists to put a picture in every report could not reach it.
    #
    # `--frame day5_night` names one directly. The old flag still works,
    # because a rule that needs a new incantation to obey is a rule that gets
    # skipped at the moment it is least convenient.
    frame = "review_day1_night.jpg" if "--night" in sys.argv else "review_day1_noon.jpg"
    if "--frame" in sys.argv:
        i = sys.argv.index("--frame")
        if i + 1 >= len(sys.argv):
            print("report-frame: --frame needs a name, e.g. --frame day5_night")
            return 2
        # `hunt_` FRAMES ARE REACHABLE TOO, and this is the third place that
        # had to learn the prefix — after the workflow's copy glob and
        # `sim-shots-stage.sh`. The sim commits a pair taken while the
        # detective is running a manhunt, which is the most dramatic state the
        # game has and therefore the frame a report most often wants; a tool
        # whose whole job is putting a picture in a report could not reach it.
        #
        # The name is taken as given if it already carries a prefix, so
        # `--frame hunt_day13_night` works and so does `--frame day1_noon`.
        want = sys.argv[i + 1].replace(".jpg", "")
        shots = ROOT / "game-design" / "sim-shots"
        frame = want + ".jpg" if want.startswith(("review_", "hunt_")) \
            else f"review_{want}.jpg"
        if not (shots / frame).exists() and (shots / f"hunt_{want}.jpg").exists():
            frame = f"hunt_{want}.jpg"
        if not (shots / frame).exists():
            have = sorted(p.name[:-len(".jpg")]
                          for p in list(shots.glob("review_*.jpg"))
                          + list(shots.glob("hunt_*.jpg")))
            print(f"report-frame: no frame called {want}. This build committed: "
                  + (", ".join(have) if have else "nothing"))
            return 2
    rel = f"game-design/sim-shots/{frame}"

    # Every commit that CHANGED this frame, newest first. A build that rendered
    # nothing leaves the file untouched, so most of the list is real — but not
    # all of it, which is what the check below is for.
    history = git("log", "--format=%H", "-40", "--", rel).split()
    if not history:
        print(f"report-frame: nothing has ever committed {frame}")
        return 1

    good = []
    for sha in history:
        # The frame is committed by the run that made it, and the run's verdict
        # is committed in the same breath — so the sha that touched the JPEG is
        # the sha to ask about.
        subject = git("log", "-1", "--format=%s", sha)
        stamp = subject.split()[-1] if subject.startswith("Sim stills from") else sha[:7]
        ok, why = ran(stamp)
        if ok:
            good.append((sha, stamp, why))
        if len(good) == 2:
            break

    if not good:
        print(f"report-frame: no commit in the last {len(history)} touching "
              f"{frame} came from a run that measured anything — do not "
              f"attach a picture, say the build produced nothing")
        return 1

    now = SHOTS / frame
    print(f"NOW   {now}")
    print(f"      from {good[0][1]} — {good[0][2]}")
    if len(good) < 2:
        print("BEFORE (none: only one measuring run has ever touched this frame)")
        return 0

    # The before goes to a temp path rather than the repository, because it is
    # a thing to look at once and not a file this project should carry.
    out = Path("/tmp") / f"before_{good[1][1]}_{frame}"
    blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{good[1][0]}:{rel}"],
                          capture_output=True)
    out.write_bytes(blob.stdout)
    print(f"BEFORE {out}")
    print(f"      from {good[1][1]} — {good[1][2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
