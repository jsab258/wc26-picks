# Streets and cars — M12 spec (player decision, 2026-07-26)

> **STATUS — SPEC.** The design for M12 streets and cars. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

> *"city can't feel real or immersive without cars and real streets. spec it
> and add it to the roadmap. needs to be built by 8 am. melee later."*

This supersedes the agency model's "vehicles: 40, late, non-differentiating"
line. The player's argument is about IMMERSION rather than about driving as
a mechanic, and that reframes it: the point is not that the player wants a
driving game, it is that a city with no traffic and one crossroads does not
read as a city, and every social system in this project is standing on the
claim that this is a real place.

## What is actually wrong today

The district's buildings already exist — `BuildDistrict` puts geometry at all
fifteen planned places. What does not exist is **any street connecting them**.
There are exactly two roads, the founding cross at x=0 and z=0, and the other
twenty-two locations sit in open ground. The city has buildings and no
streets, which is why it reads as a diorama.

## The design

### 1. A real street grid, not two axes

Five north–south avenues and five east–west, on an irregular spacing so it
reads as a place that grew rather than a chessboard:

    N–S at x = -30, -16, 0, 16, 30
    E–W at z = -18,  -8, 0, 10, 18

Twenty-five junctions, sixteen city blocks. The founding cross is preserved
exactly — x=0 and z=0 are two of the ten, so nothing already built moves.

Each of the 24 map places connects to its nearest avenue by a short **lane**.
Places stop being points in a field and become addresses on a street.

### 2. Three road classes, because a city has more than one kind of street

| class | width | what it is |
|---|---|---|
| avenue | 8 m | the grid. Traffic, both directions. |
| street | 6 m | the founding cross. |
| lane | 4 m | the connector to a doorway. Nobody drives fast here. |

### 3. The network is DATA, in Core, engine-free

`StreetMap` is nodes and edges with a router over them. That matters for
three reasons: the NPC walkers stop steering by the "nearest point on the
cross" hack and start following actual streets; the cars have something to
drive along that is not a physics guess; and CoreTests can prove the city is
connected without opening Unity.

The hard property, and the one that is tested: **every place must be
reachable from every other place**. A city with an unreachable address is
worse than a city with no streets, because the player will walk at it.

### 4. Cars

Arcade, not simulation. This is a game about people; the car is how the city
sounds and moves, not a driving model to master.

- **Traffic** drives the avenues on the network, turning at junctions,
  stopping for the player. It exists to be heard and seen. This is the part
  that does the immersion work and it lands first.
- **A driveable car**: get in, drive, get out. Accelerate, brake, steer.
  Fixed camera behind. No gears, no damage model, no handbrake physics.
- **Consequence, since this is that kind of game**: a car is a thing
  witnesses describe. Driving to a job is faster and more memorable than
  walking to one — "somebody came in a car" is a better rumor than
  "somebody was about". The coat does not hide a vehicle.

### 5. What is explicitly NOT in scope

Pedestrian collision and running people over. Car ownership, purchase,
customisation, or storage. Chases and police pursuit. Damage, fuel, parking
mechanics. Every one of those is a different game's Tuesday, and the player
asked for a city that feels real, not for a driving game.

## Order of build, and what gets cut first

Sequenced so the game is playable at every commit and the last thing to
arrive is the least important:

1. **`StreetMap` in Core** — the grid, the lanes, the router, connectivity
   tests. Nothing visible yet.
2. **Road geometry** — the avenues, lanes, pavements and junctions get built.
   *This alone fixes the diorama problem, and if everything after it is cut,
   the city still reads as a city.*
3. **Walkers use the network** — the crowd stops cutting across open ground.
4. **Traffic** — cars moving on the grid. The immersion payload.
5. **The driveable car** — get in, drive, get out.
6. **Witnesses describe the car.**

Cut from the bottom up if the runway runs out. Steps 1–2 are the ones that
answer the player's actual complaint.

## Melee

Deferred by the player in the same message. The consequence layer (injuries,
crew trauma, feuds) is unaffected and stays on the near roadmap; playable
brawling waits for the art pass, since positioning-and-timing combat cannot
be judged on capsules.
