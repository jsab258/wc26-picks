# The city is British — decision and consequences, 2026-07-31

> **STATUS: SPEC.** The design for the British setting decision and its consequences. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

Jafar chose **option 1**: change the accent direction rather than buy voices or
accept a half-cast game. He asked for the consequences beyond voices.

They are larger than accents and mostly *cheaper than expected*, for one
reason that surprised me when I went looking.

---

## The finding: the writing was already British

I expected to be costing a conversion. Counting whole words across
`game-design/` and `Assets/Scripts/`:

| already British | | American outliers | |
|---|---|---|---|
| `flat` | 82 | `bar` | 395 |
| `colour` | 67 | `Downtown` | 24 |
| `shop` | 41 | `store` | 21 |
| `pavement` | 29 | `sidewalk` | 11 |
| `constable` | 20 | `apartment` | 10 |
| `neighbourhood` | 16 | `cop`/`cops` | 6 |
| `magistrate` | 5 | `$` | economy-wide |
| `lorry` | 6 | `The Strip` | a district |

And the street names are not ambiguous at all:

> Saltmarket · Quay Street · The Esplanade · Weighhouse Lane · Tannery Row ·
> The Sidings · Winter Quay · Promenade · Pier Approach · Slipway Road ·
> Customs Way · Smelt Yard · Copper Row · Gaslight Walk · The Cut ·
> Fairview Crescent · Anchor Walk

*Saltmarket* is a real Glasgow street. *The Cut* is canal vernacular.
*Crescent*, *Terrace*, *Quay*, *Esplanade*, *Sidings* are British street
forms and nothing else. Even the code says `kerb`.

**This city has been a British port town all along.** The American accent
direction was the outlier, not the writing — and holding it was quietly
forcing the casting to fight both the corpus and the fiction. Option 1 does
not move the game; it finishes a move the game already made.

---

## The consequence that costs something: the five picks

The five voices cast so far were selected with `accent="american"` as a hard
filter, and that filter is exact — only VCTK speakers labelled `American`
could satisfy it. **The reason only five of nineteen filled is that VCTK has
very few Americans**, and those few are exactly who got cast.

So Lena, Sam, Sera Kest and both crowd voices are **the Americans in a British
corpus**, and under this decision they are now the wrong accent.

Two honest ways to handle it:

- **Re-cast them.** The listening was not wasted — it proved the pipeline end
  to end and calibrated what usable quality sounds like — but the picks
  themselves go back in the pot.
- **Keep one or two deliberately.** An American on the dock front of a British
  port is entirely plausible, and "texture at the edges" was always the
  intent. But making the bookkeeper *and* the rival head American in a British
  city is a choice that has to be argued for, not a default.

**Recommendation: re-cast all five, and hold the American slot in reserve** for
a character who benefits from being visibly not-from-here.

---

## What changes, in rough order of cost

**1. Currency: `$` → `£`.** Economy, Purses, every UI format string, and the
balance documents. Mechanically wide but shallow. One design check comes with
it: the amounts have to read as plausible late-analog sterling, not as dollar
figures with a different glyph in front.

**2. "The bar" → "the pub". 395 references, and it is an upgrade rather than a
rename.** A pub has a **landlord**, regulars, a snug, last orders, a lock-in.
That is precisely the gossip engine this game already runs on, and it gives
the inheritance a better word: *the new owner* becomes **the new landlord**,
which collides usefully with the debt and rent themes the game is about.
Risk: 395 mechanical substitutions will wreck prose. This needs a careful
pass, not `sed`.

**3. The audit becomes Customs and Excise.** The single best consequence.
A game called LEDGER, about inherited books and a business whose takings do
not reconcile, set in late-analog Britain — the antagonist is the **VAT man**.
An excise officer auditing a pub's takings is a sharper, more specific threat
than a generic inspector, and it is period-perfect.

**4. Two district renames.** `Downtown` and `The Strip` are the only two
American names on an otherwise British map. Downtown → *the Centre* or *the
Exchange*; The Strip → *the Parade* or *the Front*.

**5. The telephone work from last night pays off immediately.**
- **50 Hz mains** — this resolves the open 50/60 question outright.
- **The British double-ring**, *brr-brr … brr-brr*. Instantly recognisable,
  unmistakably not-American, and free: it is a cadence, not an asset.
- **999, not 911.**

**6. Vocabulary consistency pass.** `sidewalk`/`pavement`, `store`/`shop`,
`apartment`/`flat` are currently *mixed*, which reads as carelessness whatever
country the game is set in. This decision makes the fix unambiguous instead of
a matter of taste.

**7. Driving side.** `TrafficHost` shows no lane-handedness logic — cars appear
to follow edge centrelines — so this may cost nothing. Flagged as *needs a
look*, not as free.

---

## What gets better

**The cast names now make more sense, not less.** Novak, Zlata, Halvard,
Vesna, Emil, Ossei — a mix of Anglo and Central European and West African
names reads as dockside immigration in a British port. In a generic American
city it was just a spread; here it is a history.

**Father Emil stays Irish** and is better for it: Irish clergy in a British
port town is not a flourish, it is the ordinary case.

**VCTK stops being the wrong tool.** English and Scottish are exactly what the
corpus is rich in. The 5-of-19 yield was the accent brief fighting the corpus;
with the brief aligned, far more of the cast should fill from the same
thirty-minute run.

**Positioning.** British provincial port noir is genuinely underserved.
Shadows of Doubt is stylised-anywhere, This Is the Police is American. A wet
British dock town in the late analog era is a distinctive place to stand, and
distinctiveness is the whole strategy in `design-doc.md` — *the game that does
one thing no AAA studio currently does*.

---

## The one real risk

**Costume instead of character.** The failure mode is vernacular laid on
thick — *cor blimey*, *guv*, a Dick Van Dyke accent in prose. The writing is
currently good and restrained; it needs *consistency*, not costume. The brief
for the dialogue pass should be: regional, dry, and specific. Nobody in this
city should sound like they are performing being British at the player.

---

## Accent map, revised

English base, with texture at the edges — the same structure as before, moved
across an ocean.

| character | was | now |
|---|---|---|
| Lena | american | **english** |
| Rocco | american | **english** |
| Mara Ellis | american | **english** |
| Tobias Reese | american | **english** |
| Sera Kest | american | **english** |
| Sam | american | **scottish** |
| Ada | american | **english** |
| Vesna | english | **northernirish** — keep her the outsider |
| Marla | american | **english** |
| Joey | american | **scottish** |
| Rita | american | **scottish** |
| Hal | american | **english** |
| Father Emil | irish | **irish** — unchanged, and now obvious |
| crowd (6) | american | **english ×4, scottish ×2** |

One American slot is held in reserve rather than deleted, for a character who
earns being visibly not from here.

**All five principals share the base accent, and the selftest enforces it.**
My first draft gave Rocco and Sera Kest Scottish voices because the timbre
suited them, and the check caught it: if the principals are split, the base
is not a base and everything is texture. Scots moved outward to Sam, Joey and
Rita, where being from elsewhere is characterisation rather than noise.

---

## Addendum: the audit becomes Customs and Excise (done)

The same lesson as `bar`/`pub`, twice over.

**"Revenue" was never an Americanism.** I went in expecting to replace it and
found the opposite: in British excise law a licensed publican *is* a **revenue
trader** — it is the statutory term. So Lena's "revenue letter", the "revenue
office", "a revenue man": all correct trade vocabulary for a landlord whose
licence uses the word. Nothing was replaced. What changed is that the game now
**names the instrument**, which makes the vocabulary legible instead of vague:

> Under **section 112 of the Customs and Excise Management Act**, the licensed
> premises known as the Hook Street pub is required to produce its books of
> account, **and its records of duty paid on stock received**, for inspection.

Section 112 is real and is titled *Power of entry upon premises, etc. of
revenue traders*. It is the inspection power. Reese names it in his hard facts,
which is exactly his characterisation — he names the regulation before the
request.

**The duty clause is the mechanical win.** `LedgerStrain` already capped
plausible laundering at about a third of takings, and that third was a tuned
number with no reason behind it. Excise supplies the reason: an officer reads
takings against duty paid on stock received. *Drink you never bought cannot
have been drunk.* The ceiling stops being a balance constant and becomes a
fact about the world the player can reason about.

**And the statute handed over a mechanic I did not go looking for.** Section
112(2): an officer may not exercise the power of entry **by night unless he is
accompanied by a constable**. In a game about a pub, at night, where constables
are already simulated. It explains why Reese sits at a table in daylight and
never once turns up after hours — and it means the player's night is legally
his own unless somebody brings a constable into it. New hard fact:

> — I do not come here after dark unless a constable comes with me. That is
> not a courtesy to you. It is the section.

Not yet wired as a rule; recorded here as the obvious next Act III beat.

**`Board of Excise` → `Board of Customs and Excise`**, and the establishment
sense of `bar` cleared out of Act III (the pub explains its money, the pub is
a pub, you have a pub) while the counter sense stayed put — he is still at the
bar at ten past nine, at a table, and that is still the right word.
