// TRANSLITERATION of StreetVoice.Exchange's COMPOSITION, from
// ledger/Assets/Scripts/Core/StreetVoice.cs 131 to 296 plus the five helpers
// it needs (Pick 692, Answer 734, Hash 737, Trim 745, Cap 768).
//
// WHY IT EXISTS, in one sentence from queue 147: the probe's overheard beat
// read a dialogue bank, chose a row by the rung the memory reached and a
// variant by a seed, which is a PICK, and the town's reply was therefore one
// of N pre-written strings. Exchange is the rung above that: the teller's
// sentence is BUILT around the rumour's own Summary, so what the player
// overhears carries the thing that actually happened rather than naming a row
// that happened to be filed.
//
// TRANSLITERATION, NOT REWRITE, exactly as Gossip.h states the method: the C#
// suite is the behavioural definition, so every band, every boundary and every
// character of every line matches its source. The 98 lines of dialogue below
// were EXTRACTED FROM THE C# MECHANICALLY rather than retyped, and all 98 were
// diffed against StreetVoice.cs 146 to 283 for content AND ORDER by the
// director ruling of 2026-09-08, BY READING. NO MACHINE CHECKS THEM YET: there
// is no street_voice scenario in ledger/PerceptionGolden and therefore no
// golden row that would go red if a template changed. Queue 160 owes one row
// per template over two summaries, one a lowercase clause and one opening on a
// proper noun.
//
// SCOPE, queue 147: SpokenLine 43 to 72; Exchange 131 to 296; Pick, Answer,
// Hash, Trim, Cap. OUT OF SCOPE AND NOT HERE, so a reader can tell a missing
// member from a forgotten one: StanceKind, Stance, GazeMetres, Recognition,
// Ambient, ChatterLevel, AmbientEverySeconds, Clamp01 (LedgerCore::Clamp in
// Perception.h is the same arithmetic and is already ported).
//
// THE DEVIATIONS FROM THE C#, NAMED, in the shape the eight of
// game-design/decision-2026-09-08-the-core-port-and-its-eight-deviations.md
// use. Each is also named at its site below.
//
//   9.  THE LINES ARE TEMPLATES WITH {what} AND {What}, RENDERED, where the
//       C# is a compiler-generated concatenation of an interpolated string.
//       The C# source IS template text ($"...{what}..."), so the literals are
//       identical; what differs is that the substitution is a function here.
//       Render is the one piece of logic with no C# counterpart, and every
//       string it can produce is pinned by a golden row emitted by the C#.
//   10. THE THREE-WAY CONFIDENCE CONDITIONAL AND THE FOUR-WAY DISPOSITION
//       CONDITIONAL ARE FACTORED INTO TellBandIndex AND AnswerBandIndex.
//       Exchange calls them, so there is exactly one copy of each boundary,
//       and the probe's verdict can NAME the band that spoke without
//       re-deriving the condition. A second copy of `>= 0.8` in an instrument
//       is how a verdict comes to describe a branch the run did not take.
//   11. AN OPTIONAL ExchangeTrace OUT-PARAMETER. The C# returns the two
//       lines and nothing about how they were chosen. The four-argument
//       Exchange has the C# signature and behaviour; the five-argument one
//       additionally reports which band and which index, because
//       overheardReplyMode has to be a reading rather than a claim. No
//       branch depends on it.
//   12. ASCII-ONLY Trim, Cap AND Hash, which is deviation 4 of the port
//       ruling restated for three more functions: a C# char is a UTF-16 unit
//       and a C++ std::string iterates bytes, char.IsLower and
//       ToUpperInvariant know every alphabet and these know twenty-six
//       letters. Measured 2026-09-08: 0 non-ASCII bytes in
//       content/dialogue/crime-witness-v1.json (1 file examined), which is
//       the only producer of a Summary this run can compose from. The day a
//       non-ASCII summary enters a bank the mill reads, this and
//       GossipMill::IsWordChar are the two places the engines can part.
//       AND THE DENOMINATOR ABOVE IS THE WRONG ONE FOR Hash. Hash reads
//       REPLIER IDS, not summaries, so the bank measurement above is not its
//       denominator: canon.md carries 0 non-ASCII bytes (1 file examined,
//       2026-09-08), which is the set the cast ids derive from.
//   13. Answer's ARITHMETIC IS DONE IN uint32 AND CAST BACK. C# int
//       arithmetic is unchecked and wraps; C++ signed overflow is undefined,
//       so `seed * 97 + 31 + hash % 9973` would be UB for a large seed. The
//       two agree bit for bit on every two's-complement machine and the port
//       is defined rather than undefined where the C# merely wraps.
//   14. A NULL Summary CANNOT EXIST HERE. Rumor::Summary is a std::string, so
//       the C#'s `string.IsNullOrEmpty(what)` guard is an empty-string guard.
//       Same outcome on every input the C# defines: no lines, no speech.
//
// NO UNREAL TYPE IS IN THIS FILE, deliberately, the standing rule from 25
// August: this project's top layer does not compile in the container that
// writes it, so the decisions and the strings live where the tests run.
// ue-probe/tests/crime-probe-test.cpp and ue-probe/tests/core-port-test.cpp
// compile and RUN every line below with g++ before anything is dispatched.
//
// WHAT THIS FILE CANNOT SEE: whether anybody was in earshot, whether a frame
// was captioned with the sentence it composed, or whether the summary it
// composed from describes what the witness actually saw. Those are the run's
// business and the crime verdict's keys are how they are read.
#pragma once

#include "Gossip.h"      // Rumor, Gossiper, RumorPtr, GossiperPtr

#include <string>
#include <vector>

namespace LedgerCore
{
	// StreetVoice.cs 43 to 72. One thing somebody says out loud, with the
	// state that justifies it.
	struct SpokenLine
	{
		std::string SpeakerId;
		std::string Text;
		// True when this is about the player: those carry a lead if heard.
		bool        AboutPlayer;
		// The rumour behind it. The player who overhears this learns exactly
		// this, which is why hearing is knowing.
		RumorPtr    Source;
		// TRUE WHEN THE WORDS WERE ASSEMBLED AT RUN TIME, so no recording of
		// them can exist and none ever will. VoiceBank.ClipName keys a clip
		// by (voice, EXACT text), and a line built as template-plus-summary is
		// a different clip for every rumour the street has ever carried. Only
		// the TELLING is marked, exactly as StreetVoice.cs 289 to 295 marks
		// it: the answer is a literal from a band and is bankable as written.
		bool        Composed;

		SpokenLine() : AboutPlayer(false), Composed(false) {}
	};

	namespace StreetVoice
	{
		// ---- the helpers, StreetVoice.cs 692 to 772 ----------------------

		// StreetVoice.cs 692. Deviation 13 does not apply: the modulus and the
		// negative correction are the C#'s own, and C++11 truncates a negative
		// remainder the same way C# does.
		inline int PickIndex(int Seed, int Count)
		{
			if (Count <= 0) { return -1; }
			int I = Seed % Count;
			if (I < 0) { I += Count; }
			return I;
		}

		inline std::string Pick(int Seed, const char* const* Options, int Count)
		{
			const int I = PickIndex(Seed, Count);
			if (I < 0 || Options == 0) { return std::string(); }
			return std::string(Options[I]);
		}

		// StreetVoice.cs 737. FNV-1a rather than GetHashCode, which is
		// randomised per process on .NET Core: the same save would otherwise
		// produce different conversations on each launch. Deviation 12, ASCII.
		inline unsigned int Hash(const std::string& S)
		{
			unsigned int H = 2166136261u;
			for (std::string::size_type I = 0; I < S.size(); ++I)
			{
				H ^= (unsigned int)(unsigned char)S[I];
				H *= 16777619u;
			}
			return H;
		}

		// StreetVoice.cs 734, and the three attempts its docstring records.
		// The reply's seed is mixed with WHO IS REPLYING, because two indices
		// that are both functions of one number give fourteen fixed
		// conversations however prime the multiplier is. Deviation 13: the
		// wrap is done in uint32 so a large seed is defined rather than UB.
		inline int AnswerSeed(int Seed, const std::string& ReplierId)
		{
			const unsigned int Mixed = (unsigned int)Seed * 97u + 31u + (Hash(ReplierId) % 9973u);
			return (int)Mixed;
		}

		// StreetVoice.cs 745. s.Trim() then one trailing full stop. Deviation
		// 12: ASCII whitespace, which is every byte the banks can carry.
		inline std::string Trim(const std::string& S)
		{
			if (S.empty()) { return S; }
			std::string::size_type B = 0, E = S.size();
			while (B < E && (S[B] == ' ' || S[B] == '\t' || S[B] == '\n' || S[B] == '\r'
			                 || S[B] == '\v' || S[B] == '\f')) { ++B; }
			while (E > B && (S[E - 1] == ' ' || S[E - 1] == '\t' || S[E - 1] == '\n' || S[E - 1] == '\r'
			                 || S[E - 1] == '\v' || S[E - 1] == '\f')) { --E; }
			std::string Out = S.substr(B, E - B);
			if (!Out.empty() && Out[Out.size() - 1] == '.') { Out.erase(Out.size() - 1); }
			return Out;
		}

		// StreetVoice.cs 768. A Rumor.Summary is a lowercase clause written to
		// be spliced into the middle of a sentence, and half the templates do
		// exactly that; the other half open on it or follow a full stop, and
		// every one of those was rendering "Don't quote me. the new owner was
		// at the warehouse on Tuesday" in a subtitle. ONLY THE FIRST
		// CHARACTER MOVES: a summary that already starts with a proper noun is
		// left exactly as it is. Deviation 12, ASCII.
		inline std::string Cap(const std::string& S)
		{
			if (S.empty()) { return S; }
			if (!(S[0] >= 'a' && S[0] <= 'z')) { return S; }
			std::string Out = S;
			Out[0] = (char)(S[0] - 'a' + 'A');
			return Out;
		}

		// DEVIATION 9. The C# writes $"I'm telling you, {what}." and the
		// compiler concatenates; the literal below is that same template text
		// and this substitutes. {what} is the trimmed summary, {What} is
		// Cap(what), and a token this does not know is left standing so a
		// mistyped placeholder shows up in the string rather than vanishing.
		inline std::string Render(const std::string& Template, const std::string& What)
		{
			const std::string Capped = Cap(What);
			std::string Out;
			for (std::string::size_type I = 0; I < Template.size(); )
			{
				if (Template.compare(I, 6, "{what}") == 0) { Out += What;   I += 6; continue; }
				if (Template.compare(I, 6, "{What}") == 0) { Out += Capped; I += 6; continue; }
				Out += Template[I];
				++I;
			}
			return Out;
		}

		// ---- the bands --------------------------------------------------
		//
		// FOURTEEN A BAND RATHER THAN TWO OR THREE, and the C# records why:
		// BarkGen measured the old banks and EVERY slot in the game repeated
		// inside ninety seconds. A street that says the same eight sentences
		// all evening is a street the player stops hearing, and it takes the
		// gossip system down with it, because the whole point is that what you
		// overhear is causally true and nobody listens to a loop.

	// StreetVoice.cs 146 to 175, the band for confidence at or above 0.80:
	// somebody who saw it. TWO OF THE FOURTEEN DELIBERATELY LEAD WITH THE
	// STORY, which the C# records as a judgement rather than an oversight: at
	// this confidence, stating the thing flatly and letting it sit is what
	// certainty sounds like.
	inline const char* const* TellCertain(int& OutCount)
	{
		static const char* const Lines[14] = {
			"I'm telling you, {what}.",
			"{What}. I know what I saw.",
			"You want to know why I'm quiet lately? {What}.",
			"{What}. I'd say it in front of him.",
			"I was there. {What}, and that's the end of it.",
			"Don't look at me like that. {What}.",
			"My own eyes, not somebody's mouth. {What}.",
			"You can believe what you like. {What}.",
			"I've not slept right since. {What}.",
			"I wish I hadn't seen it, but I did: {what}.",
			"Ask me again in a year and I'll tell you the same: {what}.",
			"There's no other way to read it: {what}.",
			"I'm not guessing. {What}.",
			"Nobody's done a thing about it. {What}.",
		};
		OutCount = 14;
		return Lines;
	}

	// StreetVoice.cs 176 to 192, confidence 0.50 to 0.80: somebody who was
	// told, repeating it with the attribution still attached.
	inline const char* const* TellSecondHand(int& OutCount)
	{
		static const char* const Lines[14] = {
			"They're saying {what}.",
			"Word is {what}.",
			"Somebody told me {what}. Make of it what you like.",
			"It's going round that {what}.",
			"Two people told me {what}. Different two people.",
			"I had it off someone who'd know: {what}.",
			"You've heard, then. {What}.",
			"There's a version where {what}. I've heard worse ones.",
			"{What}, if you believe the market.",
			"I'd not repeat it, but {what}.",
			"The talk is {what}. Take that how you like.",
			"Somebody at the docks reckons {what}.",
			"{What}. That's the third time this week I've heard it.",
			"I'll say this much: {what}.",
		};
		OutCount = 14;
		return Lines;
	}

	// StreetVoice.cs 193 to 209, confidence below 0.50: a whisper the teller
	// half believes and says anyway.
	inline const char* const* TellWhisper(int& OutCount)
	{
		static const char* const Lines[14] = {
			"There's a story going round that {what}. Probably nothing.",
			"You hear all sorts. {What}, apparently.",
			"Somebody's saying {what}. Somebody's always saying something.",
			"{What}, supposedly. People talk.",
			"I heard {what}, but I heard it from Sam.",
			"Bit of nonsense going about. {What}.",
			"They'll tell you {what}. They'll tell you anything.",
			"Half the street reckons {what}. Half the street's wrong.",
			"{What}? I'd want it from somebody sober.",
			"You know how it is. {What}, they say.",
			"There's a whisper that {what}. Not worth much.",
			"{What}, or so I'm told, by people who weren't there.",
			"Don't quote me. {What}, maybe.",
			"I'd give it a week before somebody says the opposite: {what}.",
		};
		OutCount = 14;
		return Lines;
	}

	// StreetVoice.cs 216 to 232. The hearer has nerve above 0.65 and the
	// rumour is sensitive: they will not have it said out loud near them.
	inline const char* const* AnswerFrightened(int& OutCount)
	{
		static const char* const Lines[14] = {
			"Say that where it can be heard and see what it costs you.",
			"I'd keep that behind my teeth if I were you.",
			"Not here. Not with that door open.",
			"You're a braver man than me, saying it out loud.",
			"I didn't hear that. Understand me. I didn't hear it.",
			"Whatever you think you know, unknow it.",
			"There's people who'd pay to hear you say that again.",
			"Stop. I mean it. Stop.",
			"You want to be careful whose name you put in a sentence.",
			"I've got children. Talk about the weather.",
			"Some things you carry. You don't hand them round.",
			"That's the kind of talk that ends with somebody moving away.",
			"Say it quieter or don't say it.",
			"I'm going to walk off now, and you're going to let me.",
		};
		OutCount = 14;
		return Lines;
	}

	// StreetVoice.cs 233 to 249. Loyalty above 0.65: they defend the player,
	// which is what makes friendship mechanically worth having.
	inline const char* const* AnswerLoyal(int& OutCount)
	{
		static const char* const Lines[14] = {
			"That's talk. People love talk.",
			"I've known better people do worse for less.",
			"And you believed it, did you?",
			"There'll be a reason. There usually is.",
			"That's not the man I know.",
			"I'd want to hear it from him before I said it again.",
			"People are quick to have an opinion about a stranger.",
			"Mickey's family. That still means something to me.",
			"You'd say the same about anyone with a bit of money coming in.",
			"Half of that's true and the wrong half's the loud one.",
			"I'll not be the one carrying that any further.",
			"Give it a month. It'll be somebody else's turn.",
			"That's a hard thing to say about a man who's been decent to me.",
			"I've heard that story before, about somebody else.",
		};
		OutCount = 14;
		return Lines;
	}

	// StreetVoice.cs 250 to 266. Greed above 0.65: they hear a price on it.
	inline const char* const* AnswerGreedy(int& OutCount)
	{
		static const char* const Lines[14] = {
			"Interesting, that. Worth something to somebody.",
			"Who else knows?",
			"How long have you been sitting on it?",
			"There's people who'd want that. Paying people.",
			"That's not gossip. That's leverage.",
			"Keep it to yourself for a day or two. Do us both a favour.",
			"Who'd you tell before me?",
			"And what's he doing about it, that's the question.",
			"You could do something with that, you know.",
			"Does he know you know?",
			"I'd not give that away for nothing.",
			"Say that again, slowly.",
			"Now that IS worth hearing.",
			"Everything's worth something to the right ear.",
		};
		OutCount = 14;
		return Lines;
	}

	// StreetVoice.cs 267 to 283. No disposition above 0.65: an ordinary
	// neighbour hearing something about somebody they know.
	inline const char* const* AnswerPlain(int& OutCount)
	{
		static const char* const Lines[14] = {
			"Who told you that?",
			"Since when?",
			"God. And here?",
			"On this street?",
			"Are you sure it was him?",
			"That's the first I've heard of it.",
			"Well. That's the week made interesting.",
			"Since when has anybody round here been surprised by that?",
			"Hm. Does Lena know?",
			"I'd rather not have heard that, if I'm honest.",
			"What, and nobody's said anything?",
			"That would explain a few things.",
			"You're serious.",
			"There's always something.",
		};
		OutCount = 14;
		return Lines;
	}
		// ---- which band, named once ---------------------------------------
		//
		// DEVIATION 10. StreetVoice.cs 145 to 148 writes the three-way
		// conditional inline; this is the same two boundaries, in one place, so
		// the instrument that names the band reads the band the run took
		// instead of a second copy of `>= 0.8`.
		//
		// 0 = at or above 0.80, the teller saw it themselves. 1 = 0.50 to
		// 0.80, somebody told them. 2 = below 0.50, a whisper they half
		// believe. The boundaries are INCLUSIVE at the top of each band,
		// exactly as the C# >= reads.
		inline int TellBandIndex(double Confidence)
		{
			if (Confidence >= 0.8) { return 0; }
			if (Confidence >= 0.5) { return 1; }
			return 2;
		}

		inline const char* const* TellBand(int BandIndex, int& OutCount)
		{
			if (BandIndex == 0) { return TellCertain(OutCount); }
			if (BandIndex == 1) { return TellSecondHand(OutCount); }
			return TellWhisper(OutCount);
		}

		// DEVIATION 10 again, for the hearer. StreetVoice.cs 211 to 214: a
		// frightened man and a greedy one have to hear the same news
		// differently or the disposition numbers under all of this are
		// decoration. ORDER IS THE BEHAVIOUR: nerve-with-a-sensitive-rumour
		// outranks loyalty, loyalty outranks greed, and > 0.65 is strict.
		//
		// 0 = will not have it said out loud. 1 = defends the player. 2 = sees
		// a price on it. 3 = an ordinary neighbour hearing something.
		inline int AnswerBandIndex(const Gossiper& To, bool Sensitive)
		{
			if (To.Nerve > 0.65 && Sensitive) { return 0; }
			if (To.Loyalty > 0.65)            { return 1; }
			if (To.Greed > 0.65)              { return 2; }
			return 3;
		}

		inline const char* const* AnswerBand(int BandIndex, int& OutCount)
		{
			if (BandIndex == 0) { return AnswerFrightened(OutCount); }
			if (BandIndex == 1) { return AnswerLoyal(OutCount); }
			if (BandIndex == 2) { return AnswerGreedy(OutCount); }
			return AnswerPlain(OutCount);
		}

		// The band names, for an instrument that has to print WHICH. Values
		// with no spaces, because every reader of this project's key=value
		// lines splits on whitespace and truncates in silence.
		inline const char* TellBandName(int BandIndex)
		{
			return BandIndex == 0 ? "confidence-at-or-above-0.80"
			     : BandIndex == 1 ? "confidence-0.50-to-0.80"
			                      : "confidence-below-0.50";
		}

		inline const char* AnswerBandName(int BandIndex)
		{
			return BandIndex == 0 ? "nerve-above-0.65-and-sensitive"
			     : BandIndex == 1 ? "loyalty-above-0.65"
			     : BandIndex == 2 ? "greed-above-0.65"
			                      : "no-disposition-above-0.65";
		}

		// ---- what the two of them SAY -------------------------------------
		//
		// DEVIATION 11. Which band spoke and which line it took, for the
		// verdict. Nothing in Exchange branches on it.
		struct ExchangeTrace
		{
			int  TellBand, TellIndex, TellCount;
			int  AnswerBand, AnswerIndex, AnswerCount;
			int  AnswerSeedValue;
			bool bComposed;      // true when a tell was actually built
			std::string Refused; // why not, when it was not

			ExchangeTrace()
				: TellBand(-1), TellIndex(-1), TellCount(0),
				  AnswerBand(-1), AnswerIndex(-1), AnswerCount(0),
				  AnswerSeedValue(0), bComposed(false), Refused("nothing-measured")
			{
			}
		};

		/// StreetVoice.cs 131. What the two of them SAY when a rumour passes
		/// between them.
		///
		/// The teller names the story; the hearer answers in the way their own
		/// disposition dictates. Both lines carry the rumour, so a player in
		/// earshot learns it by listening: the ledger row becomes a side
		/// effect of having heard rather than the event itself.
		///
		/// THE TELLING IS THE COMPOSED HALF AND THE ANSWER IS NOT, and the C#
		/// says so at 289 to 295 rather than marking both: the tell carries
		/// the summary inside it and is a new sentence every time, while the
		/// answer is a literal from a band and is in a bank as written.
		/// Marking both would be tidier and would put a renderable hole in the
		/// structural bucket the first time a reply went missing.
		inline std::vector<SpokenLine> Exchange(const RumorPtr& R, const GossiperPtr& From,
		                                        const GossiperPtr& To, int Seed,
		                                        ExchangeTrace* OutTrace)
		{
			std::vector<SpokenLine> Lines;
			if (OutTrace != 0) { OutTrace->Refused = "none"; }
			if (!R || !From || !To)
			{
				if (OutTrace != 0) { OutTrace->Refused = "no-rumour-or-no-speaker"; }
				return Lines;
			}
			// DEVIATION 14: the C#'s IsNullOrEmpty guard is an empty-string
			// guard here. Same outcome, no speech.
			const std::string What = Trim(R->Summary);
			if (What.empty())
			{
				if (OutTrace != 0) { OutTrace->Refused = "summary-carried-no-text"; }
				return Lines;
			}

			int TellCount = 0;
			const int TellBandI = TellBandIndex(R->Confidence);
			const char* const* Tells = TellBand(TellBandI, TellCount);
			const int TellI = PickIndex(Seed, TellCount);
			const std::string Tell = Render(std::string(Tells[TellI]), What);

			int AnswerCount = 0;
			const int AnswerBandI = AnswerBandIndex(*To, R->Sensitive);
			const char* const* Answers = AnswerBand(AnswerBandI, AnswerCount);
			const int ASeed = AnswerSeed(Seed, To->Id);
			const int AnswerI = PickIndex(ASeed, AnswerCount);
			const std::string Answer(Answers[AnswerI]);

			SpokenLine L1;
			L1.SpeakerId = From->Id; L1.Text = Tell;
			L1.AboutPlayer = true;   L1.Source = R; L1.Composed = true;
			SpokenLine L2;
			L2.SpeakerId = To->Id;   L2.Text = Answer;
			L2.AboutPlayer = true;   L2.Source = R; L2.Composed = false;
			Lines.push_back(L1);
			Lines.push_back(L2);

			if (OutTrace != 0)
			{
				OutTrace->TellBand = TellBandI;
				OutTrace->TellIndex = TellI;
				OutTrace->TellCount = TellCount;
				OutTrace->AnswerBand = AnswerBandI;
				OutTrace->AnswerIndex = AnswerI;
				OutTrace->AnswerCount = AnswerCount;
				OutTrace->AnswerSeedValue = ASeed;
				OutTrace->bComposed = true;
			}
			return Lines;
		}

		/// The C# signature, for a caller that wants the two lines and nothing
		/// about how they were chosen.
		inline std::vector<SpokenLine> Exchange(const RumorPtr& R, const GossiperPtr& From,
		                                        const GossiperPtr& To, int Seed)
		{
			return Exchange(R, From, To, Seed, 0);
		}
	}
}
