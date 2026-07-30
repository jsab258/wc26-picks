#!/usr/bin/env python3
"""The clip naming rule, in Python, byte-for-byte the same as the game's.

    python3 voice_bank.py --selftest

WHY THIS FILE IS A DUPLICATE ON PURPOSE.

`Assets/Scripts/Core/VoiceBank.cs` decides what a clip is called and what
seed generates it. The game computes that name to find a recording; the
generator has to compute the SAME name to write one. They are different
languages in different processes and there is no shared runtime between
them, so one of three things had to be true:

  a) the generator writes a manifest and the game reads it — one more file
     to keep in sync, and a game that cannot find a line without it;
  b) the game shells out to Python, which it obviously cannot;
  c) the rule is small enough to state twice and PINNED BY SHARED TEST
     VECTORS so a drift is caught rather than discovered.

(c), and the vectors below are asserted in CoreTests too. If either side
changes the hash, both sides go red on the same numbers rather than the bank
silently orphaning itself — which is the failure that would look like every
voice in the game vanishing at once for no traceable reason.

Keep this file and VoiceBank.cs in agreement. The test vectors are the
contract; the implementations are just two readings of it.
"""
import struct
import sys

# The six crowd voices the casting sheet actually funds. Not a number
# somebody liked -- see VoiceBank.cs on why six is thin and why the fix is
# casting rather than a larger constant here.
POOL_MASCULINE = ("crowd_m1", "crowd_m2", "crowd_m3")
POOL_FEMININE = ("crowd_f1", "crowd_f2", "crowd_f3")

CAST = frozenset({
    "lena", "rocco", "ellis", "reese", "kest",
    "sam", "ada", "vesna", "marla", "joey", "rita", "hal", "emil",
})

# Between the voice and the words. Not an empty string: concatenating with
# nothing between them makes ("ab","cd") and ("abc","d") hash identically.
SEP = "\u001f"


def hash32(s):
    """FNV-1a, 32-bit. The same number on every platform, in every process.

    Python's own hash() is randomised per process by default and C#'s
    string.GetHashCode() is randomised in modern .NET -- either would make a
    cache key that changes for reasons nobody can see."""
    h = 2166136261
    if s is None:
        return h
    # UTF-16 CODE UNITS, not Python characters. C# iterates `s[i]` over a
    # UTF-16 string, so a character outside the basic plane is TWO units
    # there and ONE here -- the two implementations would agree on every
    # line of dialogue anybody is likely to write and disagree on the first
    # emoji or rare glyph, which is the worst possible place to differ
    # because it would look like a one-off corrupt file.
    raw = s.encode("utf-16-le")
    for unit in struct.unpack("<%dH" % (len(raw) // 2), raw):
        h ^= unit
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def normalise(text):
    """Collapse whitespace, keep case.

    Case is kept because capitals change how a text-to-speech engine reads a
    sentence, so "no" and "NO" are two performances and deserve two files."""
    if not text:
        return ""
    return " ".join(text.split())


def clip_name(voice_id, text):
    t = normalise(text)
    if not voice_id or not t:
        return None
    return "%s/%08x" % (voice_id, hash32(voice_id + SEP + t))


def seed(voice_id, text):
    t = normalise(text)
    if not voice_id or not t:
        return 0
    return hash32(voice_id + SEP + t) & 0x7FFFFFFF


def voice_for(speaker_id, cast=CAST, masculine=None):
    if not speaker_id:
        return None
    if cast and speaker_id in cast:
        return speaker_id
    h = hash32(speaker_id)
    if masculine is True:
        return POOL_MASCULINE[h % len(POOL_MASCULINE)]
    if masculine is False:
        return POOL_FEMININE[h % len(POOL_FEMININE)]
    pool = POOL_MASCULINE if h % 2 == 0 else POOL_FEMININE
    return pool[(h // 2) % len(pool)]


# THE CONTRACT, and it is written out rather than computed. Every one of
# these is asserted in CoreTests as well, against the C# implementation, so a
# drift on either side goes red on both with the same numbers instead of the
# bank silently orphaning itself.
#
# The astral entry is deliberate: it is the case where a naive Python port
# disagrees with C# about what a character is, and it disagrees SILENTLY.
VECTORS = [
    # (voice, text, clip name, seed)
    ("rocco", "He was at the yard on Tuesday.", "rocco/df92fd5e", 1603468638),
    ("lena", "He was at the yard on Tuesday.", "lena/1d5782f8", 492274424),
    ("crowd_m1", "Evening.", "crowd_m1/953df5cc", 356382156),
    # Outside the basic plane: two UTF-16 units in C#, one character in
    # Python. A naive port passes every other vector here and fails only
    # this one, which is why it is here.
    ("rocco", "Told you \U0001F600 nothing.", "rocco/f278f6c6", 1920530118),
]


def selftest():
    ok = fail = 0

    def check(cond, what, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("  FAILED: %s %s" % (what, detail))

    check(hash32("") == 2166136261, "FNV-1a offset basis")
    check(hash32("a") == 0xe40c292c, "FNV-1a of 'a'", hex(hash32("a")))
    check(hash32("foobar") == 0xbf9cf968, "FNV-1a of 'foobar'", hex(hash32("foobar")))

    check(normalise("  two   words \n") == "two words", "whitespace collapses")
    check(normalise("No") != normalise("NO"), "case is kept")

    said = "He was at the yard on Tuesday."
    check(clip_name("rocco", said) == clip_name("rocco", "  He was at the yard on Tuesday.  "),
          "a re-indented line is the same recording")
    check(clip_name("rocco", said) != clip_name("lena", said),
          "two people saying the same words are two recordings")
    check(clip_name("rocco", said).startswith("rocco/"), "the voice is the folder")
    check(len(clip_name("rocco", said)) == len("rocco/") + 8, "voice plus eight hex digits")
    check(clip_name(None, said) is None and clip_name("rocco", "  ") is None,
          "an unspeakable line gets no plausible path")

    check(seed("rocco", said) == seed("rocco", said), "the same line seeds the same take")
    check(seed("rocco", said) >= 0, "the seed is non-negative")

    check(voice_for("rocco") == "rocco", "a cast member IS their voice")
    check(voice_for("resident_8817").startswith("crowd_"), "everybody else draws a crowd voice")
    check(voice_for("resident_8817", masculine=True).startswith("crowd_m"),
          "and a known gender gets a matching voice")
    reached = {voice_for("resident_%d" % i) for i in range(4000)}
    check(len(reached) == len(POOL_MASCULINE) + len(POOL_FEMININE),
          "four thousand walkers reach every crowd voice", str(sorted(reached)))

    # THE CROSS-LANGUAGE CONTRACT, asserted rather than printed. Printing
    # them for a human to compare by eye is how two implementations stay
    # "obviously the same" right up until they are not.
    for voice, text, want_name, want_seed in VECTORS:
        check(clip_name(voice, text) == want_name,
              "vector %s/%r names %s" % (voice, text[:24], want_name),
              str(clip_name(voice, text)))
        check(seed(voice, text) == want_seed,
              "vector %s/%r seeds %d" % (voice, text[:24], want_seed),
              str(seed(voice, text)))

    print("\n%d passed, %d failed" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else selftest())
