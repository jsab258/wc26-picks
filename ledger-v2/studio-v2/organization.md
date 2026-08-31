# Organization: departments, roles, models

Structure: three tiers, adapted from the donchitos taxonomy, run under our constitution. Roles are agent definition files with standing constraints baked in (never retyped in briefs). Handoffs are files in known locations, publish-subscribe style; agents never chat with each other directly (MetaGPT lesson: shared artifact pool beats direct calls).

| Department | Roles (tier) | Model class |
|---|---|---|
| Direction | Director agent (1), plus Jafar | Top |
| Production | Producer/roadmap keeper (1), watchdogs (3) | Top for audits, cheap for watchdogs |
| Engineering | Core, engine, tools, build/CI (2 to 3) | Mid; top for architecture |
| Design | Systems, economy, level (2) | Mid |
| Narrative | Lead writer (2), dialogue writers (3), brand bible keeper (3) | Mid; cheap for bulk barks |
| World | Environment, props, set dressing, interiors (3) | Mid |
| Characters | Casting (bios), rigs, voices, faces (3) | Mid |
| Audio | Radio, ambience, foley sourcing (3) | Mid; cheap for batch runs |
| Verification | Instrument runner, judges, license gate, canon gate, playtest bots (2 to 3) | Cheap first pass, mid for judges, top for audits |
| Tools/Research | Pipeline builder, external tool evaluation (3) | Mid |

Model routing law: top models only for direction, architecture, audits and hard debugging. Authoring runs mid. Mechanical transforms, first-pass verification and watchdogs run cheap. Route up only on failure, and record the escalation in the token ledger.

Escalation path: specialist to lead to director to Jafar's decision queue. Only genuinely non-technical calls reach Jafar.
