line: production (the Unreal emitter, Phase C)
spec: found in passing 2026-09-06 by the engine-specialist reading run 24's
  verdict while fixing something else.
acceptance: the UV head connection READS BACK as connected, with the pin names
  that made it printed; or `materialConnections` stops counting a connection it
  cannot read back
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. It calls queue 062's discharge into question and
  nobody has looked at it.

## The finding

Run 24 prints, on the same line:

    materialConnections=14/14
    materialUvHeadVia=both.out.empty..in.empty
    materialUvHeadReadback=0/2..unreadable2

The UV chain head was made by a pin pair whose names are EMPTY STRINGS, and
NEITHER head reads back. So 14 of 14 is carried, in part, by a connection the
tool cannot confirm exists.

## Why it matters more than it looks

Queue 062 was DISCHARGED on exactly this number reaching 14/14. That discharge
was correct in its own terms, and the frames after it proved 062 was not the
cause of the untextured street. But "14/14 by a nameless pin that will not read
back" is not the same claim as "the UV chain is wired", and this repository has
been bitten twice this week by a count that could not fail.

`connect_material_expressions` takes the output pin name and the input pin name
as STRINGS and answers false when either names a pin the expression does not
have: no exception, no log line, one false. The sweep that found the working
combination found one that returns TRUE with both names empty. Whether an empty
name means "the default pin" or means something the API accepts and discards is
NOT ESTABLISHED, and the readback saying `unreadable2` is the reason to ask.

## What this item must NOT do

Do not lower `materialConnections`. The count is not the problem; the silence
behind two of its members is. Either make the readback work and print the pin
names that answered, or make the count refuse to include a connection it cannot
read back, and say which in the same commit.

## The bound

`materialUvHeadReadback` is the number that moves. Today it is 0 of 2 and has
never been anything else.
