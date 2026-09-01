# LEDGER Vision and Pillars v2 (2026-08-31)

## The goal
Build a photoreal, immersive crime sim and social RPG in Meridian, a fictional late-80s/early-90s British port town, that within its deliberately small footprint feels as dense, alive and high-quality as GTA 6 and KCD2, and does the one thing neither can: people who genuinely perceive, permanently remember, gossip through their days, and hold real spoken conversations with the player. Built almost entirely by Claude Code operating as an autonomous studio; Jafar directs (non-technical decisions, feel checks, one-click generation runs, evenings and weekends, small budget, no deadline). Underneath the game sit two quieter goals: prove the method (that one person directing AI agents can produce this class of game at all) and learn game development by doing it. Success is the game clearing the bar below, not shipping or sales.

## The Meridian Test (the goal's instrument, approved 2026-08-31)
The goal is met when all four hold:
1. A person who loves GTA or KCD2 plays 30 minutes and does not bounce off the visuals.
2. Within those 30 minutes the world visibly knows them at least once: recognized, gossiped about, or confronted with something they did earlier.
3. They describe the town as alive without being prompted.
4. Jafar, on a free evening, chooses playing LEDGER over replaying KCD2.
This gate sits at the end of roadmap-v2.md. Every phase gate exists to move these four numbers.

## Pillars
1. The town knows. Perception (seven slots), five-rung identification, permanent memory, gossip via schedule intersections. Nothing is ever wiped; remediation is behavioral (leave, change appearance, rebuild relationships), never a reset. This is the moat; GTA 6 ships a shallow global version and Rockstar publicly forgoes generative AI, so the ground is uncontested.
2. Real conversation. Live LLM dialogue with per-character memory, spoken via the local voice pipeline, within measured latency budgets. Conversation always matters: outputs are classifications and closed-set choices that deterministic Core executes.
3. Consequence is deterministic. Every outcome the player feels is decided in C#-style deterministic Core (whatever the engine). LLMs classify, never adjudicate. Claims need instruments.
4. Authored breadth. Content is made the way a studio makes it: per piece, with a spec, an author agent and a verifier. No procedural filler without an authoring pass and verification. The planning unit is verified pieces per week.
5. Photoreal grim Britain. Wet, overcast, sodium-lit, worn. The most forgiving photorealism there is, and the correct dressing for the noir. Density and wear carry frames: decals, clutter, signage, depth, light.
6. Small and dense, built to expand. One town done to the bar, region later. Expansion is adding data, never restructuring. Expand aggressively along axes Claude can verify (words, people, systems); conservatively along axes only Jafar can verify (look, feel).

## Worse at, and at peace with it (v2)
Animation parity with mocap studios. Physics spectacle (Euphoria-class). Landmass. AAA hand-feel on launch day. These are named so nobody quietly reopens them without a decision record.
