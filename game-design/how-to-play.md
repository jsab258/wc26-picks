# LEDGER — How to Play (prototype build)

You inherited your uncle Marek's bar on Hook Street — and the half-dead
criminal arrangement that came with it. Everyone on the street is simulated:
they keep schedules, remember everything you say, and talk to each other.
Your two lives stay apart only as long as the street can't compare notes.

## Controls

| Key | Does |
|---|---|
| WASD / Shift | move / run |
| E | talk to whoever you're near (type anything; chips above the box are optional openers) |

**You can say what you want to do, not just click it.** Every button in a
conversation can also be typed in plain words — "how much to forget you heard
that", "spring was a long time ago and you know what you owe", "I'll take the
pawnshop off him with what I know". If the words match something you could
actually do right now, the game does it. If they're something the buttons never
anticipated but the world can still price — buying the room a round, putting a
word in the wrong ear — it gets weighed against your money, your standing, your
crew, the hour, and how much of the street is watching, and it either lands or
you're told plainly why it didn't. Anything else is just talking, which is most
of what you'll say and always the safe default.

| F | get in / out of your car (it's parked outside the bar) |
| L | **the ledger** — what you believe the street knows, what you hold, THE STREET (open city) |
| C | the runner's coat — harder to name at night, harder to explain in daylight |
| F1 | debug: the brain of whoever you're near (memory file, suspicion, beliefs) |
| F2 | API key entry (conversations are live LLM; get one at console.anthropic.com) |
| F5 | save · autosaves every morning |
| Esc | close panels |

## The streets

The district is a real grid now — ten named streets, sixteen blocks, traffic
on them. Cars, vans, lorries, a bus that runs a circuit and stops at its
stops, cabs that idle at the ferry stop and the cab rank, and bicycles that
use the lanes. Lights at the four big crossings, stop signs everywhere else,
and no-entry where a lane leaves a junction — the lanes go to doorways, not
through.

**Your car is parked outside the bar. F to get in, WASD to drive, F to get
out.** It is arcade: no gears, no damage, no fuel. Traffic brakes for you,
and for anybody else in the road — **you cannot run people over.** That is a
deliberate decision and it's in the pending queue if you want it changed.

**A car is a thing witnesses describe.** Driving to a night drop is faster
and more memorable than walking to one: whoever sees you will mention the
car, and they will mention it *whether or not you were wearing the coat*. The
coat buys doubt about your face. It buys none at all about the vehicle
standing in the street.

## The week (days 1–7)

By day the bar earns **clean** money, taxed by how hot the street's talk
about you runs. At 22:00 the outfit posts a drop — find the glow before
02:00 for **dirty** pay. Witnesses seed rumors; rumors travel person to
person and cool only if nobody feeds them. The till washes $120/day of
dirty money — hoard more and Lena starts counting.

Talk your way through it: pay people off, lean on them, plant doubt, learn
their secrets (loyalty opens mouths), collect or forgive Marek's debts,
honor invitations — the street protects people it likes. Two mornings in a
row of a hostile street ends you; so does exhausting the outfit's patience.

Day 7, over the true books, Lena asks what you intend. Answer — then
**press SPACE. The city opens.**

## The open city (day 8 on)

Nobody counts days anymore. Nothing ends — things scar. Get exposed and
you do three days inside: they keep the cash you couldn't explain, and the
street stops guessing and starts *knowing*. Then you start again from there.

**The honest morning.** Meridian Parcel's board goes up by the docks each
morning until noon. Take the satchel, walk the route, deliver before
evening: $40 clean, and something money can't buy — a day in company
colors reads honest, and the whole day circle relaxes a little about you.
One round a day. The morning you spend on parcels is a morning you don't
spend on the other ledger; that's the point.

The empire verbs appear in conversation:
- **Businesses** — buy a front clean (full price, seller stays friendly),
  buy their debt and turn the key (cheaper; they fold or tell the street),
  or spend a secret you hold. Fronts pay daily and wash more money.
- **Crew** — sort what someone needs and they join by choice; use what you
  know and they join because they must. Both remember which.
- **Rackets** — put crew on a round (collection, protection; the fencing
  line needs the pawnshop). Their nerve sets who gets seen. Set each
  person's **cut** — generous buys the loyalty that survives poaching;
  skimming is free money on a fuse they can hear.
- **The Dockside arm** watches everything its people can see. First a slow
  beer at your bar, then the street's rent, then your least-loyal crew get
  offers. What they take was always a function of what you built and who
  you underpaid.
- **Two more organizations** are watching different things. The machine
  reads the deed registry — every shop you take wakes it, and it answers
  with inspectors and letters that cost clean money. The New crew watches
  how loud your street is, and answers with noise you didn't make but will
  be blamed for.
- **Whose people are whose.** Josip and Ferko answer to the Dockside;
  Tibor's customs stamp belongs to the machine; the New crew counts Ruta
  as theirs. Recruiting any of them is poaching, and it is noticed.

Press L. Two books. Keep them both, or choose which one survives.
