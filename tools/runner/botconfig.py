#!/usr/bin/env python3
"""Read the Telegram credentials out of tools/runner/config.local, and never
say what it found.

    python3 tools/runner/botconfig.py --selftest    # accepting case first

WHY THIS IS ITS OWN FILE. Nothing in this repo read config.local before
2026-09-04, so its format was never specified, and Jafar had already written
a token and a chat id into it without being told a key name. One hardcoded
spelling would have been a coin flip settled only by a failed run on his PC,
and there are no fix loops before the Monday reset. So this accepts several
spellings, either separator, and falls back to the SHAPE of the two values
when the file carries no key names at all. The canonical spelling is written
down in tools/runner/README.md so the guessing ends here.

THE CREDENTIAL RULE, which is why the parsing lives behind a function rather
than inline in the bot. Nothing here prints, logs or raises a value out of the
file. A failure names the KEY SPELLINGS it looked for and the COUNT of lines
it read, which is a denominator and not a leak (rule 3b). `redact` exists
because the token also travels inside every Telegram API URL, and an
unscrubbed traceback is how that class of file actually leaks: the gitignore
stops a commit and stops nothing else.

EXIT CODES. 0 selftest passed. 3 selftest failed. Anything else is a bug.
"""
import codecs
import os
import re
import sys

#: Spellings tried, in order, case-insensitively. Longest and most specific
#: first so that a file carrying two of them resolves the same way twice.
TOKEN_KEYS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN", "BOT_TOKEN", "TOKEN")
CHAT_KEYS = ("TELEGRAM_CHAT_ID", "CHAT_ID", "CHAT")

#: THE SHAPE FALLBACK, for a file that is two bare lines with no key names.
#: A bot token is `<numeric bot id>:<35 or so url-safe characters>`; a chat id
#: is digits, negative for groups. These match the SHAPE and never report the
#: text they matched.
TOKEN_SHAPE = re.compile(r"^\d{4,}:[A-Za-z0-9_-]{20,}$")
CHAT_SHAPE = re.compile(r"^-?\d{4,20}$")

#: A key name starts with a letter. Digits before a colon are a bot id.
KEY_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.\- ]*$")

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "config.local")


class ConfigError(Exception):
    """Carries a message that is safe to print. Nothing else may be printed."""


def decode(raw):
    """Bytes to text, sniffing the BOM Notepad and PowerShell leave behind.

    `notepad` saving as UTF-8 writes a BOM; PowerShell's `>` writes UTF-16LE.
    Either one makes the first key name unrecognisable, and the failure would
    read as a wrong key spelling rather than as an encoding, which is the
    diagnosis this file exists to make impossible.
    """
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        return raw.decode("utf-16", errors="replace")
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode("utf-8-sig", errors="replace")
    return raw.decode("utf-8", errors="replace")


def unquote(value):
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        v = v[1:-1].strip()
    return v


def parse(text):
    """Text to (entries, bare_values, lines_read).

    `entries` maps a lowercased key to its value. `bare_values` are lines with
    no separator at all, kept only so the shape fallback has something to look
    at. `lines_read` counts non-blank non-comment lines and is the denominator
    every failure message ships.

    THE SEPARATOR IS THE EARLIEST OF `=` AND `:`, not `=` then `:`. A bot
    token CONTAINS a colon, so splitting on the first colon of
    `TELEGRAM_TOKEN=123:AAH...` would have cut the value in half and produced
    a token that Telegram rejects with a 401, which reads as a bad token
    rather than as a bad parser.
    """
    entries, bare, lines_read = {}, [], 0
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("﻿")
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        lines_read += 1
        eq, co = line.find("="), line.find(":")
        cuts = [i for i in (eq, co) if i > 0]
        if not cuts:
            bare.append(unquote(line))
            continue
        cut = min(cuts)
        key = line[:cut].strip().strip("'\"").lower()
        value = unquote(line[cut + 1:])
        # A BARE TOKEN LINE LOOKS EXACTLY LIKE `key: value`, because a bot
        # token IS `<digits>:<letters>`. Read as key/value it yields a key of
        # digits and a value that is the token minus its bot id, which
        # Telegram rejects with a 401: the wrong parse would have read as a
        # wrong token. So a line whose whole text is token-shaped, or whose
        # key part is not a key name, is a bare value.
        if TOKEN_SHAPE.match(line) or not KEY_NAME.match(key):
            bare.append(unquote(line))
            continue
        if key and value:
            entries[key] = value
        elif value:
            bare.append(value)
    return entries, bare, lines_read


def pick(entries, bare, keys, shape):
    """Return (value, source) or (None, None). Source names the ROUTE, never
    the value: `key/CHAT_ID`, `shape/value-of-FOO`, `shape/bare-line`.
    No spaces in a source, because it is printed into a key=value verdict."""
    lowered = {k.lower(): k for k in keys}
    for k in keys:
        if k.lower() in entries:
            return entries[k.lower()], "key/" + lowered[k.lower()]
    for k, v in entries.items():
        if shape.match(v):
            return v, "shape/value-of-" + re.sub(r"[^A-Za-z0-9_]", "-", k)
    for v in bare:
        if shape.match(v):
            return v, "shape/bare-line"
    return None, None


def _missing(kind, keys, entries, bare, lines_read):
    return ConfigError(
        "config.local: no key matching %s, and nothing shaped like a %s "
        "(%d spelling(s) tried, %d non-comment line(s) read, %d value(s) "
        "shape-checked)"
        % ("/".join(keys), kind, len(keys), lines_read, len(entries) + len(bare)))


class Credentials(object):
    def __init__(self, token, chat_id, token_source, chat_source, lines_read):
        self.token = token
        self.chat_id = chat_id
        self.token_source = token_source
        self.chat_source = chat_source
        self.lines_read = lines_read

    @property
    def chat_shape(self):
        """`ok` or `unexpected`. A chat id that is not digits will come back
        from Telegram as `chat not found`, which reads as the wrong chat
        rather than as the wrong field, so the verdict says which one it is
        BEFORE the network is involved."""
        return "ok" if CHAT_SHAPE.match(self.chat_id or "") else "unexpected"

    def secrets(self):
        return [s for s in (self.token, self.chat_id) if s]


def load(path=None):
    """Read the file or raise ConfigError with a message that is safe to
    print. Every branch here has been asked: could this string contain any
    character that came out of the file? The answer has to be no."""
    path = path or DEFAULT_PATH
    if not os.path.exists(path):
        raise ConfigError("config.local not found at %s" % path)
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        raise ConfigError("config.local unreadable")
    entries, bare, lines_read = parse(decode(raw))
    if lines_read == 0:
        raise ConfigError("config.local is empty (0 non-comment line(s) read)")
    token, tsrc = pick(entries, bare, TOKEN_KEYS, TOKEN_SHAPE)
    if token is None:
        raise _missing("bot token", TOKEN_KEYS, entries, bare, lines_read)
    chat, csrc = pick(entries, bare, CHAT_KEYS, CHAT_SHAPE)
    if chat is None:
        raise _missing("chat id", CHAT_KEYS, entries, bare, lines_read)
    return Credentials(token, chat, tsrc, csrc, lines_read)


def redact(text, secrets):
    """Replace every secret with a placeholder, longest first so that a chat
    id which is a substring of nothing still cannot be reassembled from a
    partly-scrubbed line. Everything the bot prints goes through this,
    including exception text, because the token is inside every API URL."""
    out = str(text)
    for s in sorted([s for s in secrets if s], key=len, reverse=True):
        if s:
            out = out.replace(s, "<redacted>")
    return out


# --------------------------------------------------------------------------
# SELFTEST. Accepting case FIRST (rule 5b), synthetic fixtures in a temp
# directory, and it asserts it never opened the real file.
# --------------------------------------------------------------------------
FAKE_TOKEN = "8123456789:AA-SELFTEST-NOT-A-REAL-TOKEN-000000000"
FAKE_CHAT = "5550001234"


def _selftest():
    import tempfile
    passed, failed, accepting, rejecting = [], [], 0, 0

    def write(tmp, name, data):
        p = os.path.join(tmp, name)
        with open(p, "wb") as fh:
            fh.write(data)
        return p

    def check(name, ok, detail=""):
        (passed if ok else failed).append(name)
        print("  %-34s %s%s" % (name, "pass" if ok else "FAIL",
                                (" : " + detail) if detail and not ok else ""))

    tmp = tempfile.mkdtemp(prefix="botconfig-selftest-")

    # ---- accepting cases ------------------------------------------------
    accept = [
        ("accept/equals-plain",
         b"TELEGRAM_TOKEN=%s\nCHAT_ID=%s\n" % (FAKE_TOKEN.encode(), FAKE_CHAT.encode()),
         "key/TELEGRAM_TOKEN", "key/CHAT_ID"),
        ("accept/colon-quotes-comments",
         b"# the studio bot\n\nbot_token: '%s'\n; note\ntelegram_chat_id: \"%s\"\n"
         % (FAKE_TOKEN.encode(), FAKE_CHAT.encode()),
         "key/BOT_TOKEN", "key/TELEGRAM_CHAT_ID"),
        ("accept/bare-lines-no-keys",
         b"%s\n%s\n" % (FAKE_TOKEN.encode(), FAKE_CHAT.encode()),
         "shape/bare-line", "shape/bare-line"),
        ("accept/utf8-bom-crlf",
         codecs.BOM_UTF8 + b"TOKEN=%s\r\nCHAT=%s\r\n" % (FAKE_TOKEN.encode(), FAKE_CHAT.encode()),
         "key/TOKEN", "key/CHAT"),
        ("accept/utf16le-powershell",
         ("TELEGRAM_TOKEN=%s\r\nCHAT_ID=%s\r\n" % (FAKE_TOKEN, FAKE_CHAT)).encode("utf-16"),
         "key/TELEGRAM_TOKEN", "key/CHAT_ID"),
        ("accept/unknown-key-names",
         b"MYBOT=%s\nWHERE=%s\n" % (FAKE_TOKEN.encode(), FAKE_CHAT.encode()),
         "shape/value-of-mybot", "shape/value-of-where"),
    ]
    for name, data, tsrc, csrc in accept:
        accepting += 1
        p = write(tmp, name.replace("/", "-") + ".local", data)
        try:
            c = load(p)
            ok = (c.token == FAKE_TOKEN and c.chat_id == FAKE_CHAT
                  and c.token_source == tsrc and c.chat_source == csrc)
            check(name, ok, "got %s / %s" % (c.token_source, c.chat_source))
        except ConfigError as e:
            check(name, False, str(e))

    # ---- rejecting cases ------------------------------------------------
    # THE CONDITION IS PLANTED, never loosened: a key that exists nowhere and
    # a value that is shaped like nothing.
    reject = [
        ("reject/no-matching-key", b"COLOUR=blue\nSIZE=large\nSHAPE=round\n",
         ["TELEGRAM_BOT_TOKEN", "3 non-comment line(s) read"]),
        ("reject/empty-file", b"# only a comment\n\n", ["0 non-comment line(s) read"]),
    ]
    for name, data, musts in reject:
        rejecting += 1
        p = write(tmp, name.replace("/", "-") + ".local", data)
        try:
            load(p)
            check(name, False, "it was ACCEPTED, which is the wrong answer")
        except ConfigError as e:
            msg = str(e)
            check(name, all(m in msg for m in musts), msg)
            print("      says: %s" % msg)

    rejecting += 1
    try:
        load(os.path.join(tmp, "there-is-no-such-file.local"))
        check("reject/missing-file", False, "it was ACCEPTED")
    except ConfigError as e:
        check("reject/missing-file", "not found at" in str(e), str(e))

    # ---- the leak check, which is the one that matters ------------------
    rejecting += 1
    leaky = write(tmp, "leak.local",
                  b"COLOUR=%s\nSIZE=%s\n" % (FAKE_TOKEN.encode(), FAKE_CHAT.encode()))
    said = ""
    try:
        load(leaky)
        said = "(accepted by shape, so the failure path was not exercised)"
        # The shape fallback accepts this one, so provoke the failure path
        # with a file whose values are shaped like neither.
        leaky2 = write(tmp, "leak2.local", b"COLOUR=%s-tail\nSIZE=x%s\n"
                       % (FAKE_TOKEN.encode(), FAKE_CHAT.encode()))
        load(leaky2)
    except ConfigError as e:
        said = str(e)
    leaked = [n for n, s in (("token", FAKE_TOKEN), ("chat id", FAKE_CHAT))
              if s in said or any(part in said for part in (s[:8], s[-8:]))]
    check("reject/error-message-leaks-nothing", not leaked,
          "the message named the %s" % ", ".join(leaked))
    print("      says: %s" % said)

    # ---- redact ---------------------------------------------------------
    accepting += 1
    scrubbed = redact("HTTP Error 401 for https://api.telegram.org/bot%s/getMe"
                      % FAKE_TOKEN, [FAKE_TOKEN, FAKE_CHAT])
    check("accept/redact-scrubs-a-url", FAKE_TOKEN not in scrubbed, scrubbed)
    print("      says: %s" % scrubbed)

    # ---- it never touched the real file ---------------------------------
    accepting += 1
    check("accept/real-config-untouched", os.path.dirname(DEFAULT_PATH)
          not in tmp and tmp.startswith(tempfile.gettempdir()),
          "fixtures were not under the system temp directory")

    print("\nbotconfig selftest: %d passed, %d failed "
          "(%d case(s) run: %d accepting, %d rejecting; fixtures under %s, "
          "the real config.local was never opened)"
          % (len(passed), len(failed), len(passed) + len(failed),
             accepting, rejecting, tmp))
    return 0 if not failed else 3


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    print(__doc__.splitlines()[0])
    print("run with --selftest. This module is imported by "
          "tools/runner/telegram-bot.py and prints nothing from the file.")
    sys.exit(0)
