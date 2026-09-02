#!/usr/bin/env bash
# THE python3 NAME ON THE SELF-HOSTED RUNNER. ONE IDEA, ONE IMPLEMENTATION.
#
# The cloud image ships `python3` on bash's PATH and Jafar's PC does not:
# Git-bash there knows only `python` and `py`. The very first self-hosted run
# of the Unity build died in the lint step on exactly this, ninety seconds in.
# A shim on GITHUB_PATH maps the name once for every later bash step; on the
# cloud image the whole thing is a no-op.
#
# WHERE THIS CAME FROM AND WHAT IS STILL DUPLICATED, SAID OUT LOUD RATHER THAN
# LEFT FOR THE NEXT PERSON TO FIND. The logic below is the step
# `python3 shim (self-hosted parity)` of .github/workflows/ledger-build-windows.yml
# (lines 104 to 156 on 2026-09-02), moved into a file so that
# ledger-vignette-fetch.yml can use it without becoming a second copy. THE
# UNITY WORKFLOW STILL CARRIES ITS INLINE COPY: switching it over is a
# two-line edit and it is deliberately NOT made in this change, because that
# workflow is the project's only compile channel and the right way to move it
# is one deliberate change dispatched alongside a build, which is exactly how
# tools/runner/bootstrap-paths.cmd was moved (probe run 15). Until then this
# file and that step are twins, and the twin is named here so a change to one
# cannot quietly miss the other.
#
# CALLERS:
#     - name: python3 shim (self-hosted parity)
#       shell: bash
#       run: bash tools/runner/python3-shim.sh
#
# SELFTEST, BOTH OUTCOMES, RUNNABLE ANYWHERE:
#     bash tools/runner/python3-shim.sh --selftest
set -u

# Actions sets both of these. Defaulted so the selftest can run outside CI,
# and the fallback is announced rather than silent.
: "${RUNNER_TEMP:=${TMPDIR:-/tmp}}"

# CANDIDATES ARE TESTED BY RUNNING THEM, never by existence. Run 32595552209
# of the Unity build: C:\Windows\py.exe existed (a machine-wide LAUNCHER) but
# its registered interpreters were per-user, so `py -3` had nothing to launch
# under the service account. A launcher on a machine path proves nothing about
# the interpreter behind it.
try() { "$@" --version >/dev/null 2>&1; }

# Returns the interpreter to shim to, on stdout, or nothing.
# SHIM_NO_FETCH=1 disables the download half, which is what makes the
# rejecting case testable in a container with no network.
pick_interpreter() {
  if try python; then echo "python"; return 0; fi
  if try py -3; then echo "py -3"; return 0; fi
  if try /c/LedgerTools/python312/python.exe; then
    echo "/c/LedgerTools/python312/python.exe"; return 0
  fi
  if [ "${SHIM_NO_FETCH:-0}" = "1" ]; then
    echo "no interpreter on this machine and the fetch is disabled" >&2
    return 1
  fi
  # SELF-HEALING, so no round trips through a person's mouse: python.org's
  # zip build needs no installer (the MSI service is blocked on this PC) and
  # lands where the next run finds it cached. Everything the runner executes
  # is single-file stdlib, which the zip carries; its ._pth is removed so
  # script-directory imports work if one ever grows a sibling.
  echo "no machine-visible python - fetching python.org's zip build (11 MB, one-time)" >&2
  curl -sSL --retry 2 --retry-delay 3 -o "$RUNNER_TEMP/py-embed.zip" \
    "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip" >&2 || true
  mkdir -p /c/LedgerTools/python312 2>/dev/null || true
  /c/Windows/System32/tar.exe -xf "$(cygpath -w "$RUNNER_TEMP/py-embed.zip")" \
    -C "C:\\LedgerTools\\python312" >&2 2>/dev/null || true
  rm -f /c/LedgerTools/python312/python312._pth
  if try /c/LedgerTools/python312/python.exe; then
    echo "/c/LedgerTools/python312/python.exe"; return 0
  fi
  return 1
}

selftest() {
  bad=0
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT

  # ACCEPTING CASE FIRST: a working interpreter named `python` on PATH is
  # found and named. The fake is a script, so this runs on a machine that has
  # no python at all and still proves the pick.
  mkdir -p "$tmp/bin"
  printf '#!/usr/bin/env bash\necho "Python 3.0.0-fake"\n' > "$tmp/bin/python"
  chmod +x "$tmp/bin/python"
  got="$(PATH="$tmp/bin:$PATH" SHIM_NO_FETCH=1 bash "$0" --pick 2>/dev/null || true)"
  if [ "$got" = "python" ]; then
    echo "  ok   ACCEPTING: a runnable python on PATH is picked ($got)"
  else
    echo "  FAIL ACCEPTING: expected 'python', got '$got'"; bad=1
  fi

  # REJECTING 1: something CALLED python that does not run. This is the
  # Windows Store App Execution Alias in miniature, and it is the case
  # `command -v` gets wrong.
  printf '#!/usr/bin/env bash\nexit 9\n' > "$tmp/bin/python"
  chmod +x "$tmp/bin/python"
  got="$(PATH="$tmp/bin" SHIM_NO_FETCH=1 bash "$0" --pick 2>/dev/null || true)"
  if [ -z "$got" ]; then
    echo "  ok   rejecting: a python that exits non-zero is not picked"
  else
    echo "  FAIL rejecting: a broken python was picked as '$got'"; bad=1
  fi

  # REJECTING 2: nothing at all, and the fetch disabled.
  got="$(PATH="$tmp/empty" SHIM_NO_FETCH=1 bash "$0" --pick 2>/dev/null || true)"
  if [ -z "$got" ]; then
    echo "  ok   rejecting: no interpreter anywhere returns nothing"
  else
    echo "  FAIL rejecting: something was picked out of an empty PATH: '$got'"; bad=1
  fi

  # AND THE PRODUCT OF THE SHIM RUNS, which is the half a pick cannot prove.
  mkdir -p "$tmp/bin"
  printf '#!/usr/bin/env bash\necho "Python 3.0.0-fake"\n' > "$tmp/bin/python"
  chmod +x "$tmp/bin/python"
  RUNNER_TEMP="$tmp" GITHUB_PATH="$tmp/gh-path" \
    PATH="$tmp/bin:$PATH" SHIM_NO_FETCH=1 SHIM_FORCE=1 bash "$0" >/dev/null 2>&1
  if [ -x "$tmp/shim/python3" ] && "$tmp/shim/python3" --version >/dev/null 2>&1; then
    echo "  ok   ACCEPTING: the shim it wrote runs and answers --version"
  else
    echo "  FAIL the written shim did not run"; bad=1
  fi
  if grep -q "shim" "$tmp/gh-path" 2>/dev/null; then
    echo "  ok   ACCEPTING: the shim directory was appended to GITHUB_PATH"
  else
    echo "  FAIL nothing was appended to GITHUB_PATH"; bad=1
  fi

  echo "python3-shim selftest: $( [ "$bad" -eq 0 ] && echo PASS || echo FAILED )"
  return "$bad"
}

case "${1:-}" in
  --selftest) selftest; exit $? ;;
  --pick)     pick_interpreter; exit $? ;;
esac

# THE OUTER GUARD TESTS BY EFFECT TOO. `command -v python3` SUCCEEDS on any
# interactive Windows account, because Microsoft ships a python3.exe App
# Execution Alias that exists solely to open the Store when run. The desktop
# session agent's first run (32620912473) found it, skipped the shim, and Lint
# died in zero seconds. The service account never had the alias, which is why
# a night of service-session runs never met it.
if [ "${SHIM_FORCE:-0}" != "1" ] && python3 --version >/dev/null 2>&1; then
  echo "python3 already runs here ($(python3 --version 2>&1)); no shim needed"
  exit 0
fi

pick="$(pick_interpreter || true)"
if [ -z "$pick" ]; then
  echo "NO WORKING PYTHON and the zip fallback failed - the reason is above."
  exit 1
fi
mkdir -p "$RUNNER_TEMP/shim"
printf '#!/usr/bin/env bash\nexec %s "$@"\n' "$pick" > "$RUNNER_TEMP/shim/python3"
chmod +x "$RUNNER_TEMP/shim/python3"
# PROVE THE SHIM'S OWN PRODUCT RUNS before anything depends on it.
if ! "$RUNNER_TEMP/shim/python3" --version >/dev/null 2>&1; then
  echo "the python3 shim did not run (picked: $pick)"
  exit 1
fi
if [ -n "${GITHUB_PATH:-}" ]; then
  echo "$RUNNER_TEMP/shim" >> "$GITHUB_PATH"
  echo "python3 -> $pick, and $RUNNER_TEMP/shim is on the job PATH"
else
  echo "python3 -> $pick, written to $RUNNER_TEMP/shim (no GITHUB_PATH set, so"
  echo "this run put nothing on any PATH: that is the outside-CI case)"
fi
exit 0
