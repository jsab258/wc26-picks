line: production (the visual bar, and the asset pipeline that feeds it)
spec: this file, plus the artifact-reader QA report over all 45 images
acceptance: (1) every prompt in tools/imagegen/prompts.json carries an explicit framing clause and the generator REFUSES a prompt that lacks one, with a selftest fixture in both directions; (2) a regenerated set in which the artwork fills the frame edge to edge, square on, with no surrounding scene, measured rather than eyeballed: a printed per-image usableFraction with its method named, over a denominator of all 45; (3) the crop rectangles the queue 046 builder wrote by hand are DELETED as dead code, or the record says which images still need one and why
max_sessions: 2
status: PARTLY LANDED 2026-09-03, commit 991aabf9, and OPEN by the 3 September ruling. Acceptance (1) is met: 41 of 45 recipes moved onto the orthographic prefix and imagegen run 4 regenerated them, skipped=4 remadeRecipeChanged=41 exactly as predicted. Acceptance (2), a usableFraction per image, and (3), the crop rectangles, are NOT met and become queue 057. Was: READY 2026-09-02, blocked on the QA report landing.

## The finding

The generated images are PHOTOGRAPHS OF SIGNS IN A STREET, not sign plates.
A decal needs the artwork and nothing else. What we have is the artwork
sitting in a scene, with pavement, sky, other buildings and a depth-of-field
blur around it.

Three independent lines of evidence, none of them "it looks wrong to me":

1. The prompts never ask for anything else. `sign_ferry`, read in full, is
   "a British ferry terminal sign, white enamel on a black steel plate, tall
   condensed capitals reading 'MERIDIAN FERRY' ... bolted at four corners".
   Nothing in it says square on, nothing says fill the frame, nothing says no
   background. The model answered the question it was asked.
2. The queue 046 builder, wiring the pictures onto the street, had to write
   FOUR DIFFERENT CROP RECTANGLES for four shopfront signs, because
   "`fascia_mickeys` is a signboard, `fascia_fish_market` is a whole
   shopfront with a sky in it". Hand-cropping in the consumer is the fault
   showing up as somebody else's work.
3. Two wall images turn out to be 1024 tiling SURFACES rather than stamps,
   so a whole class was generated against a different idea of what it was
   for.

## Why this is not a small thing

Forty-five images were generated, banked and reported as an asset library.
Any of them that cannot be applied to a surface is inventory, which is the
same fault queue 046 exists to fix one level up: the props existed for weeks
and the street used none of them. A picture nothing can apply and a prop
nothing places are the same kind of nothing.

It is also cheap to fix and expensive to leave. GPU time on that machine
costs nothing against the ceiling, so regenerating the whole set with a
correct framing clause costs a night. Cropping 45 images by hand in the
consumer costs every consumer, for ever.

## The work

1. A framing clause on every prompt, written once and applied to all: square
   on, artwork filling the frame edge to edge, no surrounding scene, no
   perspective, even light, no depth of field. The exact wording is a
   builder decision informed by what the QA report says actually went wrong,
   not a guess made here.
2. THE GENERATOR REFUSES A PROMPT WITHOUT ONE. A rule nobody can forget beats
   a rule in a document. Accepting fixture first (a prompt that carries the
   clause generates), then the rejecting one (a prompt that does not is
   refused by name).
3. Measure the result. `usableFraction` per image with its method stated, and
   a denominator of 45, so "the set is fixed" is a number and not an
   impression. A zero here needs its denominator like every other zero.

## The trap

Do not fix this by cropping in the consumer and calling it done. The crop
rectangles in the scene file are a workaround for a generator fault and they
are the thing to DELETE, not the thing to extend. If any image still needs a
hand crop after regeneration, that image is named in the record with the
reason, and the count of them is printed.

## Not in scope

The tiling wall surfaces are queue 052, a different fault with a different
fix (they belong in the AssetLibrary surface path). Do not fold them in.
