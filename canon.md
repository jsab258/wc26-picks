# canon.md: world facts that outrank everything

STATUS: APPROVED 2026-08-31 by Jafar, with rulings recorded in
ledger-v2/respec/decision-register/D8 and D9. This outranks every document and
agent; violating it is a gate failure.

## Game
- LEDGER: open-town crime sim and social RPG. Single player, PC first.
- Town: Meridian, a fictional British port town. One map, seven districts:
  the Hook (old port, the player's pub), Copper Row (market quarter), the Exchange
  (offices, lawyers), the Parade (nightlife), Fairview (residential hills), Ironside
  (industrial), Gullwing (faded resort waterfront).
- Streets minted: Quay Street, Weighhouse Lane, Tannery Row.
- Street districts, minted 2026-09-02 by the director on delegated authority,
  struck on sight if Jafar disagrees: Quay Street is in the Hook, Weighhouse
  Lane in Copper Row, Tannery Row in Ironside.
- THE BUILT STREET IS QUAY STREET, IN THE HOOK, and Mickey's stands on it.
  Ruled by Jafar 2026-09-08, option C, after a director briefly moved Mickey's
  to the Parade and canon contradicted itself for one commit. The 593 pieces
  keep their `east_parade_*` identifiers: those are ASSET NAMES minted before
  the street had a district and they carry no claim about where it is. Renaming
  them would break the bill of materials, the golden rows and every verdict key
  that has ever named a piece, for nothing. Canon and the atlas agree: one
  street, Quay Street, the Hook, the player's pub on it.
- Graffiti tags, minted 2026-09-02 (Jafar delegated the naming to the studio
  on 2 September): TANNER (Ironside), SNIDE (Copper Row), GULL (Gullwing),
  QUAY FIRM (the Hook), PARADE RATS (the Parade). Wall names, not any of the
  three rival organisations; reasoning in
  game-design/canon-proposal-graffiti-crews.md.

## Era
- Late 1980s to early 1990s. Working window 1988 to 1992.
- Late-analog: landlines, phone boxes, answering machines, pagers for dealers and
  fixers, cash and paper. CCTV rare: the bank, and a second site that is
  Jafar's to name (the off-licence was struck 2026-09-10 under D18 and
  nothing was minted in its place), tape recycled weekly. One camcorder in
  town, a rare witness type. No internet, no mobiles in ordinary pockets.
- Any 1950s or 1970s framing is wrong, corrected on sight. Both drifts have happened.

## Tone
- Grounded noir. Comedy: dry British wit plus seaside-postcard smut, sparingly, so
  the noir holds. Tabloid and Viz-adjacent flavour. Never GTA-style American satire.
- Visual target: photoreal, wet, overcast, grimy Britain. Weather and grime are the
  strategy, not stylization. The bar is the Meridian Test (D8, D9); GTA V PS3 is
  retired as a reference bar.

## Premise and cast (baseline pending OPEN 2)
- Player: Tom Novak, arriving with one suitcase and a letter. His uncle Mickey
  has died and left him the pub, Mickey's, in the Hook, plus a half-dead criminal
  outfit and a book of uncollectable debts.
- Inherited loyalists: Rocco (old muscle), Lena (older bookkeeper).
- Three rival organisations: the old-money machine (corruption and lawyers, head
  Aldous Vane), the dockside syndicate (muscle and smuggling, head Sera Kest, called
  the Widow), the new crew (flashy and reckless, head Danny Ro).
- Detective: Mara Ellis. Day-life ring: Sam, Ada, June (Mickey's estranged daughter),
  Father Emil, Noor (journalist love interest), Elias (teacher love interest), the
  Fixer (broker between all three rivals).
- What the town calls you reads out your standing: the new owner, then Novak, then
  Tom, then Toma. The gate is knowing, not liking.

## The content rule (D18, permanent)

APPROVED 2026-09-10 by Jafar, recorded at
ledger-v2/respec/decision-register/D18-content-rule.md, which extends D17.
This is a RULE, not a note: it governs what may exist in this work at all, in
image and in speech, and it voids decisions already taken.

- Alcohol and gambling are out ENTIRELY: never shown, served, drunk or spoken
  of, in image or speech. PUBS MAY EXIST AS PLACES. What the pub is for
  without drink is a design task, not a subtraction.
- Tobacco stays.
- Violence stays, including blood and light gore. No torture and no cruelty
  as spectacle.
- Killing is possible, rare, permanent, and the town remembers it forever.
- Full period swearing is allowed. NO SLURS OF ANY KIND.
- Drugs exist as an off-screen economy other people run: never shown, never
  used, never a player verb.
- No prostitution and no sexual content. Seaside-postcard innuendo under Tone
  is not sexual content and stays.
- NO CHILDREN ANYWHERE: none rendered, none in the crowd, none in dialogue or
  image prompts. THE SCHOOL STANDS CLOSED for the game's window; the building
  is there and nobody is in it.
- Racism and sectarianism may exist as FACTS ABOUT CHARACTERS, never voiced
  as slurs, never rewarded.
- Religion is present as part of life, never mocked, never a mechanic.
- Police are corruptible as individuals, never as a thesis.

Enforced at five sites: this rule; every image spec's content clause; the
word-list gate `tools/content-gate.py` over dialogue and spoken lines; crowd
generation, which is the one site that is code; and the brand bible. Half of
this rule permits a FACT and forbids the DEPICTION or the REWARD, and no word
list can read intent: `python3 tools/content-gate.py --enforceable` prints
which clauses the gate checks and which it does not claim to.

## The moat (unchangeable)
- Every act exposes seven perceivable slots.
- Five-rung identification ladder; the top rung, recognition, is gated by
  relationship, never by distance and light alone.
- Permanent per-NPC memory. Nothing is ever wiped; remediation is behavioral.
- Gossip spreads through schedule intersections.
- Live LLM conversations with per-character memory and local voice.
- Deterministic Core decides every outcome the player feels. LLMs classify, never
  adjudicate.

## Brands and law
- Every brand, band, club, product, weapon and vehicle is fictional. No real people,
  voices, logos, lyrics, car models. The license allowlist is law.
- Minted: Mickey's (the pub), the Tivoli (cinema), Meridian Harbour Board, Meridian
  Ferry. The brand bible still owes: the football club, the local paper, the pirate
  radio station, the regional TV channel, the telephone operator (the kiosk's
  mark and lettering) and the postal cypher (the pillar box); the last two were
  found owed by the vignette bill of materials on 2026-09-02.

## OPEN
1. Engine. Unity holds the codebase; the UE5 probe is authorized (D1). No document
   pre-commits before the probe lands.
2. Narrative survival. Whether Tom Novak, Acts I to III and the empire roster survive
   as baseline is decided in Phase 1 planning, along with the cast-sketch-versus-
   built-cards mismatch (Sam and Ada, written at one-street scale).
