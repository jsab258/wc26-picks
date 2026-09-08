// TRANSLITERATION of ledger/Assets/Scripts/Core/Gossip.cs, D1 probe.
//
// TRANSLITERATION, NOT REWRITE, and the distinction is the whole method: the
// C# suite is the behavioural definition, so every constant and every branch
// here matches its source line for line, and where the C# is subtle the
// comment explaining why travels with it. A port that "improved" something
// would make the two engines incomparable, which is the one thing D1 must
// not allow.
//
// WHAT THIS FILE IS FOR, in one sentence from the crime ruling: THE ONE RULE
// THAT DECIDES WHETHER ONE CHARACTER PASSES A RUMOUR TO ANOTHER is
// GossipMill.Tick, Gossip.cs 356 to 383, and its heart is 371 to 372:
// passed = r.Confidence * tie * HopDecay, then a floor. Nothing else in 976
// lines decides a hop.
//
// SCOPE, from the ruling section 1 item 6: SocialGraph 9 to 32; Rumor 37 to
// 59; Gossiper 64 to 118 less Suspicion; GossipEvent 122 to 128; and from
// GossipMill only _agents, _graph, the four tunables 141 to 144, the
// constructor 146, Tie 152, Add 154, Get 178 to 179, WitnessesOffered and
// WitnessesDropped 194 to 195, SummariesSaying, SaysWord and IsWordChar 225
// to 256, Witness 262 to 325, and Tick 341 to 430 with together as a
// function argument.
//
// OUT OF SCOPE AND NOT HERE, so a reader can tell a missing member from a
// forgotten one: Forget, PlayerClaims, CompareNotes, KnowsSecret,
// DayCircleHeat, Leads, ExposureOf, Bribe, Intimidate, Discredit, UseHook,
// Age, HoldsIndelible, Contain, Backfire, RestoreDiscredited and
// StrongestSurvivingPlayerLead.
//
// THE ONE OMISSION INSIDE A PORTED FUNCTION, named at each of its two sites
// below: SuspicionTracker is out of scope, so Tick's two Suspicion.Raise
// calls (Gossip.cs 402 and 412) are absent while ev.Contradiction and
// ev.Exposure are set exactly as 406 and 413 set them. The crime verdict
// prints gossipSuspicionPorted=no/SuspicionTracker-out-of-scope.
//
// REFERENCE SEMANTICS, AND WHERE THIS PORT KEEPS THEM. C# Rumor, Gossiper,
// MemoryStore and KnowledgeBase are classes, and the mill MUTATES them
// through handles it got from a list: Witness raises an existing rumour's
// confidence in place, Tick appends to a listener it fetched by id. Those
// four are therefore shared_ptr here, because a value copy would silently
// make the mutation land on a temporary and the rumour would never firm up.
// Fact is the one class this port holds BY VALUE: its three fields are
// written only by its constructor and no ported line mutates a Fact after
// it exists, so sharing it buys nothing and costs every call site a
// dereference. That is a deviation and it is named rather than hidden.
//
// NO UNREAL TYPE IS IN THIS FILE, deliberately, and it is the standing rule
// from 25 August: the decisions and the strings live where the tests run,
// because this project's top layer does not compile in the container that
// writes it. The probe module supplies distances, ids and live world state
// and nothing else.
#pragma once

#include "GameTime.h"
#include "MemoryStore.h"
#include "Perception.h"      // LedgerCore::Clamp
#include "Suspicion.h"

#include <cctype>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace LedgerCore
{
	// Gossip.cs 9 to 32. Undirected weighted acquaintance graph: how likely,
	// and how faithfully, two NPCs pass talk about a third party (usually the
	// player). Weight is 0..1.
	//
	// A VECTOR OF ROWS RATHER THAN A HASH MAP, AND THE ORDER IS THE REASON.
	// Tick walks Contacts(speaker) and the events it returns come out in that
	// order, so the container's iteration order is part of the observable
	// behaviour. C#'s Dictionary enumerates in insertion order in practice
	// when nothing is ever removed, and nothing here removes (Forget is the
	// only remover in the C# and it is out of scope). Insertion order is
	// therefore the honest transliteration, and a hash map would have made
	// the two engines disagree about which event came first for no reason a
	// reader could see.
	class SocialGraph
	{
	public:
		void Link(const std::string& A, const std::string& B, double Weight)
		{
			if (A == B) return;
			Put(A, B, Weight);
			Put(B, A, Weight);
		}

		double Tie(const std::string& A, const std::string& B) const
		{
			const Row* R = FindRow(A);
			if (R == 0) return 0.0;
			for (std::vector<Edge>::size_type I = 0; I < R->Edges.size(); ++I)
			{
				if (R->Edges[I].To == B) return R->Edges[I].Weight;
			}
			return 0.0;
		}

		std::vector<std::string> Contacts(const std::string& Id) const
		{
			std::vector<std::string> Out;
			const Row* R = FindRow(Id);
			if (R == 0) return Out;      // C#: Enumerable.Empty<string>()
			for (std::vector<Edge>::size_type I = 0; I < R->Edges.size(); ++I)
			{
				Out.push_back(R->Edges[I].To);
			}
			return Out;
		}

	private:
		struct Edge { std::string To; double Weight; };
		struct Row  { std::string From; std::vector<Edge> Edges; };
		std::vector<Row> Ties;

		const Row* FindRow(const std::string& From) const
		{
			for (std::vector<Row>::size_type I = 0; I < Ties.size(); ++I)
			{
				if (Ties[I].From == From) return &Ties[I];
			}
			return 0;
		}

		void Put(const std::string& From, const std::string& To, double W)
		{
			const double Clamped = Clamp(W, 0.0, 1.0);   // C#: Math.Clamp
			for (std::vector<Row>::size_type I = 0; I < Ties.size(); ++I)
			{
				if (Ties[I].From != From) continue;
				for (std::vector<Edge>::size_type J = 0; J < Ties[I].Edges.size(); ++J)
				{
					// row[to] = w: an existing key keeps its position.
					if (Ties[I].Edges[J].To == To) { Ties[I].Edges[J].Weight = Clamped; return; }
				}
				Edge E; E.To = To; E.Weight = Clamped;
				Ties[I].Edges.push_back(E);
				return;
			}
			Row R; R.From = From;
			Edge E; E.To = To; E.Weight = Clamped;
			R.Edges.push_back(E);
			Ties.push_back(R);
		}
	};

	// Gossip.cs 37 to 59. A propagating piece of talk about someone. Content
	// is a structured Fact so it can be checked against what an NPC already
	// knows; Confidence decays each hop so third-hand rumour carries less
	// weight than an eyewitness account.
	class Rumor
	{
	public:
		Fact        Content;      // e.g. player.location_d2_evening = warehouse
		std::string OriginId;     // the first-hand source
		std::string Summary;      // human or model readable phrasing of the content
		double      Confidence;   // 0..1
		int         Hops;         // 0 = witnessed first-hand
		bool        Sensitive;    // pertains to the player's hidden (night) life

		/// A FACT, not a story. Set only by a killing (combat spec 7b).
		///
		/// Every other rumour in this game can be muddied, bought quiet,
		/// scared quiet, held on a leash or simply left to go cold. None of
		/// that machinery touches a corpse: Age, Discredit, Contain and the
		/// hop decay in Tick all step over an indelible rumour. That
		/// asymmetry against literally everything else in the mill is the
		/// whole reason killing a witness is terrifying rather than
		/// efficient: it works, and it is the one thing you can never take
		/// back.
		bool Indelible;

		Rumor(const Fact& InContent)
			: Content(InContent), Confidence(0.0), Hops(0),
			  Sensitive(false), Indelible(false)
		{
		}

		std::string TopicKey() const { return Content.Subject + "." + Content.Predicate; }
	};

	typedef std::shared_ptr<Rumor> RumorPtr;

	// Gossip.cs 64 to 118, less Suspicion. One NPC's social side: their
	// memory, what they factually know, the rumours they carry, and which of
	// the player's two faces they belong to.
	//
	// SuspicionTracker IS THE ONE MEMBER THAT DID NOT COME. The C# field and
	// the constructor's fifth argument are both absent here, by the ruling.
	class Gossiper
	{
	public:
		std::string Id;
		std::string DisplayName;
		std::string Circle;       // "day" | "night" | "both"
		std::shared_ptr<MemoryStore>   Memory;
		std::shared_ptr<KnowledgeBase> Knowledge;
		std::vector<RumorPtr>          Rumors;

		// How the player's damage control lands on this NPC. Greed: how
		// readily they take a bribe. Nerve: how hard they are to intimidate
		// (high means will not scare). Loyalty: goodwill toward the player.
		// All 0..1. Nothing in scope reads them; they are here because the
		// constructor sets them and the ruling ported the constructor.
		double Greed;
		double Nerve;
		double Loyalty;

		// Topics this NPC has agreed (or been made) to keep quiet about: they
		// still remember, but they will not pass it on.
		std::vector<std::string> Suppressed;

		// Standing coercion (design doc 6.3, strong hook): the player holds
		// something over them, and NOTHING about the player leaves their
		// lips, current topics and future ones alike. They remember
		// everything.
		bool Leashed;

		Gossiper(const std::string& InId, const std::string& InDisplayName,
		         const std::shared_ptr<MemoryStore>& InMemory,
		         const std::shared_ptr<KnowledgeBase>& InKnowledge,
		         const std::string& InCircle = "day",
		         double InGreed = 0.5, double InNerve = 0.5, double InLoyalty = 0.5)
			: Id(InId), DisplayName(InDisplayName), Circle(InCircle),
			  Memory(InMemory), Knowledge(InKnowledge),
			  Greed(InGreed), Nerve(InNerve), Loyalty(InLoyalty), Leashed(false)
		{
			// C#: Memory = memory ?? new MemoryStore(id), and the same for
			// Knowledge. The SuspicionTracker line between them is the one
			// omission, named in this file's header.
			if (!Memory)    { Memory    = std::make_shared<MemoryStore>(InId); }
			if (!Knowledge) { Knowledge = std::make_shared<KnowledgeBase>(); }
		}

		bool SuppressedHas(const std::string& TopicKey) const
		{
			for (std::vector<std::string>::size_type I = 0; I < Suppressed.size(); ++I)
			{
				if (Suppressed[I] == TopicKey) return true;
			}
			return false;
		}

		bool Holds(const std::string& TopicKey, const std::string& Value) const
		{
			for (std::vector<RumorPtr>::size_type I = 0; I < Rumors.size(); ++I)
			{
				if (Rumors[I]->TopicKey() == TopicKey && Rumors[I]->Content.Value == Value) return true;
			}
			return false;
		}

		// OrderByDescending(Confidence).FirstOrDefault(). C#'s OrderBy is a
		// STABLE sort, so among equal confidences the earliest-added rumour
		// wins; the strict > below reproduces that without sorting at all.
		RumorPtr Best(const std::string& TopicKey) const
		{
			RumorPtr BestR;
			for (std::vector<RumorPtr>::size_type I = 0; I < Rumors.size(); ++I)
			{
				if (Rumors[I]->TopicKey() != TopicKey) continue;
				if (!BestR || Rumors[I]->Confidence > BestR->Confidence) BestR = Rumors[I];
			}
			return BestR;
		}

		/// The strongest telling of this PARTICULAR version of the story. The
		/// re-tell guards compare against this rather than Best(): two agents
		/// holding conflicting values must settle, not re-copy each other's
		/// version every round (audit 2026-07-27).
		RumorPtr BestOfValue(const std::string& TopicKey, const std::string& Value) const
		{
			RumorPtr BestR;
			for (std::vector<RumorPtr>::size_type I = 0; I < Rumors.size(); ++I)
			{
				if (Rumors[I]->TopicKey() != TopicKey) continue;
				if (Rumors[I]->Content.Value != Value) continue;
				if (!BestR || Rumors[I]->Confidence > BestR->Confidence) BestR = Rumors[I];
			}
			return BestR;
		}
	};

	typedef std::shared_ptr<Gossiper> GossiperPtr;

	// Gossip.cs 122 to 128. One thing that happened during a gossip round,
	// for the sim report and for the player-facing heat readout.
	struct GossipEvent
	{
		std::string FromId, ToId;
		// C# names this field Rumor. g++ refuses a field whose name changes
		// the meaning of its own type, so the field carries Ref; the type
		// keeps the C# name.
		RumorPtr RumorRef;
		bool Contradiction;   // the rumour collided with a claim the player made to ToId
		bool Exposure;        // a night-life rumour reached a day-circle NPC

		GossipEvent() : Contradiction(false), Exposure(false) {}
	};

	// Gossip.cs 133 onward. The rumour network. Seeds first-hand sightings
	// and, each round, lets socially tied NPCs who are together pass talk
	// along.
	class GossipMill
	{
	public:
		// Gossip.cs 141 to 144. Tunables. Confidence is multiplied by tie
		// strength and this factor per hop; a rumour stops spreading once it
		// drops below the share floor.
		double HopDecay;
		double MinConfidenceToShare;
		double ContradictionSuspicion;   // scaled by rumour confidence
		double LeakSuspicion;            // day NPC hears a night rumour, no prior lie

		// Gossip.cs 146.
		explicit GossipMill(const std::shared_ptr<SocialGraph>& InGraph)
			: HopDecay(0.8), MinConfidenceToShare(0.2),
			  ContradictionSuspicion(0.35), LeakSuspicion(0.12),
			  Graph(InGraph ? InGraph : std::make_shared<SocialGraph>()),
			  Offered(0), Dropped(0)
		{
		}

		/// Gossip.cs 152. How strongly two people are connected, 0..1.
		/// Exposed as a passthrough rather than by handing out the graph:
		/// callers outside the mill want to ASK about a relationship, not to
		/// hold and possibly mutate the thing that defines every
		/// relationship.
		double Tie(const std::string& A, const std::string& B) const { return Graph->Tie(A, B); }

		/// Gossip.cs 154: _agents[g.Id] = g. An existing id is REPLACED in
		/// place and keeps its position, which is what a C# Dictionary does
		/// and what Tick's iteration order depends on.
		void Add(const GossiperPtr& G)
		{
			for (std::vector<GossiperPtr>::size_type I = 0; I < AgentList.size(); ++I)
			{
				if (AgentList[I]->Id == G->Id) { AgentList[I] = G; return; }
			}
			AgentList.push_back(G);
		}

		/// Gossip.cs 178 to 179. NULL IS A MISS, NOT A THROW.
		/// Dictionary.TryGetValue(null) raises ArgumentNullException, the one
		/// lookup method whose whole purpose is not to throw. SaveChaos
		/// reached it through SaveCodec, from a saved agent record whose id
		/// key had been deleted, and the exception escaped Restore past the
		/// only type the front end catches. "No agent by that name" is the
		/// honest answer for a name that is not there. A std::string cannot
		/// be null, so the C#'s null guard has nothing to guard here and the
		/// miss is the only outcome left; an empty id simply matches no
		/// agent.
		GossiperPtr Get(const std::string& Id) const
		{
			for (std::vector<GossiperPtr>::size_type I = 0; I < AgentList.size(); ++I)
			{
				if (AgentList[I]->Id == Id) return AgentList[I];
			}
			return GossiperPtr();
		}

		const std::vector<GossiperPtr>& Agents() const { return AgentList; }

		/// Gossip.cs 194 to 195. HOW MANY SIGHTINGS WERE OFFERED TO THIS
		/// MILL, AND HOW MANY IT REFUSED BECAUSE IT HAD NEVER HEARD OF THE
		/// WITNESS.
		///
		/// Instance fields rather than statics: a test builds several mills
		/// and a static count would sum them into a number describing no
		/// world at all. Dropped is a subset of Offered by construction, both
		/// incremented on the same call before and after the one branch, so
		/// the ratio is a real fraction and not two counters that happen to
		/// sit near each other.
		///
		/// A non-zero Dropped is not automatically a bug. It IS automatically
		/// a question, and there was no way to ask it before.
		int WitnessesOffered() const { return Offered; }
		int WitnessesDropped() const { return Dropped; }

		/// Gossip.cs 225 to 241. How many rumour summaries say `word` out
		/// loud.
		///
		/// WHY THIS IS IN CORE AND NOT A GREP. A rumour has two halves that
		/// look alike and are not: Content is a FACT, keyed on ids, and
		/// Summary is PROSE that a person reads on the ledger screen and a
		/// model reads in a prompt. The id for the player is the literal
		/// string "player", which is correct in a Fact and is not a word any
		/// character in this game would ever say. It shipped: a panel
		/// readback from 0eeee6d held four rumours reading "Mitch says it was
		/// player, and came to say so". A grep cannot find it because the
		/// leak is in the RUNNING world, not in the source.
		int SummariesSaying(const std::string& Word) const
		{
			if (Word.empty()) return 0;
			int N = 0;
			for (std::vector<GossiperPtr>::size_type I = 0; I < AgentList.size(); ++I)
			{
				const GossiperPtr& G = AgentList[I];
				if (!G) continue;
				for (std::vector<RumorPtr>::size_type J = 0; J < G->Rumors.size(); ++J)
				{
					if (G->Rumors[J] && SaysWord(G->Rumors[J]->Summary, Word)) N++;
				}
			}
			return N;
		}

		/// Gossip.cs 245 to 254. Does `text` contain `word` as a whole word?
		/// Case-insensitive, because a sentence that starts "Player was
		/// seen..." is the same bug. WHOLE WORDS: "a player's entrance" is a
		/// leak; "two players" is a different word and matching it would make
		/// the number un-actionable.
		static bool SaysWord(const std::string& Text, const std::string& Word)
		{
			if (Text.empty() || Word.empty()) return false;
			for (std::string::size_type I = 0; I + Word.size() <= Text.size(); )
			{
				const std::string::size_type At = IndexOfIgnoreCase(Text, Word, I);
				if (At == std::string::npos) return false;
				const std::string::size_type End = At + Word.size();
				const bool bLeftFree  = At == 0 || !IsWordChar(Text[At - 1]);
				const bool bRightFree = End >= Text.size() || !IsWordChar(Text[End]);
				if (bLeftFree && bRightFree) return true;
				I = At + 1;
			}
			return false;
		}

		/// Gossip.cs 256. char.IsLetterOrDigit is Unicode-aware in C# and
		/// this is ASCII, which is the same answer for every string this
		/// probe builds and is named here rather than assumed.
		static bool IsWordChar(char C)
		{
			return std::isalnum((unsigned char)C) != 0 || C == '_';
		}

		/// Gossip.cs 262 to 325. A first-hand sighting enters the network.
		/// Confidence defaults to certain; a disguise (or distance, or
		/// darkness) passes less than 1.0: the witness saw SOMETHING but
		/// cannot swear to who, and everything downstream (spread, heat,
		/// bribe prices) inherits that doubt.
		void Witness(const std::string& WitnessId, const Fact& Content,
		             const std::string& Summary, bool bSensitive, const GameTime& Now,
		             double Confidence = 1.0, bool bIndelible = false)
		{
			GossiperPtr W = Get(WitnessId);
			// A DROPPED WITNESS IS NOW A NUMBER, BECAUSE IT WAS NOTHING AT
			// ALL AND IT COST THE PROJECT ITS ENTIRE CROWD.
			//
			// This line was `if (w == null) return;`, an early return with no
			// trace. Every crowd walker's body was spawned under a person's
			// name while their agent was registered under r0000-style ids, so
			// seven hundred people witnessed things for months and not one
			// observation was ever stored. Nothing anywhere went red: a mill
			// that files nothing and a mill that is never told anything
			// produce identical output, which is rule 3b in its purest form.
			//
			// The behaviour is unchanged on purpose: refusing an unknown
			// witness is CORRECT, and creating one here would invent people
			// the world does not have. What changes is that it leaves a mark.
			//
			// Offered is the denominator and it counts BEFORE the refusal, so
			// "nothing was offered" and "everything offered was refused"
			// cannot read the same.
			Offered++;
			if (!W) { Dropped++; return; }
			Confidence = Clamp(Confidence, 0.0, 1.0);
			if (Confidence >= 0.95) W->Knowledge->Learn(Content);   // only certainty becomes hard knowledge
			RumorPtr Already = W->BestOfValue(Content.Subject + "." + Content.Predicate,
			                                  Content.Value);
			if (!Already)
			{
				RumorPtr R = std::make_shared<Rumor>(Content);
				R->OriginId = WitnessId; R->Summary = Summary;
				R->Confidence = Confidence; R->Hops = 0; R->Sensitive = bSensitive;
				R->Indelible = bIndelible;
				W->Rumors.push_back(R);
			}
			else if (bIndelible && !Already->Indelible)
			{
				// Somebody who half-heard a scuffle later learns there was a
				// body in it. The doubtful version does not survive that: it
				// is upgraded in place, at whatever certainty the body
				// carries, rather than sitting alongside as a live maybe.
				Already->Indelible = true;
				Already->Confidence = Already->Confidence > Confidence ? Already->Confidence : Confidence;
				Already->Hops = 0;
				Already->Summary = Summary;
				if (Already->Confidence >= 0.95) W->Knowledge->Learn(Content);
			}
			else if (Confidence > Already->Confidence)
			{
				// A clearer second look strengthens a doubtful first one.
				// This used to drop the repeat on the floor, so no later
				// sighting could ever firm up an early maybe (audit
				// 2026-07-27).
				Already->Confidence = Confidence;
				Already->Hops = 0;
				Already->Summary = Summary;
			}
			// THE MEMORY LINE IS WRITTEN ON EVERY CALL, including the fourth
			// branch where nothing about the rumour changed: seeing it again
			// is a thing that happened to them.
			//
			// THE COMMA IN "I think I saw it, couldn't swear to it" IS A
			// CORRECTION MADE IN BOTH ENGINES IN ONE BATCH. Gossip.cs 324 had
			// an em-dash there, and this run writes that string into a
			// committed memory file, which the formatting law forbids. The C#
			// was changed to the comma in the same commit as this port, so
			// the two still agree line for line and the golden table pins the
			// exact sentence.
			W->Memory->Append(MemoryEvent(Now, "observation", bSensitive ? 0.9 : 0.6,
				Confidence >= 0.95 ? "I saw it myself: " + Summary
				                   : "I think I saw it, couldn't swear to it: " + Summary));
		}

		/// Gossip.cs 341 to 430. One gossip round. `together` decides which
		/// tied pairs are actually in a position to talk this round
		/// (co-located in game, or always true in tests). Returns everything
		/// that propagated, for logging.
		typedef std::function<bool(const std::string&, const std::string&)> TogetherFn;

		std::vector<GossipEvent> Tick(const GameTime& Now, const TogetherFn& Together = TogetherFn())
		{
			std::vector<GossipEvent> Events;

			// Snapshot each agent's rumours so a rumour picked up THIS round
			// does not also hop again in the same round (keeps spread to one
			// hop per round, and the loop deterministic and terminating).
			std::vector<std::pair<std::string, std::vector<RumorPtr> > > Snapshot;
			for (std::vector<GossiperPtr>::size_type I = 0; I < AgentList.size(); ++I)
			{
				Snapshot.push_back(std::make_pair(AgentList[I]->Id, AgentList[I]->Rumors));
			}

			for (std::vector<GossiperPtr>::size_type SI = 0; SI < AgentList.size(); ++SI)
			{
				const GossiperPtr Speaker = AgentList[SI];
				const std::vector<std::string> Contacts = Graph->Contacts(Speaker->Id);
				for (std::vector<std::string>::size_type CI = 0; CI < Contacts.size(); ++CI)
				{
					const std::string& ListenerId = Contacts[CI];
					GossiperPtr Listener = Get(ListenerId);
					if (!Listener) continue;
					// C#: if (together != null && !together(a, b)) continue.
					// An unset std::function is the null.
					if (Together && !Together(Speaker->Id, ListenerId)) continue;

					const double TieW = Graph->Tie(Speaker->Id, ListenerId);
					if (TieW <= 0) continue;

					const std::vector<RumorPtr>& Held = SnapshotOf(Snapshot, Speaker->Id);
					for (std::vector<RumorPtr>::size_type RI = 0; RI < Held.size(); ++RI)
					{
						const RumorPtr& R = Held[RI];
						if (R->Confidence < MinConfidenceToShare && !R->Indelible) continue;
						// Money and hooks buy silence about STORIES. Nobody
						// keeps a body to themselves because they were paid to.
						if (!R->Indelible && Speaker->SuppressedHas(R->TopicKey())) continue;   // bribed or scared into silence
						if (!R->Indelible && Speaker->Leashed && R->Content.Subject == "player") continue;   // held by a hook
						// A body arrives at the far end of the street exactly
						// as true as it left. Hop decay is how a story turns
						// into a maybe; this is not a story.
						const double Passed = R->Indelible ? R->Confidence : R->Confidence * TieW * HopDecay;
						if (Passed < MinConfidenceToShare) continue;

						// Do not re-tell something the listener already holds
						// at least as strongly: stops rumours amplifying by
						// bouncing back and forth. Compared against the
						// listener's best rumour OF THIS VALUE, not the
						// topic's best overall: when two agents hold
						// conflicting values, comparing against the overall
						// best let each re-add an identical copy of the
						// other's version every round, growing Rumors and
						// Memory without bound (audit 2026-07-27).
						const RumorPtr Existing = Listener->BestOfValue(R->TopicKey(), R->Content.Value);
						if (Existing && Existing->Confidence >= Passed) continue;

						RumorPtr Heard = std::make_shared<Rumor>(R->Content);
						Heard->OriginId = R->OriginId; Heard->Summary = R->Summary;
						Heard->Confidence = Passed; Heard->Hops = R->Hops + 1;
						Heard->Sensitive = R->Sensitive; Heard->Indelible = R->Indelible;
						Listener->Rumors.push_back(Heard);
						Listener->Memory->Append(MemoryEvent(Now, "heard",
							Clamp(Passed * 0.8, 0.2, 0.85),
							"I heard from " + Speaker->DisplayName + " that " + R->Summary));

						GossipEvent Ev;
						Ev.FromId = Speaker->Id; Ev.ToId = ListenerId; Ev.RumorRef = Heard;

						// Consequence 1: the rumour collides with a claim the
						// player made to this listener, and the lie is
						// exposed.
						if (Listener->Knowledge->CheckClaim(R->Content) == ClaimResult::Contradiction)
						{
							// OMITTED HERE, Gossip.cs 402: the C# raises the
							// listener's suspicion by ContradictionSuspicion
							// times passed. SuspicionTracker is out of scope
							// by the ruling, so the raise is absent and
							// nothing else on these lines is. The tunable
							// above is kept so the number is still readable
							// beside the port that does not spend it.
							Listener->Memory->Append(MemoryEvent(Now, "observation", 0.85,
								"What I heard about " + ReplaceAll(R->TopicKey(), "player.", "")
								+ " doesn't match what they told me to my face."));
							Ev.Contradiction = true;
						}
						// Consequence 2: a night-life secret reaches someone
						// from the player's daytime world, and the double
						// life springs a leak.
						else if (R->Sensitive && Listener->Circle == "day")
						{
							// OMITTED HERE, Gossip.cs 412: the C# raises the
							// listener's suspicion by LeakSuspicion times
							// passed with the reason "heard something that
							// doesn't fit the person I thought I knew".
							// SuspicionTracker is out of scope; ev.Exposure
							// is still set exactly as 413 sets it.
							Ev.Exposure = true;
						}

						// AFTER the contradiction check, never before: an
						// indelible rumour arrives at certainty however many
						// mouths it crossed, and certainty is hard knowledge.
						// Learning it first would make the listener's own new
						// fact agree with itself and swallow the very
						// contradiction the killing is supposed to expose.
						if (Heard->Indelible && Heard->Confidence >= 0.95)
						{
							Listener->Knowledge->Learn(Heard->Content);
						}

						Events.push_back(Ev);
					}
				}
			}
			return Events;
		}

	private:
		std::shared_ptr<SocialGraph> Graph;
		std::vector<GossiperPtr>     AgentList;
		int Offered;
		int Dropped;

		static const std::vector<RumorPtr>& SnapshotOf(
			const std::vector<std::pair<std::string, std::vector<RumorPtr> > >& Snapshot,
			const std::string& Id)
		{
			for (std::vector<std::pair<std::string, std::vector<RumorPtr> > >::size_type I = 0;
			     I < Snapshot.size(); ++I)
			{
				if (Snapshot[I].first == Id) return Snapshot[I].second;
			}
			// Unreachable: every agent is in the snapshot by construction,
			// exactly as snapshot[speaker.Id] assumes in the C#. An empty
			// list rather than a throw keeps the failure quiet in the shape
			// the C# would fail in (a KeyNotFoundException there would be a
			// crash; here the speaker simply says nothing), and it can only
			// be reached if the snapshot loop above stops matching the agent
			// loop below it.
			static const std::vector<RumorPtr> None;
			return None;
		}

		static std::string::size_type IndexOfIgnoreCase(const std::string& Text,
		                                                const std::string& Word,
		                                                std::string::size_type From)
		{
			if (Word.size() > Text.size()) return std::string::npos;
			for (std::string::size_type I = From; I + Word.size() <= Text.size(); ++I)
			{
				std::string::size_type J = 0;
				for (; J < Word.size(); ++J)
				{
					const int A = std::tolower((unsigned char)Text[I + J]);
					const int B = std::tolower((unsigned char)Word[J]);
					if (A != B) break;
				}
				if (J == Word.size()) return I;
			}
			return std::string::npos;
		}
	};
}
