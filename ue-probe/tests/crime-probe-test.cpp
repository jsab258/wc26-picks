// THE CRIME PROBE'S OWN DECISIONS, COMPILED AND RUN IN THE CONTAINER.
//
// WHY THIS EXISTS, and it is a correction rather than an addition. CrimeProbe.h
// says at its top that everything in it is plain C++ over the ported LedgerCore
// headers "so g++ compiles and RUNS it before any dispatch". That was true of
// the header and false of the repository: no binary under ue-probe/tests
// included CrimeProbe.h, so LedgerCrime::Selftest() ran ONLY on Jafar's PC,
// and a decision layer that broke would have been found by a 25-minute round
// trip. Measured 2026-09-08, before this file: `grep -rn CrimeProbe.h ue-probe/`
// returned two hits, both Unreal translation units. This is the gate that
// makes the header's sentence true, and ledger/verify.py runs it as the fourth
// ue-probe binary.
//
// TWO THINGS ARE CHECKED, in this order.
//
// 1. LedgerCrime::Selftest(), the live decision path on fixed inputs, which is
//    the same call CrimeProbe.cpp makes at Start() so its result reaches the
//    verdict. Its check count is reported here, so a row added there is a
//    number that moves here.
// 2. THE OVERHEARD BEAT'S DATA PATH ON THE LIVE BANK, which is this project's
//    rule for a tool that checks the project itself: the accepting fixture is
//    the committed file, so doing the work the tool prompts can never break the
//    tool. The real content/dialogue/crime-witness-v1.json is read, the rung-3
//    row is picked by the real seed, a two-agent mill passes it at the real tie
//    and hop decay, and StreetVoice.Exchange composes what the two of them say.
//    The composed sentence is PRINTED, because a green number is not the
//    artifact and the prose is the thing a reader has to judge.
// 3. ALL TWELVE witness_summary ROWS, SPLICED INTO BOTH FRAMES A Rumor.Summary
//    is spliced into at run time, and printed. Queue 157 added a `clause` to
//    each row because the bank held only finished first-person sentences and
//    both consumers splice: the composed telling and the heard memory. NO
//    SHAPE CHECK CAN SEE PERSON, so the twelve lines are written out for a
//    reader and the counts beside them are the cheap half.
//
// WHAT IT CANNOT SEE, said plainly: nothing here proves an actor spawned, that
// a pawn stood in earshot, that a frame was captioned or that a verdict reached
// a commit. Those are the run's business and the verdict's keys are how they
// are read.
//
//   g++ -std=c++11 -O1 -Wall -I ue-probe/Source/LedgerProbe/Public
//       -I ue-probe/tests/unreal-shim -o /tmp/crime-probe-test
//       ue-probe/tests/crime-probe-test.cpp
//       ue-probe/Source/LedgerProbe/Private/Perception.cpp
//   /tmp/crime-probe-test content/dialogue/crime-witness-v1.json
#include "CrimeProbe.h"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

using namespace LedgerCore;

static int gChecks = 0;
static int gFailed = 0;

static void Check(bool bOk, const std::string& What)
{
	++gChecks;
	if (!bOk) { ++gFailed; std::printf("  FAIL %s\n", What.c_str()); }
}

static void Loud(bool bOk, const std::string& What)
{
	Check(bOk, What);
	std::printf("  %s %s\n", bOk ? "ok  " : "FAIL", What.c_str());
}

// DOES THIS TEXT SPEAK IN THE FIRST PERSON. Word-boundary over letters and
// apostrophes, lowercased, so "I've" and "me" are caught and "him" is not.
//
// IT IS A SNIFF AND NOT A PERSON CHECK, and the difference matters: it can
// prove that a spliced memory still says "me", which is the fault that shipped
// in production/d1-probe/ue-crime-memory-n2.md, and it cannot prove that a
// third-person clause refers to the right third person. Both outcomes are
// exercised below, the accepting case first, with the shipped string as the
// planted case so the guard is known to be able to fire.
static bool SaysFirstPerson(const std::string& S)
{
	static const char* kWords[] = { "i", "i'd", "i'll", "i'm", "i've", "me", "my",
	                                "mine", "myself", "we", "us", "our" };
	std::string Word;
	for (std::string::size_type I = 0; I <= S.size(); ++I)
	{
		const char C = I < S.size() ? S[I] : ' ';
		if ((C >= 'a' && C <= 'z') || (C >= 'A' && C <= 'Z') || C == '\'')
		{
			Word += (C >= 'A' && C <= 'Z') ? (char)(C - 'A' + 'a') : C;
			continue;
		}
		if (!Word.empty())
		{
			for (std::size_t K = 0; K < sizeof(kWords) / sizeof(kWords[0]); ++K)
			{
				if (Word == kWords[K]) { return true; }
			}
			Word.clear();
		}
	}
	return false;
}

// THE LIMIT THAT TRAVELS WITH THE NUMBER, A7 of the ruling of 2026-09-09.
// The comment above states it correctly and the number is printed 280 lines
// below, where no comment travels with it: a reader meeting
// memoriesInFirstPerson=0/12 meets it in a verify footer or a CI log. This
// project's own convention already answers that, propBurialStat and
// overheardSummaryShapeRule both carrying their limit inside the printed
// value, so the limit goes on the line.
static const char* kSniffLimit =
	"sniff=word-boundary-over-the-text-after-the-first-that"
	"/catches-me-and-I've-and-not-him"
	"/CANNOT-tell-whether-a-third-person-clause-names-the-right-third-person"
	"/over=memories-ACTUALLY-SNIFFED-never-rows-picked";

// AND ITS DENOMINATOR IS THE MEMORIES SNIFFED, NOT THE ROWS READ. The old
// denominator was RowsRead, which is bank rows PICKED: a row whose mill passed
// nothing leaves Memory at nothing-measured, AfterTheThat returns the whole
// string, the sniff says false, and an unexamined row counted as clean. Rule 3b
// asks what THIS denominator counted, so it counts what was sniffed, and a row
// that filed nothing reads as the words and never as a pass.
static std::string PersonSniffValue(int InFirstPerson, int InSniffed)
{
	char B[360];
	if (InSniffed <= 0)
	{
		std::snprintf(B, sizeof(B), "nothing-measured/0-memories-were-sniffed/%s",
		              kSniffLimit);
		return std::string(B);
	}
	std::snprintf(B, sizeof(B), "%d/%d/%s", InFirstPerson, InSniffed, kSniffLimit);
	return std::string(B);
}

// The spliced half of a heard memory: everything after the FIRST " that ",
// which is the end of Gossip.h 586's fixed prefix "I heard from <name> that ".
// Taking the first occurrence matters, because several clauses contain "that"
// themselves and the last one would cut the clause in half.
static std::string AfterTheThat(const std::string& Memory)
{
	const std::string::size_type At = Memory.find(" that ");
	return At == std::string::npos ? Memory : Memory.substr(At + 6);
}

int main(int argc, char** argv)
{
	const char* BankPath = argc > 1 ? argv[1] : "content/dialogue/crime-witness-v1.json";

	// ---- 1. the decision layer's own selftest ---------------------------
	const LedgerCrime::SelftestResult S = LedgerCrime::Selftest();
	// NOT THE WORDS "check(s), N failure" ON THIS LINE, DELIBERATELY.
	// ledger/verify.py sums every line matching that shape, and these rows are
	// already inside this binary's own total below: the first wiring of this
	// file reported 274 checks for 147, which is the double count an
	// instrument's summary line must never produce.
	std::printf("  CrimeProbe.h selftest rows: %d run, %d failed, first=%s\n",
	            S.Checks, S.Failed, S.FirstFailure.c_str());
	Check(S.Checks > 0, "the crime selftest ran at all");
	Check(S.Failed == 0, "the crime selftest is green: " + S.FirstFailure);
	// Its rows count here too, so adding one there moves the number verify.py
	// prints rather than hiding inside a single pass/fail.
	gChecks += S.Checks;
	gFailed += S.Failed;

	// ---- 2. the overheard beat, on the committed bank --------------------
	std::ifstream In(BankPath);
	std::stringstream Buf;
	Buf << In.rdbuf();
	const std::string Bank = Buf.str();
	Loud(!Bank.empty(), std::string("the live bank was read: ") + BankPath);
	if (Bank.empty())
	{
		std::printf("crime-probe-test: %d check(s), %d failure(s), bank=UNREADABLE\n",
		            gChecks, gFailed);
		return 2;
	}

	// The run's own inputs: D1 12:00, so the seed is 43 (GossipDirector.cs 586).
	const GameTime Now(1, 12, 0);
	const int Seed = LedgerCrime::Seed(Now);
	Loud(Seed == 43, "the seed at D1 12:00 is 43");

	std::string SummaryId, SummaryText, SummaryClause, Speaker, Why;
	std::string ReplyId, ReplyText, ReplyClause, ReplyWhy;
	int Variants = 0, ReplyVariants = 0;
	const bool bPickedSummary = LedgerCrime::BankPick(Bank, "witness_summary", 3, Seed,
		SummaryId, SummaryText, SummaryClause, Speaker, Variants, Why);
	Loud(bPickedSummary, "the bank carries a witness_summary at rung 3: " + Why);
	const bool bPickedReply = LedgerCrime::BankPick(Bank, "overheard", 3, Seed,
		ReplyId, ReplyText, ReplyClause, Speaker, ReplyVariants, ReplyWhy);
	Loud(bPickedReply, "the bank carries an overheard reply at rung 3: " + ReplyWhy);
	// TWO STRINGS OFF ONE ROW, queue 157: the sentence she says and the clause
	// the mill files. The third line is the one the defect was measured on.
	std::printf("  row %s says    : %s\n", SummaryId.c_str(), SummaryText.c_str());
	std::printf("  row %s files   : %s\n", SummaryId.c_str(), SummaryClause.c_str());
	Loud(LedgerCrime::ClauseShape(SummaryClause) == "clause",
	     "the rung-3 row's clause is spliceable: " + LedgerCrime::ClauseShape(SummaryClause));
	Loud(SummaryClause != SummaryText, "and it is not the sentence she speaks");
	Loud(ReplyClause.empty(),
	     "an overheard row carries no clause, because nothing splices it");
	Loud(SummaryId == "cw-ws-r3-02" && ReplyId == "cw-ov-r3-02",
	     "the two ids are the pair run 32 measured: " + SummaryId + "," + ReplyId);

	// A TWO-AGENT MILL AT THE PROBE'S OWN NUMBERS, so the confidence the
	// exchange composes at is the one the mill produced and not one typed here.
	std::shared_ptr<SocialGraph> Graph = std::make_shared<SocialGraph>();
	Graph->Link("w1", "n2", LedgerCrime::kTie);
	GossipMill Mill(Graph);
	GossiperPtr W1 = std::make_shared<Gossiper>("w1", "the shopkeeper",
		std::shared_ptr<MemoryStore>(), std::shared_ptr<KnowledgeBase>(), "day");
	GossiperPtr N2 = std::make_shared<Gossiper>("n2", "the lad in the yard",
		std::shared_ptr<MemoryStore>(), std::shared_ptr<KnowledgeBase>(), "day");
	Mill.Add(W1);
	Mill.Add(N2);
	// The certainty the resolver measures for the accepting vantage, 0.94, and
	// THE ROW'S CLAUSE as the summary, through the same header call
	// ResolveAndFile uses, so what is filed here is what the probe files.
	std::string FiledWhy;
	const std::string Filed = LedgerCrime::SummaryToFile(SummaryId, SummaryClause, FiledWhy);
	Loud(Filed == SummaryClause && FiledWhy == "none",
	     "what the probe files is the clause, not the sentence: " + FiledWhy);
	Mill.Witness("w1", Fact("player", "broke_a_window", "east_parade_glass0"),
	             Filed, /*bSensitive=*/false, Now, 0.94, /*bIndelible=*/false);
	const std::vector<GossipEvent> Events = Mill.Tick(Now, GossipMill::TogetherFn(0));
	RumorPtr Carried;
	for (std::vector<GossipEvent>::size_type I = 0; I < Events.size(); ++I)
	{
		if (Events[I].FromId == "w1" && Events[I].ToId == "n2") { Carried = Events[I].RumorRef; }
	}
	Loud(Carried.get() != 0, "the mill passed one rumour from w1 to n2");
	if (!Carried)
	{
		std::printf("crime-probe-test: %d check(s), %d failure(s), mill=PASSED-NOTHING\n",
		            gChecks, gFailed);
		return 2;
	}
	Loud(LedgerCrime::F2(Carried->Confidence) == "0.45",
	     "it arrives at 0.94*0.6*0.8 = " + LedgerCrime::F2(Carried->Confidence));
	Loud(Carried->Hops == 1, "one hop");

	const LedgerCrime::ComposedExchange C =
		LedgerCrime::ComposeOverheard(Carried, W1, N2, Seed, SummaryText, ReplyText);
	std::printf("  composed telling: %s\n", C.TellText.c_str());
	std::printf("  composed answer : %s\n", C.ReplyText.c_str());
	std::printf("  the pick would have said: %s\n", C.PickedReplyText.c_str());
	std::printf("  carried summary shape: %s\n",
	            LedgerCrime::SummaryShape(C.CarriedSummary).c_str());
	Loud(C.Mode == "COMPOSED", "the beat composes rather than picking: " + C.Mode);
	Loud(C.TellText != SummaryText,
	     "the telling is not the bank row it was built from");
	Loud(C.ReplyText != ReplyText,
	     "the answer is not the bank's overheard row either");
	Loud(C.bCarriesSummary, "the composed telling carries the words the mill carried");
	Loud(C.BeatsStaged == 2 && C.BeatsComposed == 1 && C.BeatsPicked == 1,
	     "one of two beats is composed and the other is a literal from a disposition band");
	Loud(C.TellBand == "confidence-below-0.50",
	     "a rumour one hop old speaks from the whisper band: " + C.TellBand);

	// THE VERDICT LINES THEMSELVES, because the acceptance is a string on a
	// line and not a field in a struct.
	LedgerCrime::OverheardReading O;
	O.Events = 1;
	O.IdRung = 3;
	O.SummaryId = SummaryId;
	O.ReplyId = ReplyId;
	O.SeedValue = Seed;
	O.Variants = Variants;
	O.VariantPicked = LedgerCrime::VariantIndex(Seed, Variants);
	O.bBankRead = true;
	O.BankPath = BankPath;
	O.Reply = C;
	const std::string Line = LedgerCrime::OverheardLine(O);
	const std::string Text = LedgerCrime::OverheardTextLine(O);
	std::printf("  %s\n", Line.c_str());
	std::printf("  %s\n", Text.c_str());
	Loud(Line.find("overheardReplyMode=COMPOSED/") != std::string::npos,
	     "the verdict names which, in words");
	Loud(Line.find("overheardBeatsComposed=1/2") != std::string::npos
	     && Line.find("overheardBeatsPicked=1/2") != std::string::npos,
	     "with the count of beats in each mode over the beats staged");
	Loud(Line.find("overheardLineIds=cw-ws-r3-02,cw-ov-r3-02") != std::string::npos,
	     "and keeps the bank ids run 32 measured");

	// NO VALUE ON EITHER LINE MAY CARRY A SPACE. Every reader of this
	// project's key=value lines splits on whitespace and truncates in silence,
	// so the line is walked token by token rather than trusted.
	int Tokens = 0, Empty = 0;
	const std::string Both = Line + " " + Text;
	std::string Tok;
	std::stringstream Split(Both);
	while (Split >> Tok)
	{
		++Tokens;
		const std::string::size_type Eq = Tok.find('=');
		if (Eq == std::string::npos || Eq + 1 >= Tok.size()) { ++Empty; }
	}
	std::printf("    verdictTokens=%d emptyOrKeyless=%d/%d\n", Tokens, Empty, Tokens);
	Loud(Tokens > 30 && Empty == 0, "every token on both lines is a key=value with a value");

	// ---- 3. ALL TWELVE ROWS, SPLICED BOTH WAYS, PRINTED -------------------
	//
	// NO SHAPE CHECK CAN SEE PERSON, which is why this section prints prose
	// rather than counting passes. A clause can be lowercase with no interior
	// stop and still say "me" about the witness inside a third party's memory:
	// that is the fault queue 157 was opened for, it passed every mechanical
	// rule in CrimeProbe.h, and it shipped. So all twelve rows are spliced both
	// ways and written out for a reader to judge, and the counts underneath are
	// the cheap half.
	//
	// FRAME A is the composed telling, built by the ported StreetVoice. The
	// three seeds 15, 29 and 43 all satisfy seed % 14 == 1, so the whisper
	// band's template is HELD CONSTANT ("You hear all sorts. {What},
	// apparently.") while seed % 3 moves the variant over 0, 2 and 1 in turn.
	// The twelve lines therefore differ by their own words and not by the frame
	// around them, which is what makes them comparable by eye.
	//
	// FRAME B is the heard memory, appended by the real GossipMill at Gossip.h
	// 586. The string printed is the MemoryEvent text that
	// production/d1-probe/ue-crime-memory-n2.md carries after its timestamp.
	//
	// AND THE PAIRED REPLY AT THE SAME INDEX BESIDE EACH SUMMARY, A6 of the
	// ruling of 2026-09-09. THE BANK'S PICK IS BY INDEX: variant k of
	// `overheard` answers variant k of `witness_summary` at the same rung and
	// the same seed. On 8 September the three rung-2 pairs were every one of
	// them rotated, so the reply about a limp and a cap deflated a summary that
	// had given a donkey jacket, and nothing caught it: the spec listed the
	// twelve summaries and the twelve replies as two bundles of three, and
	// three lines read in two groups read as correct while the same three read
	// as PAIRS do not. The checklist shaped the check. At seeds 15, 29 and 43
	// the index goes 0, 2 and 1, so all three variants of every rung are
	// visited here and that fault would have been one screen wide.
	const int FrameSeeds[3] = { 15, 29, 43 };
	int RowsRead = 0, RowsWithClause = 0, ClauseShaped = 0, FramesComposed = 0, FirstPerson = 0;
	// THE SNIFF'S OWN DENOMINATOR, A7: memories actually sniffed, which is not
	// the same set as rows picked.
	int MemoriesSniffed = 0;
	// THE PAIRING'S OWN DENOMINATORS, counted separately because a rung with no
	// reply row and a rung whose reply is misaligned are different faults.
	int RepliesPaired = 0, PairIdsAligned = 0, PairVariantsAgree = 0;
	const int RowsExpected = 12;
	std::printf("  ---- the twelve witness_summary rows, spliced both ways, "
	            "each with the reply it is paired with BY INDEX ----\n");
	for (int Rung = 1; Rung <= 4; ++Rung)
	{
		for (int V = 0; V < 3; ++V)
		{
			const int RowSeed = FrameSeeds[V];
			std::string RId, RText, RClause, RSpk, RWhy;
			int RVariants = 0;
			if (!LedgerCrime::BankPick(Bank, "witness_summary", Rung, RowSeed,
			                           RId, RText, RClause, RSpk, RVariants, RWhy))
			{
				std::printf("    rung %d seed %d: NO ROW (%s)\n", Rung, RowSeed, RWhy.c_str());
				continue;
			}
			++RowsRead;
			if (!RClause.empty()) { ++RowsWithClause; }
			const std::string Shape = LedgerCrime::ClauseShape(RClause);
			if (Shape == "clause") { ++ClauseShaped; }

			// THE REPLY THE RUNTIME WOULD PAIR WITH IT: same context pair, same
			// rung, same seed, so the index is the run's own arithmetic and not
			// one typed here.
			std::string PId, PText, PClause, PSpk, PWhy;
			int PVariants = 0;
			const bool bPaired = LedgerCrime::BankPick(Bank, "overheard", Rung, RowSeed,
			                                           PId, PText, PClause, PSpk,
			                                           PVariants, PWhy);
			std::string PairWord;
			if (bPaired)
			{
				++RepliesPaired;
				PairWord = LedgerCrime::PairIdShape(RId, PId);
				if (PairWord.compare(0, 7, "aligned") == 0) { ++PairIdsAligned; }
				if (PVariants == RVariants) { ++PairVariantsAgree; }
			}
			else
			{
				PairWord = "no-reply-row/" + PWhy;
				PText = "nothing-measured";
				PId = "none";
			}

			// A FRESH MILL PER ROW. One mill across twelve rows would keep only
			// the strongest rumour per topic (Gossip.h's BestOfValue guard), so
			// rows two to twelve would pass nothing and this printout would
			// silently be one row long with eleven "nothing-measured" lines.
			std::shared_ptr<SocialGraph> RowGraph = std::make_shared<SocialGraph>();
			RowGraph->Link("w1", "n2", LedgerCrime::kTie);
			GossipMill RowMill(RowGraph);
			GossiperPtr RowW1 = std::make_shared<Gossiper>("w1", "the shopkeeper",
				std::shared_ptr<MemoryStore>(), std::shared_ptr<KnowledgeBase>(), "day");
			GossiperPtr RowN2 = std::make_shared<Gossiper>("n2", "the lad in the yard",
				std::shared_ptr<MemoryStore>(), std::shared_ptr<KnowledgeBase>(), "day");
			RowMill.Add(RowW1);
			RowMill.Add(RowN2);
			std::string RowWhy;
			RowMill.Witness("w1", Fact("player", "broke_a_window", "east_parade_glass0"),
			                LedgerCrime::SummaryToFile(RId, RClause, RowWhy),
			                /*bSensitive=*/false, Now, 0.94, /*bIndelible=*/false);
			const std::vector<GossipEvent> RowEvents = RowMill.Tick(Now, GossipMill::TogetherFn(0));
			RumorPtr RowCarried;
			for (std::vector<GossipEvent>::size_type K = 0; K < RowEvents.size(); ++K)
			{
				if (RowEvents[K].FromId == "w1" && RowEvents[K].ToId == "n2")
				{
					RowCarried = RowEvents[K].RumorRef;
				}
			}
			std::string Memory = "nothing-measured";
			if (RowN2->Memory && !RowN2->Memory->Events.empty())
			{
				Memory = RowN2->Memory->Events.back().Text;
			}
			std::string Telling = "nothing-measured";
			if (RowCarried)
			{
				const LedgerCrime::ComposedExchange Row = LedgerCrime::ComposeOverheard(
					RowCarried, RowW1, RowN2, RowSeed, RText, ReplyText);
				Telling = Row.TellText;
				if (Row.Mode == "COMPOSED") { ++FramesComposed; }
			}
			// THE SNIFF, AND WHAT IT WAS TAKEN OVER. A row that filed no
			// memory is NOT sniffed and NOT clean: it says the words.
			const char* SniffWord = "nothing-measured/no-memory-filed";
			if (Memory != "nothing-measured")
			{
				++MemoriesSniffed;
				if (SaysFirstPerson(AfterTheThat(Memory)))
				{
					++FirstPerson;
					SniffWord = "FIRST-PERSON";
				}
				else { SniffWord = "third-person"; }
			}
			// PER-SAMPLE NUMBERS ON THE SAMPLE LINE. The whole-run counts and
			// the two stat strings are on the done line below, once.
			// BOTH SIDES OF EVERY PAIRED READING, IN ONE ORDER: summary first,
			// reply second, everywhere on this line. Two indices and two
			// moduli, because the pick is only by one index while they agree,
			// and a single number here would hide the moment they stop.
			std::printf("    pair=%s..%s/summary..reply rung=%d seed=%d"
			            " variantIndex=%d..%d variants=%d..%d"
			            " pairIds=%s shape=%s sniff=%s\n",
			            RId.c_str(), PId.c_str(), Rung, RowSeed,
			            LedgerCrime::VariantIndex(RowSeed, RVariants),
			            LedgerCrime::VariantIndex(RowSeed, PVariants),
			            RVariants, PVariants, PairWord.c_str(), Shape.c_str(), SniffWord);
			// THE PAIR ITSELF, ON TWO ADJACENT LINES, which is the whole of A6:
			// what she says and what he answers, at one index, where a reply
			// that deflates a mark she never gave cannot hide in a bundle.
			std::printf("      she says: %s\n", RText.c_str());
			std::printf("      he says : %s\n", PText.c_str());
			std::printf("      telling : %s\n", Telling.c_str());
			std::printf("      memory  : %s\n", Memory.c_str());
		}
	}
	// THE DONE LINE FOR THIS PRINTOUT: WHOLE-RUN NUMBERS ONLY, each with the
	// denominator it was taken over, and the two limits once each.
	std::printf("    clauseRowsRead=%d/%d clauseRowsWithClause=%d/%d clauseShapeIsClause=%d/%d"
	            " tellingsComposed=%d/%d repliesPaired=%d/%d pairIdsAligned=%d/%d"
	            " pairVariantsAgree=%d/%d memoriesInFirstPerson=%s"
	            " clausePairIdStat=%s\n",
	            RowsRead, RowsExpected, RowsWithClause, RowsRead, ClauseShaped, RowsRead,
	            FramesComposed, RowsRead, RepliesPaired, RowsRead,
	            PairIdsAligned, RepliesPaired, PairVariantsAgree, RepliesPaired,
	            PersonSniffValue(FirstPerson, MemoriesSniffed).c_str(),
	            LedgerCrime::PairIdStat());
	Loud(RowsRead == RowsExpected, "all twelve witness_summary rows were read off the live bank");
	Loud(RowsWithClause == RowsRead && RowsRead > 0, "every row read carries a clause");
	Loud(ClauseShaped == RowsRead && RowsRead > 0,
	     "every clause is lowercase-initial with no interior and no trailing full stop");
	Loud(FramesComposed == RowsRead && RowsRead > 0,
	     "every one of them composed a telling rather than refusing");
	Loud(RepliesPaired == RowsRead && RowsRead > 0,
	     "every summary row read has a reply row at the same rung, so every pair "
	     "above is a pair and not a summary beside a blank");
	Loud(PairIdsAligned == RepliesPaired && RepliesPaired > 0,
	     "and every pair's two ids carry the same index, which is the MECHANICAL "
	     "half: what the reply SAYS is the printed half above");
	Loud(PairVariantsAgree == RepliesPaired && RepliesPaired > 0,
	     "with the same variant count in both contexts at every rung, because a "
	     "bank that grows one and not the other moves one pick and not the other");
	// THE ZERO AND ITS DENOMINATOR, ASSERTED AS A PAIR. FirstPerson==0 over
	// nothing sniffed is not a clean result, so the count sniffed is checked
	// against the rows read in its own Loud rather than folded into this one.
	Loud(FirstPerson == 0,
	     "no heard memory speaks in the first person after its 'that', over "
	     + std::string(PersonSniffValue(FirstPerson, MemoriesSniffed)));
	Loud(MemoriesSniffed == RowsRead && RowsRead > 0,
	     "and every row read filed a memory to sniff, so the zero above has the "
	     "rows read as its denominator and not a smaller set");

	// THE REFUSING CASE, PLANTED, because a guard that cannot fire is a
	// ratchet. A witness_summary row with no clause must refuse by name and
	// must never file the sentence instead: filing the sentence is the defect.
	std::string MissingWhy;
	const std::string RefusedSummary = LedgerCrime::SummaryToFile("cw-ws-r3-02", "", MissingWhy);
	std::printf("  a row with no clause files: %s\n", RefusedSummary.c_str());
	Loud(LedgerCrime::IsUnreadableSummary(RefusedSummary),
	     "a missing clause refuses through the sentinel the composer already rejects");
	Loud(MissingWhy == "row-cw-ws-r3-02-has-no-clause-to-splice",
	     "and names the row that was short: " + MissingWhy);
	Loud(RefusedSummary.find(SummaryText) == std::string::npos,
	     "and never falls back to the sentence");
	Loud(SaysFirstPerson("He looked straight at me before he ran"),
	     "the person sniff fires on the string that shipped in ue-crime-memory-n2.md");
	Loud(!SaysFirstPerson(SummaryClause),
	     "and does not fire on the clause that replaced it");
	// AND THE NEVER-RAN CASE OF THE VALUE ITSELF, PLANTED, because a zero over
	// nothing is the one reading this key must never print as clean. Rule 3b.
	const std::string NothingSniffed = PersonSniffValue(0, 0);
	std::printf("  a row that filed nothing prints: memoriesInFirstPerson=%s\n",
	            NothingSniffed.c_str());
	Loud(NothingSniffed.compare(0, 17, "nothing-measured/") == 0
	     && NothingSniffed.find("0-memories-were-sniffed") != std::string::npos,
	     "PLANTED CASE - the person reading with nothing sniffed says the words "
	     "nothing measured and never 0/0");
	Loud(PersonSniffValue(1, 12).compare(0, 5, "1/12/") == 0,
	     "and with something sniffed it is numerator over MEMORIES SNIFFED");
	Loud(NothingSniffed.find(' ') == std::string::npos
	     && PersonSniffValue(0, 12).find(' ') == std::string::npos,
	     "and neither form carries a space, so the limit travels with the number "
	     "through every reader that splits on whitespace");
	Loud(NothingSniffed.find("CANNOT-tell-whether-a-third-person-clause") != std::string::npos,
	     "and both forms carry the limit IN THE VALUE, which is where the reader "
	     "meets the number");

	std::printf("crime-probe-test: %d check(s), %d failure(s) over 1 live bank, "
	            "%d selftest row(s)\n", gChecks, gFailed, S.Checks);
	return gFailed == 0 ? 0 : 2;
}
