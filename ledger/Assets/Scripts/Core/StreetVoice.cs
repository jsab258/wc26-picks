using System;
using System.Collections.Generic;

namespace Ledger.Core
{
    /// M15.1 — THE CITY BECOMES AUDIBLE.
    ///
    /// The gossip mill has always known who is telling whom what about you.
    /// Until now the player's only way to find out was a row in a panel:
    /// `ReportOverheard` detected two people trading a rumour six metres away
    /// and answered by updating a ledger. Two people were discussing the
    /// warehouse fire in front of him and the game said nothing out loud.
    ///
    /// This turns that state into SPEECH. Every line here is causally true —
    /// it exists because a specific person heard a specific thing from a
    /// specific source — which is the thing recorded barks cannot do and the
    /// whole reason this game has a gossip network under it.
    ///
    /// DELIBERATELY NOT LLM-GENERATED (yet). Lines are selected from real
    /// state, so they are free, deterministic, testable in CI, and they still
    /// work with no API key — the world stays audible even when it cannot
    /// think. The LLM's job is to make this ELOQUENT later, per-cast-member;
    /// its job is not to make it exist.
    public enum StanceKind
    {
        /// You are a person in the street like any other.
        Indifferent = 0,
        /// They clock you. A look, no more.
        Notices = 1,
        /// The look lasts. They keep you in view while you are in it.
        Watches = 2,
        /// They say something — to you, or pointedly near you.
        Comments = 3,
        /// They would rather be elsewhere, and go there.
        Avoids = 4,
        /// They will not deal with you. The door does not open.
        Refuses = 5,
        /// They come to you about it.
        Confronts = 6,
    }

    /// One thing somebody says out loud, with the state that justifies it.
    public class SpokenLine
    {
        public string SpeakerId;
        public string Text;
        /// True when this is about the player — those carry a lead if heard.
        public bool AboutPlayer;
        /// The rumour behind it, when there is one. The player who overhears
        /// this learns exactly this, which is why hearing is knowing.
        public Rumor Source;
    }

    public static class StreetVoice
    {
        // ---- the reaction ladder (M15.2) ----

        /// How somebody stands toward the player right now.
        ///
        /// Everything here already existed as numbers the player could only
        /// read in a panel. As a STANCE it becomes something they can watch
        /// happen: the room going quiet, a face turning away, a door not
        /// opening. That is the same information delivered by the world
        /// instead of by the interface.
        ///
        /// Loyalty pulls DOWN the ladder — a friend who has heard something
        /// bad about you asks you about it rather than crossing the street,
        /// which is what makes friendship mechanically worth having.
        public static StanceKind Stance(double suspicion, double loyalty,
            double strongestAboutPlayer, bool leashed, bool wearingCoat)
        {
            // A leash is a mouth held shut, not a mind changed: they still
            // watch, they simply do not speak.
            double pressure = Clamp01(0.55 * Clamp01(suspicion) + 0.45 * Clamp01(strongestAboutPlayer));
            // Somebody fond of you gives you the benefit of the doubt, right
            // up until it is unmistakable.
            pressure -= 0.35 * Clamp01(loyalty - 0.5) * 2.0 * (pressure < 0.85 ? 1.0 : 0.4);
            // The coat is deniability, and deniability buys distance from the
            // ladder — but only from people who are not already certain.
            if (wearingCoat && pressure < 0.7) pressure -= 0.12;
            pressure = Clamp01(pressure);

            if (pressure >= 0.86 && !leashed) return StanceKind.Confronts;
            if (pressure >= 0.72) return StanceKind.Refuses;
            if (pressure >= 0.58) return StanceKind.Avoids;
            if (pressure >= 0.42) return leashed ? StanceKind.Watches : StanceKind.Comments;
            if (pressure >= 0.26) return StanceKind.Watches;
            if (pressure >= 0.12) return StanceKind.Notices;
            return StanceKind.Indifferent;
        }

        /// How far away somebody starts tracking you with their eyes. An
        /// ordinary passer-by does not; somebody who has heard about the
        /// warehouse can pick you out down the length of a street.
        public static double GazeMetres(StanceKind stance) =>
            stance <= StanceKind.Indifferent ? 0
            : stance == StanceKind.Notices ? 6
            : stance == StanceKind.Watches ? 14
            : stance == StanceKind.Comments ? 12
            : stance == StanceKind.Avoids ? 18
            : 22;

        // ---- overheard exchanges: the mill, out loud ----

        /// What the two of them SAY when a rumour passes between them.
        ///
        /// The teller names the story; the hearer answers in the way their
        /// own disposition dictates. Both lines carry the rumour, so a player
        /// in earshot learns it by listening — the ledger row becomes a side
        /// effect of having heard, rather than the event itself.
        public static List<SpokenLine> Exchange(Rumor r, Gossiper from, Gossiper to, int seed)
        {
            var lines = new List<SpokenLine>();
            if (r == null || from == null || to == null) return lines;
            string what = Trim(r.Summary);
            if (string.IsNullOrEmpty(what)) return lines;

            string tell =
                r.Confidence >= 0.8 ? Pick(seed, new[]
                {
                    $"I'm telling you, {what}.",
                    $"{what}. I know what I saw.",
                    $"You want to know why I'm quiet lately? {what}.",
                })
                : r.Confidence >= 0.5 ? Pick(seed, new[]
                {
                    $"They're saying {what}.",
                    $"Word is {what}.",
                    $"Somebody told me {what}. Make of it what you like.",
                })
                : Pick(seed, new[]
                {
                    $"There's a story going round that {what}. Probably nothing.",
                    $"You hear all sorts. {what}, apparently.",
                });

            // The hearer's answer is their character, not a canned reply.
            string answer =
                to.Nerve > 0.65 && r.Sensitive ? Pick(seed + 1, new[]
                {
                    "Say that where it can be heard and see what it costs you.",
                    "I'd keep that behind my teeth if I were you.",
                })
                : to.Loyalty > 0.65 ? Pick(seed + 1, new[]
                {
                    "That's talk. People love talk.",
                    "I've known better people do worse for less.",
                })
                : to.Greed > 0.65 ? Pick(seed + 1, new[]
                {
                    "Interesting, that. Worth something to somebody.",
                    "Who else knows?",
                })
                : Pick(seed + 1, new[]
                {
                    "Who told you that?",
                    "Since when?",
                    "God. And here?",
                });

            lines.Add(new SpokenLine { SpeakerId = from.Id, Text = tell, AboutPlayer = true, Source = r });
            lines.Add(new SpokenLine { SpeakerId = to.Id, Text = answer, AboutPlayer = true, Source = r });
            return lines;
        }

        /// Something said as the player goes past, by somebody who is holding
        /// a story about them. Short, pointed, and STOPPABLE — the player can
        /// turn round and ask what they meant, because the speaker's memory
        /// holds the same rumour this line came from.
        public static SpokenLine Recognition(Gossiper g, Rumor about, StanceKind stance, int seed)
        {
            if (g == null || stance < StanceKind.Comments) return null;
            string text =
                stance >= StanceKind.Confronts ? Pick(seed, new[]
                {
                    "You and I need a word. Not here.",
                    "I've been waiting to see you, as it happens.",
                })
                : stance == StanceKind.Refuses ? Pick(seed, new[]
                {
                    "I've nothing for you today.",
                    "Whatever it is, no.",
                })
                : stance == StanceKind.Avoids ? Pick(seed, new[]
                {
                    "...",
                    "Excuse me.",
                })
                : about != null && about.Sensitive ? Pick(seed, new[]
                {
                    "There they are. The busy one.",
                    "Heard your name this week. More than once.",
                    "Funny hours you keep.",
                })
                : Pick(seed, new[]
                {
                    "Marek's one. Still standing, then.",
                    "All right.",
                });
            return new SpokenLine { SpeakerId = g.Id, Text = text, AboutPlayer = about != null, Source = about };
        }

        // ---- ambient life: the city that is busy without you ----

        /// Two people talking about THEIR OWN lives, not yours.
        ///
        /// This is the half that makes a place feel like it existed before
        /// the player arrived — and it is the half that was entirely absent.
        /// Everything here is drawn from state the game already simulates, so
        /// a street that has been squeezed sounds squeezed.
        public static List<SpokenLine> Ambient(Gossiper a, Gossiper b, GameTime now,
            double prosperity, double priceLevel, bool aInjured, bool feuding, int seed)
        {
            var lines = new List<SpokenLine>();
            if (a == null || b == null) return lines;

            string opener;
            string reply;

            if (feuding)
            {
                opener = Pick(seed, new[]
                {
                    "I've nothing to say to you.",
                    "Don't. Just don't.",
                });
                reply = Pick(seed + 1, new[]
                {
                    "Suits me.",
                    "That's how it is, then.",
                });
            }
            else if (aInjured)
            {
                opener = Pick(seed, new[]
                {
                    "It's not healing. I've stopped pretending it is.",
                    "Can't lift with it. Can't do the work either.",
                });
                reply = Pick(seed + 1, new[]
                {
                    "Get it seen to before it goes bad.",
                    "You said that last week.",
                });
            }
            else if (priceLevel > 1.12)
            {
                opener = Pick(seed, new[]
                {
                    "Bread's gone up again. Again.",
                    "Everything's dearer and nobody will say why.",
                    "I paid what I paid last month and got less of it.",
                });
                reply = Pick(seed + 1, new[]
                {
                    "It's the deliveries. Ask anyone who takes one.",
                    "My money's the same money it was.",
                    "You'll get used to it. We always do.",
                });
            }
            else if (prosperity < 0.35)
            {
                opener = Pick(seed, new[]
                {
                    "Nobody's spending. You can feel it on the street.",
                    "Third quiet week. I've started counting them.",
                });
                reply = Pick(seed + 1, new[]
                {
                    "It'll turn. It always turns.",
                    "Says who? I've not seen it turn yet.",
                });
            }
            else if (now.Hour >= 21 || now.Hour < 5)
            {
                opener = Pick(seed, new[]
                {
                    "You're out late.",
                    "Long shift?",
                });
                reply = Pick(seed + 1, new[]
                {
                    "It's the only quiet part of the day.",
                    "Someone has to be.",
                });
            }
            else
            {
                opener = Pick(seed, new[]
                {
                    "Cold one.",
                    "How's your mother keeping?",
                    "Did you settle that business with the landlord?",
                    "You'll be at the market Thursday?",
                });
                reply = Pick(seed + 1, new[]
                {
                    "Same as ever.",
                    "Better this week, thanks for asking.",
                    "Don't ask me about the landlord.",
                    "If the weather holds.",
                });
            }

            lines.Add(new SpokenLine { SpeakerId = a.Id, Text = opener });
            lines.Add(new SpokenLine { SpeakerId = b.Id, Text = reply });
            return lines;
        }

        // ---- the street's volume IS its temperature ----

        /// How loud the street is about you, 0..1 — the thing the status line
        /// used to say in words. A hot street is a talkative one, and the
        /// player should learn to read the NOISE rather than the readout.
        public static double ChatterLevel(double dayCircleHeat, int peopleInEarshot) =>
            Clamp01(0.25 + 0.75 * Clamp01(dayCircleHeat)) * Clamp01(peopleInEarshot / 6.0);

        /// How often, in seconds, an ambient exchange should start near the
        /// player. Busier when there are more people and when there is
        /// something to talk about.
        public static double AmbientEverySeconds(double dayCircleHeat, int peopleInEarshot)
        {
            if (peopleInEarshot < 2) return double.MaxValue;
            double busy = 0.5 + 0.5 * Clamp01(dayCircleHeat);
            return Math.Max(6.0, 26.0 / busy / Math.Max(1, peopleInEarshot) * 3.0);
        }

        // ---- helpers ----

        static string Pick(int seed, string[] options)
        {
            if (options == null || options.Length == 0) return "";
            int i = seed % options.Length;
            if (i < 0) i += options.Length;
            return options[i];
        }

        static string Trim(string s)
        {
            if (string.IsNullOrEmpty(s)) return s;
            s = s.Trim();
            if (s.EndsWith(".")) s = s.Substring(0, s.Length - 1);
            return s;
        }

        static double Clamp01(double v) => v < 0 ? 0 : v > 1 ? 1 : v;
    }
}
