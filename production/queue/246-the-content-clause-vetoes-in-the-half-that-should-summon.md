# 246. The D18 content clause spends the positive prompt vetoing, and never says "adults"

STATUS: READY, 2026-09-10. Found by the resident reviewing the D18 image
enforcement before commit, by reading `tools/imagegen/imagegen.py` rather than
the lane's report. The mechanism is right. The wording defeats it.

## What is right, and it is most of it

`build_prompt` at `tools/imagegen/imagegen.py:560` FAILS CLOSED. Line 595 raises
unless the clause is present and unaltered, so no prompt can be built without
it. Line 623 puts it in the composed positive prompt:

    parts = [prefix.strip(), item["prompt"].strip(), suffix.strip(),
             rules_clause.strip()]

So the clause is in the POSITIVE half, which is the half that is evaluated. That
matters here more than usual: at cfg 1.0 the negative prompt is never evaluated
at all, and the copper-row spec says so in its own note. A D18 rule parked in
the negatives would have done nothing. It is not parked there. That is right.

## What is wrong

The clause is: "nothing poured or consumed, no games of chance, nobody under
eighteen and no school in use, nothing sexual".

Every term is a VETO, and it is sitting in the half whose job is to SUMMON.

Jafar's standing rule, 2026-09-10: "a negative vetoes but cannot summon;
anything that must appear is named in the positive half." The clause obeys the
letter of that rule, since it is in the positive half, and breaks its point: a
model conditioned on "nobody under eighteen" has been given no instruction to
draw an adult. It has been given the word eighteen and the concept of a person
under it. Negation in a positive prompt is weak at best and summoning at worst.

## The proof is already in the repo, and the gate itself names it

`python3 tools/content-gate.py --enforceable` prints, as its last row:

    what-a-picture-actually-shows  NOT MECHANICAL, AND MEASURED.
    fairview_theirs_vs_ours_finished.jpg was drawn from a prompt asking for
    `three nonidentifiable people` and came back with two children in school
    uniform at a FAIRVIEW SCHOOL gate.

The resident opened that file independently and confirms it: a FAIRVIEW SCHOOL
sign in both views, figures in school uniform in both, and a swatch captioned
SCHOOL SATCHEL. The prompt said "people". The model chose who. Nothing in the
prompt said adults, and nothing in the new clause says it either.

## Done looks like

The clause names, affirmatively, everything that MUST appear when it appears at
all. At minimum: every figure an adult. Then:

- the clause is re-written once and written identically into all 7 prompt-bearing
  specs, since `content-gate.py` already checks `specsClauseIdentical=7/7` and
  that check is what stops the seven drifting;
- the token self-trip check is re-run before anything generates. The lane that
  built this already caught its own first wording, "nothing served or drunk",
  which contained the token `drunk` and would have made all 45 library items
  refuse themselves. An affirmative rewording can trip the same wire;
- the accepting case first: a real generation of a scene WITH people in it, and
  a person opens the file and counts the adults. Rule 4 applies with full force
  here, because this is the one D18 clause no word gate can check. The gate says
  so itself, in the row quoted above.

## Dependencies and risk

Independent of queue 243 and 244; all three touch the same tool's report, so
sequence them rather than running them together.

Risk if ignored: the image half of D18 reads as enforced, prints
`specsCarryClause=7/7`, and still returns children, because a clause that only
forbids has told the model nothing about what to draw instead. That is a green
number standing in for the frame it claims to describe, which is the failure
this project has a numbered rule about.

## The project already knows this, has a guard for it, and the D18 clause is EXEMPT

Found after this item was filed, by chasing a line in the minicab commission's
report: its image spec was refused on the first run for "the word no in the
positive half". So there is a guard. `tools/imagegen/imagegen.py:782`:

    hits, scanned = scan_exclusions(prompt, exempt=(rules,))
    if hits:
        problems.append(
            f"{who}: the POSITIVE prompt still says {hits} - an exclusion "
            "belongs in `negatives`, because a diffusion model reads the "
            "noun and draws it. That is what put a sign board on "
            "wall_soot_brick.")

Three things follow, and together they make this item more serious than it was.

FIRST, THIS IS NOT A THEORY IN THIS PROJECT. The guard's own message states the
mechanism, "a diffusion model reads the noun and draws it", and names the
incident that bought it: a sign board appeared on `wall_soot_brick` because an
exclusion sat in the positive half. The reasoning in this queue item is the
codebase's own, already paid for once.

SECOND, `exempt=(rules,)` EXEMPTS THE D18 CLAUSE FROM EXACTLY THAT GUARD. The
one string that rides on EVERY positive prompt is the one string the check
cannot see. Every other exclusion in the library is caught; the content rule is
waved through.

THIRD, THE EXEMPTION IS NOT A BLUNDER, AND THAT IS WHY THIS NEEDS A DESIGN AND
NOT A DELETION. Without it the clause would trip the guard on all 45 items at
once, which is a real failure mode the gate lane already hit from the other
side: its first wording, "nothing served or drunk", contained the token `drunk`
and would have made every item refuse itself. So the exemption keeps the
library working, and its cost is that the fault the guard exists to catch is
unmeasured on the only line that appears everywhere.

## What that changes about "done looks like"

The affirmative rewrite in the section above is still the fix. Add to it:

- After the clause is affirmative, RE-TEST IT AGAINST THE GUARD ITSELF by
  running `scan_exclusions` on the clause with no exemption, and print the
  hits. A clause that passes its own guard unexempted no longer needs
  `exempt=(rules,)`, and removing that exemption is how this stops recurring.
  If it cannot pass unexempted, print the residue and say why each survivor
  has to stay, rather than keeping a blanket exemption.
- The rejecting fixture is now free: plant the CURRENT clause and prove the
  unexempted scan fires on it. That is a guard tested on the case it should
  reject, using text that really shipped.
