#!/usr/bin/env python3
"""THE C# TOKENISER, CHECKED AGAINST THE ONE IT IS COPYING.

    python3 tools/voice-live/tokenizer-reference.py --cs   # C# literals
    python3 tools/voice-live/tokenizer-reference.py --selftest

WHY. `Core/SpeechTokenizer` turns words into the numbers the model reads. It
is the last piece of the pipeline that had to be reimplemented rather than
converted, and it has the same danger as the sampler: every way of getting it
slightly wrong still produces speech. A word split into the wrong pieces is
still pronounceable — it just sounds like somebody reading a language they do
not speak.

So the real thing is asked. HuggingFace's `tokenizers` installs from PyPI
(unlike the model weights, which do not), and `tools/voice-live/tokenizer.json`
came off Jafar's machine on 7 August, so the exact tokeniser the game will ship
can be run right here and its answers pasted into the C# tests as literals.

WHAT THE FILE TURNED OUT TO BE, read rather than assumed:

    BPE, 704 tokens, 265 merges
    normalizer            null            — nothing is lowercased or stripped
    pre_tokenizer         Whitespace      — the regex \\w+|[^\\w\\s]+
    post_processor        null            — no automatic start/end tokens
    unk_token             [UNK]
    fuse_unk              false           — two unknowns stay two tokens
    continuing_subword_prefix / end_of_word_suffix   both null

AND THE TWO BEHAVIOURS THAT WOULD HAVE BEEN GUESSED WRONG:

  `[SPACE]` is an ADDED TOKEN (id 2), so it is cut out of the text before the
  pre-tokeniser ever sees it. chatterbox replaces every space with that
  literal string first (`tokenizer.py: txt.replace(' ', SPACE)`), so a naive
  implementation that pre-tokenises first would split it into `[`, `SPACE`,
  `]` and produce three wrong tokens per word gap.

  CAPITALS HAVE NO MERGES. The merge table was learned on lower case, so
  "Hello" comes out as H + e + ll + o rather than as one piece. That is not a
  bug to fix — it is what the model was trained on, and `punc_norm`
  capitalises the first letter of every line, so it happens constantly.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
VOCAB = ROOT / "tools" / "voice-live" / "tokenizer.json"
SPACE = "[SPACE]"

# CHOSEN TO EXERCISE ONE RULE EACH, and several are outputs of `punc_norm`
# rather than raw text, because that is what actually reaches the tokeniser.
TEXTS = [
    "I was on the docks when it happened.",   # a real line, the default one
    "Hello there.",                           # a capital with no merges
    "Wait,  what.",                           # punc_norm's double space
    "the",                                    # a whole word that is one token
    "a",                                      # a single character
    "aaaaaaaa",                               # merges applied repeatedly
    "don't",                                  # an apostrophe splits the word
    "one-two",                                # a hyphen does too
    "ZQXJ",                                   # capitals, no merges at all
    "...",                                    # punctuation only, one run
    "he said, go now.",
    "éclair naïve",                 # accented letters that ARE in the vocab
    "中文",                           # not in the vocab at all -> UNK
    "Ends with a dash -",
]


def cs(s):
    """A C# string literal, non-ASCII escaped so an encoding change cannot
    silently alter what a test is testing."""
    out = ['"']
    for ch in s:
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ord(ch) < 32 or ord(ch) > 126:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def rows():
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(VOCAB))
    out = []
    for t in TEXTS:
        e = tok.encode(t.replace(" ", SPACE))
        out.append({"text": t, "ids": e.ids, "tokens": e.tokens})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cs", action="store_true", help="print C# test literals")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if not VOCAB.exists():
        # A DENOMINATOR ON THE SKIP. "the vocabulary has not been fetched" and
        # "every case passed" must not print the same way.
        print(f"  skipped: no {VOCAB.relative_to(ROOT)} — "
              f"0 of {len(TEXTS)} texts checked. Run '4 PREPARE THE VOICES.bat'.")
        return 0
    try:
        data = rows()
    except ImportError as e:
        print(f"  skipped: {e} — 0 of {len(TEXTS)} texts checked")
        return 0

    if a.cs:
        for r in data:
            print("            Same(%s, %s);"
                  % (cs(r["text"]), ", ".join(str(i) for i in r["ids"])))
        return 0

    for r in data:
        print(f"  {r['text']!r}\n      {r['ids']}\n      {r['tokens']}")

    if a.selftest:
        bad = []
        by = {r["text"]: r for r in data}
        # THE TWO BEHAVIOURS A REIMPLEMENTATION WOULD GUESS WRONG. If either
        # stops holding, the vocabulary file has changed under us and every
        # literal in the C# tests is stale.
        gap = by["I was on the docks when it happened."]
        if gap["tokens"].count(SPACE) != 7:
            bad.append(f"[SPACE] is not surviving as one token: {gap['tokens']}")
        if by["Hello there."]["tokens"][:4] != ["H", "e", "ll", "o"]:
            bad.append(f"capitals have started merging: {by['Hello there.']['tokens']}")
        if by["Wait,  what."]["tokens"].count(SPACE) != 2:
            bad.append("punc_norm's double space is not two [SPACE] tokens")
        if by["中文"]["tokens"] == []:
            bad.append("out-of-vocabulary text produced nothing at all")
        for b in bad:
            print(f"  FAIL  {b}")
        print(f"\ntokenizer-reference --selftest: "
              f"{'PASS' if not bad else str(len(bad)) + ' FAILED'} — {len(data)} texts")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
