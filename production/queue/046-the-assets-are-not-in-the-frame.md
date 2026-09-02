line: production (D1 comparison, the visual bar)
spec: this file
acceptance: the street scene places the held props by name from the shared JSON, and the generated decals are applied to the surfaces the bill of materials assigns them to; a printed count of propsPlaced=N/M and decalsApplied=N/M on the sim verdict; a still in which the difference is visible
max_sessions: 1
status: READY 2026-09-02. systems-builder. Found by Jafar asking what the images are FOR.

## The finding, and it is the project's own rule

37 props exist under `ledger/Assets/Props/base-mesh/` (awnings, bins,
benches, crowd barriers, a phone kiosk) and 14 generated decals exist under
`ledger/Assets/StreamingAssets/Decals/generated/`. THE STREET SCENE USES
NEITHER.

Measured, not supposed:

    grep -c "base-mesh|BaseMesh" StreetVignetteHost.cs  -> 0
    grep -c "base-mesh|BaseMesh" StreetVignette.cs      -> 0
    grep -rln "fascia_mickeys|sign_ferry|notice_tide" --include=*.cs -> nothing

The four frames Jafar has seen are built entirely from primitive shapes.
Every prop and every picture in this repository was absent from them.

BUILT IS NOT RUNNING. The resident has been reporting asset counts as
progress while the thing that matters, the asset being IN THE FRAME, had
never happened. A prop nothing places and a picture nothing applies are
inventory, not a street.

## Why this outranks generating more

The overnight batch adds 31 pictures to a directory nothing reads. That is
worth doing because it is free and the pictures will be wanted, but it moves
no number the Meridian Test measures. THIS item is what turns the existing
inventory into a visible street, and it is also what tells us whether the
generated decals look right AT SIZE, ON A SURFACE, IN THE RAIN, which is the
only test that matters and which no amount of opening PNGs can answer.

## The work

1. The scene JSON gains a placement for held props by NAME, so props arrive
   through the same shared-JSON generator route as everything else and the
   UE side gets them for free from the piece list.
2. The bill of materials already assigns decals to surfaces (A5 double
   yellows to the kerb line, E10 the plate to a wall, C11 the interior card
   behind glass). Apply them.
3. Print `propsPlaced=N/M` and `decalsApplied=N/M` on the sim verdict, with M
   the number the JSON asked for. A zero here needs its denominator like any
   other, and the current silent zero is exactly why this went unnoticed.

## The trap

Do not place all 37 because they exist. The BOM says which the vignette
wants; the rest are inventory for later streets. Placing everything to make
a number go up is the opposite of the point.
