#!/usr/bin/env python3
"""Print the numbers for the Copper Row sheet spec, using imagegen.py's OWN
functions rather than a second copy of its arithmetic.

Why it exists: every number in the delivery must be re-derivable by somebody
who does not believe the delivery. It imports the tool, so if the tool's
exclusion scanner, its prompt composer or its cost anchors change, this
printer changes with them and the number moves. A printer with its own copy of
the maths is the silent-instrument failure this project keeps paying for.

Run from the repository root:
    python3 production/art/concept-copper-row-2026-09-10/check-copper-row-sheet.py

Every zero below carries its denominator, and a never-ran case says so in
those words rather than printing a clean nothing.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC = HERE / "copper-row-sheet-2026-09-10.json"
sys.path.insert(0, str(REPO / "tools" / "imagegen"))

import imagegen as ig                                            # noqa: E402


def main():
    spec, path, state = ig.load_spec(SPEC)
    if spec is None:
        return ig.refuse_missing_spec(path, state)
    print(ig.spec_line(path, str(SPEC), spec))

    problems = ig.validate_spec(spec)
    items = spec["items"]
    rules = spec["content_rules"]["rules_clause"]
    forbidden = spec["content_rules"]["forbidden_tokens"]
    style = spec["style"]
    print(f"validate problems={len(problems)}/{len(items)}itemsExamined "
          f"forbiddenTokensInGuard={len(forbidden)}")
    for p in problems:
        print(f"  problem {p}")

    total = 0.0
    for it in items:
        prompt = ig.build_prompt(it, rules, style)
        neg = ig.build_negative(it, spec)
        # THE EXEMPTION IS NAMED, NOT SILENT: the content-rules clause is the
        # one exclusion clause allowed in a positive prompt (build_prompt's
        # own reasoning), so it is removed by identity before the scan and
        # said so here. Everything else in the positive half is scanned.
        pos_hits, pos_words = ig.scan_exclusions(prompt, exempt=(rules,))
        neg_hits, neg_words = ig.scan_exclusions(neg)
        bad = ig.check_forbidden(prompt + " " + neg, forbidden)
        cfg = ig.item_cfg(it, spec["defaults"])
        active, why = ig.negative_state(cfg, neg)
        secs = ig.estimate_seconds(it["width"], it["height"], cfg)
        total += secs
        print(f"item {it['id']} {it['width']}x{it['height']} "
              f"seed={ig.item_seed(it, spec['defaults'])} cfg={cfg:g} "
              f"positiveExclusions={len(pos_hits)}/{pos_words}wordsScanned "
              f"negativeExclusions={len(neg_hits)}/{neg_words}wordsScanned "
              f"forbiddenHits={len(bad)}/{len(forbidden)}tokensScanned "
              f"rulesClauseExempted=by-identity "
              f"framingClausePresent={style['framing_required'] in prompt} "
              f"negativeActive={active} "
              f"estSeconds={secs:.0f}")
        if pos_hits:
            print(f"  positive-exclusion-words {pos_hits}")
        if neg_hits:
            print(f"  negative-exclusion-words {neg_hits}")
        if bad:
            print(f"  forbidden-marks {bad}")
    print(f"done itemsInSpec={len(items)} "
          f"estMinutesWholeRunSum={total / 60:.1f} "
          f"estSource={ig.COST_SOURCE.replace(' ', '-')} "
          f"vaePathNote=every-size-here-and-all-three-cost-anchors-exceed-"
          f"{ig.VULKAN_VAE_DIRECT_MAX_PX}px-so-all-take-the-vae-on-cpu-path")
    return 1 if (problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
