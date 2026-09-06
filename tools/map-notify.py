#!/usr/bin/env python3
"""THE CONSUMER OF THE MAP'S MATERIAL-CHANGE DETECTOR: a published page that
answers, a state he has not been told about, and a message written for the
sender. Nothing here delivers anything.

    python3 tools/map-notify.py --served-map URL --map-link URL \\
        --expect-commit <sha>            # the one live path, run in CI
    python3 tools/map-notify.py --selftest        # accepting case FIRST

WHY THIS FILE EXISTS. `tools/map.py` computes `mapMaterialChange` and prints
it, and on 2026-09-06 a grep for that key returned hits inside `tools/map.py`
and nowhere else: a good instrument nobody asks a question of. Jafar asked for
the map's link on Telegram whenever the page changes materially. This is the
half between the detector and the sender.

WHERE IT RUNS, AND THE MEASUREMENT THAT DECIDED IT. It runs on the GitHub
Actions runner, in a job after the deploy, NOT in the studio container and NOT
inside `tools/publish-glance.py`. Measured 2026-09-06 from the container:

    curl https://jsab258.github.io/wc26-picks/map.html
    curl: (56) CONNECT tunnel failed, response 403       http=000

The container cannot request the served page at all, so a consumer there could
only ASSUME publication succeeded, and a notification linking to a page that
did not publish is worse than no notification. It is not inside
publish-glance.py because that file's own docstring rules what it is: it does
not generate, it does not write into the tree, and its selftest builds into a
temporary directory. Writing an outbox message and a committed record is a
second responsibility with a different permission (`contents: write`), which is
why it is a separate job in the same workflow rather than a fourth thing the
publisher does.

WHAT "PUBLISHED" MEANS HERE, and it is not an exit code. The served URL is
REQUESTED and the body is read: `tools/publish-glance.py:evaluate` decides
whether that body is our page built from this commit (200, text/html, our
stamp, the expected commit). Only `pageResult=OK` may notify. A request that
does not complete is NOT a 404 and is not a failure to publish either: it is
nothing measured, and it refuses to notify rather than assume.

WHERE THE TWO STATES COME FROM, and why not from the done line. The CURRENT
state is read out of the SERVED BODY: `tools/map.py` writes
`<!-- mapDigest=... mapFields=... -->` into the page, so the state being
announced is the state of the page he will actually open. The PREVIOUS state is
the record below. The detector's own `mapMaterialChange=` value on map.py's
done line is deliberately NOT the input, and the reason is measured rather than
preferred: `publish-glance.py:build` runs each generator into a fresh
`TemporaryDirectory`, and `map.py:previous_digest` reads the file it is about
to overwrite, so in the publish job that value is `nothing-measured` on every
run, for ever.

    $ python3 tools/map.py --out FRESH/map.html | grep mapDigest
    mapDigest=dbd1725188a7 mapDigestPrev=nothing-measured
    mapMaterialChange=nothing-measured mapChangedFields=nothing-measured
    $ python3 tools/map.py --out FRESH/map.html | grep mapDigest   # again
    mapDigest=dbd1725188a7 mapDigestPrev=dbd1725188a7
    mapMaterialChange=no mapChangedFields=none

A consumer gated on that key would never fire. So the DETECTOR IS NOT
RE-DERIVED and is not re-implemented either: `material_fields`, `digest_of`,
`changed_groups` and the page decoder are imported from `tools/map.py` and
applied to the honest pair, which is (what is served now, what he was last
told). One implementation of the rule, in the file that owns it.

THE IDEMPOTENCE RECORD is `production/map-notified.json`, committed by the
notify job. It survives a fresh CI checkout because a checkout is where it
comes from; a sidecar in a container does not survive anything. It holds the
digest, the full material state behind that digest (so the groups that moved
can be NAMED without a second page to compare against), and whether a message
was written for it. Two states are recorded and both suppress a message: a
state that was announced, and a BASELINE state recorded on the first run, which
was never announced and never will be, because a first reading is not a change.

    THE FILENAME IS THE SECOND LAYER. A message is named
    <date>-the-map-changed-<digest>.unprompted.md, so a run whose commit was
    lost to a race re-writes THE SAME PATH rather than a second message.

AN OUTBOX FILE IS NOT A DELIVERY, and nothing this program prints may be read
as one. The message it writes is preparation. The only evidence that Jafar was
told anything is a receipt under `production/outbound/` carrying the platform's
own message id, written by `tools/runner/outbox.py` on his PC, and no such
receipt has ever existed. The done line says so in a key.

EXIT CODES, distinct per outcome, so a workflow can branch without parsing
prose. 0 a message was written. 2 the message this program wrote was REFUSED by
the register and removed again (a fault in this program, printed loudly). 3 the
selftest failed. 4 a component could not be imported. 10 the served state is
the recorded state (a regenerated clock, or a second publish of one state).
11 nothing was recorded before, so this run recorded the baseline and announced
nothing. 12 the served page is not the page this commit published. 13 the
served page could not be requested: NOTHING MEASURED. 14 the served page
carries no material state. 15 the served page disagrees with itself. 16 the
digest moved and no material group did. 17 the record exists and cannot be
read, which is refused rather than treated as a first run.
"""
import argparse
import datetime
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = "tools/map-notify.py"
HERE = Path(__file__).resolve().parent
REPO = HERE.parent

EXIT_WRITTEN = 0
EXIT_REGISTER_REFUSED = 2
EXIT_SELFTEST_FAILED = 3
EXIT_COMPONENT_MISSING = 4
EXIT_NO_CHANGE = 10
EXIT_BASELINE = 11
EXIT_PAGE_NOT_OURS = 12
EXIT_PAGE_NOT_MEASURED = 13
EXIT_PAGE_NO_STATE = 14
EXIT_PAGE_INCONSISTENT = 15
EXIT_NO_GROUP_MOVED = 16
EXIT_RECORD_UNREADABLE = 17


def _load(path, name):
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:                                            # noqa: BLE001
        return None


# ONE IMPLEMENTATION PER IDEA. The detector, the fetch and the served-page
# verdict all already exist in this repository and are imported, never retyped.
MAP = _load(HERE / "map.py", "ledger_map")
PUB = _load(HERE / "publish-glance.py", "ledger_publish_glance")
PRODUCER_CHECK = HERE / "producer-check.py"
if MAP is None or PUB is None or not PRODUCER_CHECK.is_file():
    sys.stderr.write(
        "%s: a component is missing, so nothing was measured: map.py=%s "
        "publish-glance.py=%s producer-check.py=%s\n"
        % (TOOL, "ok" if MAP else "MISSING", "ok" if PUB else "MISSING",
           "ok" if PRODUCER_CHECK.is_file() else "MISSING"))
    sys.exit(EXIT_COMPONENT_MISSING)

RECORD_REL = "production/map-notified.json"
OUTBOX_REL = "production/outbox"
RECEIPT_DIR = "production/outbound"
HISTORY_CAP = 20

# THE THREE MATERIAL GROUPS IN HIS WORDS, not in the key's. The right-hand side
# is the page's own heading (tools/map.py: "what you can run today", "what
# state each area is in", "the next three"), so the message names what he sees
# rather than a group id. The keys are map.py's and the order is map.py's.
GROUP_WORDS = {
    "q1": "the list of what you can run today",
    "q2": "the state an area is in",
    "q3": "the next three",
}
GROUP_ORDER = ("q1", "q2", "q3")


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ the page

RESULT_RX = re.compile(r"pageResult=(\S+)")
REASON_RX = re.compile(r"reason=(\S+)")


def read_served_state(body):
    """(digest, fields, why). The material state OUT OF THE SERVED BYTES.

    Both readings come from tools/map.py: the digest pattern it writes and the
    decoder for the base64 state beside it. `why` names which half was absent
    when either is, because "no state" and "no page" are different facts.
    """
    m = MAP.DIGEST_RX.search(body or "")
    digest = m.group(1) if m else None
    fields = MAP.decode_fields(body or "")
    if digest is None and fields is None:
        return None, None, "neither-mapDigest-nor-mapFields-in-the-served-body"
    if digest is None:
        return None, fields, "no-mapDigest-in-the-served-body"
    if fields is None:
        return digest, None, "no-mapFields-in-the-served-body"
    return digest, fields, ""


# ---------------------------------------------------------------- the record

def read_record(repo):
    """(record, why). `record` is None when there is none, which is a FIRST
    RUN. An unreadable record is neither None nor a record: it comes back as
    (False, why) so the caller refuses instead of announcing a change it cannot
    prove is one."""
    p = Path(repo) / RECORD_REL
    if not p.is_file():
        return None, "no-record-file-at-%s" % RECORD_REL
    try:
        blob = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                                       # noqa: BLE001
        return False, "record-did-not-parse/%s" % type(e).__name__
    last = blob.get("last")
    if not isinstance(last, dict) or not last.get("digest"):
        return False, "record-carries-no-last-digest"
    return last, ""


def write_record(repo, last, whole=None):
    """Rewrite the record, keeping a capped history whose cap announces itself.

    The history is the SERIES: every state this consumer has ever accepted as
    served, with whether a message was written for it. A bound on how often the
    map moves materially would be read off this file, and there is nothing to
    read it off yet.
    """
    p = Path(repo) / RECORD_REL
    blob = whole
    if blob is None:
        try:
            blob = json.loads(p.read_text(encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            blob = {}
    if not isinstance(blob, dict):
        blob = {}
    history = [h for h in blob.get("history", []) if isinstance(h, dict)]
    history.append({k: last[k] for k in ("digest", "at", "notified", "why",
                                         "changedFields", "message")
                    if k in last})
    dropped = int(blob.get("historyDropped", 0))
    if len(history) > HISTORY_CAP:
        dropped += len(history) - HISTORY_CAP
        history = history[-HISTORY_CAP:]
    out = {
        "what": ("The material state of the published map that this consumer "
                 "last ACCEPTED AS SERVED, and whether a message was written "
                 "for it. Written only by " + TOOL + ", only from a page that "
                 "answered as ours. A state recorded here is never announced "
                 "twice; a baseline recorded here was never announced at all, "
                 "because a first reading is not a change. An outbox message "
                 "is not a delivery: the receipt under " + RECEIPT_DIR +
                 " carrying the platform's message id is."),
        "last": last,
        "historyCap": HISTORY_CAP,
        "historyDropped": dropped,
        "history": history,
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                 encoding="utf-8")
    return out


# -------------------------------------------------------------- the decision

def decide(page_code, page_result, page_reason, digest, fields, state_why,
           record, record_why):
    """PURE. (result, reason, groups, exitCode).

    Every refusal is a NAMED reason with no spaces in it, because this value
    reaches a key=value line and every reader of one splits on whitespace.
    Kept free of I/O so the selftest drives the same arithmetic the CI run
    prints, which is why the ordering below is testable at all: publication
    first, then a state to read, then a state to compare against, then change.
    """
    if page_code == 3:
        return ("NONE", "the-published-page-could-not-be-requested/%s"
                % (page_reason or "request-did-not-complete"), None,
                EXIT_PAGE_NOT_MEASURED)
    if page_code != 0:
        return ("NONE", "the-served-page-is-not-this-run's-page/%s/%s"
                % (page_result or "unknown", page_reason or "no-reason-given"),
                None, EXIT_PAGE_NOT_OURS)
    if digest is None or fields is None:
        return ("NONE", "the-served-page-carries-no-material-state/%s"
                % (state_why or "unknown"), None, EXIT_PAGE_NO_STATE)
    if MAP.digest_of(fields) != digest:
        return ("NONE", "the-served-page-disagrees-with-itself..its-fields-do-"
                        "not-hash-to-its-digest", None, EXIT_PAGE_INCONSISTENT)
    if record is False:
        return ("NONE", "the-record-exists-and-could-not-be-read/%s..refusing-"
                        "rather-than-treating-it-as-a-first-run"
                % (record_why or "unknown"), None, EXIT_RECORD_UNREADABLE)
    if record is None:
        return ("NONE", "nothing-was-ever-recorded/%s..this-run-records-the-"
                        "baseline-and-announces-nothing"
                % (record_why or "unknown"), None, EXIT_BASELINE)
    if record.get("digest") == digest:
        return ("NONE", "the-served-state-is-the-recorded-state..a-fresh-clock-"
                        "or-a-second-publish-of-one-state-is-not-a-change",
                None, EXIT_NO_CHANGE)
    groups = MAP.changed_groups(fields, record.get("fields"))
    if not groups:
        return ("NONE", "the-digest-moved-and-no-material-group-did..nothing-"
                        "could-be-named", None, EXIT_NO_GROUP_MOVED)
    return ("WRITTEN", "material-change", groups, EXIT_WRITTEN)


# --------------------------------------------------------------- the message

def join_words(parts):
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def render_message(groups, map_link):
    """The message, from the changed groups, in his words. PURE.

    THE REGISTER IS LAW AND IT IS ENFORCED ELSEWHERE: this returns text and
    `tools/producer-check.py` grades it in a subprocess before it is allowed to
    stay in the tree. Written to the unprompted register: five sections in
    order, under the word cap, no numerals, no keys, no paths, one link, and it
    is the map's.
    """
    names = [GROUP_WORDS[g] for g in GROUP_ORDER if g in groups]
    phrase = join_words(names)
    head = phrase[0].upper() + phrase[1:]
    verb = "has changed" if len(names) == 1 else "have changed"
    return (
        "HEADLINE: The map changed: %s.\n"
        "\n"
        "WHAT CHANGED: [%s %s on the map](%s). A fresh time on the page alone "
        "would not have sent this.\n"
        "\n"
        "NEEDS YOU: nothing.\n"
        "\n"
        "NEXT VISIBLE THING: unknown.\n"
        "\n"
        "BUDGET: nothing measured here.\n"
        % (phrase, head, verb, map_link))


def message_name(day, digest):
    """<date>-the-map-changed-<digest>.unprompted.md.

    THE DIGEST IS IN THE NAME ON PURPOSE. The register wants a date and a slug;
    the digest makes the path itself idempotent, so a run that wrote a message
    and then lost its commit to a push race rewrites the same path instead of
    leaving him two messages about one change.
    """
    return "%s-the-map-changed-%s.unprompted.md" % (day, digest)


def grade(path):
    """(ok, output). The register check, run the way the SENDER runs it: a
    subprocess on this machine, not an import and not a promise."""
    p = subprocess.run([sys.executable, str(PRODUCER_CHECK),
                        "--kind", "unprompted", str(path)],
                       capture_output=True, text=True)
    return p.returncode == 0, ((p.stdout or "") + (p.stderr or "")).rstrip()


def outbox_count(repo):
    d = Path(repo) / OUTBOX_REL
    if not d.is_dir():
        return 0
    return len([p for p in d.rglob("*.md") if p.name != "README.md"])


def receipts_count(repo):
    d = Path(repo) / RECEIPT_DIR
    if not d.is_dir():
        return None
    return len([p for p in d.rglob("*.receipt.txt")])


# ------------------------------------------------------------------ the run

def run(repo, served_url, map_link, expect_commit, now=None, quiet=False):
    """The whole path. Returns (exitCode, doneLine, messageRel or '')."""
    now = now or now_utc()
    out = [] if quiet else None

    def say(s):
        if quiet:
            out.append(s)
        else:
            print(s)

    res = PUB.fetch(served_url)
    line, extra, page_code = PUB.evaluate(res, expect_commit, None)
    say("%s attempt=1/1-no-retry-loop-here reason=the-publish-job-already-"
        "retried-this-url url=%s" % (TOOL, served_url))
    say("  " + line)
    for e in extra:
        say("  " + e)
    m = RESULT_RX.search(line)
    page_result = m.group(1) if m else "none"
    m = REASON_RX.search(line)
    page_reason = m.group(1) if m else ""

    body = res.get("body", "") if res.get("measured") else ""
    digest, fields, state_why = read_served_state(body)
    record, record_why = read_record(repo)
    result, reason, groups, code = decide(page_code, page_result, page_reason,
                                          digest, fields, state_why,
                                          record, record_why)

    message_rel, register = "", "not-run"
    if code == EXIT_WRITTEN:
        rel = "%s/%s" % (OUTBOX_REL, message_name(now.strftime("%Y-%m-%d"),
                                                  digest))
        path = Path(repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_message(groups, map_link), encoding="utf-8")
        ok, said = grade(path)
        if not ok:
            # THE ONLY WAY THIS FIRES IS A FAULT IN THIS PROGRAM'S OWN WORDING,
            # so it is loud, and the file is removed: a message that fails the
            # register must never sit in the tree, where it would also take
            # ledger/verify.py red for everybody.
            path.unlink()
            say("  the message this program wrote was REFUSED by the register "
                "and has been removed. Nothing was written and nothing was "
                "recorded. The check said:")
            for l in said.splitlines():
                say("    " + l)
            result, reason, code = ("REFUSED",
                                    "the-register-refused-the-message-this-"
                                    "program-wrote", EXIT_REGISTER_REFUSED)
        else:
            register = "SEND"
            message_rel = rel
            write_record(repo, {
                "digest": digest, "fields": fields, "at": iso(now),
                "notified": True, "why": "material-change",
                "changedFields": "/".join(groups),
                "message": rel, "servedUrl": served_url,
                "pageCommit": expect_commit or "none",
            })
    elif code == EXIT_BASELINE:
        write_record(repo, {
            "digest": digest, "fields": fields, "at": iso(now),
            "notified": False, "why": "baseline-recorded-no-message-written",
            "changedFields": "none", "message": None,
            "servedUrl": served_url, "pageCommit": expect_commit or "none",
        })

    prev_digest = (record or {}).get("digest") if isinstance(record, dict) \
        else ("unreadable" if record is False else "none")
    receipts = receipts_count(repo)
    done = (
        "%s mapNotifyResult=%s reason=%s "
        # THE PAIRED READING: the state he was last told about and the state
        # being served now, in one token, at the one instant this run read
        # them. Two keys would be two moments a grep across lines merges.
        "mapDigestRecordedThenServed=%s..%s mapChangedFields=%s "
        "materialGroupsCompared=%s pageResult=%s messageWritten=%s "
        "registerCheck=%s outboxMessages=%d-under-%s "
        "delivered=no..the-receipt-under-%s-is-the-only-evidence "
        "receiptsInThisCheckout=%s"
        % (TOOL, result, reason,
           prev_digest or "none", digest or "nothing-measured",
           "/".join(groups) if groups else
           ("none" if code == EXIT_NO_CHANGE else "nothing-measured"),
           "%d/%d-material" % (len(GROUP_ORDER), len(GROUP_ORDER))
           if (fields and isinstance(record, dict)) else
           "nothing-measured..no-pair-to-compare",
           page_result, message_rel or "none", register,
           outbox_count(repo), OUTBOX_REL, RECEIPT_DIR,
           "%d" % receipts if receipts is not None
           else "nothing-measured..no-such-directory-in-this-checkout"))
    say(done)
    if code == EXIT_WRITTEN:
        say("  A MESSAGE WAS WRITTEN, AND NOBODY HAS BEEN TOLD ANYTHING. It "
            "sits in the outbox for the sender on his PC, which runs the "
            "register check again and writes a receipt carrying the platform's "
            "message id. That receipt is the only evidence of a delivery, and "
            "this program never writes one.")
    if quiet:
        return code, done, message_rel, "\n".join(out)
    return code, done, message_rel, ""


# ------------------------------------------------------------------ selftest

def _fixture_page(commit, when):
    """The real map page for THIS repository, stamped exactly as the publisher
    stamps it. instruments.md: for a tool that checks this project, the live
    codebase is the accepting fixture. Both halves are the real functions,
    tools/map.py:build and tools/publish-glance.py:inject_stamp, so these bytes
    are the bytes the publish job uploads."""
    tmp = Path(tempfile.mkdtemp(prefix="map-notify-fixture-"))
    try:
        page, model = MAP.build(REPO, when, out_path=tmp / "map.html")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    stamp = PUB.make_stamp(commit, when)
    return PUB.inject_stamp(page, stamp), model


def _repo(tmp):
    """A synthetic tree with the two directories this program writes into."""
    r = Path(tmp)
    (r / OUTBOX_REL).mkdir(parents=True, exist_ok=True)
    return r


def selftest():
    checks, failed = [], []

    def ok(name, cond, note):
        checks.append(name)
        print("  %s %s | %s" % ("PASS" if cond else "FAIL", name, note))
        if not cond:
            failed.append(name)

    print("%s selftest: ACCEPTING CASE FIRST" % TOOL)
    tmp = Path(tempfile.mkdtemp(prefix="map-notify-"))
    codes = {}
    try:
        commit = "aaaaaaaa"
        when = now_utc()
        # ACCEPTING 0: THE FIXTURE EXISTS. The live map generator builds a page
        # in this checkout. If it does not, everything below is unmeasured
        # rather than passing, and this says so in one line instead of a
        # traceback (CLAUDE.md rule 12: a report that ends in a stack trace
        # after a correct run costs twenty minutes before anyone reads it).
        try:
            page, model = _fixture_page(commit, when)
        except Exception as e:                                   # noqa: BLE001
            ok("liveMapGeneratorBuildsTheAcceptingFixture", False,
               "tools/map.py could not build a page in this checkout, so the "
               "accepting fixture does not exist and NOTHING below was "
               "measured: %s: %s" % (type(e).__name__, e))
            print("\n%s selftest: %d check(s) run, %d failed"
                  % (TOOL, len(checks), len(failed)))
            return EXIT_SELFTEST_FAILED
        served_digest = model["digest"]
        served_fields = model["fields"]
        ok("liveMapGeneratorBuildsTheAcceptingFixture", True,
           "the live map built: mapDigest=%s pageBytes=%d materialGroups=%d/%d"
           % (served_digest, len(page.encode("utf-8")),
              len([g for g in GROUP_ORDER if g in served_fields]),
              len(GROUP_ORDER)))

        # A SYNTHETIC PREVIOUS STATE, one group different from the live one.
        # The rejecting half of every fixture in this file is synthetic and the
        # accepting half is the live tree, so doing the work this tool prompts
        # can never break the tool.
        prev_fields = json.loads(json.dumps(served_fields))
        prev_fields["q2"] = ["planted|previously-a-different-word"]
        prev_digest = MAP.digest_of(prev_fields)

        # A regenerated page: same material state, later clock, different
        # bytes. This is the timestamp case, and it is built rather than
        # asserted.
        later = when + datetime.timedelta(hours=3)
        page_later, model_later = _fixture_page(commit, later)

        no_state = re.sub(r"<!-- mapDigest=[^>]*-->", "", page)
        srv, base = PUB._serve({
            "/map.html": (200, "text/html; charset=utf-8", page),
            "/later.html": (200, "text/html; charset=utf-8", page_later),
            "/nostate.html": (200, "text/html; charset=utf-8", no_state),
            "/foreign.html": (200, "text/html; charset=utf-8",
                              "<!DOCTYPE html><html><body>WC26 Picks</body>"
                              "</html>"),
            "/stale.html": (200, "text/html; charset=utf-8",
                            page.replace("commit=aaaaaaaa", "commit=old00000")),
        })
        try:
            # ---------------------------------------------------- ACCEPTING 1
            # A REAL MAP CHANGE, ALL THE WAY TO A GRADED MESSAGE. The page is
            # the live map served over HTTP; the previous state is one group
            # different; the message is graded by the real producer-check in a
            # subprocess, exactly as the sender grades it.
            r1 = _repo(tmp / "accept")
            write_record(r1, {"digest": prev_digest, "fields": prev_fields,
                              "at": iso(when), "notified": True,
                              "why": "planted-previous-state",
                              "changedFields": "none", "message": None})
            before = outbox_count(r1)
            code, done, rel, _ = run(r1, base + "/map.html",
                                     "https://jsab258.github.io/wc26-picks/"
                                     "map.html", commit)
            codes["accept"] = code
            wrote = (Path(r1) / rel).is_file() if rel else False
            graded = grade(Path(r1) / rel)[0] if wrote else False
            ok("acceptRealChangeWritesAGradedMessage",
               code == EXIT_WRITTEN and wrote and graded
               and "mapChangedFields=q2" in done,
               "exit=%d outboxMessages=%d..%d(before..after) registerCheck=%s "
               "file=%s" % (code, before, outbox_count(r1),
                            "SEND" if graded else "DO-NOT-SEND",
                            rel or "none"))
            body_written = (Path(r1) / rel).read_text(encoding="utf-8") \
                if wrote else ""
            ok("acceptMessageNamesTheFieldAndCarriesTheMapLink",
               GROUP_WORDS["q2"] in body_written
               and "jsab258.github.io/wc26-picks/map.html" in body_written
               and "q2" not in body_written,
               "namesTheGroupInWords=%s carriesTheMapLink=%s carriesAKey=%s"
               % (GROUP_WORDS["q2"] in body_written,
                  "map.html" in body_written, "q2" in body_written))
            ok("acceptRecordsTheServedDigest",
               read_record(r1)[0].get("digest") == served_digest
               and read_record(r1)[0].get("notified") is True,
               "recorded=%s served=%s"
               % (read_record(r1)[0].get("digest"), served_digest))

            # EVERY MESSAGE THIS PROGRAM CAN EVER WRITE, GRADED. Seven group
            # combinations exist and all seven are put through the register,
            # because the one that fails is the one nobody generated by hand.
            combos = [["q1"], ["q2"], ["q3"], ["q1", "q2"], ["q1", "q3"],
                      ["q2", "q3"], ["q1", "q2", "q3"]]
            passes, sample = 0, ""
            for c in combos:
                f = tmp / ("combo-%s.unprompted.md" % "-".join(c))
                f.write_text(render_message(
                    c, "https://jsab258.github.io/wc26-picks/map.html"),
                    encoding="utf-8")
                good, said = grade(f)
                passes += 1 if good else 0
                if not good and not sample:
                    sample = said.splitlines()[-1] if said else "no output"
            ok("everyPossibleMessagePassesTheRegister", passes == len(combos),
               "registerPasses=%d/%d-possible-group-combination(s)%s"
               % (passes, len(combos),
                  "" if passes == len(combos) else " first failure: " + sample))

            # ---------------------------------------------------- REJECTING 1
            # A REGENERATED TIMESTAMP PRODUCES NONE. The bytes differ and the
            # material state does not, and both halves are asserted: a test
            # that only checked the outcome could pass with an identical page.
            r2 = _repo(tmp / "timestamp")
            write_record(r2, {"digest": served_digest, "fields": served_fields,
                              "at": iso(when), "notified": True,
                              "why": "planted-already-notified",
                              "changedFields": "none", "message": None})
            code, done, rel, _ = run(r2, base + "/later.html",
                                     "https://jsab258.github.io/wc26-picks/"
                                     "map.html", commit, quiet=True)
            codes["timestamp"] = code
            ok("rejectRegeneratedTimestamp",
               code == EXIT_NO_CHANGE and not rel and outbox_count(r2) == 0
               and page_later != page
               and model_later["digest"] == served_digest,
               "exit=%d bytesDiffer=%s digestSame=%s messagesWritten=%d/0-"
               "expected" % (code, page_later != page,
                             model_later["digest"] == served_digest,
                             outbox_count(r2)))

            # ---------------------------------------------------- REJECTING 2
            # NOTHING MEASURED: no record at all is a first run, not a change.
            # The baseline is recorded so the NEXT change can be measured, and
            # no message is written.
            r3 = _repo(tmp / "firstrun")
            code, done, rel, _ = run(r3, base + "/map.html",
                                     "https://jsab258.github.io/wc26-picks/"
                                     "map.html", commit, quiet=True)
            codes["firstrun"] = code
            rec3 = read_record(r3)[0]
            ok("rejectFirstRunAndRecordTheBaseline",
               code == EXIT_BASELINE and not rel and outbox_count(r3) == 0
               and rec3 and rec3.get("digest") == served_digest
               and rec3.get("notified") is False,
               "exit=%d messagesWritten=%d/0-expected baselineRecorded=%s "
               "notified=%s" % (code, outbox_count(r3),
                                (rec3 or {}).get("digest"),
                                (rec3 or {}).get("notified")))
            # ... and the run after the baseline is silent too, which is the
            # half that proves the baseline is not an announcement deferred.
            code2, _, rel2, _ = run(r3, base + "/map.html",
                                    "https://jsab258.github.io/wc26-picks/"
                                    "map.html", commit, quiet=True)
            ok("rejectTheRunAfterABaseline",
               code2 == EXIT_NO_CHANGE and not rel2 and outbox_count(r3) == 0,
               "exit=%d messagesWritten=%d/0-expected" % (code2,
                                                          outbox_count(r3)))

            # A SERVED PAGE WITH NO MATERIAL STATE is also nothing measured.
            r4 = _repo(tmp / "nostate")
            code, done, rel, _ = run(r4, base + "/nostate.html",
                                     "https://jsab258.github.io/wc26-picks/"
                                     "map.html", commit, quiet=True)
            codes["nostate"] = code
            ok("rejectServedPageWithNoMaterialState",
               code == EXIT_PAGE_NO_STATE and not rel
               and (Path(r4) / RECORD_REL).exists() is False,
               "exit=%d messagesWritten=%d/0-expected recordWritten=%s"
               % (code, outbox_count(r4), (Path(r4) / RECORD_REL).exists()))

            # ---------------------------------------------------- REJECTING 3
            # THE SAME DIGEST TWICE PRODUCES ONE MESSAGE. The first run is the
            # accepting half of this pair and is asserted too, so a tool that
            # never wrote anything could not pass it.
            r5 = _repo(tmp / "twice")
            write_record(r5, {"digest": prev_digest, "fields": prev_fields,
                              "at": iso(when), "notified": True,
                              "why": "planted-previous-state",
                              "changedFields": "none", "message": None})
            c_a, _, rel_a, _ = run(r5, base + "/map.html",
                                   "https://jsab258.github.io/wc26-picks/"
                                   "map.html", commit, quiet=True)
            after_first = outbox_count(r5)
            c_b, _, rel_b, _ = run(r5, base + "/map.html",
                                   "https://jsab258.github.io/wc26-picks/"
                                   "map.html", commit, quiet=True)
            codes["twice"] = c_b
            ok("rejectTheSecondPublishOfOneState",
               c_a == EXIT_WRITTEN and c_b == EXIT_NO_CHANGE
               and after_first == 1 and outbox_count(r5) == 1 and not rel_b,
               "exits=%d..%d messagesWritten=%d..%d(first..second-run) "
               "expected=1..1" % (c_a, c_b, after_first, outbox_count(r5)))

            # ---------------------------------------------------- REJECTING 4
            # A PUBLISH THAT DID NOT PUBLISH. Four shapes, because "the deploy
            # failed" reaches this program as four different bodies and only
            # one of them is a 404.
            r6 = _repo(tmp / "publishfail")
            write_record(r6, {"digest": prev_digest, "fields": prev_fields,
                              "at": iso(when), "notified": True,
                              "why": "planted-previous-state",
                              "changedFields": "none", "message": None})
            shapes = [("never-published-404", base + "/map404.html",
                       EXIT_PAGE_NOT_OURS),
                      ("someone-elses-page", base + "/foreign.html",
                       EXIT_PAGE_NOT_OURS),
                      ("previous-deploy-still-served", base + "/stale.html",
                       EXIT_PAGE_NOT_OURS)]
            got = []
            for label, url, want in shapes:
                c, _, rl, _ = run(r6, url, "https://jsab258.github.io/"
                                  "wc26-picks/map.html", commit, quiet=True)
                got.append("%s=%d%s" % (label, c, "" if c == want
                                        else "-EXPECTED-%d" % want))
            ok("rejectEveryShapeOfAFailedPublish",
               all(("EXPECTED" not in g) for g in got)
               and outbox_count(r6) == 0,
               "%s messagesWritten=%d/0-expected over %d planted shape(s)"
               % (" ".join(got), outbox_count(r6), len(shapes)))
        finally:
            srv.shutdown()

        # A REQUEST THAT DID NOT COMPLETE IS NOT A FAILED PUBLISH. Nothing was
        # measured, and the refusal says so in those words. This is the case
        # the container is in every day, measured 2026-09-06.
        r7 = _repo(tmp / "unreachable")
        write_record(r7, {"digest": prev_digest, "fields": prev_fields,
                          "at": iso(when), "notified": True,
                          "why": "planted-previous-state",
                          "changedFields": "none", "message": None})
        code, done, rel, _ = run(r7, "http://127.0.0.1:1/map.html",
                                 "https://jsab258.github.io/wc26-picks/"
                                 "map.html", commit, quiet=True)
        codes["unreachable"] = code
        ok("refusalToRequestIsNotAFailedPublish",
           code == EXIT_PAGE_NOT_MEASURED and not rel
           and outbox_count(r7) == 0 and "could-not-be-requested" in done,
           "exit=%d messagesWritten=%d/0-expected reason=%s"
           % (code, outbox_count(r7),
              (REASON_RX.search(done).group(1)[:60] if REASON_RX.search(done)
               else "none")))

        # THE REGISTER CHECK CAN FAIL, AND THE FILE DOES NOT SURVIVE IT. A
        # guard nothing can fail is a ratchet, so the condition is planted: a
        # link the ruled band forbids. The bound is not loosened.
        r8 = _repo(tmp / "badlink")
        write_record(r8, {"digest": prev_digest, "fields": prev_fields,
                          "at": iso(when), "notified": True,
                          "why": "planted-previous-state",
                          "changedFields": "none", "message": None})
        srv2, base2 = PUB._serve({"/map.html": (200, "text/html; charset=utf-8",
                                                page)})
        try:
            code, done, rel, _ = run(r8, base2 + "/map.html",
                                     "https://example.invalid/not-the-map.html",
                                     commit, quiet=True)
        finally:
            srv2.shutdown()
        codes["badlink"] = code
        ok("rejectAMessageTheRegisterRefuses",
           code == EXIT_REGISTER_REFUSED and not rel
           and outbox_count(r8) == 0
           and read_record(r8)[0].get("digest") == prev_digest,
           "exit=%d messagesLeftInTheTree=%d/0-expected recordUnchanged=%s"
           % (code, outbox_count(r8),
              read_record(r8)[0].get("digest") == prev_digest))

        # AN UNREADABLE RECORD IS NOT A FIRST RUN.
        r9 = _repo(tmp / "badrecord")
        (Path(r9) / RECORD_REL).parent.mkdir(parents=True, exist_ok=True)
        (Path(r9) / RECORD_REL).write_text("{not json", encoding="utf-8")
        rec, why = read_record(r9)
        result, reason, groups, code = decide(0, "OK", "", served_digest,
                                              served_fields, "", rec, why)
        codes["badrecord"] = code
        ok("rejectAnUnreadableRecord",
           rec is False and code == EXIT_RECORD_UNREADABLE
           and result == "NONE", "exit=%d reason=%s" % (code, reason[:70]))

        # EVERY OUTCOME LEAVES BY ITS DOCUMENTED EXIT CODE, or the workflow
        # branches on the wrong one. The table is written out rather than
        # derived from what happened: a check that compares a run to itself
        # passes whatever the run does. Two rows share code 10 on purpose (a
        # regenerated clock and a second publish of one state ARE one outcome),
        # and that is asserted rather than tolerated.
        want = {"accept": EXIT_WRITTEN, "badlink": EXIT_REGISTER_REFUSED,
                "badrecord": EXIT_RECORD_UNREADABLE,
                "firstrun": EXIT_BASELINE, "nostate": EXIT_PAGE_NO_STATE,
                "timestamp": EXIT_NO_CHANGE, "twice": EXIT_NO_CHANGE,
                "unreachable": EXIT_PAGE_NOT_MEASURED}
        wrong = ["%s=%d-wanted-%d" % (k, codes.get(k, -1), v)
                 for k, v in sorted(want.items()) if codes.get(k) != v]
        ok("everyOutcomeLeavesByItsDocumentedExitCode", not wrong,
           "outcomesExercised=%d/%d-in-the-table distinctCodes=%d wrong=%s "
           "codes=%s"
           % (len(codes), len(want), len(set(codes.values())),
              ",".join(wrong) or "none",
              ",".join("%s:%d" % (k, v) for k, v in sorted(codes.items()))))

        # THE HISTORY CAP ANNOUNCES ITSELF.
        r10 = _repo(tmp / "cap")
        for i in range(HISTORY_CAP + 3):
            write_record(r10, {"digest": "%012d" % i, "fields": served_fields,
                               "at": iso(when), "notified": False,
                               "why": "planted-for-the-cap",
                               "changedFields": "none", "message": None})
        blob = json.loads((Path(r10) / RECORD_REL).read_text(encoding="utf-8"))
        ok("historyCapAnnouncesItself",
           len(blob["history"]) == HISTORY_CAP and blob["historyDropped"] == 3,
           "historyKept=%d/%d-cap historyDropped=%d over %d planted"
           % (len(blob["history"]), blob["historyCap"], blob["historyDropped"],
              HISTORY_CAP + 3))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n%s selftest: %d check(s) run, %d failed" % (TOOL, len(checks),
                                                         len(failed)))
    return EXIT_SELFTEST_FAILED if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--served-map", metavar="URL",
                    help="the published map, as served, requested and read")
    ap.add_argument("--map-link", metavar="URL",
                    help="the link that goes in the message (the ruled "
                         "destination, checked by the register)")
    ap.add_argument("--expect-commit", default="",
                    help="the commit whose page this run published")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.served_map or not a.map_link:
        ap.print_help()
        print("\n%s: nothing measured. --served-map and --map-link are both "
              "required: this program refuses to decide anything about a page "
              "it has not requested." % TOOL)
        return 2
    code, _done, _rel, _ = run(a.repo, a.served_map, a.map_link,
                               a.expect_commit)
    return code


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    sys.exit(main())
