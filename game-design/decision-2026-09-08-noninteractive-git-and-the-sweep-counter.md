# Ruling: non-interactive git and the sweep counter. LAND WITH AMENDMENTS

> **STATUS: LOG, 2026-09-08.** Director ruling on the uncommitted tree after
> `7722b45` (07:38:52Z, the rebased pick of dc8b930). Subject: every git call
> the bot makes on Jafar's PC, the bounded runner under it, the per-pass
> sweep counter, and the re-enabled CI sweep step. NOT CURRENT once the
> amended commit lands; from then the files are the reading copies and this
> is the record of why. Row: agent-log line 361, 2026-09-08T12:16:04Z.

VERDICT: LAND WITH AMENDMENTS. Every amendment below is dictated text, so the
resident applies it. Two of them are bugs found by reading, not taste: the
timeout message names `-c` instead of the subcommand on every real call, and
a verification that times out is reported as "the push sent nothing".

- A1. `_run_bounded`: the reader returns nothing on the exact fault it exists
  for, and the words then claim a measurement not made. Section 3.
- A2. `errors="replace"` on the pipes, or a decode error loses git's words in
  silence. Section 3.
- A3. A stopped plumbing command leaves `ledger-inbox-index.lock`; nothing
  removes it; every later pass then fails in words for ever. Section 3.
- A5. An `ls-remote` that times out reads as "sent nothing", a false claim
  with a sha on it, on the one question Jafar asked. Section 3.
- A6. The "no credential" case never reaches a credential and its bound
  admits a killed hang as "fast". Section 5.
- A7. The sweep counter can go stale without saying so. Section 6.
- A8. The exception path of the counter is asserted and untested. Section 6.
- A10, A11. The flush file must name which code ran, and its header is cut
  mid-sentence. Section 7.
- A12. An unmeasured sentence about push speed is replaced with what was
  measured. Section 4.
- A9. The bot is running the old `inbox.py` and stays so until restarted: a
  second push, after this one lands, not with it. Section 7.

## 0. What this director could and could not check

This spawn had Read, Grep, Glob and WebSearch and no shell. So: no selftest
run, no `git diff`, no `git status`. THE THREE SELFTEST OUTPUTS ARE A COMMIT
CONDITION, pasted into the message, and no count in this record is mine.

What I did verify by reading, with the instant each belongs to:

- The reference commit is `7722b45` at epoch 1788853132 (`.git/logs/HEAD`
  line 503). My row is 12:16:04Z, newer, so the stamp pairs.
- `production/pc-ops/inbox-flush.txt` at cfb6dc9 (`@1788849775`, which is
  06:42:55Z; the stream lines say 08:42:55, his local clock): `flushStatus=
  HUNG flushWaitedSec=150`, ten stdout lines all stamped 08:42:55, zero
  stderr lines. It printed the waiting list and then nothing for 150 s.
- `production/pc-ops/push-diagnosis.txt` at cfb6dc9 (`@1788849773`, two
  seconds earlier): `credentialHelper=manager`, `lsRemoteSec=0.5`,
  `pushDryRunExit=0 pushDryRunSaid=Everything~up-to-date`.
- The diagnosis step itself (workflow lines 207-216) runs its dry-run push
  under `GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`, `GIT_ASKPASS=echo`
  and `GCM_PROVIDER=generic`, and its comment records that the 2592c14 run of
  the same step hung for its whole four minutes before those were set.
- `/usr/lib/python3.12/subprocess.py` lines 552-563: after `TimeoutExpired`,
  `run()` calls `process.kill()` and then, on Windows only,
  `process.communicate()` with no timeout ("communicate() _after_ kill() is
  required"); on POSIX it calls `process.wait()`. Read, not recalled.
- GCM's own documentation for `GCM_INTERACTIVE` ("if interaction is required
  but has been disabled, an error is returned ... preferable to fail than to
  hang") and `GCM_GUI_PROMPT` ("if an equivalent terminal/text-based prompt
  is available, that will be shown instead"), via search; links at the end.
- `telegram-bot.py` 1202-1204: `flush_inbox()` then `sweep_outbox()` run in
  the `finally` of every poll iteration. `flush_inbox` (826-847) calls
  `push_pending` whenever anything is pending, at most once a minute.
- `tools/runner/outbox.py`: no lock of any kind (grep `lock|single_instance`,
  only unrelated hits). `telegram-bot.py`: no `single_instance` use.
- `tools/pc-watcher.py:524-526`: its own `git()` is `subprocess.run` with no
  env and a 600 s timeout, force-pushing `pc-results` at 779 and 909.
  `tools/runner/executor.py:636-667`: `GIT_TERMINAL_PROMPT=0` only,
  `subprocess.run`, 180 s. Neither is touched by this batch.
- The restart workflow fires on a push touching only
  `production/pc-ops/telegram-bot-restart.request`, and its own header
  (lines 32-36) says why it must not share a push with the install workflow.

## 1. The diagnosis, attacked

THE CLAIM: `GIT_TERMINAL_PROMPT=0` binds git's own prompt and says nothing to
Git Credential Manager, which opened a window. That is the best-supported
explanation, and here is what supports it beyond the assertion: git's own
variable is documented as terminal-only; GCM documents its own two switches
and states that the purpose of `GCM_INTERACTIVE` is to fail instead of hang
on a build server; the diagnosis step in the same runner context hung for
four minutes on 2592c14 and returned in 0.5 s once GCM's switches were set,
which is a before-and-after in the same seat. The Windows drain (section 3)
then explains why a 120 s ceiling did not bound it.

THE CONTRARY DATUM, which the batch does not mention. Two seconds before the
flush hung, the diagnosis step's `push --dry-run` did the full receive-pack
handshake against GitHub AS THE SAME USER ON THE SAME MACHINE and exited 0,
non-interactively. So "no credential in the store" is not the explanation:
a credential is there and works. The two environments differ in one member,
`GCM_PROVIDER=generic`, which the bot does not set. What fits that: GCM's
GitHub provider selecting differently from the generic one (an account
picker when two credentials are stored, or a browser refresh of an OAuth
token), either of which is a window. I do NOT order `GCM_PROVIDER=generic`
into the bot: it changes which provider serves his real pushes, and the
next run carries both readings side by side, which is the cheapest decisive
measurement. If the bot's push fails in words while the dry-run beside it
still exits 0, that one variable is the next thing to measure.

WHERE IT HUNG IS NOT MEASURED. `push_pending` says nothing between steps;
the 150 s covers read-tree, twelve hash-objects, twelve update-indexes,
write-tree, commit-tree, push and ls-remote alike. The new rc 124 text names
the subcommand, which is the instrument for the next run, once A1 makes the
name correct.

THE UNIFIED EXPLANATION, stated because it changes what the counter means.
`flush_inbox` runs inside the poll loop's `finally`, before `sweep_outbox`.
Under the old code one unanswered prompt hung `push_pending` for 120 s and
then the Windows drain for as long as the window stood. That stalls the whole
loop: no poll, no sweep, no reply, process alive, uptime climbing. It is the
shape of 11:19 to 23:48 on the 7th exactly, and of "works when he is at the
desk and dismisses the window". The two halves were one fault. It follows
that `botSweepPasses` freezing with an old `botSweepWrittenAt` is the
signature of a hanging push, and that the bounded runner is what lets the
counter move while a push fails in words.

## 2. Change 1: the environment and the `-c` flags. Approved

WHITELIST. `git_call` tests `args[0]` at line 287 and builds `cmd` at 310 by
prepending `NONINTERACTIVE_ARGS`; a caller passing `["-c", ...]` is refused
because `-c` is not on `ALLOWED`. The injection cannot widen the guard. The
flags reach GCM: git exports `-c` overrides to every child through
`GIT_CONFIG_PARAMETERS`, which GCM's config reads honour.

NAMES. `GCM_INTERACTIVE`: documented; GCM Core's canonical form is `false`
or `0`, and `Never` is the older spelling that GCM for Windows requires and
GCM Core maps in its compatibility table. Keep `Never`: the config half
`credential.interactive=false` carries the canonical form, so the pair covers
both generations, and the diagnosis step already ran his GCM under
`GCM_INTERACTIVE=never` with a working credential and exited 0, which is the
measurement that the value does not break the working case.
`GCM_GUI_PROMPT` / `credential.guiPrompt`: GCM Core only, ignored by older
GCM, harmless. `GIT_ASKPASS=echo`: in git's `git_prompt` an askpass program
takes precedence over `GIT_TERMINAL_PROMPT`, so git runs `echo`, takes the
prompt text back as the answer, presents it, is refused, and dies with
"Authentication failed" in seconds; if `echo` does not resolve on his PATH
the askpass fails and `GIT_TERMINAL_PROMPT=0` dies with "terminal prompts
disabled". Both branches are fast and in words. One consequence to know: on
an expired stored credential git calls the helper's `erase`, so the next
time Jafar pushes by hand he is asked once, and the bot works again after.
`-c core.askPass=` is legal (empty value). `SSH_ASKPASS_REQUIRE=never` is
OpenSSH 8.4 and later, ignored earlier, irrelevant to an https remote.
`GIT_FLUSH=1` is harmless.

## 3. Change 2: `_run_bounded`. Approved with four amendments

THE CLAIM IS CORRECT, and now checked rather than argued: subprocess.py
552-563 above. On Windows, `communicate()` after `kill()` joins reader
threads that block in `read()` until every handle to the pipe's write end
closes. `git push` over https spawns `git-remote-https`, which spawns the
credential helper; both inherit stderr; `TerminateProcess` on `git.exe`
closes only git's handles. So the call outlives its timeout for as long as
the helper stands, which is what 150 against 120 says. On POSIX `run()`
calls `wait()` and does not drain, so the fault is Windows-only, which is
where the bot runs. Daemon threads never joined on the timeout path are the
right shape.

FAULTS IN THE REPLACEMENT, found by reading it:

(a) "Whatever the readers reached so far is returned immediately" (line
213) is false as coded. `got[key] = stream.read()` (230) assigns once, at
end of file, and on the fault this function exists for end of file never
comes. So on a real hang `got["err"]` is empty and line 255 prints "It
printed nothing, which is the shape of a credential prompt", a measurement
that was not made: git may have printed plenty. And line 252 names the
subcommand as `cmd[1]`, which since line 310 is `-c` on every real call:
"git -c did not finish within 30 second(s)". The selftest passes a python
command whose `cmd[1]` is also `-c`, so it could not see this. A1.

(b) No `errors="replace"`: a stray byte on a Windows pipe raises inside
the reader, `except Exception: pass` swallows it, and the output is lost
with rc 0. `executor.py:658` already does it right. A2.

(c) Killing only the direct child is NOT enough on Windows, and the batch
knows it: the tree survives by design. Each hang leaves `git-remote-https`,
the helper, and two blocked daemon threads in the bot, once a minute while
the hang persists. If the environment works there is no hang and no leak; if
it does not, the leak is the case Jafar told us not to assume away. Next
rung, not this batch: `taskkill /F /T /PID` on the timeout path on Windows,
exactly as `executor.py:910` does, printing what it killed. Queue, with a
trigger: it lands before the bot is left running for a day if the first run
shows rc 124 rather than a fast failure in words.

(d) A plumbing command stopped mid-write leaves `.git/ledger-inbox-index
.lock`; `push_pending` (727-731) removes only the index. From then every
pass fails fast with "File exists" and the channel is dead in words. A3
removes a lock older than `LOCAL_TIMEOUT`, which cannot belong to a live
command of this file because none lives that long, and leaves a younger one
to the CI flush that may be running beside it.

(e) `ls-remote` rc != 0 falls into `seen=""` and reports "the push sent
nothing: X is not what pc-inbox holds (no such branch)" (799-804). A push
that landed and a verification that timed out then reads as a failed push,
which is precisely the misreading Jafar's ruling forbids. A5.

NORMAL-CASE LOSS: none I can construct. The 5 s join after `wait()` returns
loses output only if a grandchild holds the pipe for more than 5 s after
git itself exited; `git push` waits for its transport, which waits for its
helper, and the plumbing spawns nothing.

## 4. Change 3: 20 and 30 seconds. Accepted as ceilings, not as bounds

Rule 2 is not met and the batch says so. Accepted because a ceiling that is
too low announces itself: rc 124 prints the subcommand and the number in the
window and in the flush file, so a misclassification is loud, which is the
property the rule protects. What IS measured: one `ls-remote` from his PC at
0.5 s. What is not: any push. The sentence "A push of a dozen small files
over a home line takes under five seconds" (193-194) is a number nobody
printed; A12 replaces it. The series that sets these properly: per-call
elapsed, with the pass peak and the timed-out count published beside the
sweep counter (`botGitCallSecPeak`, `botGitCallsTimedOut`, `botGitCalls`),
read after a day of passes. Queue item, named. The flush step's 90 s is
three times the network ceiling and bounds ONE hang, not a pass of 27 calls;
the record says so rather than the step.

## 5. Change 4: the five cases. Two accepted, one renamed, one amended

`noninteractive-flags-do-not-break-a-working-push` restates `res_crlf` from
the block above; honest as labelled, and it is the accepting case that would
go red on a flag git refuses. `a-command-that-hangs-is-stopped-inside-its-
own-timeout` tests a sleeping DIRECT child with no grandchild: the old
`subprocess.run` passes it too, on every platform, because the pipes close
when the child dies. It proves the bound and the words and cannot tell the
regression from the improvement on the fault claimed (rule 5b). Keep it; the
decisive fixture is named for the queue: a child that spawns a grandchild
inheriting the pipes and outliving it, plus a local http server answering
401 with a fake helper that sleeps unless `GCM_INTERACTIVE` is `Never`. That
pair plants both faults and both outcomes, in the tested layer, in about
forty lines, and it lands before the return-half item closes.

`a-push-with-no-credential-fails-fast-and-holds-the-message` never reaches
a credential: `example.invalid` never resolves (here the proxy refuses it),
so git fails before any 401 and no prompt path runs. It is a DNS-failure
case wearing an auth name, and its bound `NETWORK_TIMEOUT + 10` admits a
push that hung and was killed at 30 s as "fast". A6 renames it to what it
proves, asserts on the shape of the failure, and prints the elapsed as the
first sample of the series section 4 asks for. The phone case is tautological
on three constants and stands as a guard against a future edit.

## 6. The sweep counter. Approved with two amendments

WRITER: read 880-946. Written at construction (593) with passes 0 and the
note `no-pass-yet`; on the raise path (936-938) the pass counts and the note
names the exception; on the normal path (940-946). The selftest's `Captured`
passes `repo=watcher`, a fixture, so no case writes into this checkout.
READER: 529-551 gives three genuinely distinct outputs, no-file, file-empty,
and read/N with the keys copied verbatim; the three supervisor cases cover
exactly those. Good.

CAN IT GO STALE WITHOUT SAYING SO? Yes. `botSweepWrittenAt` is copied
through and nothing prints its age. A loop wedged in a hanging push (section
1, and it is the same `finally`) leaves a frozen number under a fresh
supervisor `written=`; a reader must subtract two local timestamps by hand,
which is how the 11:19 silence was misread for a day. A7 has the supervisor
print `botSweepAgeSec` on the same clock, and sets no bound on it: print the
series first. The counter is per process and resets on restart;
`botUptimeSec` beside it says so, and that is fine.

The exception path is asserted in a comment and tested by nothing; A8 plants
it. Jafar's question closes when two CI status reads ten or more minutes
apart show `botSweepPasses` differing by about the gap over 120 and
`botSweepAgeSec` under 120 on both, or when the bot's window shows the same.

## 7. The workflow. Re-enable stands; the discipline is named; one push, then another

RE-ENABLE. Jafar's words bind and the switch is his. The hazard it was
retired for is the same in kind with it on or off: the bot's own loop sends
whatever pc-watcher has synced within 120 s, and the CI step only shortens
that to the run's arrival. The discipline that actually prevents it is
mechanical, and it is this: a commit carrying a ruling that refuses outbox
text carries the text's removal or replacement in the SAME commit, and before
`git push` the resident greps `production/outbox/` for the refused headline.
A refused message that has already gone is not rewritten (the previous
record, section 9). The real cost of two senders is elsewhere: no lock in
`outbox.py`, so two passes inside the same seconds can both send one file
and the second receipt overwrites the first. Queue: a pass lock, skip and
say. Not blocking; a duplicate on his phone is a nuisance, not a lost half.

150 TO 90: fine, with section 4's caveat on what 90 bounds.

WHAT THIS PUSH FIRES (rule 9): the install workflow, because its `paths`
names itself; install, diagnosis, sweep (SENDS anything unsent in his
checkout), flush, status, pc-inbox read. The flush runs a fresh python in
HIS checkout, so it runs the new `inbox.py` only if pc-watcher has synced
by then; A10 makes the file say which. THE BOT ITSELF KEEPS THE OLD CODE
LOADED until it restarts (rule 6, built is not running), and the restart
request must NOT ride this push: the restart workflow's own header says the
two jobs rewrite `supervisor-status.txt` from one base and the second one's
evidence dies on the agent. A9 is therefore a second commit after the first
has landed by ancestry.

## 8. Adjacent, named for the queue, not in this batch

- `tools/pc-watcher.py:524`: no env, 600 s, `subprocess.run`, force-push of
  `pc-results`. The other channel, both faults, untouched. QUEUE: route it
  through one bounded non-interactive runner shared with `inbox.py`.
- `tools/runner/executor.py:636`: `GIT_TERMINAL_PROMPT=0` only, 180 s,
  `subprocess.run`; pushes at 782. Same. Same queue item.
- The tree kill (3c), the two fixtures (5), the elapsed series (4), the
  outbox pass lock (7). Four names, four lines in `production/queue/`.

## 9. What I refuse, exactly

1. The timeout message as written (subcommand `-c`, "It printed nothing"
   on a blocked reader, "Nothing on this PC was changed" unmeasured). A1.
2. The `ls-remote` failure reported as "the push sent nothing". A5.
3. The case name `a-push-with-no-credential-fails-fast...` and its 40 s
   bound. A6.
4. The sentence "takes under five seconds" in the timeout comment, and
   "fetch" in the same comment for a subcommand the whitelist refuses. A12.
5. Touching `telegram-bot-restart.request` in this commit. A9 is the next.

## 10. The amendments, dictated

A1. `tools/runner/inbox.py`. Line 201, the signature becomes:

    def _run_bounded(cmd, cwd, env, timeout, what=None):

Lines 228-232, the whole `drain` function becomes:

    def drain(stream, key):
        # LINE BY LINE, so the timeout path can return what was printed
        # BEFORE the hang. A single read() returns only at end of file,
        # and on the fault this function exists for, end of file is
        # exactly what never comes.
        try:
            for line in iter(stream.readline, ""):
                got[key] += line
        except Exception:                                     # noqa: BLE001
            pass

Lines 249-256, the return statement on the timeout path, becomes:

        alive = [t for t in readers if t.is_alive()]
        said = one_line(got["err"].strip() or got["out"].strip(), 120)
        return 124, got["out"].strip(), (
            "git %s did not finish within %d second(s) and was stopped, so "
            "its result is unknown; the next pass rebuilds from the branch's "
            "own tree.%s%s"
            % (what or (cmd[1] if len(cmd) > 1 else "?"), timeout,
               (" It said: " + said) if said
               else " It printed nothing before it was stopped.",
               (" Something it started is still running and holding its "
                "output open, which is the shape of a credential helper "
                "waiting for somebody.") if alive else ""))

Line 311 becomes:

    return _run_bounded(cmd, repo, env, timeout, what=args[0])

And in the selftest, line 1303 becomes `watcher, dict(os.environ), 2, what="push")`
and lines 1308-1310 become:

    check("accept/and-the-hang-is-reported-in-words-naming-the-subcommand",
          "git push did not finish within 2 second(s)" in err_h
          and "printed nothing" in err_h, err_h[:140])

A2. Line 221: `universal_newlines=True)` becomes
`universal_newlines=True, errors="replace")`.

A3. After line 731 (the `pass` closing the index removal), insert:

    # THE LOCK TOO, WHEN IT IS STALE. A plumbing command stopped by the
    # timeout in `_run_bounded` leaves `<index>.lock` behind, and git then
    # refuses every later pass with "File exists" for ever. A lock older
    # than LOCAL_TIMEOUT cannot belong to a live command of this file,
    # because no command of this file lives that long; a younger one may
    # be the CI flush running beside this process, and is left alone.
    lock = index + ".lock"
    try:
        if os.path.exists(lock) and \
                time.time() - os.path.getmtime(lock) > LOCAL_TIMEOUT:
            os.remove(lock)
    except OSError:
        pass

A5. Lines 799-804 become:

    seen = remote.split()[0] if rc == 0 and remote.strip() else ""
    if rc != 0:
        # THE CHECK ITSELF FAILED, which says nothing about the push. A
        # push that landed and a verification that timed out must not read
        # as "sent nothing": that is a false claim with a sha on it. The
        # tip stays where it was, so the next pass re-pushes and re-checks.
        return held(out, pending, PLAIN_ARRIVE,
                    "the push may have landed but could not be verified "
                    "(%s)" % one_line(why(remote, _rerr), 120))
    if seen != commit:
        return held(out, pending, PLAIN_ARRIVE,
                    "the push sent nothing: %s is not what %s holds (%s)"
                    % (commit[:7], INBOX_BRANCH,
                       (seen[:7] or "no such branch")))

A6. Lines 1312-1314 (the three comment lines) become:

    # THE REJECTING HALF, AS FAR AS THIS CONTAINER CAN TAKE IT. This remote
    # never resolves, so git fails before any 401 and no credential prompt
    # runs here; the prompt is exercised only on his PC, and the fixture
    # that plants it is queued (ruling 2026-09-08, section 5).

Lines 1322-1326 become:

    check("reject/an-unreachable-remote-fails-in-words-and-holds-the-message",
          (not res_auth["ok"]) and res_auth["pending"]
          and "did not finish within" not in res_auth["detail"],
          "took=%.1fs ok=%s pending=%d detail=%s"
          % (auth_took, res_auth["ok"], len(res_auth["pending"]),
             res_auth["detail"][:80]))
    print("      says: unreachableRemoteFailSec=%.1f networkTimeoutSec=%d"
          % (auth_took, NETWORK_TIMEOUT))

A12. Lines 192-196, the comment above the two constants, becomes:

    #: TIMEOUTS IN SECONDS: ceilings on a hang, never targets, and NOT YET
    #: SET FROM A SERIES (rule 2). What is measured: one ls-remote from his
    #: PC at 0.5 s (push-diagnosis, cfb6dc9); no push has been timed. A
    #: ceiling that is too low announces itself: rc 124 names the
    #: subcommand and the number in the window and in the flush file. The
    #: series that sets these is the per-call elapsed published beside the
    #: sweep counter; read a day of it, then set. NETWORK covers push and
    #: ls-remote; LOCAL covers the plumbing, which touches no network.

A7. `tools/supervise.py`. Line 551 becomes:

    # THE AGE, ON THIS MACHINE'S OWN CLOCK. A number that stopped moving
    # looks exactly like one still moving until something says how old it
    # is. Both stamps are local time from one clock, so the subtraction is
    # honest; no bound is set here, the series is printed first (rule 2).
    age = "nothing-measured/no-botSweepWrittenAt"
    for kv in raw:
        if kv.startswith("botSweepWrittenAt="):
            try:
                then = time.mktime(time.strptime(kv.split("=", 1)[1],
                                                 "%Y-%m-%dT%H:%M:%S"))
                age = "%d" % int(time.time() - then)
            except (ValueError, OverflowError):
                age = "nothing-measured/unparseable-botSweepWrittenAt"
    return raw + ["botSweepAgeSec=%s" % age,
                  "botSweepStatus=read/%d-key(s)" % len(raw)]

After line 1142 (the accept check), insert:

    check("accept/and-the-supervisor-prints-how-old-that-number-is",
          any(k.startswith("botSweepAgeSec=") and k.split("=", 1)[1].isdigit()
              for k in got), got)

A8. `tools/runner/telegram-bot.py`. After line 2371, insert:

    # AND THE EXCEPTION PATH, PLANTED (rule 5b): a sweep that raises is
    # still a pass that happened, and the file must say so rather than
    # freezing on the last good number.
    b8 = Captured()
    b8.creds = creds
    real_pass = outbox_pass
    try:
        globals()["outbox_pass"] = (lambda *a, **k: (_ for _ in ()).throw(
            RuntimeError("planted")))
        b8.sweep_outbox(every=0)
    finally:
        globals()["outbox_pass"] = real_pass
    raised = open(fresh, encoding="utf-8").read() if os.path.exists(fresh) \
        else ""
    check("accept/a-sweep-that-raised-still-counts-and-names-the-raise",
          b8.out_passes == 1 and "botSweepPasses=1" in raised
          and "botSweepLastResult=raised/RuntimeError" in raised,
          raised.replace("\n", " ")[:150])

A10. `.github/workflows/ledger-install-supervisor-task.yml`. After line 451
(`flushPython=`), insert two lines at the same indentation:

              $head = (& git -c safe.directory=* -C $repo rev-parse --short HEAD 2>&1 | Out-String).Trim()
              "flushRepoHead=$($head -replace '\s','~')" | Add-Content $out

A11. Same file: lines 431-436 (the six lines from "THE READING THIS STEP NOW
EXISTS FOR" to "Last measurement: HUNG at 150s, 12 waiting.") move to after
line 438, so the older sentence reads whole before the newer block.

A9. NOT IN THIS COMMIT. After the first push has landed by ancestry, a
second commit changing only `production/pc-ops/telegram-bot-restart.request`
to the single line
`reason=load-noninteractive-git-and-the-sweep-counter date=2026-09-08`.

## 11. Before commit

1. Apply A1, A2, A3, A5, A6, A12, A7, A8, A10, A11. Nothing else changes.
2. Run and paste, whole output, the three suites: `python3 tools/runner/
   inbox.py --selftest`, `python3 tools/supervise.py --selftest`, `python3
   tools/runner/telegram-bot.py --selftest`. The message must show the lines
   `accept/and-the-hang-is-reported-in-words-naming-the-subcommand`,
   `reject/an-unreachable-remote-fails-in-words-and-holds-the-message`, the
   `says: unreachableRemoteFailSec=` line, `accept/and-the-supervisor-prints-
   how-old-that-number-is`, and `accept/a-sweep-that-raised-still-counts-and-
   names-the-raise`, each `pass`. The counts are theirs, not mine.
3. Grep `production/outbox/` for anything a ruling has refused and not yet
   replaced; the re-enabled sweep sends what it finds.
4. `python3 ledger/verify.py` green; footer from the file.
5. Push. Watch by ancestry for a landed install run whose commit contains
   this one. Open `production/pc-ops/inbox-flush.txt` and read, in order:
   `flushRepoHead=` (old code or new), `flushStatus=`, then the `flush
   done:` line. THE READINGS: `ok=True` with `pcInboxHeadShort` in the same
   run's `scheduled-task-verify.txt` no longer `22973f8` closes the return
   half. `ok=False` with a `detail=` naming a subcommand and git's words is
   an answer and the next measurement, read against `pushDryRunExit` beside
   it (section 1). `HUNG` under `flushRepoHead=` new code means the
   environment did not reach the helper and the tree kill (3c) moves to the
   front. Anything else is NO RUN and says so.
6. Then A9 as its own commit, and the reading that closes Jafar's second
   question: `telegram-botStarts` up by one, `botSweepPasses=0` with a small
   `botSweepAgeSec`, then a later read with a larger count (section 6).

## 12. Quality ladder at close

This is the first working rung: every call bounded and named, the loop able
to move while a push fails, the counter off the machine. Not the best
available, and the next rungs are named rather than blank: the tree kill on
Windows, the two fixtures that plant the real fault, the elapsed series that
turns two guessed ceilings into measured ones, the one runner shared by the
three git callers on that PC, and the outbox pass lock. The aspect whose rung
is closest to blank is still the window: every fault this week printed its
reason to a console nobody reads, and the previous record's queue line (each
daemon's last twenty lines in the status file) stands.

<!--RULING spawn=2026-09-08T12:16:04Z-->
