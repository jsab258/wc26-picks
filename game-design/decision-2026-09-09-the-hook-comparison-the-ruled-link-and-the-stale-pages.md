# Ruling: the Hook comparison runs in the lane's own dialect, one link is ruled by whole URL, and the pages are stale, not absent

STATUS: LOG, 2026-09-09. NOT CURRENT once the amendments in sections 1.6, 2.5
and 3.4 land; from then the files are the reading copies and this is the
record of why. Director ruling on two guard changes blocking Jafar's items 4(a)
and 4(c) of this morning, spawn `2026-09-09T08:04:25Z` (line 431 of
`.claude/agent-log.tsv`), read-only, no shell. The batch review of the seven
builders comes to this same spawn later and is not in this record.

THE THREE DECISIONS, SO THE RESIDENT CAN ACT BEFORE READING THE WHY:

1. HOOK. The exclusion guard in `tools/imagegen/imagegen.py` is NOT widened,
   not by a per-item flag and not by a name list. The comparison IS made in
   house, from the CREATION prompt (`concept-prompts.json` key `hook`), with
   every exclusion clause translated into the lane's own dialect exactly as the
   library already did for "no people, no cars", the translation recorded
   clause by clause beside the image, and the item living in its OWN spec file
   under a new `--spec` flag so the library is untouched. Running the edit
   prompt is refused. A verbatim run is refused because it is impossible in
   this lane and would rig the comparison against us.
2. LINK. Jafar's instruction of this morning lifts the band of 2026-09-06 for
   THIS message and repeals nothing. Mechanism: a `RULED_LINKS` tuple in
   `tools/producer-check.py`, one entry, matched by WHOLE URL inside
   `link_ok()`, each entry naming the ruling record that admits it, the tuple's
   length asserted by the selftest. Sending no link is refused; sending a glance
   link over research the glance does not carry is refused.
3. PAGES. The resident's sentence "the pages have never been served" is FALSE
   on this tree's own evidence and is corrected here. They were served on
   2026-09-07. They are STALE: eight publish runs this morning died on our own
   gate before the deploy step. A stale page and a missing page are different
   faults with different fixes, and the register cannot see either.

## 0. What was read, what was not run

NOTHING WAS RUN. Every measurement quoted below was taken by the resident or a
builder and is marked as such; what I did is read the code the claims are
about. Read at the line this session: `tools/imagegen/imagegen.py` 555 to 801
(`build_prompt`, `build_negative`, `negative_state`, `EXCLUSION_WORDS`,
`scan_exclusions`, `validate_spec`), 2016 to 2050 (the manifest record), 2929,
4289 to 4386 and 4482 and 4599 (the three sites that hardcode `prompts.json`);
`tools/imagegen/prompts.json` 120 to 249 and 481 to 507; `tools/producer-check.py`
1 to 240, 400 to 489, 585 to 724, 1197 to 1206 and 2066 to 2102;
`tools/runner/outbox.py` 80 to 119 and 670 to 749; `tools/runner/telegram-bot.py`
255 to 294; `tools/publish-glance.py` 78 to 132; `tools/gallery.py` 1 to 60 and
950 to 959; `.github/workflows/publish-glance.yml` 120 to 279;
`.github/workflows/ledger-imagegen.yml` 1 to 80; `.claude/agents/producer.md`;
`production/NOW.md` 1 to 110 and 240 to 299; `production/decision-queue.md` 1
to 80 and 245 to 307; `production/queue/139`; `production/findings.txt` 1912 to
1939; `production/map-notified.json`; the held digest; the 2026-09-06 ruling on
the link band (the precedent for both mechanisms here); `tools/docs-check.py`
100 to 199.

NOT READABLE FROM THIS SEAT: `production/art/atlas-01/data/*.json`,
`concepts/hook.png` and `PROVENANCE.md` live on `origin/art/atlas-01`, and the
working tree holds only `production/art/atlas-01/REVIEW.md`. Their contents
are taken from the builder's reading as recorded in `findings.txt` 1916 to 1939:
two keys, both edit instructions, and the creation prompt at 1599 characters
refused with `['no', 'not']`, one problem of one item examined. Section 1.6
has the builder print all three again before anything is generated.

PREMISE CHECK, CLAUDE.md section 0: a Hook district concept sheet of a
late-analog British port town, and period research on pubs, housing, dockers
and buses in the 1988 to 1992 window. Nothing here drifts. Nothing is
purchased: the lane is Jafar's PC, the model is already on the allowlist.

## 1. The Hook comparison

### 1.1 The instruction as given cannot be obeyed, and obeying it would repeat the fault he named

Confirmed from the builder's reading and from the code: `concept-final-prompts.json`
holds edit instructions ("Make a single spatial correction to the lower street
panel of this Hook district concept board"), and the lane has no image input.
`negative_state` (imagegen.py 664 to 693) quotes the shipped binary: a model
with no image conditioning has `img_cfg` forced to 1.0. There is nothing to
edit. A run from that file would answer "what does a text-to-image model draw
when handed a correction note", which is a different question from his, and
his complaint in the same sentence was that the previous run answered a
different question. REFUSED.

### 1.2 A verbatim run of the creation prompt is impossible here, guard or no guard

The resident framed the choice as "widen the guard for a verbatim prompt, or
tell him it cannot be done". Both halves rest on a premise the code refutes:
THIS LANE CANNOT RUN A VERBATIM STRING AT ALL. `build_prompt` (560 to 624)
refuses to return a prompt that does not carry the content-rules clause
(595 to 597, "no trade marks") and refuses a prefix that does not contain
`style.framing_required` (599 to 621), and it composes prefix, item, suffix
and rules clause into one string (622 to 624). So the composed prompt for any
item is at least three additions to whatever the item says. There is no
verbatim path to bypass a guard for.

And the deeper fault a bypass would commit: at cfg 1.0, which is the lane's
measured setting for this distilled model (prompts.json 198 to 209, the probe
pair read 26 Aug at 503 to 507), the negative channel is INERT. A prompt
carrying "no X" in the positive puts X into the only channel the model reads.
That is not a risk of the 41-of-45 fault, it is the fault, measured: `no
signage legible` produced a sign board reading WEORED S HONJ (imagegen.py 700
to 701). A verbatim run would therefore draw the things Codex's prompt
excludes, Jafar would see a worse board than our lane can make, and he would
decide a real question off a rigged picture. REFUSED, and the guard stays as
written. No per-item opt-in, no name list, no flag. The shape the resident
offered ("a hole used once, visible in the item's own JSON") is a smaller hole
than a logic hole; it is still a hole in an instrument whose incident cost a
night of GPU time, and it is not needed.

### 1.3 The third option is not a corruption of the brief; it is the brief in this lane's dialect

The resident asked me to close "edit the prompt to remove the negative
phrasing" as changing the brief. I rule the opposite, narrowly. The BRIEF is
what the board should show. The PROMPT STRING is one lane's encoding of it,
written for a model that handles exclusions. Codex's prompt in Codex's lane and
the same brief in ours, each spoken the way that lane works, is the comparison
that answers "can concept images be made in house". The library has the exact
precedent (prompts.json 122 to 129): `no people, no cars` became `deserted,
empty street`, "the same intent said as a thing to draw rather than a thing to
omit". That is translation, not authorship, and it is what the incident taught.

What makes it honest rather than a rewrite is that it is bounded and recorded:
only the clauses the guard names are touched; each is rewritten as the positive
equivalent of the same intent, or moved to the negatives block where the
manifest will record it as inert at cfg 1.0; every pair is listed beside the
image; the untouched remainder is byte-identical and the report proves it.
APPROVED as the mechanism.

### 1.4 The comparison must be fair in the lane's terms, and cannot pollute the library

Three facts from the code fix the shape.

(a) THE LANE'S DEFAULT PREFIX ASKS FOR A TEXTURE SHEET. `style.prefix` is "flat
orthographic texture sheet, square-on to the surface ... the artwork filling
the frame edge to edge" (prompts.json 173) and the default suffix ends "one
single flat surface" (174). Composed round a concept board that is a request
for a texture sample of a picture. The `interior` kind (180 to 183) is the
precedent for a kind whose prefix keeps the required substring and says
something else. A `concept` kind is needed, with a prefix that is the shortest
phrase satisfying the guard and describing nothing the original does not, and
an EXPLICIT empty suffix, because `resolve_style` (555 to 557) falls back to
the default suffix when a kind omits the key.

(b) `prompts.json` IS HARDCODED AT THREE SITES (2929, 4482, 4599) and there is
no `--spec` flag (4291 to 4385). An item added to the library is generated by
every future night's `all` run, its PNG lands under the decals directory, and
the resume rule (prompts.json 125 to 129) regenerates anything whose recipe
changed. A one-off comparison board does not belong in the shipped library or
its output directory. The lane gains `--spec PATH`, defaulting to the library,
so a one-off spec runs through every guard unchanged and touches nothing.

(c) ONE DRAW IS A LOTTERY, AND CHOOSING AMONG DRAWS IS TASTE. Constitution 9:
no agent self-certifies quality on a taste dimension. So the item carries a
FIXED seed; the image sent is that seed's, chosen by nobody; three more seeds
are generated and banked because they cost PC minutes and nothing else, and
the caption says they exist. He may ask for them.

### 1.5 The channel cannot send "two images in ONE message" today

`tools/runner/telegram-bot.py` has `send_photo` (259 to 272, `sendPhoto`, one
picture, one caption) and `send_video`; a grep for `sendMediaGroup`,
`media_group` and `InputMediaPhoto` over `tools/runner` finds nothing. Jafar's
item 4(a) says two images in ONE message, and item 1 makes the channel this
morning's first work. So the media group is built by the channel builder, not
worked round: `sendMediaGroup` with two `InputMediaPhoto` entries attached by
multipart, caption on the FIRST entry, a two-photo sidecar convention beside
the outbox message in the shape `PHOTO_REF_SUFFIX` already uses (outbox.py 99
to 109), and a receipt carrying BOTH platform message ids and both `photo`
arrays, since the array is the proof a file arrived as a picture (outbox.py
267 to 270). Ordering in the array is the ordering he sees, and the caption
names it. FALLBACK, only if the media group has not landed when the boards
exist: two `sendPhoto` calls in succession, Codex's first, the caption on the
second saying it is the second of two. That is not what he asked for and the
caption says so in those words.

### 1.6 Dictated to the builders, one turn each, reviewed at batch

B1, instrument-builder, `tools/imagegen/imagegen.py`. Add `--spec PATH`
(default: the library beside the tool) and make the three hardcoded sites read
it. `--only`, `--out`, `--run-sha`, `--verdict`, `--staged-files` and the
manifest all follow the chosen spec and out directory. Selftest, accepting
first: `--spec` naming the live `prompts.json` produces the same plan as no
flag; rejecting: a path that does not exist prints "nothing measured" and
exits non-zero; a spec with schema other than 2 is refused by `validate_spec`
as today. The workflow's sentinel gains `spec=` and `out=` keys read by
`batch_settings`, printed with the source that won, fallback the library and
the default directory, in the shape the existing three keys use.

B2, content-wrangler, `tools/imagegen/compare-hook-2026-09-09.json`, schema 2.
`content_rules` and `forbidden_tokens` copied verbatim from the library.
`style.framing_required` copied verbatim. `style.by_kind.concept` with
`prefix` = "the whole board filling the frame edge to edge," and `suffix` =
"" (the key present and empty). ONE item: `id` `hook_compare`, `kind`
`concept`, `binds_to` = "COMPARISON ONLY - not shipped, not bound to anything.
Jafar 2026-09-09 item 4(a), Codex's Hook sheet against this lane." (the
probe items' marker at prompts.json 485 is the precedent), `seed` fixed and
written in the file, `width` and `height` at `hook.png`'s aspect ratio with
the long edge at the largest long edge the lane has banked without a blank
(read off the manifest series and printed; if `hook.png` is larger, say so in
the item's note and in the caption). A `source` block: the art branch commit
read, the file, the key, the sha256 of the original prompt text. A
`translation` list: every pair (original clause, what replaced it), and nothing
else in the text changed. The report prints the unified diff between the
original prompt and the item prompt; the diff must consist of the listed
clauses and nothing else, and the builder pastes that diff into the report. If
a clause has no honest positive equivalent, it goes to `negative` and the
manifest's `inert_at_cfg1` count is what records that it did nothing. Then
`validate_spec` on the new file, printed: zero problems of one item examined,
with the exclusion scan's word count beside the zero. Three more items,
`hook_compare_s2` to `_s4`, identical but for the seed.

B3, the channel builder already on item 1: section 1.5, media group first, the
two-photo sidecar, the receipt. Guard both ways: the accepting case sends two
fixture photos and reads two `photo` arrays back; the rejecting case is a
sidecar naming a file over `PHOTO_MAX_BYTES` and refuses with the measured size.

B4, resident, the run: sentinel push with `spec=` and `out=production/art/compare/hook-2026-09-09`
and `--only hook_compare,hook_compare_s2,hook_compare_s3,hook_compare_s4`,
watched by ancestry. Before the message: open all four PNGs (rule 4), print
the verdict line and the four `blank` readings with their bound, and confirm
the gallery walks the compare directory or add it (one line, printed), so the
gallery link in the caption points at where the boards will show.

B5, Producer, the caption, under the unprompted register, one gallery link.
Dictated in substance; the Producer keeps the register:

    HEADLINE: Two Hook sheets: the one you have, and ours, drawn on your PC
    from the same description.
    WHAT CHANGED: The file you named was a correction note for a board that
    already existed, not the description, so ours was drawn from the
    description that made the first board. Our tool draws whatever it is told
    not to draw, so the do-not sentences were reworded as what to draw
    instead; nothing else in the description changed. First is theirs, second
    is ours, one draw at a fixed seed, with three more banked if you want
    them. Your eye decides whether concept sheets are made in house.
    NEEDS YOU: Are concept sheets made in house? The card is waiting.
    NEXT VISIBLE THING: Mickey's five previews; when, unknown.
    BUDGET: nothing bought.

B6, Producer, the card, so his answer is a record and not a chat preference.
"Are concept sheets made in house?" CLASS: DECISION. A: in house, this lane,
for boards and plates. B: outside for boards (Codex), in house for plates.
C: outside for both. RECOMMENDATION B until ours reads as close: the lane is a
distilled eight-step model built and measured for flat plates, and a
multi-panel board is outside anything it has been measured on; that is a fact
about the evidence, not a prediction of the picture. DEFAULT B if unruled by
2026-09-11 09:00. EVIDENCE: the two boards in the message and the four banked
draws.

WHAT MUST BE SAID TO HIM, in whatever words the Producer chooses: that the file
he named was a correction note; that the description behind the first board
was used instead; that the exclusion sentences were reworded and nothing else
was; that ours is one draw at a fixed seed; and, if true, that ours is smaller.
Nothing else was compared and the caption must not imply otherwise.

## 2. The link in the research digest

### 2.1 What the code says the Producer's analysis got right

Checked at the line, all four claims hold. (a) The sender's path never learns
list membership: `outbox.run_check` (702 to 727) invokes
`producer-check.py --kind <kind> <file>`, and `main()` (2085 to 2102) calls
`check(text, kind, now)` with no `legacy_links`, so a name list in the gate
alone would pass `verify.py` and still be refused at the send. (b)
`LEGACY_LINK_RULES` cannot grow: the selftest at 1197 to 1206 asserts every
name is dated before 2026-09-06 AND that the tuple has exactly three members.
(c) No site page mentions the research: a grep of every `*.html` in the tree
for `atlas-02` and `research` returns no file. (d) `link_ok` (425 to 439) is
the one function both the gate and the single-file check call, so a
destination admitted there is admitted at both instants, which is the property
the 2026-09-06 ruling required ("every destination test reads the same
instant", 609 to 612).

### 2.2 Does his instruction override his rule?

YES, FOR THIS MESSAGE, AND IT REPEALS NOTHING. He wrote the band on 2026-09-06
("never to a repo markdown file, only to the glance, map or gallery") and he
wrote item 4(c) this morning ("with the link"). A later, specific instruction
from the rule's own author governs its instance; it does not silently rewrite
the general rule, and a mechanism that read it as a repeal would be the
fifteen-link dump one message later. So the mechanism admits ONE URL, names the
ruling that admits it, and cannot admit a prefix.

### 2.3 The fourth option, no link, is refused; so is the glance-link dodge

"Send no link and put the findings in the body" fails twice. The body already
carries the findings; the link's only job is the evidence behind them, and
constitution law 12, his, says a claim with no artifact behind it may not be
sent. `linkfloor` (640 to 661) enforces exactly that and is unconditional in
the unprompted register. "Link to the glance instead" passes the gate and is
worse: it is a green link to a page that shows none of what the sentence
claims, the false-green shape the 2026-09-06 ruling named at its section 1(d),
and it teaches the next writer that the floor is a token to be satisfied. Both
REFUSED.

### 2.4 Why the whole-URL entry and not a site page today

The BEST AVAILABLE answer is a research page on the site: readable on a phone
without GitHub's file listing, inside the band with no exception at all, and
the code already names where the allowlist grows (`SITE_PAGES`, 204). It is
not available today: the publish lane has failed eight runs this morning
(section 3), the un-embed fix in `tools/gallery.py` has not been seen through a
deploy, and a page nobody has served is the fault the register already has. He
asked for the message this morning. So the entry is the FIRST WORKING rung, and
the site page is the named next rung that DELETES the entry.

The URL is the branch tree of the research directory, not a commit-pinned
tree: the message goes after the commit that carries this ruling and the
research is pushed, and a sha typed into a tool constant by hand is the kind of
hand-typed value the cadence gate refuses in its own domain.

### 2.5 Dictated to the builder, `tools/producer-check.py`

A1. A frozen tuple `RULED_LINKS` of `(url, label, rulingRecordPath)`, one
member: `("https://github.com/jsab258/wc26-picks/tree/claude/game-dev-ai-automation-2h67ix/production/art/atlas-02/research",
"atlas-02-research", "game-design/decision-2026-09-09-the-hook-comparison-the-ruled-link-and-the-stale-pages.md")`.
The comment beside it quotes item 4(c) verbatim, names this record and section
2, and says in those words that the next rung deletes the entry.

A2. `ruled_link(url)`: the SAME normalisation `site_page` uses (drop the
fragment, strip the trailing slash), then whole-string equality against each
entry. No prefix, no host, no `startswith`. `link_ok` consults it after
`site_page` and before the legacy branch. `link_rule_generation` appends
`/plus-ruled-url` only when a ruled entry was matched in the message, so the
report never carries the exception silently.

A3. The gate prints `linksRuledUsed=N/M` (N matched across the walk, M the
tuple length) on both the PASS and FAIL lines beside `filesLegacyLinks`, and
the per-file line for a file that used one says `ruled-link:atlas-02-research`.

A4. Selftest, accepting first: the held digest's text under an unprompted name
passes with the ruled URL. Rejecting, each refused by `linkdest`: the parent
directory (`.../production/art/atlas-02`); a child blob
(`.../research/transport-timetables.md` under `blob/`); the same path under
`blob/` instead of `tree/`; the same path on branch `main`; the URL with one
character appended. Then `len(RULED_LINKS) == 1`, and for every entry the
ruling file exists in the tree and contains the URL string. The existing
`BAD["linkdest"]` fixture (`blob/main/q.md`) stays refused.

A5. `SITE_PAGES` gains `("world.html", "the-world")`. This is not adjacent
work: `publish-glance.py` `PAGES` (119 to 124) already publishes `world.html`
under Jafar's item 2 of this morning, and the register's list and the
publisher's list are two copies of one idea that the same batch left out of
step. The comment cites item 2 and this record. One tuple entry, one selftest
line, reversible in one line if he says the band stays at three.

A6. Resident: the held file moves back to
`production/outbox/2026-09-09-atlas-02-research-digest.unprompted.md`, dated
the day it is sent. Before it goes, the Producer confirms the last-bus card
("When does the last bus leave Meridian?", decision-queue, added 2026-09-09
from this research) went to him as its own message under item 1; if it did
not, NEEDS YOU names it instead of "nothing new". Then
`python3 tools/producer-check.py production/outbox/2026-09-09-atlas-02-research-digest.unprompted.md`
printed, and `--gate` printed with `linksRuledUsed=1/1`.

WHAT MUST BE SAID TO HIM: nothing about the mechanism. He asked for the link;
he gets the link. The digest as held is 117 words, in shape, and I read nothing
in it that the research files in the tree do not support at the level a
120-word message can carry.

## 3. The pages: stale, not absent, and the register cannot tell

### 3.1 The correction

The brief handed to this spawn says "THE PAGES HAVE NEVER BEEN SERVED" and
"every message that passed [the register] carried a link to a 404". Rule 3,
applied to the brief itself. The tree says otherwise in three places I opened:

- `production/queue/139`, status: DONE 2026-09-07, "publish run 12 attempt 2
  succeeded on 85b5222a, and run 13 on 284cfb76. The glance, the map and the
  gallery are served."
- `production/NOW.md` 258 to 271, the 2026-09-07 entry, same facts, and the
  notification path proven "against the served page rather than a local
  build".
- `production/map-notified.json`: `last.at` 2026-09-07T20:24:44Z, `servedUrl`
  `https://jsab258.github.io/wc26-picks/map.html`, `pageCommit`
  `45de6c2198d069117af1d2ee0287eb4501db6181`, written "only from a page that
  answered as ours".

So the eleven refusals under the environment protection rule are 2026-09-05
and 2026-09-06 history that Jafar lifted on 2026-09-07, and the card in the
decision queue's ON US section already says so at its amendment. What is true
today, from the resident's measurement on run 48: runs 41 to 48 died on
`tools/gallery.py --selftest` (`pageBytes` 1000108 against 1000000) before
`actions/deploy-pages` (the step order at publish-glance.yml 244 to 269), so
nothing has deployed this morning. Runs 14 to 40 are unknown to me. The three
destinations therefore EXIST and are STALE: the newest content they can show is
whatever the last successful deploy carried, at latest known 2026-09-07
20:24Z, and every message since has linked to a page that does not show what
the message describes. That is a real fault. It is not a 404, and the two need
different fixes: a 404 needs a setting Jafar changes, a stale page needs our
gate to go green and a run to reach the deploy.

### 3.2 The thing worth saying, in plain words

Two instruments, no coupling. The register mandates a link to one of three
pages and checks the URL's shape. The publish lane decides whether those pages
show anything current. Nothing joins them: `producer-check` cannot see a
publish run and prints `PASS` over a link to a page eight runs stale, and
`publish-glance --check` can see the served commit and is not consulted by
anything that sends. A rule that mandates evidence and cannot see whether the
evidence is there is a rule about tokens, and the 2026-09-06 ruling said the
same of a host allowlist.

### 3.3 What is NOT done in this ruling

No gate is moved and no bound is set. The un-embed fix is in the tree and is
with the seven builders; a run reaching the deploy is what proves it, and
whether the environment rule bites again is unknown until a run gets there.
Item 2 of Jafar's order owns it.

### 3.4 What is done, dictated

C1, resident, before ANY message goes today: run the existing entry point and
read it, per `.claude/rules/ci.md`:
`python3 tools/publish-glance.py --check https://jsab258.github.io/wc26-picks/ --expect-commit <HEAD>`
and the same for `map.html` and `gallery.html`. Quote the three served
commits and their dates in the commit message. That one command replaces the
argument about what is served.

C2, queue item, named for filing: "the register cannot see that the page it
links to is stale". The gate reads the served commit from
`production/map-notified.json` (`last.pageCommit`, `last.at`) or from a
committed served-verdict file when one exists, and prints
`servedPageAgeHours=` and `servedPageCommit=` on the gate's done line beside
`filesChecked`, PRINTED AND NOT GATED until a series has been read. Ships with
the two outcomes watched: a fixture with a fresh reading and one with a
reading older than a day, both printing, neither refusing.

C3, queue item: "the research lives on the site". A generated page from the
five research files under `production/art/atlas-02/research/`, published by
`publish-glance` like `world.html`, added to `SITE_PAGES`, and on landing
`RULED_LINKS` loses its entry and the selftest's length assertion goes to
zero. Acceptance is the served page answering with this branch's stamp and
the entry gone in the same commit.

## 4. Nothing here goes to Jafar as a card except the one he asked for

Ruling 1 is a method choice about running his comparison fairly; he is told
in the caption and decides off the picture; the card in B6 records what he
decides. Ruling 2 is a reading of his own two instructions where the later,
specific one governs one instance; if the reading is wrong the cost is one
link he did not want and the entry comes out in one line. Ruling 3 is a
correction of the record. None needs a decision from him.

## 5. The ladder, asked at close

The Hook comparison: FIRST WORKING, and the next rung is named. A lane built
and measured for flat plates is being asked for a board; the rung after this
one is a concept kind with its own measured settings (size, steps, cfg with the
negative channel active, which the probe pair at prompts.json 503 to 507 says
this model can take), read off a printed series from these four draws and the
next batch, not guessed. The link: FIRST WORKING by construction, next rung
C3. The register's blindness to the served page: BLANK next rung until C2
prints a series, and a blank next rung is a research task, not a finished
aspect.

## 6. What this spawn did not get to

I could not open the art branch, so the character count, the two exclusion
hits and the edit-prompt reading are the builder's until B2 prints them. I did
not read the workflow's commit and verdict steps (ledger-imagegen.yml beyond
line 80) to confirm `--staged-files` follows an alternate out directory
without a second change; B1 must print the staged list from the compare
directory before the sentinel push. I did not count the research digest's
words against `count_words`; the Producer's 117 is quoted, and A6 prints it.

<!--RULING spawn=2026-09-09T08:04:25Z-->
