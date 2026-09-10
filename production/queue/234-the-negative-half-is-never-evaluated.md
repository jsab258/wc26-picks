line: art (the visual bar) and instruments, jointly
spec: Every spec in the image lane says on its own face whether its negative is
  live, so no reader can take a veto for a control that was never evaluated.
acceptance: negativeActive printed per item on every validate run, and each
  shipped spec carrying a line saying what its negative is FOR given that value
max_sessions: 1
status: READY 2026-09-10 07:40Z. Found by a builder, confirmed against the
  tool's own source note, and it refutes a sentence the resident wrote into
  NOW.md the same morning.

  THE FACT. A negative prompt at cfg 1.0 does NOTHING.
  tools/imagegen/imagegen.py's negative_state carries the reasoning, read out of
  stable-diffusion.cpp's resolve_guidance on 25 August: use_uncond is set only
  when img_cfg differs from txt_cfg, and a model with no image conditioning has
  img_cfg forced to 1.0. THIS LANE RUNS EVERY ITEM AT cfg 1.0. Every item in the
  Fairview and Copper Row specs reports negativeActive=False, and so does every
  Hook item that has ever been drawn.

  SO THE NEGATIVE HALF OF EVERY SPEC THIS LANE HAS SHIPPED IS DOCUMENTATION.
  It is wired, passed, logged and never once evaluated, which the tool's own
  docstring names as the silent-instrument failure exactly.

  WHAT IT REFUTES. The resident read the Hook sheet's leisure drift and wrote
  that the negative had done its job because there is no yacht in the picture,
  and that what it could not do was summon the trawlers. THE FIRST HALF IS
  FALSE. No yacht is the positive prompt's doing or it is chance. The studio
  had a veto it believed in and did not have.

  WHAT IT DOES NOT CHANGE, AND STRENGTHENS. Jafar ruled 2026-09-10 that a
  negative vetoes but cannot summon, and that anything that must appear is named
  in the positive half. At cfg 1.0 a negative cannot even veto, so BOTH what
  must appear and what must not are the positive half's problem. The rule holds
  and its reason is stronger than the one it was given.

  DO NOT FIX THIS BY RAISING cfg. The model is distilled for 1.0, cfg above 1
  doubles the cost by arithmetic, and whether this model tolerates it is
  unmeasured. That is a probe with a printed series, not a setting to change on
  the strength of this item.
