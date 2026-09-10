# 250. NPC gossip goes through walls. The player's hearing does not. Same town, two physics.

STATUS: READY, 2026-09-10. Found by the world-designer lane while designing a
two-room pub, and verified in the code by the resident before filing. This is a
MOAT bug, not a polish item: the information pillar is one of the three things
this project exists to be better at than KCD2.

## The two halves, read rather than remembered

`ledger/Assets/Scripts/Game/GossipDirector.cs:660`:

    bool Together(string a, string b)
    {
        var pa = PositionOf(a);
        var pb = PositionOf(b);
        if (pa == null || pb == null) return false;
        return Vector3.Distance(pa.Value, pb.Value) <= TalkRange;
    }

`TalkRange = 6f` at line 34. Straight-line distance and nothing else.
`GossipDirector` references `Acoustics` ZERO times, checked by grep.

`ledger/Assets/Scripts/Core/Acoustics.cs` meanwhile carries occlusion properly:
`LowPassHz(metres, occluded)` caps at 700 Hz through a wall at line 76,
`Intelligibility(metres, occluded, ...)` multiplies clarity by 0.25 at line 96,
and `CanMakeOutWords(metres, occluded, ...)` reads that at line 101. Its
consumers are `Game/SpeechBubble.cs`, `Game/LawHost.cs` and `Core/Combat.cs`.

So the model exists, it is correct, it is tested, and the gossip mill does not
call it.

## What that means in play

Two NPCs six metres apart with a wall between them are, to the mill, standing
together. Gossip crosses walls, floors, shut doors and the fronts of buildings,
everywhere in town, at all times.

The player's own overhearing does NOT, because the player's path goes through
`Acoustics`. So the town runs two different physics: the one the player
experiences, where a shut door protects a conversation, and the one the
simulation runs, where it does not.

That is worse than either rule applied consistently, because the player learns
the first rule by playing and the world obeys the second.

## Why it is urgent rather than interesting

- IT SILENTLY DELETES INTERIOR DESIGN. Any layout whose point is separation is
  fictional to the mill. The immediate case is the pub in
  `production/specs/the-pub-without-drink.md`, whose back room and front bar
  are meant to be different information spaces and currently are not. The cab
  office in `production/art/mickeys-cars/` has the same shape: its whole design
  is that the public and the drivers are never in one room, with a screen and a
  speaking gap deciding what crosses.
- IT MOVES A PHASE GATE'S NUMBER. Phase 1's exit gate is "a witnessed crime
  reaching a second and a third NPC within one in-game week"
  (`production/ladder.md:86`). Propagation through walls makes that gate easier
  to pass than the design intends, so the gate could go green on a mill that is
  wrong. A gate that cannot tell the fixed case from the broken one is the
  fault this project has a rule about.

## Done looks like

`Together` asks `Acoustics` rather than only `Vector3.Distance`, with:

- the occlusion term sourced the same way the player's path sources it, so
  there is ONE implementation of "is there a wall between these two" and not a
  second that drifts;
- a printed series BEFORE any threshold moves: run the sim and print the
  distribution of NPC-to-NPC pair distances and how many pairs are occluded, so
  whatever bound replaces the bare 6f is set from evidence rather than picked;
- the accepting case first: a run where two NPCs in the same room DO pass a
  story, proving the change did not simply switch gossip off;
- the rejecting case planted: two NPCs six metres apart with a wall between
  them, who must not;
- the phase 1 gate re-read after the fix, with the before and after numbers
  side by side, because this changes what that gate measures.

## Dependencies and risk

Independent. It is a SIMULATION change, so it escalates to a director by the
standing rule and does not land on a resident's read.

Risk of fixing: gossip may slow to the point where the phase 1 gate stops
passing. That would not be a regression, it would be the gate finally measuring
what it claims to. Print both numbers and rule on them; do not loosen the bound
to keep the green.

Risk of not fixing: every interior the studio designs from now on is designed
against a mill that cannot see it.

## One thing NOT established, and not to be repeated as fact

The lane that found this also derived that ties below about 0.56 cannot carry a
story to a third person, from `Core/Gossip.cs:393` and `:494`,
`Math.Clamp(passed * 0.8, 0.2, 0.85)`. The resident confirmed the constant
exists at both sites and did NOT confirm the derivation: that clamp has a LOWER
bound of 0.2, so confidence never decays below 0.2, which does not obviously
support the claim. Treat the tie threshold as UNVERIFIED until somebody reads
the surrounding code and prints the series. It is a separate question from the
occlusion bug, which is verified.
