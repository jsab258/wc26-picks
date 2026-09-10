#!/usr/bin/env python3
"""The content rule, D17 and D18, as a word-list gate over speech and prompts.

    python3 tools/content-gate.py                  # gate the live corpus
    python3 tools/content-gate.py --report         # every hit, with denominators
    python3 tools/content-gate.py --series         # per-rule hit counts: the printer
    python3 tools/content-gate.py --enforceable    # what this gate can and cannot check
    python3 tools/content-gate.py --selftest       # accepting case FIRST, then rejecting
    python3 tools/content-gate.py --carry-write    # rewrite the carried inventory

THE AUTHORITY is ledger-v2/respec/decision-register/D18-content-rule.md, which
extends D17-no-alcohol-no-gambling.md rather than replacing it, and canon.md,
section "The content rule". D17: alcohol is never shown, served, drunk or
spoken of, and gambling likewise, anywhere, in image or speech; PUBS MAY EXIST
AS PLACES. D18 adds the rest of the permanent content rule.

WHAT THIS GATE CAN ENFORCE, AND WHAT IT CANNOT. Half of D18 permits the FACT
and forbids the DEPICTION or the REWARD, and a word list cannot read intent.
Printed by --enforceable so the claim is never bigger than the instrument:

  MECHANICAL, this gate checks it:
    alcohol as substance and activity          D17
    gambling as substance and activity         D17
    children, anywhere, in any of the corpora  D18
    slurs, from content/rules/slurs-v1.json    D18
    drug USE and paraphernalia                 D18 ("never shown, never used")
    prostitution and explicit sexual content   D18
    torture named as an act                    D18, the word only

  NOT MECHANICAL, and this gate says so rather than pretending:
    "cruelty AS SPECTACLE"  is about framing and duration, not vocabulary. A
      scene can be cruel without a listed word and can name torture while
      condemning it. Belongs to a reader, or to the D7 judge.
    "killing rare, permanent, remembered forever" is a property of Core's
      memory and homicide tables, not of any text. Belongs to a systems gate.
    "racism as a FACT about a character, never voiced" - the gate enforces
      the second half only. It cannot tell a card that says a man is a bigot
      from a card that endorses him.
    "never rewarded" is an outcome-table property. No word appears.
    "drugs as an off-screen economy others run" - the gate can refuse the
      verbs and the paraphernalia. It cannot see whether a scene is on screen,
      and it cannot see whether a verb is a PLAYER verb, which lives in the
      interaction table in Core.
    "religion never mocked, never a mechanic" - mockery is tone; a mechanic
      is an entry in the systems inventory.
    "police corruptible as individuals, never as a thesis" - a thesis is a
      reading of the whole work. No sentence carries it.
    A RENDERED IMAGE. The gate reads prompts, and the Fairview comparison
      proves the difference: the outside delivery's prompt asked for
      "nonidentifiable people" and the picture came back with two children in
      school uniform at a FAIRVIEW SCHOOL gate. Only opening the file caught
      that. See --enforceable.

EXIT CODES, distinct per outcome, in the order they are decided:
    2  nothing measured: a corpus glob matched no files, or a file would not
       open. A zero from a run that opened nothing is the failure this project
       names in its own rules, so it can never be reported as clean.
    5  the selftest failed (only in --selftest).
    3  the image-spec content clause is not identical across every spec, or a
       spec's forbidden_tokens is missing a clause token. Site 2 is broken.
    1  at least one hit that the carried inventory does not cover.
    4  the carried inventory has an entry whose text is no longer there. The
       line was fixed and the entry was not deleted, so the carried count in
       the footer is now a lie that reads low.
    0  clean, with every denominator printed beside the zero.

WHAT THE BOUNDARY IS, and it is the whole difficulty of this tool.

The rule bars alcohol and gambling AS SUBSTANCE AND AS ACTIVITY. It does not
bar the building. A gate that refused the word "pub" would be wrong, would be
routed around within a day, and would be worse than no gate. So:

  ALLOWED, and each of these is a live string in the corpus this gate passes:
    pub, pubs            "How's the pub treating you?"
    bar (the fitting)    "New face behind an old bar."
    port                 "Two bolts short on the port side."  (a PORT TOWN)
    landlord, landlady   "Did you settle that business with the landlord?"
    glass (window)       "All I saw was a shape by the glass."
    snug, lounge, public bar, working men's club: rooms and places.

  DELIBERATELY NOT CAUGHT, because the innocent sense is live in this corpus
  and mangling ordinary dialogue is the worse error. Each is named in
  UNDER_CAUGHT below with the live line that decided it:
    drink, drinks, drank  "Drinks lime and soda. Tips like a magistrate."
    bet, bets             "Caught more than gulls, I'd bet."
    odds, stakes          idiom and narrative vocabulary
    porter, barmaid, barman, punter, pontoon, gill, plonk, chaser, bender
    dominoes, cribbage, darts, arrows: PUB GAMES ARE NOT GAMBLING. D17 says
    pub games are not added as SYSTEMS; it does not ban the word. A darts
    league sheet on a wall is decor and stays.

  CAUGHT DELIBERATELY THOUGH THE WORD HAS AN INNOCENT SENSE, listed in
  DECIDED below with the reasoning, because the rule names the thing and a
  reword is cheap: gambling (the metaphor "it's a gamble" goes too), stout
  (the build sense goes too), sober (but NOT "sobering", which describes
  news), drinking (so "drinking tea" must become "having tea"), bingo,
  jackpot, raffle, blackjack, boozer, teetotal, optics, accumulator, dice.

  CONTEXT-MATCHED rather than banned outright, because the adjective is
  ordinary British and the noun is the drink: bitter, mild, pint, rum,
  spirits, poker, round. Read the patterns: each requires a drink or wager
  context word, or excludes the noun it usually qualifies. "a bitter man",
  "bitter cold", "the mild weather", "a pint of milk", "a rum do", "in good
  spirits", "the fire poker" and "round here" all pass, and do so in the
  selftest's accepting half.

WHAT D18 EXPLICITLY PERMITS, and the gate proves it permits them. The
selftest's accepting half runs a line of tobacco, a line of violence with
blood in it, and a line of period swearing, and REQUIRES zero hits. A gate
that quietly crept into flagging profanity would fail its own selftest:

    tobacco    "Give us a light. He rolled one and put it behind his ear."
    violence   "He put him down on the cobbles and there was blood on the kerb."
    swearing   "Bloody hell, you daft bastard, sod off before I lose my rag."

THE CHILDREN RULE IS THE WIDEST NET HERE and it is worth saying why. D18 says
none rendered, none in the crowd, none in dialogue or image prompts. So a
MENTION counts, and "I've got children" is a live bark that this gate refuses.
But "boy", "girl", "lad", "lass", "son" and "daughter" are NOT caught: in
British speech "the Hendricks boy" is a grown man out of work, "the lads" are
dockers, and a son can be forty. What is caught is a child by age or by role:
child, children, kid, baby, toddler, pram, schoolboy, pupil, playground,
satchel, teenager, and any person given an age under eighteen. THE SCHOOL
STANDS: "school" alone is not a hit, because D18 keeps the building and
closes it. "school yard", "school run", "school uniform" and "schoolchildren"
are hits, because they are the school in use.

WHY TWO CHANNELS. `speech` rules are word-boundary regexes read over spoken
text. `prompt` rules are the crude substrings imagegen already enforces
through `content_rules.forbidden_tokens`, matched by `in`, which is why
"ale" cannot be a prompt token (it is inside "pale") and why the existing
list carries "bass " with a trailing space. One table, two columns, so there
is one answer to "is this alcohol" and two matchers for the two channels.

WHY THE CLAUSE'S OWN WORDS ARE NOT PROMPT TOKENS. `rules_clause` rides in
every POSITIVE prompt and `validate_spec` scans the composed prompt against
forbidden_tokens. A token list containing "alcohol" or "gambling" would
therefore refuse every prompt in the library, including clean ones. So the
clause says "no alcohol" and "no gambling" and the token list says "beer",
"lager", "bingo": the abstract nouns instruct, the concrete nouns refuse.
Measured, not assumed: run --selftest, whose accepting half composes a real
prompt and checks it passes imagegen's own forbidden scan.
"""
import argparse
import json
import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
# (the baseline lives in this file, see BASELINE below)
NOTHING = "nothing measured"

# THE CLAUSE. It goes in every image spec's `content_rules.rules_clause`,
# appended to the existing no-trade-marks sentence, and this gate proves it
# is byte-identical across every spec. No spaces matter here: it is prose in
# a JSON string, not a key=value value.
# NOT "nothing served or drunk", though that was the first wording. The
# token list contains "drunk", the clause rides in the POSITIVE prompt,
# and imagegen scans that composed prompt against the tokens: the first
# wording would have made every prompt in the library refuse itself. The
# selftest's self-trip check found it before it shipped, which is the
# whole reason that check exists.
CLAUSE = ("no alcohol and no gambling anywhere in frame, nothing poured "
          "or consumed, no games of chance, nobody under eighteen and no "
          "school in use, nothing sexual")

# THE WORD LIST. Each entry: id, channel(s), pattern (speech), token (prompt),
# kind, why. `pattern` is compiled case-insensitive unless `cased` is set.
#
# HOW TO EDIT THIS LIST. Add the narrowest thing that catches the real line.
# If the word has an innocent sense that is live in this corpus, either write
# the context into the pattern (see `bitter`) or put it in UNDER_CAUGHT with
# the line that decided it. Never widen a pattern to catch one line at the
# cost of refusing ordinary speech: the gate people route around is the gate
# that does nothing. Run --series after any edit and read the counts.
W = []


def rule(rid, kind, why, pattern=None, token=None, cased=False, speech=True):
    W.append({"id": rid, "kind": kind, "why": why, "pattern": pattern,
              "token": token, "cased": cased, "speech": speech})


# ---------------------------------------------------------------- alcohol
rule("beer", "alcohol", "the substance", r"\bbeers?\b", token="beer")
rule("lager", "alcohol", "the substance", r"\blagers?\b", token="lager")
rule("ale", "alcohol", "the substance; NO prompt token because the substring "
     "sits inside pale, male, scale and wholesale",
     r"\bales?\b")
rule("stout", "alcohol", "the substance. DECIDED: the build sense (a stout "
     "woman, stout boots) is caught too, because the drink sense is what pub "
     "dialogue says and heavyset is one word away",
     r"\bstouts?\b", token="stout")
rule("bitter_noun", "alcohol", "the drink, NOT the adjective. Needs a drink "
     "context word or a bare noun at the end of a clause, so 'a bitter man', "
     "'bitter cold' and 'a bitter truth' all pass",
     r"(?:\b(?:pints?|halves?|half|glass(?:es)?|drinks?|drinking|pulling|"
     r"pour\w*|serv\w*)\s+(?:of\s+)?bitter\b)|(?:\ba bitter\b(?!\s+[a-z]))",
     token=None)
rule("mild_noun", "alcohol", "the drink, NOT the adjective. 'Mild and "
     "self-effacing' is a live cast card and must pass; 'the mild on the "
     "left' must not",
     r"(?:\b(?:pints?|halves?|half|glass(?:es)?|drinks?|drinking|pulling|"
     r"pour\w*|serv\w*)\s+(?:of\s+)?mild\b)|"
     r"(?:\bthe mild\b(?!\s+(?:weather|winter|spring|summer|autumn|day|"
     r"night|case|form|version|one|steel|soap|cheese|sort|kind|manner)))")
rule("pint", "alcohol", "the measure, when it is not milk. A crate of pint "
     "milk bottles on a doorstep is period-correct and innocent",
     r"\bpints?\b(?!\s+(?:bottles?|of\s+(?:milk|water|cream|paraffin|oil|"
     r"blood|tea|squash)))(?<!milk pint)", token="pint of")
rule("whisky", "alcohol", "the substance", r"\bwhisk(?:e)?y\b", token="whisky")
rule("whiskey_tok", "alcohol", "the other spelling, prompt channel",
     pattern=None, token="whiskey", speech=False)
rule("vodka", "alcohol", "the substance", r"\bvodkas?\b", token="vodka")
rule("gin_drink", "alcohol", "the substance, in drink context only. Bare 'gin' "
     "is inside imagine, original and engine, and a gin is also a trap and a "
     "cotton machine",
     r"\b(?:glass(?:es)?|bottles?|measures?|tots?|drop|shot|double)\s+of\s+gin\b"
     r"|\bgin\s+and\s+(?:tonic|it|orange|lime)\b")
rule("brandy", "alcohol", "the substance. Cased, because Brandy is a name",
     r"\bbrandy\b", token="brandy", cased=True)
rule("sherry", "alcohol", "the substance. Cased, because Sherry is a name",
     r"\bsherry\b", token="sherry", cased=True)
rule("rum_drink", "alcohol", "the substance, in drink context only. 'A rum do' "
     "and 'rum business' are period British for odd and must pass",
     r"\b(?:glass(?:es)?|bottles?|measures?|tots?|drop|shot|double)\s+of\s+rum\b"
     r"|\brum\s+and\s+(?:coke|black|pep)\b")
rule("wine", "alcohol", "the substance", r"\bwines?\b", token="wine")
rule("cider", "alcohol", "the substance", r"\bciders?\b", token="cider")
rule("champagne", "alcohol", "the substance", r"\bchampagne\b", token="champagne")
rule("cocktail", "alcohol", "the substance", r"\bcocktails?\b", token="cocktail")
rule("liquor", "alcohol", "the substance", r"\bliqueurs?\b|\bliquor\b",
     token="liquor")
rule("spirits_drink", "alcohol", "the drink, in serving context only. 'In good "
     "spirits' and 'the spirit of the thing' must pass",
     r"\b(?:bottled?|bottles?\s+of|optics?|shelf\s+of|measures?\s+of|"
     r"serv\w+|sell\w*|selling)\s+spirits\b|\bspirits\s+(?:optic|shelf|"
     r"measure|licence|bottle)s?\b")
rule("booze", "alcohol", "the substance", r"\bbooze\b|\bboozing\b", token="booze")
rule("boozer", "alcohol", "DECIDED: caught even though it means the pub. The "
     "rule allows the place; this word names the place by the drink, and "
     "'the pub' is the replacement",
     r"\bboozer\b")
rule("shandy", "alcohol", "the substance", r"\bshandy\b", token="shandy")
rule("snakebite", "alcohol", "the substance", r"\bsnakebite\b")
rule("grog", "alcohol", "the substance", r"\bgrog\b")
rule("tipple", "alcohol", "the substance", r"\btipple\b")
rule("nightcap", "alcohol", "the drink", r"\bnightcaps?\b")
rule("tankard", "alcohol", "the vessel", r"\btankards?\b", token="tankard")
rule("firkin", "alcohol", "the cask. A live prompt asked for a 'beer firkin'",
     r"\bfirkins?\b", token="firkin")
rule("cask", "alcohol", "the cask. D17 voids the cask line by name",
     r"\bcasks?\b", token="cask")
rule("keg", "alcohol", "the cask", r"\bkegs?\b", token="keg")
rule("brewery", "alcohol", "the trade. NOT 'brewing' or 'brewed': brewing tea "
     "and trouble brewing are both ordinary and both innocent",
     r"\bbrewer(?:y|ies|s)?\b", token="brewery")
rule("offlicence", "alcohol", "a shop whose whole function is alcohol, unlike "
     "a pub, which can be a room people sit in",
     r"\boff-?licen[cs]es?\b|\boffies?\b", token="off-licence")
rule("lastorders", "alcohol", "the serving ritual", r"\blast orders\b")
rule("lockin", "alcohol", "after-hours drinking", r"\block-?ins?\b")
rule("happyhour", "alcohol", "the serving ritual", r"\bhappy hour\b")
rule("freehouse", "alcohol", "means not tied to a brewery. D17 voids the "
     "free-house question by name",
     r"\bfree\s?house\b|\btied\s?house\b")
rule("pubcrawl", "alcohol", "the activity", r"\bpub crawls?\b")
rule("pump", "alcohol", "the bar fitting. D17 voids the pump clips by name. "
     "'pump handle' is a PROMPT token only: a pump handle in a pub interior "
     "is always a beer pump, while a spoken pump handle can be a water pump",
     r"\bpump ?clips?\b|\bbeer pumps?\b|\bbar pumps?\b|\bhand ?pulls?\b",
     token="pump clip")
rule("pumphandle_tok", "alcohol", "prompt channel only, see `pump`",
     pattern=None, token="pump handle", speech=False)
rule("beermat", "alcohol", "the bar fitting", r"\bbeer ?mats?\b")
rule("optic", "alcohol", "the spirit measure on a back bar. DECIDED: the "
     "lens sense and the 2010s 'the optics of it' sense are caught too. The "
     "C# Optics() function is not in this corpus, which is spoken text",
     r"\boptics?\b", token="optic")
rule("drinkware", "alcohol", "the vessel named by its contents",
     r"\b(?:wine|beer|pint|spirit)\s?glass(?:es)?\b", token="wine glass")
rule("drunk", "alcohol", "the state", r"\bdrunks?\b|\bdrunken(?:ness)?\b|"
     r"\bdrunkards?\b", token="drunk")
rule("drinking", "alcohol", "DECIDED: the gerund is caught, so 'drinking tea' "
     "must become 'having tea'. 'I was drinking on my break' is a live cast "
     "card secret and is exactly what this must catch. Bare 'drink' and "
     "'drinks' are NOT caught, see UNDER_CAUGHT",
     r"\bdrinking\b")
rule("sober", "alcohol", "a drunkenness reference by implication: 'I'd want "
     "it from somebody sober'. NOT 'sobering', which describes news",
     r"\bsober(?:s|ed|ly)?\b")
rule("pissed", "alcohol", "the state. 'Pissed off', 'pissed about' and "
     "'pissed down' are ordinary period British and pass",
     r"\bpissed\b(?!\s+(?:off|about|down|on|up|myself|himself|herself|"
     r"themselves|it))")
rule("tipsy", "alcohol", "the state",
     r"\btipsy\b|\bsozzled\b|\bsloshed\b|\blegless\b|\bparalytic\b|"
     r"\bsquiffy\b|\btiddly\b|\bhalf-?cut\b|\bthree sheets\b")
rule("hangover", "alcohol", "the after-state", r"\bhang-?overs?\b|\bhungover\b")
rule("teetotal", "alcohol", "DECIDED: caught though it describes abstaining. "
     "It can only be said by speaking of drink",
     r"\bteetotal\w*\b")
rule("onthesauce", "alcohol", "the activity",
     r"\bon the sauce\b|\bhair of the dog\b|\bone for the road\b")
rule("aroundofdrinks", "alcohol", "buying drinks. Needs the possessive or "
     "article form, so 'round here', 'word got round' and 'all round' pass",
     r"\b(?:a|your|my|his|her|their|our|whose|another|next)\s+round\b"
     r"(?!\s+(?:of\s+applause|trip|the|here|robin|number|figure))")

# --------------------------------------------------------------- gambling
rule("gambling", "gambling", "DECIDED: the whole family, metaphor included. "
     "The rule names this word, so 'it's a gamble' is reworded to 'it's a "
     "risk' rather than argued about",
     r"\bgambl\w*\b", token="gambling-den")
rule("betting", "gambling", "the activity. Bare 'bet' and 'bets' are NOT "
     "caught, see UNDER_CAUGHT: 'I'd bet' is live and innocent",
     r"\bbetting\b|\bbettors?\b|\bbet\s+on\s+(?:the\s+)?(?:horses|dogs|race|"
     r"races|match|game|fight|nose)\b|\bhad a bet\b|\bplace[ds]? a bet\b|"
     r"\btakes? bets\b|\blay(?:s|ing)? (?:a )?bet\b", token="betting shop")
rule("bettingslip", "gambling", "the object", r"\bbet(?:ting)? ?slips?\b",
     token="betting slip")
rule("bookie", "gambling", "the trade",
     r"\bbookies?\b|\bbookmakers?(?:'s)?\b|\bturf accountants?\b",
     token="bookmaker")
rule("oddson", "gambling", "the wager form. Bare 'odds' is NOT caught: "
     "'against the odds', 'odds and ends' and the design term 'visible odds' "
     "are all innocent",
     r"\bodds-?on\b|\bodds\s+of\s+\d|\b(?:short|long|better)\s+odds\b")
rule("wager", "gambling", "the activity", r"\bwager\w*\b", token="wager")
rule("fruitmachine", "gambling", "the machine",
     r"\bfruit machines?\b|\bone-?armed bandits?\b|\bslot machines?\b|"
     r"\bpuggys?\b", token="fruit machine")
rule("jackpot", "gambling", "DECIDED: the metaphor is caught too",
     r"\bjackpots?\b", token="jackpot")
rule("poker_game", "gambling", "the card game, NOT the fire iron. Excluded "
     "after fire, coal, brass, iron and hearth, and before 'face'",
     r"(?<!fire )(?<!coal )(?<!brass )(?<!iron )(?<!hearth )\bpoker\b"
     r"(?!\s*face)", token="poker table")
rule("blackjack", "gambling", "DECIDED: the card game. The cosh sense is "
     "American and the sweet is a liquorice stick; both can be reworded",
     r"\bblackjack\b", token="blackjack")
rule("roulette", "gambling", "the game",
     r"\broulette\b|\bbaccarat\b|\bcraps\b", token="roulette")
rule("bingo", "gambling", "DECIDED: the hall and the game. The exclamation "
     "goes too, because it is the game's word",
     r"\bbingo\b", token="bingo")
rule("lottery", "gambling", "the game", r"\blotter(?:y|ies)\b", token="lottery")
rule("raffle", "gambling", "DECIDED: the church raffle is a game of chance",
     r"\braffles?\b|\btombolas?\b|\bsweepstakes?\b", token="raffle")
rule("pools", "gambling", "the football pools. Bare 'pools' is not caught: "
     "puddles and swimming pools exist",
     r"\bthe pools\b|\bfootball pools\b|\bpools coupons?\b")
rule("accumulator", "gambling", "DECIDED: the bet. The software sense is real "
     "but lives in engineering prose, which is not this corpus",
     r"\baccumulators?\b")
rule("stakeon", "gambling", "wagering. Bare 'stakes' is NOT caught: narrative "
     "stakes and a stake in a business are the usual senses here",
     r"\bstake[ds]?\s+on\b|\bstakes\s+on\b")
rule("dogtrack", "gambling", "the venue",
     r"\bdog tracks?\b|\bgreyhound\s+(?:racing|track|stadium)\b|"
     r"\brace\s?courses?\b|\bracetracks?\b|\brace meetings?\b",
     token="dog track")
rule("threecard", "gambling", "the street game",
     r"\bthree-?card\b|\bfind the lady\b|\bcrown and anchor\b")
rule("moneyongame", "gambling", "staking cash on a result",
     r"\b(?:fiver|tenner|quid|pound|score)\s+on\s+(?:the\s+)?(?:horses|dogs|"
     r"match|game|fight|nose|favourite)\b|\bcards for money\b|"
     r"\bpenny a point\b")
rule("dice", "gambling", "DECIDED: the game. 'A dice roll' as engineering "
     "metaphor lives in prose, not in this corpus",
     r"\bdice\b", token="dice")
rule("casino", "gambling", "the venue",
     r"\bcasinos?\b|\bbetting shops?\b|\bamusement arcades?\b")

# --------------------------------------------------------- D18: children
#
# D18: none rendered, none in the crowd, none in dialogue or image prompts,
# and THE SCHOOL STANDS CLOSED. So the building survives and its use does
# not, and a MENTION is a hit because the rule says "none in dialogue".
rule("child", "children", "the word itself, in any form",
     r"\bchild(?:ren|ren's|'s|s)?\b", token="child")
rule("kid", "children", "the word itself. 'Kidding' is a different word and "
     "is not matched",
     r"\bkids?\b", token="kid")
rule("baby", "children", "the youngest case",
     r"\bbab(?:y|ies)\b|\btoddlers?\b|\binfants?\b|\bnewborns?\b",
     token="baby")
rule("pram", "children", "the object that implies one",
     r"\bprams?\b|\bpushchairs?\b|\bperambulators?\b", token="pram")
rule("schoolchild", "children", "the school IN USE. Bare 'school' is not "
     "caught: D18 keeps the building and closes it, so 'the old school' and "
     "a FAIRVIEW SCHOOL nameplate on a shut building both pass",
     r"\bschool\s?(?:boys?|girls?|child(?:ren)?|kids?)\b|\bpupils?\b|"
     r"\bschool\s?yards?\b|\bplaygrounds?\b|\bnurser(?:y|ies)\b|\bcreche\b|"
     r"\bschool\s?runs?\b|\bschool\s?uniforms?\b|\bschool\s?bells?\b|"
     r"\b(?:infant|primary|junior|secondary|nursery)\s+schools?\b|"
     r"\bschool\s?bus(?:es)?\b", token="schoolchildren")
rule("schoolboy_tok", "children", "prompt channel spellings, see schoolchild",
     pattern=None, token="schoolboy", speech=False)
rule("schoolgirl_tok", "children", "prompt channel spellings, see schoolchild",
     pattern=None, token="schoolgirl", speech=False)
rule("pupil_tok", "children", "prompt channel, see schoolchild",
     pattern=None, token="pupil", speech=False)
rule("playground_tok", "children", "prompt channel, see schoolchild",
     pattern=None, token="playground", speech=False)
rule("satchel", "children", "D18 names the school satchel by name as not "
     "surviving. It is in the object row of all five landed Fairview sheets",
     r"\bsatchels?\b", token="satchel")
rule("littlechild", "children", "the qualified forms. Bare boy, girl, lad "
     "and lass are NOT caught: 'the Hendricks boy' is a grown man and 'the "
     "lads' are dockers. AND NOT 'little ones' or 'small one', WHICH IS A "
     "REPAIR RATHER THAN A PREFERENCE: the first version matched them and "
     "produced 11 hits, every one of them false. The live bark is 'The "
     "little ones are the ones that get you. Penny here, penny there' and "
     "it is about small expenses, and a delivery record's 'it is not a "
     "small one' is about a limit. A qualifier plus a person-word is the "
     "narrowest thing that catches a child",
     r"\b(?:little|young|small|wee)\s+(?:boys?|girls?|lads?|lasses)\b",
     token="little boy")
rule("littlegirl_tok", "children", "prompt channel, see littlechild",
     pattern=None, token="little girl", speech=False)
rule("teenager", "children", "under eighteen by another name",
     r"\bteenagers?\b|\bteenaged?\b|\byoungsters?\b|\badolescents?\b|"
     r"\bjuveniles?\b|\bschoolleavers?\b|\bschool leavers?\b",
     token="teenager")
rule("underage", "children", "ANY person given an age under eighteen, in "
     "words or figures. This is the rule that closes the hole a noun list "
     "leaves: 'a girl of nine' names no listed word",
     r"\baged?\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
     r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|[1-9]|1[0-7])\b"
     r"|\b(?:[1-9]|1[0-7])[-\s]years?[-\s]old\b")

# ------------------------------------------------------------ D18: drugs
#
# THE FACT STAYS, THE VERB GOES. D18 keeps drugs as an off-screen economy
# other people run, so the TRADE vocabulary is not touched: dealer, supply,
# consignment, the trade, smuggling, gear all pass, and so does the bare
# word "drugs" in a sentence about who runs what. What is caught is USE and
# PARAPHERNALIA, which is the half a word list can actually see.
rule("hardsubstance", "drugs", "named substances", r"\bheroin\b|\bcocaine\b|"
     r"\bcannabis\b|\bmarijuana\b|\bamphetamines?\b|\bbarbiturates?\b|"
     r"\bmethadone\b|\bmandrax\b|\blsd\b|\bspliffs?\b|\breefers?\b|"
     r"\bsmack\b(?!\s+(?:in|on|of|him|her|them|it))", token="heroin")
rule("cocaine_tok", "drugs", "prompt channel", pattern=None, token="cocaine",
     speech=False)
rule("cannabis_tok", "drugs", "prompt channel", pattern=None,
     token="cannabis", speech=False)
rule("druguse", "drugs", "the act. THIS IS THE HALF THE GATE CAN SEE: 'never "
     "shown, never used'. Bare 'needle', 'pipe', 'joint', 'coke', 'crack', "
     "'speed', 'weed', 'hash' and 'dope' are NOT caught: sewing needles, "
     "tobacco pipes (tobacco STAYS), a joint of meat, coke the fuel in a "
     "port, a crack in a wall, speed the velocity, a garden weed, hash "
     "browns and a dope meaning a fool are all ordinary here",
     r"\bshoot(?:ing)? up\b|\binject(?:ed|ing|s)?\b|\bsyringes?\b|"
     r"\bsnort(?:ed|ing|s)?\b|\btrack marks?\b|\bskin(?:ning)? up\b|"
     r"\brolling a joint\b|\bstoned\b|\bdoped up\b|\boverdos(?:e|ed|ing)\b|"
     r"\bneedle in (?:his|her|their|the) arm\b|\bdirty needles?\b|"
     r"\bwrap of\b|\bbaggies?\b|\bline of (?:coke|charlie|whizz)\b",
     token="syringe")

# ----------------------------------------- D18: prostitution and sex
#
# NOTE THE WORD THAT IS NOT HERE. "tom" is period police slang for a
# prostitute AND IT IS THE PLAYER'S NAME. It is not in any pattern in this
# file and must never be: the gate would refuse the premise.
rule("prostitution", "sex", "the trade, which D18 removes entirely",
     r"\bprostitut\w*\b|\bbrothels?\b|\bhookers?\b|\bwhores?\b|"
     r"\bkerb.?crawl\w*\b|\bstreet.?walkers?\b|\bmassage parlours?\b|"
     r"\bon the game\b|\bred.?light\b|\bworking girls?\b|\bpimps?\b",
     token="brothel")
rule("sexual", "sex", "explicit content. NOT BARE 'sex', WHICH IS A REPAIR: "
     "the first version matched it and caught the crime-witness spec saying "
     "a witness could not make out 'a garment or a sex', which is the "
     "period word for which of the two somebody is and is exactly the "
     "ordinary writing a gate must not mangle. SEASIDE-POSTCARD SMUT ALSO "
     "SURVIVES: canon's Tone section keeps innuendo, and innuendo names "
     "nothing, so this is explicit acts and explicit anatomy only",
     r"\bsexual(?:ly)?\b|\bsexy\b|\b(?:had|having|have)\s+sex\b|"
     r"\bsex\s+(?:with|scene|act|worker)\b|\bnaked\b|\bnude\b|"
     r"\bnudity\b|\btopless\b|\bporn\w*\b|\bfellati\w*\b|"
     r"\bmasturbat\w*\b|\borgasm\w*\b|\berotic\w*\b", token="nude")

# ------------------------------------------------ D18: cruelty and torture
#
# THE WORD ONLY, AND THE GATE SAYS SO. "No torture or cruelty as spectacle"
# is a judgement about framing that no vocabulary can carry: a scene can be
# cruel with none of these words in it. VIOLENCE STAYS, INCLUDING BLOOD AND
# LIGHT GORE, so blood, punch, knife, kicking, broken and bleeding are NOT
# caught, and the selftest proves it.
rule("torture", "cruelty", "the act named as an act. Flags for a READER, "
     "because the rule is about spectacle and this is only the word",
     r"\btortur\w*\b|\bkneecap(?:ped|ping)?\b|\bblowtorch\w*\b|"
     r"\bpliers on\b|\bfingernails? (?:out|off|pulled)\b|\bmutilat\w*\b|"
     r"\bdismember\w*\b|\bdisembowel\w*\b", token="torture")

# WHAT D18 EXPLICITLY PERMITS. These run through the scanner in the FIRST
# half of the selftest and must produce zero hits. They are here because the
# expensive failure for a content gate is not missing a violation, it is
# creeping outward until it refuses the things the rule allows: a gate that
# flagged swearing would be wrong against the rule as given, and the writer
# who hit it would learn to route around the gate rather than read it.
PERMITTED = (
    ("tobacco", "Give us a light. He rolled one and put it behind his ear, "
                "and the ashtray had not been emptied since Friday."),
    ("violence", "He put him down on the cobbles and there was blood on the "
                 "kerb, and the man got up and the man did not."),
    ("swearing", "Bloody hell, you daft bastard, sod off out of it before I "
                 "lose my rag and knock your bollocks in."),
    ("religion", "Father Emil says the chapel roof wants doing and the "
                 "collection will not do it."),
    ("police", "That copper takes an envelope on a Friday. Not all of them "
               "do, mind."),
    ("drugtrade", "The gear comes through somebody else's warehouse and none "
                  "of it is ours. That is the Fixer's business, not mine."),
    ("thepub", "Mickey's is open, the bar wants a wipe, and the snug is "
               "freezing."),
)

# Words deliberately NOT caught, with the live line that decided each. The
# selftest runs every `line` below through the scanner and REQUIRES zero hits,
# so a widened pattern that starts refusing ordinary dialogue fails the tool
# rather than the dialogue.
UNDER_CAUGHT = (
    ("pub", "the place, and the rule says pubs may exist",
     "How's the pub treating you?"),
    ("bar", "the fitting and the room",
     "New face behind an old bar. That stool's got a bad leg, same as its owner."),
    ("port", "this is a PORT TOWN",
     "Two bolts short on the port side. I've got the right ones somewhere."),
    ("landlord", "a tenancy word first",
     "Did you settle that business with the landlord?"),
    ("glass", "a smashed window is the crime in the witness bank",
     "All I saw was a shape by the glass, and then there wasn't."),
    ("drink/drinks/drank", "the live line proves the innocent sense, and this "
     "line is the MODEL of a pub scene without alcohol",
     "There's a copper asks questions in here Wednesdays. Drinks lime and soda."),
    ("bet/bets", "'I'd bet' means 'I reckon'",
     "Caught more than gulls, I'd bet."),
    ("odds", "idiom and the design term 'visible odds'",
     "What are the odds of that, then."),
    ("stakes", "narrative stakes, a stake in a business, a stake in the ground",
     "The stakes are higher than he thinks."),
    ("porter", "a porter carries luggage, and a hospital porter exists",
     "The porter on the night shift saw nothing."),
    ("barmaid/barman", "staff of a place the rule permits. UNDER-CAUGHT ON "
     "PURPOSE: they can serve tea and food",
     "New barmaid at the working men's club, Tom."),
    ("punter", "British slang for any customer",
     "Two punters in all morning and neither of them buying."),
    ("pontoon", "a floating landing stage, in a port",
     "They moored it against the pontoon."),
    ("dominoes/cribbage/darts/arrows", "PUB GAMES ARE NOT GAMBLING. D17 says "
     "they are not added as systems; the words are not banned",
     "Half the darts team's suddenly very committed to practice."),
    ("merry/hammered/plastered", "cheerful, a hammer, and a wall",
     "He plastered the back room and hammered the batten in, merry as anything."),
    ("sobering", "describes news, not a person",
     "That's a sobering thought."),
    ("brewing/brewed", "tea, and trouble",
     "She's brewing up. There's trouble brewing at the yard."),
    ("pissed off", "ordinary period British for annoyed",
     "He was pissed off about the hours."),
    ("a round trip / round here", "the other senses of round",
     "Word'll be round the Hook before the glass is swept up, and it's a "
     "round trip of twenty minutes."),
    ("gill", "a fish has gills, in a port town",
     "The gills were still red, so it came in this morning."),
)

# Rules whose innocent sense is knowingly refused. The selftest proves each
# one still fires, so this list cannot quietly become decoration.
DECIDED = ("stout", "gambling", "sober", "drinking", "bingo", "jackpot",
           "raffle", "blackjack", "boozer", "teetotal", "optic",
           "accumulator", "dice")


SLUR_FILE = REPO / "content" / "rules" / "slurs-v1.json"


def load_slurs():
    """The slur list, from the one file it lives in. Returns (words, note).

    AN EMPTY LIST IS A FAILURE, NOT A PASS. A slur gate with no slurs waves
    everything through and looks identical to a clean run, which is exactly
    the shape canon-gate's `forbidden_brands` refuses for the same reason.
    The file's own `count` is compared to the length, so a hand edit that
    adds a word without touching the count is caught here rather than read
    as an accurate denominator later.
    """
    if not SLUR_FILE.exists():
        return None, NOTHING + "/no-slur-file"
    doc = json.loads(SLUR_FILE.read_text(encoding="utf-8"))
    words = [w.strip().lower() for w in doc.get("slurs", []) if w.strip()]
    if not words:
        return None, NOTHING + "/slur-list-empty"
    if doc.get("count") != len(words):
        return None, "slur-list-count-says-%s-but-holds-%d" % (doc.get("count"),
                                                               len(words))
    return words, "%d-word(s)-from-%s" % (len(words), SLUR_FILE.name)


SLURS, SLUR_NOTE = load_slurs()
if SLURS:
    rule("slur", "slur", "D18: no slurs of any kind. FULL PERIOD SWEARING IS "
         "ALLOWED and no swear word is in this list; see the file's own "
         "header for the boundary and for the words excluded on purpose",
         "|".join(r"\b" + re.escape(w) + r"\b" for w in SLURS))


def compiled():
    """The speech rules, compiled. Returns [(rule, regex)].

    Compiled once and handed around, because a recompile per line over 4,000
    strings is the kind of thing that makes a gate too slow to run, and a gate
    too slow to run is a gate nobody wires in.
    """
    out = []
    for r in W:
        if not r["speech"] or not r["pattern"]:
            continue
        flags = 0 if r["cased"] else re.IGNORECASE
        out.append((r, re.compile(r["pattern"], flags)))
    return out


RULES = compiled()


#: The prompt channel's substrings, matched the way imagegen matches them.
#: Held separately from RULES because the semantics differ: `in`, not a word
#: boundary. Two matchers over ONE table, which is why `token` is a column of
#: the same rule rather than a second list somebody has to keep in step.
PROMPT_TOKENS = [(r["id"], r["kind"], r["token"]) for r in W if r["token"]]


def scan(text, rules=None, channel="speech", exempt=()):
    """Every hit in one string. Returns [(rule_id, kind, matched_text)].

    The matched text travels with the rule id because a report that says
    "pint" without saying which seven characters it matched sends the reader
    back to the file to find out whether the gate is right.

    ON A PROMPT, BOTH MATCHERS RUN. The word-boundary rules catch what a
    reader would catch; the substring tokens catch what imagegen's own
    `check_forbidden` will refuse, so this gate and the renderer cannot
    disagree about whether a spec is shippable. Found by measurement: the
    live `interior_bar_back` prompt asks for "brass pump handles along the
    counter edge" and NO word-boundary rule fires on it, because a spoken
    pump handle can be a water pump. The prompt token catches it.
    """
    # THE CLAUSE IS EXEMPT BY IDENTITY, and it is printed when it bites.
    # `rules_clause` is appended to every positive prompt and it NAMES the
    # banned things in order to forbid them, so scanning a composed prompt
    # without stripping it would report every clean item in the library as a
    # violation. Same exemption, same reason and the same shape as
    # imagegen.scan_exclusions, which has done this since 25 August.
    for e in exempt:
        if e:
            text = text.replace(e, " ")
    hits = []
    for r, rx in (rules or RULES):
        for m in rx.finditer(text):
            frag = m.group(0).strip()
            if frag:
                hits.append((r["id"], r["kind"], frag))
    if channel == "prompt":
        low = " " + text.lower() + " "
        seen = {h[0] for h in hits}
        for rid, kind, tok in PROMPT_TOKENS:
            if tok.lower() in low and rid not in seen:
                hits.append((rid, kind, tok))
    return hits


# -------------------------------------------------------------- the corpus
#
# Every source is a glob plus a reader. A glob that matches NOTHING is an
# instrument failure and exits 2: "0 hits over 0 files" and "0 hits over 6
# files" are different facts, and only one of them is clean. New banks are
# picked up by the glob rather than by a list somebody has to remember.

def _bank(doc):
    for ln in doc.get("lines", []):
        who = ln.get("id", "?")
        yield who, ln.get("text", "")
        if ln.get("clause"):
            yield who + "/clause", ln["clause"]


def _barks(doc):
    for slot in doc.get("slots", []):
        sid = slot.get("id", "?")
        if slot.get("brief"):
            yield sid + "/brief", slot["brief"]
        for i, line in enumerate(slot.get("lines", [])):
            yield "%s/%d" % (sid, i), line


def _renders(doc):
    rows = doc.get("renders", doc) if isinstance(doc, dict) else doc
    for i, r in enumerate(rows):
        yield "%s/%s/%s" % (r.get("slot", "?"), r.get("index", "?"),
                            r.get("voice", r.get("clip", i))), r.get("line", "")


def _cards(doc):
    for c in doc:
        cid = c.get("id", "?")
        for k in ("summary", "personality", "speech", "need", "occupation"):
            if c.get(k):
                yield cid + "/" + k, c[k]
        for i, x in enumerate(c.get("hardFacts") or []):
            yield "%s/hardFacts/%d" % (cid, i), x
        for i, x in enumerate(c.get("lines") or []):
            yield "%s/lines/%d" % (cid, i), x
        sec = c.get("secret") or {}
        if sec.get("line"):
            yield cid + "/secret", sec["line"]


def _spec(doc):
    """What a prompt ASKS FOR. Vetoes are read by `_veto` under their own
    channel, because a negative prompt naming a forbidden thing is the veto
    doing its job and must not be counted as a request for it."""
    for it in doc.get("items", []):
        iid = it.get("id", "?")
        for k in ("id", "prompt"):
            if it.get(k):
                yield iid + "/" + k, it[k]
    for k in ("style", "defaults", "batch_name"):
        v = doc.get(k)
        if v:
            yield "(spec)/" + k, json.dumps(v)


def _veto(doc):
    """What a prompt PUSHES AWAY. Same words, opposite meaning."""
    for it in doc.get("items", []):
        if it.get("negative"):
            yield it.get("id", "?") + "/negative", it["negative"]
    if doc.get("negatives"):
        yield "(spec)/negatives", json.dumps(doc["negatives"])


def _furniture(doc):
    """Sheet furniture: the lettering laid OVER a drawn panel. It is text the
    player reads on the image, so it is in scope even though no model drew
    it. Walks every string in the document rather than a field list, because
    this schema puts copy in tiles, annotations, taglines and footers and a
    field list would silently miss the next one."""
    def walk(node, path):
        if isinstance(node, str):
            if node.strip():
                yield path, node
        elif isinstance(node, dict):
            for k, v in node.items():
                yield from walk(v, path + "/" + str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + "/%d" % i)
    yield from walk(doc, "")


def _brands(doc):
    for b in doc.get("brands", []):
        bid = b.get("id", "?")
        for k in ("name", "kind", "register", "physical", "says",
                  "neverConfuse"):
            if b.get(k):
                yield bid + "/" + k, b[k]


def _md(text):
    for n, line in enumerate(text.split("\n"), 1):
        if line.strip():
            yield "L%d" % n, line


CORPUS = (
    # (channel, glob, reader, json?)
    ("speech", "content/dialogue/*.json", _bank, True),
    ("speech", "game-design/barks.json", _barks, True),
    ("speech", "game-design/bark-names.json", _renders, True),
    ("speech", "ledger/Assets/StreamingAssets/Audio/Voice/barks-manifest.json",
     _renders, True),
    ("speech", "game-design/tier2-batch-1.json", _cards, True),
    ("speech", "ledger/Assets/StreamingAssets/tier2-batch-1.json", _cards, True),
    ("prompt", "tools/imagegen/prompts.json", _spec, True),
    ("prompt", "tools/imagegen/compare-hook-*.json", _spec, True),
    ("prompt", "tools/meshgen/specs/*.json", _spec, True),
    ("prompt", "production/art/concept-*/[a-z]*-sheet-*.json", _spec, True),
    ("prompt", "production/art/concept-*/[a-z]*-pair-*.json", _spec, True),
    ("brand", "content/brands/brand-bible-v1.json", _brands, True),
    ("spec", "production/specs/dialogue-*.md", _md, False),
    # D18 reaches the landed art, so the delivery records and the sheet
    # furniture are corpus too. The furniture is the lettering laid over a
    # drawn panel: text a player reads on the picture.
    ("spec", "production/art/*/DELIVERY.md", _md, False),
    # A delivery names what is ON the sheet. What came OFF it is named in the
    # D17/D18 pass file beside it, which is not corpus. Ruling 2026-09-10 s14.
    ("prompt", "production/art/concept-*/[a-z]*-furniture-*.json", _furniture, True),
    # THE VETO CHANNEL, read last so its own line sits under the requests.
    ("veto", "tools/imagegen/prompts.json", _veto, True),
    ("veto", "tools/imagegen/compare-hook-*.json", _veto, True),
    ("veto", "tools/meshgen/specs/*.json", _veto, True),
    ("veto", "production/art/concept-*/[a-z]*-sheet-*.json", _veto, True),
    ("veto", "production/art/concept-*/[a-z]*-pair-*.json", _veto, True),
)

#: Sources D18 names that are NOT IN THE TREE. Printed on every report with
#: the words "nothing measured", because "the gate found nothing there" and
#: "there is no there" are different facts and only one of them is clean.
#: D18 cites the atlas as carrying the F1 chapel and school gate; the atlas
#: data file it cites is referenced by production/art/concept-fairview-
#: 2026-09-10/DELIVERY.md and is not tracked by git.
DECLARED_ABSENT = (
    ("production/art/atlas-01/data/atlas.json",
     "D18-cites-it-for-F1-chapel/school-gate;-not-tracked-by-git"),
    ("production/art/atlas-01/DISTRICTS.md",
     "cited-by-fairview-DELIVERY.md-line-127;-not-tracked-by-git"),
)

# Paths whose text may legitimately contain the banned words: the rule
# itself, the decisions that made it, this tool, and the judge's REJECTING
# fixtures, which contain canon violations by construction. Same shape and
# same reason as tools/canon-gate.py, and printed whenever it bites.
EXEMPT = ("canon.md", "ledger-v2/", "legacy/", "tools/content-gate.py",
          "production/specs/judge-")


def read_corpus():
    """Open everything. Returns (rows, opened, missing, exempted, strings).

    rows is [(channel, relpath, locator, text)]. `missing` lists globs that
    matched nothing AND files that would not parse, and either one makes the
    run unmeasured rather than clean.
    """
    rows, opened, missing, exempted = [], [], [], []
    for channel, pattern, reader, is_json in CORPUS:
        matched = sorted(REPO.glob(pattern))
        if not matched:
            missing.append("glob/" + pattern.replace(" ", "_") + "/matched0")
            continue
        for p in matched:
            rel = str(p.relative_to(REPO))
            if any(rel.startswith(e) for e in EXEMPT):
                exempted.append(rel)
                continue
            try:
                raw = p.read_text(encoding="utf-8")
                doc = json.loads(raw) if is_json else raw
            except (OSError, ValueError) as e:
                missing.append("unreadable/" + rel + "/" + type(e).__name__)
                continue
            n = 0
            for loc, text in reader(doc):
                if isinstance(text, str) and text.strip():
                    rows.append((channel, rel, loc, text))
                    n += 1
            opened.append((channel, rel, n))
    return rows, opened, missing, exempted, len(rows)


# ------------------------------------------------------- site 2: the clause
def spec_files():
    out = []
    for channel, pattern, _r, _j in CORPUS:
        if channel == "prompt":
            out.extend(sorted(REPO.glob(pattern)))
    return out


def clause_audit():
    """Every image spec's content clause, compared to every other one.

    THE FAILURE THIS EXISTS FOR: a one-off spec beside the library that
    carries a weaker clause. Three of the seven specs say in their own
    comments that the block was copied by hand, and one of those comments
    says a previous hand-copy dropped the block entirely. Nothing compared
    them until now; the comments were the comparison.

    Returns (rows, problems). rows is per spec so the reader can see WHICH
    one drifted, not just that one did.
    """
    rows, problems = [], []
    want_tokens = [r["token"] for r in W if r["token"]]
    files = spec_files()
    if not files:
        return [], ["clause audit measured nothing: no spec matched the globs"]
    base_clause = None
    for p in files:
        rel = str(p.relative_to(REPO))
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            problems.append("%s: unreadable (%s)" % (rel, type(e).__name__))
            continue
        cr = doc.get("content_rules") or {}
        clause = cr.get("rules_clause", "")
        toks = [t.lower() for t in cr.get("forbidden_tokens") or []]
        # A SPEC THAT ASKS A MODEL FOR A PICTURE MUST CARRY THE CLAUSE. A
        # spec that asks a mesh backend for geometry need not, and two of
        # the nine matched here are exactly that (props-local-01 and
        # props-trellis-01: 49 items between them, not one `prompt` field).
        # Criterion is mechanical rather than a path list, so a new image
        # spec is covered the day it is written; and the non-bearing ones
        # still print a line, because a spec silently exempted is a spec
        # nobody rechecks when it grows a prompt.
        bearing = any((it.get("prompt") or "").strip()
                      for it in doc.get("items") or [])
        if not bearing:
            rows.append({"spec": rel, "clauseIdentical": None,
                         "carriesD17": None, "tokens": len(toks),
                         "d17TokensAbsent": 0, "promptBearing": False})
            continue
        if not clause:
            problems.append("%s: no content_rules.rules_clause at all" % rel)
        if base_clause is None and clause:
            base_clause = clause
        same = (clause == base_clause)
        if clause and not same:
            problems.append(
                "%s: rules_clause is NOT identical to %s. A one-off spec with "
                "a weaker clause is the hole D17 names."
                % (rel, str(files[0].relative_to(REPO))))
        if clause and CLAUSE not in clause:
            problems.append("%s: rules_clause does not carry the D17 clause" % rel)
        absent = [t for t in want_tokens if t.lower() not in toks]
        if absent:
            problems.append(
                "%s: forbidden_tokens is missing %d clause token(s): %s"
                % (rel, len(absent), _cap(absent, 6)))
        rows.append({"spec": rel, "clauseIdentical": same,
                     "carriesD17": CLAUSE in clause,
                     "tokens": len(toks), "d17TokensAbsent": len(absent),
                     "promptBearing": True})
    return rows, problems


def _cap(items, n=8):
    """A truncation that says it bit. (+N more not shown)."""
    items = list(items)
    if len(items) <= n:
        return ", ".join(str(i) for i in items)
    return ", ".join(str(i) for i in items[:n]) + " (+%d more not shown)" % (len(items) - n)


# ---------------------------------------------------------- the baseline
#
# THE BASELINE, STAMPED 2026-09-10, THE DAY D18 WAS RULED.
#
# WHAT IT IS. Every hit that ALREADY EXISTED in the corpus when this gate
# first ran. It is here so that wiring the gate into ledger/verify.py does
# not turn every commit red on content nobody has had a chance to rewrite
# yet. It is not a permission list and it is not an opinion about whether
# these lines are acceptable: they are not, all of them fail D18, and the
# report prints every one of them under its own heading.
#
# THIS LIST IS TO BE EMPTIED BY A CONTENT PASS. IT IS NOT TO BE GROWN.
# Adding an entry by hand means writing a line that breaks the rule and then
# recording permission for it, which is the shape this project calls a
# ratchet with no teeth. The only legitimate edits are DELETIONS, as lines
# get rewritten. `--baseline-write` exists to regenerate it after a content
# pass and prints every line it writes; it is a separate invocation somebody
# has to type on purpose.
#
# HOW IT IS KEYED: file|rule|first 12 hex of the sha1 of the offending TEXT.
# Not the line number, because renumbering a bank is not a content change;
# and not the locator, because one bark line appears at 49 locators in three
# files and 49 identical entries would be noise. The text hash is what makes
# this a ratchet rather than a waiver: change one character of a baselined
# line and its hash changes, so the rewritten line is gated like new writing
# and cannot be quietly re-broken under cover of an old entry.
BASELINE_STAMPED = "2026-09-10"
BASELINE = (
    "content/dialogue/pub-regular-v1.json|aroundofdrinks|8a36466e9c90",
    "content/dialogue/pub-regular-v1.json|aroundofdrinks|9efa82944c04",
    "content/dialogue/pub-regular-v1.json|betting|8e7b2d926e0e",
    "content/dialogue/pub-regular-v1.json|bitter_noun|2e1613fca5f3",
    "content/dialogue/pub-regular-v1.json|bitter_noun|9efa82944c04",
    "content/dialogue/pub-regular-v1.json|casino|8e7b2d926e0e",
    "content/dialogue/pub-regular-v1.json|dogtrack|5b36c9ca985f",
    "content/dialogue/pub-regular-v1.json|mild_noun|fc6aee7c89b5",
    "content/dialogue/pub-regular-v1.json|offlicence|23184f703bae",
    "content/dialogue/pub-regular-v1.json|pint|2e1613fca5f3",
    "content/dialogue/pub-regular-v1.json|pint|db63ce06c1da",
    "content/dialogue/pub-regular-v1.json|stout|7ac6b30a2d7f",
    "game-design/bark-names.json|child|39281f3a70f9",
    "game-design/bark-names.json|sober|49466b5ebf3e",
    "game-design/barks.json|child|055ef4f3a16a",
    "game-design/barks.json|child|16b162e54417",
    "game-design/barks.json|child|2dce9027326a",
    "game-design/barks.json|child|39281f3a70f9",
    "game-design/barks.json|child|5095714fae84",
    "game-design/barks.json|child|52684df0ba09",
    "game-design/barks.json|child|5373012ae7f6",
    "game-design/barks.json|child|5b6466fef99b",
    "game-design/barks.json|child|6f38e74503c8",
    "game-design/barks.json|child|711d7addcc58",
    "game-design/barks.json|child|78e25c8c9d88",
    "game-design/barks.json|child|8b206bfe9eac",
    "game-design/barks.json|child|8e3ab263a0ec",
    "game-design/barks.json|child|a5d038cfd070",
    "game-design/barks.json|child|a5ee21fa0f3f",
    "game-design/barks.json|child|b7b9c9a80b1a",
    "game-design/barks.json|child|b8f94f5db758",
    "game-design/barks.json|child|bfb08e2584b4",
    "game-design/barks.json|child|c64f488b11ad",
    "game-design/barks.json|child|d2aff5f0abdd",
    "game-design/barks.json|child|daeb130b3d11",
    "game-design/barks.json|child|e11f354c041a",
    "game-design/barks.json|child|e575458cb632",
    "game-design/barks.json|child|e834dbd18002",
    "game-design/barks.json|child|eebcda49a3ef",
    "game-design/barks.json|child|f1e505134030",
    "game-design/barks.json|child|fa7970ad1c99",
    "game-design/barks.json|child|fdb39aa9df73",
    "game-design/barks.json|sober|041b10b16f08",
    "game-design/barks.json|sober|05b030204363",
    "game-design/barks.json|sober|0849b53ff6f0",
    "game-design/barks.json|sober|114d4362cf31",
    "game-design/barks.json|sober|1698224e4870",
    "game-design/barks.json|sober|1dcc12ced8e9",
    "game-design/barks.json|sober|202258b45f8d",
    "game-design/barks.json|sober|2298882182db",
    "game-design/barks.json|sober|23096730fa60",
    "game-design/barks.json|sober|348b3987e521",
    "game-design/barks.json|sober|453a565fcc1b",
    "game-design/barks.json|sober|49466b5ebf3e",
    "game-design/barks.json|sober|52cef45ad43c",
    "game-design/barks.json|sober|53882011fc01",
    "game-design/barks.json|sober|5835f168999e",
    "game-design/barks.json|sober|587accd108f4",
    "game-design/barks.json|sober|60aeba2a4bf9",
    "game-design/barks.json|sober|6793390ebe23",
    "game-design/barks.json|sober|679c5b6d4f81",
    "game-design/barks.json|sober|6f38e74503c8",
    "game-design/barks.json|sober|772dba9dbf82",
    "game-design/barks.json|sober|77dc57c5072e",
    "game-design/barks.json|sober|789954b1d18b",
    "game-design/barks.json|sober|8020cced4763",
    "game-design/barks.json|sober|80a8bc8d556d",
    "game-design/barks.json|sober|a1b723643d3b",
    "game-design/barks.json|sober|a5d7df6473e0",
    "game-design/barks.json|sober|a93e13c9512c",
    "game-design/barks.json|sober|bfcbf8c6f9aa",
    "game-design/barks.json|sober|c52dfdeeb16e",
    "game-design/barks.json|sober|cbe468226df8",
    "game-design/barks.json|sober|d21c5ca6d4dc",
    "game-design/barks.json|sober|d9256daf0119",
    "game-design/barks.json|sober|e5bae8c9f75c",
    "game-design/barks.json|sober|edf6f01dea93",
    "game-design/barks.json|sober|fb3fae36f785",
    "game-design/barks.json|sober|fe198ca22cbe",
    "game-design/tier2-batch-1.json|baby|8747b2a4faa3",
    "game-design/tier2-batch-1.json|bettingslip|9293a096779a",
    "game-design/tier2-batch-1.json|betting|9293a096779a",
    "game-design/tier2-batch-1.json|child|cd043ce2f17d",
    "game-design/tier2-batch-1.json|child|ce0a8040c4ed",
    "game-design/tier2-batch-1.json|drinking|17e9815e6804",
    "game-design/tier2-batch-1.json|gambling|3cdb3afc232e",
    "game-design/tier2-batch-1.json|gambling|a492de045fef",
    "game-design/tier2-batch-1.json|kid|bba024332d0e",
    "game-design/tier2-batch-1.json|teenager|9be92b51bed8",
    "game-design/tier2-batch-1.json|whisky|25a19293a5da",
    "game-design/tier2-batch-1.json|wine|34527b182aed",
    "game-design/tier2-batch-1.json|wine|624956f77fa8",
    "game-design/tier2-batch-1.json|wine|6903a063e162",
    "game-design/tier2-batch-1.json|wine|ba381b6d0212",
    "game-design/tier2-batch-1.json|wine|c515bbf7bf2b",
    "game-design/tier2-batch-1.json|wine|d12de04a959a",
    "ledger/Assets/StreamingAssets/Audio/Voice/barks-manifest.json|child|39281f3a70f9",
    "ledger/Assets/StreamingAssets/Audio/Voice/barks-manifest.json|sober|49466b5ebf3e",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|baby|8747b2a4faa3",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|bettingslip|9293a096779a",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|betting|9293a096779a",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|child|cd043ce2f17d",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|child|ce0a8040c4ed",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|drinking|17e9815e6804",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|gambling|3cdb3afc232e",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|gambling|a492de045fef",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|kid|bba024332d0e",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|teenager|9be92b51bed8",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|whisky|25a19293a5da",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|wine|34527b182aed",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|wine|624956f77fa8",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|wine|6903a063e162",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|wine|ba381b6d0212",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|wine|c515bbf7bf2b",
    "ledger/Assets/StreamingAssets/tier2-batch-1.json|wine|d12de04a959a",
    "production/art/atlas-02/DELIVERY.md|beer|4300c1457cc6",
    "production/art/atlas-02/DELIVERY.md|beer|6044b2baa82b",
    "production/art/atlas-02/DELIVERY.md|beer|78f49a19611e",
    "production/art/atlas-02/DELIVERY.md|beer|950d69df8a8a",
    "production/art/atlas-02/DELIVERY.md|beer|97297b330f28",
    "production/art/atlas-02/DELIVERY.md|beer|98c4fddc07d8",
    "production/art/atlas-02/DELIVERY.md|beer|c11c2795f69b",
    "production/art/atlas-02/DELIVERY.md|beer|d681c517b1af",
    "production/art/atlas-02/DELIVERY.md|beer|e5eff71b977a",
    "production/art/atlas-02/DELIVERY.md|brewery|40232ee0a921",
    "production/art/atlas-02/DELIVERY.md|brewery|c5698e03b96f",
    "production/art/atlas-02/DELIVERY.md|brewery|f57064635e03",
    "production/art/atlas-02/DELIVERY.md|cask|950d69df8a8a",
    "production/art/atlas-02/DELIVERY.md|drinking|2527f3ebc650",
    "production/art/atlas-02/DELIVERY.md|firkin|78f49a19611e",
    "production/art/atlas-02/DELIVERY.md|firkin|f2f1b2a6c91d",
    "production/art/atlas-02/DELIVERY.md|freehouse|09cfdd661adc",
    "production/art/atlas-02/DELIVERY.md|freehouse|9177ff8eb8ec",
    "production/art/atlas-02/DELIVERY.md|freehouse|f57064635e03",
    "production/art/concept-copper-row-2026-09-10/copper-row-sheet-2026-09-10.json|pram|7962da73f367",
    "production/art/concept-copper-row-2026-09-10/copper-row-sheet-2026-09-10.json|schoolchild|497c8cc9caf9",
    "production/art/concept-fairview-2026-09-10/DELIVERY.md|satchel|f072ba6b9fdf",
    "production/art/concept-fairview-2026-09-10/DELIVERY.md|schoolchild|29aaf65169a0",
    "production/art/concept-fairview-2026-09-10/fairview-furniture-2026-09-10.json|satchel|7f6549e06683",
    "production/art/concept-fairview-2026-09-10/fairview-pair-2026-09-11.json|satchel|1c062b7d132c",
    "production/art/concept-fairview-2026-09-10/fairview-pair-2026-09-11.json|satchel|668d6305460a",
    "production/art/concept-fairview-2026-09-10/fairview-sheet-2026-09-10.json|satchel|2ede859cb185",
    "production/art/concept-fairview-2026-09-10/fairview-sheet-2026-09-10.json|satchel|81f81542aa23",
    "production/art/concept-fairview-2026-09-10/fairview-sheet-2026-09-10.json|schoolchild|2ede859cb185",
    "production/art/concept-fairview-2026-09-10/fairview-sheet-2026-09-10.json|schoolchild|81f81542aa23",
    "production/specs/dialogue-pub-regular-v1.md|beer|830d1391199b",
    "production/specs/dialogue-pub-regular-v1.md|stout|830d1391199b",
    "tools/imagegen/compare-hook-2026-09-09-pass2.json|beer|0cbf170bfbdb",
    "tools/imagegen/compare-hook-2026-09-09-pass2.json|firkin|0cbf170bfbdb",
    "tools/imagegen/compare-hook-2026-09-09.json|beer|96781507b2ee",
    "tools/imagegen/compare-hook-2026-09-09.json|firkin|96781507b2ee",
    "tools/imagegen/prompts.json|beer|31c696265cb7",
    "tools/imagegen/prompts.json|bingo|035868373af3",
    "tools/imagegen/prompts.json|bingo|c9d9bd144d99",
    "tools/imagegen/prompts.json|pumphandle_tok|76dc404d0c60",
)


def _key(rel, rid, text):
    import hashlib
    return "%s|%s|%s" % (rel, rid,
                         hashlib.sha1(text.encode("utf-8")).hexdigest()[:12])


def partition(rows, baseline):
    """Split hits into new (these fail) and baselined (these report), and
    find baseline entries that no longer match anything. All three counts
    print, because two of them are usually zeros."""
    fresh, covered, seen = [], [], set()
    for channel, rel, loc, text in rows:
        for rid, kind, frag in scan(text, channel=channel):
            k = _key(rel, rid, text)
            if k in baseline:
                covered.append((channel, rel, loc, rid, kind, frag, text))
                seen.add(k)
            else:
                fresh.append((channel, rel, loc, rid, kind, frag, text))
    stale = [k for k in baseline if k not in seen]
    return fresh, covered, stale


# ---------------------------------------------------------------- printing
def hit_line(h):
    channel, rel, loc, rid, kind, frag, text = h
    return ("  %-6s %s:%s rule=%s kind=%s matched=%s\n      %s"
            % (channel, rel, loc, rid, kind, frag.replace(" ", "_"),
               text.strip()[:150]))


def by_channel(res):
    """filesExamined and hits PER CHANNEL, and a channel with zero hits
    prints the count it examined beside the zero.

    A channel that appears in the registry and opened no file at all prints
    the words "nothing measured" on its own line: no channel can report a
    clean zero without saying what it looked at.
    """
    order, seen = [], set()
    for channel, _p, _r, _j in CORPUS:
        if channel not in seen:
            seen.add(channel)
            order.append(channel)
    out = []
    for ch in order:
        files = {rel for c, rel, _n in res["opened"] if c == ch}
        strings = sum(n for c, _rel, n in res["opened"] if c == ch)
        fresh = [h for h in res["fresh"] if h[0] == ch]
        based = [h for h in res["baselined"] if h[0] == ch]
        if not files:
            out.append("  channel=%-6s %s: the registry names this channel "
                       "and no file opened." % (ch, NOTHING))
            continue
        out.append("  channel=%-6s filesExamined=%d stringsExamined=%d "
                   "hits=%d hitsNew=%d hitsBaselined=%d distinctTexts=%d"
                   % (ch, len(files), strings, len(fresh) + len(based),
                      len(fresh), len(based),
                      len({h[6] for h in fresh + based})))
    return out


def done_line(res):
    """The whole-run numbers, on the run's done line, one moment.

    Per-channel and per-file numbers print above on their own lines and are
    not repeated here under the same keys: a reader greping two lines for
    one pair would get two moments as one.
    """
    s = res["strings"]
    if s == 0:
        return ("content-gate: " + NOTHING + " - filesOpened=0 "
                "stringsScanned=0; no corpus was read, so this run cannot "
                "tell clean from blind.")
    return ("content-gate: hitsNew=%d hitsBaselined=%d staleBaseline=%d "
            "over stringsScanned=%d filesOpened=%d filesExempt=%d "
            "declaredAbsent=%d rulesSpeech=%d rulesPrompt=%d slurs=%s "
            "specsClauseIdentical=%d/%d specsCarryClause=%d/%d "
            "distinctTextsNew=%d distinctTextsBaselined=%d baselineStamped=%s"
            % (len(res["fresh"]), len(res["baselined"]), len(res["stale"]),
               s, len(res["opened"]), len(res["exempted"]),
               len(DECLARED_ABSENT), len(RULES),
               len(PROMPT_TOKENS),
               str(len(SLURS)) if SLURS else NOTHING.replace(" ", "-"),
               sum(1 for r in res["specs"] if r["clauseIdentical"]),
               sum(1 for r in res["specs"] if r["promptBearing"]),
               sum(1 for r in res["specs"] if r["carriesD17"]),
               sum(1 for r in res["specs"] if r["promptBearing"]),
               len({h[6] for h in res["fresh"]}),
               len({h[6] for h in res["baselined"]}),
               BASELINE_STAMPED))


def run_gate():
    rows, opened, missing, exempted, strings = read_corpus()
    fresh, covered, stale = partition(rows, set(BASELINE))
    specs, problems = clause_audit()
    return {"rows": rows, "opened": opened, "missing": missing,
            "exempted": exempted, "strings": strings, "fresh": fresh,
            "baselined": covered, "stale": stale, "specs": specs,
            "clauseProblems": problems}


def verdict(res):
    if res["strings"] == 0 or res["missing"]:
        return 2
    if res["clauseProblems"]:
        return 3
    if res["fresh"]:
        return 1
    if res["stale"]:
        return 4
    return 0


def report(res, full=False):
    out = []
    if res["missing"]:
        out.append("INSTRUMENT FAILURE, %d source(s) not measured:"
                   % len(res["missing"]))
        for m in res["missing"]:
            out.append("  " + m)
    out.append("DECLARED ABSENT, %d source(s) D18 names that are not in the "
               "tree. %s for each:" % (len(DECLARED_ABSENT), NOTHING))
    for path, why in DECLARED_ABSENT:
        out.append("  absent=%s stringsExamined=0 why=%s" % (path, why))
    out.append("PER CHANNEL:")
    out.extend(by_channel(res))
    if full:
        out.append("PER FILE (the denominators the channel counts sum from):")
        for channel, rel, n in res["opened"]:
            out.append("  %-6s %-62s strings=%d" % (channel, rel, n))
        if res["exempted"]:
            out.append("  EXEMPT BY PATH, and it bit: " + _cap(res["exempted"]))
    out.append("THE CONTENT CLAUSE, per image spec (site 2):")
    for row in res["specs"]:
        if not row["promptBearing"]:
            out.append("  spec %-62s promptBearing=false clauseRequired=false "
                       "(mesh spec, no item asks a model for a picture)"
                       % row["spec"])
            continue
        out.append("  spec %-62s clauseIdentical=%s carriesClause=%s "
                   "tokens=%d tokensAbsent=%d"
                   % (row["spec"], str(row["clauseIdentical"]).lower(),
                      str(row["carriesD17"]).lower(), row["tokens"],
                      row["d17TokensAbsent"]))
    for p in res["clauseProblems"]:
        out.append("  CLAUSE " + p)
    if res["fresh"]:
        out.append("NEW HITS, %d over %d distinct text(s). THESE FAIL THE "
                   "GATE:" % (len(res["fresh"]), len({h[6] for h in res["fresh"]})))
        shown = res["fresh"] if full else res["fresh"][:20]
        for h in shown:
            out.append(hit_line(h))
        if len(shown) < len(res["fresh"]):
            out.append("  (+%d more not shown)" % (len(res["fresh"]) - len(shown)))
    else:
        out.append("NEW HITS: 0, over %d string(s) examined."
                   % res["strings"] if res["strings"] else
                   "NEW HITS: " + NOTHING)
    if res["baselined"]:
        out.append("BASELINED HITS, %d over %d distinct text(s), stamped %s. "
                   "Every one of these breaks D18 and is waiting on a content "
                   "pass. THIS LIST IS TO BE EMPTIED, NEVER GROWN:"
                   % (len(res["baselined"]),
                      len({h[6] for h in res["baselined"]}), BASELINE_STAMPED))
        if full:
            seen = set()
            for h in res["baselined"]:
                k = _key(h[1], h[3], h[6])
                if k in seen:
                    continue
                seen.add(k)
                out.append(hit_line(h))
        else:
            out.append("  (run --report to see them)")
    if res["stale"]:
        out.append("STALE BASELINE ENTRIES, %d. The line was rewritten and "
                   "the entry was not deleted, so the baselined count reads "
                   "low. Delete these from BASELINE in this file:"
                   % len(res["stale"]))
        for k in res["stale"][:10]:
            out.append("  " + k)
        if len(res["stale"]) > 10:
            out.append("  (+%d more not shown)" % (len(res["stale"]) - 10))
    return out


def series(res):
    """Per-rule hit counts over the real corpus: the printer a bound comes
    from. No threshold is read from this. It is here so that the next person
    who wants one reads a series first."""
    tally = {}
    for channel, rel, loc, text in res["rows"]:
        for rid, kind, frag in scan(text, channel=channel):
            t = tally.setdefault(rid, {"kind": kind, "hits": 0, "texts": set(),
                                       "files": set(), "frags": set()})
            t["hits"] += 1
            t["texts"].add(text)
            t["files"].add(rel)
            t["frags"].add(frag.lower())
    out = ["SERIES, per rule, over the live corpus. hits counts string "
           "occurrences; distinctTexts counts authored lines, and the two "
           "differ by a factor of 49 on one bark because the pair slots "
           "repeat it.",
           "%-16s %-9s %6s %6s %6s  %s"
           % ("rule", "kind", "hits", "texts", "files", "matched")]
    for rid in sorted(tally, key=lambda k: -tally[k]["hits"]):
        t = tally[rid]
        out.append("%-16s %-9s %6d %6d %6d  %s"
                   % (rid, t["kind"], t["hits"], len(t["texts"]),
                      len(t["files"]), _cap(sorted(t["frags"]), 5)))
    fired = len(tally)
    out.append("series: rulesFired=%d rulesSilent=%d rulesTotal=%d "
               "stringsScanned=%d" % (fired, len(RULES) - fired, len(RULES),
                                      res["strings"]))
    if res["strings"] == 0:
        out.append("series: " + NOTHING)
    return out


#: What this gate checks mechanically, and what it does not. Printed by
#: --enforceable so a reader never has to infer the instrument's reach from
#: its silence. `can` is a claim the selftest backs; `cannot` is a claim
#: nothing in this file pretends to.
ENFORCEABLE = (
    ("alcohol", True, "substance and activity, D17. Pubs stay as places."),
    ("gambling", True, "substance and activity, D17. Pub games stay."),
    ("children", True, "by noun and by any stated age under eighteen, D18. "
     "The school building stands; its USE is caught."),
    ("slurs", True, "a closed list, content/rules/slurs-v1.json, D18. "
     "SWEARING IS ALLOWED and no swear word is in it."),
    ("drug-use", True, "the verbs and the paraphernalia only. The off-screen "
     "ECONOMY is permitted by D18 and is not touched."),
    ("prostitution", True, "the trade, D18."),
    ("sexual-content", True, "explicit acts and anatomy. Seaside-postcard "
     "innuendo survives, per canon's Tone section."),
    ("tobacco", False, "PERMITTED by D18. The gate proves it permits it: a "
     "tobacco line is an accepting fixture in the selftest."),
    ("violence-blood-gore", False, "PERMITTED by D18. Also an accepting "
     "fixture."),
    ("swearing", False, "PERMITTED by D18. Also an accepting fixture."),
    ("cruelty-as-spectacle", False, "NOT MECHANICAL. Framing and duration, "
     "not vocabulary. The word `torture` is flagged for a reader; the "
     "judgement is not made here."),
    ("killing-rare-permanent-remembered", False, "NOT MECHANICAL. A property "
     "of Core's homicide and memory tables. No text carries it."),
    ("racism-as-fact-never-voiced", False, "HALF ONLY. The slur list enforces "
     "`never voiced`. Nothing here can tell a card that says a man is a "
     "bigot from a card that endorses him."),
    ("never-rewarded", False, "NOT MECHANICAL. An outcome-table property."),
    ("drugs-off-screen-never-a-player-verb", False, "NOT MECHANICAL. Whether "
     "a scene is on screen, and whether a verb is a PLAYER verb, live in the "
     "interaction table in Core, not in any sentence."),
    ("religion-never-mocked-never-a-mechanic", False, "NOT MECHANICAL. "
     "Mockery is tone; a mechanic is a systems-inventory entry."),
    ("police-never-a-thesis", False, "NOT MECHANICAL. A thesis is a reading "
     "of the whole work."),
    ("what-a-picture-actually-shows", False, "NOT MECHANICAL, AND MEASURED. "
     "fairview_theirs_vs_ours_finished.jpg was drawn from a prompt asking "
     "for `three nonidentifiable people` and came back with two children in "
     "school uniform at a FAIRVIEW SCHOOL gate. No word gate can see that. "
     "Somebody opens the file."),
)


def enforceable_lines():
    can = [e for e in ENFORCEABLE if e[1]]
    out = ["WHAT THIS GATE ENFORCES MECHANICALLY: %d of %d clauses. The rest "
           "are named below and are NOT claimed."
           % (len(can), len(ENFORCEABLE))]
    for name, mech, why in ENFORCEABLE:
        out.append("  %-38s mechanical=%s  %s" % (name, str(mech).lower(), why))
    out.append("enforceable: mechanical=%d notMechanical=%d total=%d"
               % (len(can), len(ENFORCEABLE) - len(can), len(ENFORCEABLE)))
    return out


# ---------------------------------------------------------------- selftest
def selftest():
    """ACCEPTING CASE FIRST. A validator nothing survives is the expensive
    failure, so the first half of this is the live corpus's own innocent
    lines plus the three things D18 explicitly PERMITS, and only then the
    synthetic guilty ones.

    The accepting fixtures are REAL STRINGS from the live banks and the live
    brand bible and the live prompt library, which means doing the work this
    gate asks for cannot break the gate: rewrite a pub line and the fixture
    here is still the clean part of the sentence. The rejecting fixtures are
    synthetic and name nothing that exists, per the standing rule.
    """
    ok = fail = 0
    lines = []

    def check(label, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
            lines.append("  ok      " + label)
        else:
            fail += 1
            lines.append("  FAILED  " + label)

    lines.append("ACCEPTING HALF A, what D18 PERMITS. A gate that crept into "
                 "flagging these would fail here rather than in a writer's "
                 "face.")
    for what, line in PERMITTED:
        hits = scan(line)
        check("%-10s passes: %s" % (what, line[:64]), hits == [])
        if hits:
            lines.append("          matched %s" % (hits,))

    lines.append("ACCEPTING HALF B, %d innocent fixture(s): ordinary period "
                 "British that must pass." % len(UNDER_CAUGHT))
    for word, why, line in UNDER_CAUGHT:
        hits = scan(line)
        check("'%s' passes (%s): %s" % (word, why[:38], line[:56]), hits == [])
        if hits:
            lines.append("          matched %s" % (hits,))

    lines.append("ACCEPTING HALF C, THE LIVE REPO AS THE FIXTURE.")
    bible = REPO / "content" / "brands" / "brand-bible-v1.json"
    if bible.exists():
        doc = json.loads(bible.read_text(encoding="utf-8"))
        pub = [b for b in doc.get("brands", []) if b.get("kind") == "pub"]
        check("the live brand bible's pub entry exists and is clean, so "
              "'pubs may exist as places' is proved on live data",
              len(pub) == 1 and not scan(" ".join(
                  str(v) for v in pub[0].values() if isinstance(v, str))))
    else:
        check("the live brand bible was readable", False)

    prompts = REPO / "tools" / "imagegen" / "prompts.json"
    if prompts.exists():
        doc = json.loads(prompts.read_text(encoding="utf-8"))
        cr = doc.get("content_rules") or {}
        clause = cr.get("rules_clause", "")
        toks = [t.lower() for t in cr.get("forbidden_tokens") or []]
        check("the live rules_clause carries the content clause",
              CLAUSE in clause)
        # MEASURED, NOT ASSUMED: the clause rides in the POSITIVE prompt and
        # imagegen scans that prompt against forbidden_tokens, so a token
        # list containing the clause's own words would refuse every prompt
        # in the library. This is why "alcohol", "gambling" and "child" are
        # clause words and "beer", "bingo" and "satchel" are tokens.
        self_trip = [t for t in toks if t and t in clause.lower()]
        check("no forbidden token is a substring of the clause itself, so "
              "the clause cannot refuse every prompt in the library (found "
              "%d)" % len(self_trip), not self_trip)
        # THE CLAUSE NAMES WHAT IT FORBIDS, so it fires on its own rules by
        # design. What must hold is that appending it to a CLEAN item's
        # prompt does not turn that item into a violation: exempt by
        # identity, the way imagegen already exempts it.
        raw = "a galvanised steel dustbin against a soot brick wall"
        composed = raw + ", " + clause
        check("appending the clause to a clean prompt leaves it clean, so "
              "the clause instructs without refusing every item",
              scan(composed, channel="prompt", exempt=(clause,)) == [])
        check("and WITHOUT the exemption the same prompt would report %d "
              "false hit(s), which is what the exemption is for"
              % len(scan(composed, channel="prompt")),
              len(scan(composed, channel="prompt")) > 0)
    else:
        check("the live prompt library was readable", False)

    check("the slur list loaded and is not empty (%s)" % SLUR_NOTE,
          bool(SLURS))
    live = run_gate()
    check("the live corpus opens: stringsScanned is not zero (%d)"
          % live["strings"], live["strings"] > 0)
    check("the live corpus has no unreadable source (%d)"
          % len(live["missing"]), not live["missing"])
    check("every channel in the registry opened at least one file, so no "
          "channel reports a zero it did not earn",
          not any(NOTHING in l for l in by_channel(live)))

    lines.append("REJECTING HALF, synthetic fixtures naming nothing that "
                 "exists in this repo.")
    guilty = (
        ("a pint of bitter and a packet of crisps", "pint"),
        ("Mickey kept the SYNTHETICALE on the left", None),
        ("two bottles of whisky behind the counter", "whisky"),
        ("he was drunk by four and drunker by six", "drunk"),
        ("I'd want it from somebody sober", "sober"),
        ("I was drinking on my break", "drinking"),
        ("she found a betting slip in his trousers", "bettingslip"),
        ("a gambling debt he has not told his wife about", "gambling"),
        ("the fruit machine in the corner ate his wages", "fruitmachine"),
        ("bingo every night at the SYNTHETICHALL", "bingo"),
        ("a half of stout, when you find the glasses", "stout"),
        ("your round, by my arithmetic", "aroundofdrinks"),
        ("brass pump clips along the counter", "pump"),
        ("he put a fiver on the horses at the bookies", "bookie"),
        ("the lads had an accumulator on four races", "accumulator"),
        ("a beer firkin by the cellar flap", "firkin"),
        # D18
        ("two children on the steps outside the SYNTHETICGATE", "child"),
        ("a kid ran off up the SYNTHETICROAD", "kid"),
        ("she left the pram outside the SYNTHETICSHOP", "pram"),
        ("the school yard was full at half nine", "schoolchild"),
        ("a leather school satchel on the step", "satchel"),
        ("a little girl in a red coat", "littlechild"),
        ("a witness aged nine, they reckon", "underage"),
        ("a 12-year-old saw the whole thing", "underage"),
        ("he was shooting up behind the SYNTHETICWORKS", "druguse"),
        ("a wrap of SYNTHETICPOWDER changed hands", "druguse"),
        ("heroin came through the SYNTHETICDOCK", "hardsubstance"),
        ("a brothel above the SYNTHETICSHOP", "prostitution"),
        ("she was on the game by then", "prostitution"),
        ("they tortured him in the SYNTHETICYARD", "torture"),
    )
    for text, want in guilty:
        hits = scan(text)
        ids = {h[0] for h in hits}
        if want is None:
            check("synthetic word with no rule is NOT invented as a hit: %s"
                  % text[:52], hits == [])
        else:
            check("caught %-16s in: %s" % (want, text[:46]), want in ids)

    # THE SLUR REJECTING FIXTURE, and it is deliberately not spelled here.
    # The list is the fixture: every word in it must fire, and the check
    # prints the COUNT rather than the words.
    fired = sum(1 for w in SLURS or [] if "slur" in {h[0] for h in scan(
        "the SYNTHETICMAN called him a " + w + " and walked off")})
    check("every one of the %d slurs fires in a sentence (fired %d)"
          % (len(SLURS or []), fired), SLURS and fired == len(SLURS))

    # Every DECIDED over-catch must still fire, or the list is decoration.
    fires = {
        "stout": "a half of stout", "gambling": "it was a gamble",
        "sober": "stone sober", "drinking": "drinking tea",
        "bingo": "bingo night", "jackpot": "hit the jackpot",
        "raffle": "a raffle at the chapel", "blackjack": "a hand of blackjack",
        "boozer": "down the boozer", "teetotal": "he is teetotal",
        "optic": "an optic on the shelf", "accumulator": "an accumulator",
        "dice": "a game of dice",
    }
    for rid in DECIDED:
        hits = {h[0] for h in scan(fires[rid])}
        check("DECIDED over-catch '%s' still fires on %r" % (rid, fires[rid]),
              rid in hits)

    lines.append("INSTRUMENT HALF: the gate's own zero, its caps, its "
                 "channels and its baseline key.")
    empty = {"rows": [], "opened": [], "missing": [], "exempted": [],
             "strings": 0, "fresh": [], "baselined": [], "stale": [],
             "specs": [], "clauseProblems": []}
    check("a run that read nothing prints the words '%s'" % NOTHING,
          NOTHING in done_line(empty))
    check("a run that read nothing exits 2, never 0", verdict(empty) == 2)
    check("a channel that opened no file says '%s' rather than zero hits"
          % NOTHING, all(NOTHING in l for l in by_channel(empty)))
    check("a cap announces when it bites",
          "(+3 more not shown)" in _cap(list("abcdefgh"), 5))
    check("a cap that does not bite says nothing", _cap(["a", "b"], 5) == "a, b")
    check("done-line values carry no spaces",
          all(" " not in part.split("=", 1)[1]
              for part in done_line({**empty, "strings": 1}).split()
              if "=" in part))
    check("the baseline key changes when the text changes by one character",
          _key("f", "r", "a line") != _key("f", "r", "a line."))
    check("the baseline key is the same for the same text at two locators, "
          "so one bark repeated 49 times is one entry",
          _key("f", "r", "same") == _key("f", "r", "same"))
    check("the prompt channel runs the substring tokens as well as the "
          "word rules: 'brass pump handles' is caught on a prompt",
          {h[0] for h in scan("brass pump handles along the counter",
                              channel="prompt")} and
          not scan("brass pump handles along the counter"))
    check("--enforceable claims fewer clauses than it lists",
          0 < len([e for e in ENFORCEABLE if e[1]]) < len(ENFORCEABLE))

    lines.append("content-gate selftest: %d ok, %d failed, %d fixture(s) total"
                 % (ok, fail, ok + fail))
    return ok, fail, lines


def baseline_write(res):
    """Rewrite BASELINE in this file from the current run.

    Deliberately a SEPARATE invocation somebody has to type, and it prints
    every line it writes. A gate that silently absorbed its own findings
    would be a ratchet with no teeth.
    """
    keys = sorted({_key(h[1], h[3], h[6])
                   for h in res["fresh"] + res["baselined"]})
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    start = src.index("BASELINE = (")
    end = src.index("\n\n", start)
    block = "BASELINE = (\n" + "".join(
        '    "%s",\n' % k for k in keys) + ")"
    pathlib.Path(__file__).write_text(src[:start] + block + src[end:],
                                      encoding="utf-8")
    return len(keys)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true",
                    help="every hit and every per-file denominator")
    ap.add_argument("--series", action="store_true",
                    help="per-rule hit counts over the live corpus")
    ap.add_argument("--enforceable", action="store_true",
                    help="what this gate can and cannot check mechanically")
    ap.add_argument("--selftest", action="store_true",
                    help="accepting case first, then rejecting")
    ap.add_argument("--baseline-write", action="store_true",
                    help="rewrite BASELINE in this file from this run")
    a = ap.parse_args()

    # A correct run that ends in a BrokenPipeError traceback costs twenty
    # minutes before anybody notices it worked.
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass

    if a.enforceable:
        for l in enforceable_lines():
            print(l)
        return 0

    if a.selftest:
        ok, fail, lines = selftest()
        for l in lines:
            print(l)
        return 5 if fail else 0

    res = run_gate()
    if a.series:
        for l in series(res):
            print(l)
        return 2 if res["strings"] == 0 else 0

    if a.baseline_write:
        n = baseline_write(res)
        print("content-gate: wrote %d baseline entry(ies), stamped %s"
              % (n, BASELINE_STAMPED))
        for h in res["fresh"]:
            print(hit_line(h))
        return 0

    for l in report(res, full=a.report):
        print(l)
    print(done_line(res))
    return verdict(res)


if __name__ == "__main__":
    sys.exit(main())
