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

	std::string SummaryId, SummaryText, Speaker, Why, ReplyId, ReplyText, ReplyWhy;
	int Variants = 0, ReplyVariants = 0;
	const bool bPickedSummary = LedgerCrime::BankPick(Bank, "witness_summary", 3, Seed,
		SummaryId, SummaryText, Speaker, Variants, Why);
	Loud(bPickedSummary, "the bank carries a witness_summary at rung 3: " + Why);
	const bool bPickedReply = LedgerCrime::BankPick(Bank, "overheard", 3, Seed,
		ReplyId, ReplyText, Speaker, ReplyVariants, ReplyWhy);
	Loud(bPickedReply, "the bank carries an overheard reply at rung 3: " + ReplyWhy);
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
	// the bank's own words as the summary, exactly as ResolveAndFile files it.
	Mill.Witness("w1", Fact("player", "broke_a_window", "east_parade_glass0"),
	             SummaryText, /*bSensitive=*/false, Now, 0.94, /*bIndelible=*/false);
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

	std::printf("crime-probe-test: %d check(s), %d failure(s) over 1 live bank, "
	            "%d selftest row(s)\n", gChecks, gFailed, S.Checks);
	return gFailed == 0 ? 0 : 2;
}
