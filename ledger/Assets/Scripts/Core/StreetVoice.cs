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

            // Fourteen a band rather than two or three. BarkGen measured the
            // old banks: EVERY slot in the game repeated inside ninety
            // seconds, and the ambient ones inside thirty. A street that says
            // the same eight sentences all evening is a street the player
            // stops hearing, and it takes the gossip system down with it —
            // the whole point is that what you overhear is causally true, and
            // nobody listens to a loop.
            string tell =
                r.Confidence >= 0.8 ? Pick(seed, new[]
                {
                    $"I'm telling you, {what}.",
                    $"{what}. I know what I saw.",
                    $"You want to know why I'm quiet lately? {what}.",
                    $"{what}. I'd say it in front of him.",
                    $"I was there. {what}, and that's the end of it.",
                    $"Don't look at me like that. {what}.",
                    $"{what}. My own eyes, not somebody's mouth.",
                    $"You can believe what you like. {what}.",
                    $"I've not slept right since. {what}.",
                    $"{what}. I wish I hadn't seen it.",
                    $"Ask me again in a year and I'll tell you the same: {what}.",
                    $"{what}. There's no other way to read it.",
                    $"I'm not guessing. {what}.",
                    $"{what}. And nobody's done a thing about it.",
                })
                : r.Confidence >= 0.5 ? Pick(seed, new[]
                {
                    $"They're saying {what}.",
                    $"Word is {what}.",
                    $"Somebody told me {what}. Make of it what you like.",
                    $"It's going round that {what}.",
                    $"Two people told me {what}. Different two people.",
                    $"I had it off someone who'd know: {what}.",
                    $"You've heard, then. {what}.",
                    $"There's a version where {what}. I've heard worse ones.",
                    $"{what}, if you believe the market.",
                    $"I'd not repeat it, but {what}.",
                    $"The talk is {what}. Take that how you like.",
                    $"Somebody at the docks reckons {what}.",
                    $"{what}. That's the third time this week I've heard it.",
                    $"I'll say this much: {what}.",
                })
                : Pick(seed, new[]
                {
                    $"There's a story going round that {what}. Probably nothing.",
                    $"You hear all sorts. {what}, apparently.",
                    $"Somebody's saying {what}. Somebody's always saying something.",
                    $"{what}, supposedly. People talk.",
                    $"I heard {what}, but I heard it from Sam.",
                    $"Bit of nonsense going about — {what}.",
                    $"They'll tell you {what}. They'll tell you anything.",
                    $"Half the street reckons {what}. Half the street's wrong.",
                    $"{what}? I'd want it from somebody sober.",
                    $"You know how it is. {what}, they say.",
                    $"There's a whisper that {what}. Not worth much.",
                    $"{what}, or so I'm told, by people who weren't there.",
                    $"Don't quote me. {what}, maybe.",
                    $"I'd give it a week before somebody says the opposite: {what}.",
                });

            // The hearer's answer is their character, not a canned reply.
            // The reply is CHARACTER, not acknowledgement. The same news has
            // to land differently on a frightened man and a greedy one, or
            // the disposition numbers under all of this are decoration.
            string answer =
                to.Nerve > 0.65 && r.Sensitive ? Pick(Answer(seed, to.Id), new[]
                {
                    "Say that where it can be heard and see what it costs you.",
                    "I'd keep that behind my teeth if I were you.",
                    "Not here. Not with that door open.",
                    "You're a braver man than me, saying it out loud.",
                    "I didn't hear that. Understand me — I didn't hear it.",
                    "Whatever you think you know, unknow it.",
                    "There's people who'd pay to hear you say that again.",
                    "Stop. I mean it. Stop.",
                    "You want to be careful whose name you put in a sentence.",
                    "I've got children. Talk about the weather.",
                    "Some things you carry. You don't hand them round.",
                    "That's the kind of talk that ends with somebody moving away.",
                    "Say it quieter or don't say it.",
                    "I'm going to walk off now, and you're going to let me.",
                })
                : to.Loyalty > 0.65 ? Pick(Answer(seed, to.Id), new[]
                {
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
                })
                : to.Greed > 0.65 ? Pick(Answer(seed, to.Id), new[]
                {
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
                })
                : Pick(Answer(seed, to.Id), new[]
                {
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
            // Every one of these has to INVITE being stopped, because it can
            // be: the speaker's memory holds the same rumour the line came
            // from, so the player can turn round and ask what they meant. A
            // line that closes the subject wastes the only bark system in the
            // genre that can be interrogated.
            string text =
                stance >= StanceKind.Confronts ? Pick(seed, new[]
                {
                    "You and I need a word. Not here.",
                    "I've been waiting to see you, as it happens.",
                    "Don't walk past me. Not today.",
                    "Stop there. You know why.",
                    "I've been rehearsing this. Give me a minute of it.",
                    "There you are. I've had four days to think about this.",
                    "You're going to stand there and hear it.",
                    "A word. It won't take long and it won't be pleasant.",
                    "I want to hear you say it to my face.",
                    "You've been avoiding this street. I noticed.",
                    "No. You don't get to nod and keep walking.",
                    "Two minutes. You owe me that much.",
                    "I'd like an answer, and I'd like it today.",
                    "Look at me when I'm talking to you.",
                })
                : stance == StanceKind.Refuses ? Pick(seed, new[]
                {
                    "I've nothing for you today.",
                    "Whatever it is, no.",
                    "Door's shut. Try somebody else.",
                    "Not for you. Not any more.",
                    "I'd rather not, and I'd rather not explain why.",
                    "We're closed. To you.",
                    "You'll want to ask somebody who doesn't know you.",
                    "No. And don't ask twice.",
                    "There's nothing here you want.",
                    "I've made up my mind about you.",
                    "Save your breath.",
                    "Not today. Not tomorrow either.",
                    "I've heard enough to know my answer.",
                    "Ask me in a year.",
                })
                : stance == StanceKind.Avoids ? Pick(seed, new[]
                {
                    "...",
                    "Excuse me.",
                    "Sorry — in a hurry.",
                    "Can't stop.",
                    "Another time.",
                    "Mm.",
                    "I'm late as it is.",
                    "Not now. Sorry.",
                    "Right. Right.",
                    "Somebody's waiting on me.",
                    "Yes. No. Sorry.",
                    "I've got to be somewhere.",
                    "Mind yourself.",
                    "...Evening.",
                })
                : about != null && about.Sensitive ? Pick(seed, new[]
                {
                    "There they are. The busy one.",
                    "Heard your name this week. More than once.",
                    "Funny hours you keep.",
                    "You get about, don't you.",
                    "Sleeping all right?",
                    "You want to be careful, a man as talked-about as you.",
                    "Someone was asking after you. I said I hadn't seen you.",
                    "Busy week, was it.",
                    "Odd, the places a name turns up.",
                    "I'd not say what I've heard. But I've heard it.",
                    "You'll know what people are saying.",
                    "Still standing. That surprises some.",
                    "Careful on that corner. People watch it.",
                    "You and I should have a proper talk one day.",
                })
                : Pick(seed, new[]
                {
                    "Mickey's one. Still standing, then.",
                    "All right.",
                    "How's the pub treating you?",
                    "Cold enough for you?",
                    "Your uncle'd have hated this weather.",
                    "Tell Lena I said hello.",
                    "Still open, is it?",
                    "You've the look of him, you know. Around the eyes.",
                    "Long day?",
                    "Mind how you go.",
                    "That step of yours needs seeing to.",
                    "Good to see the lights on down there.",
                    "You'll be at the market Thursday, I expect.",
                    "Evening.",
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

            // Fourteen a band. This is the family the player hears MOST — a
            // busy street starts one of these every thirteen seconds — and
            // BarkGen measured the original four-line bank looping inside
            // half a minute. The writing here is deliberately ordinary:
            // nothing in this function is about the player, and the moment a
            // line reaches for interest it stops being a city and starts
            // being a stage set with something to tell you.
            if (feuding)
            {
                opener = Pick(seed, new[]
                {
                    "I've nothing to say to you.",
                    "Don't. Just don't.",
                    "You've a nerve, standing there.",
                    "Walk on.",
                    "I saw you coming and I stayed anyway. Don't make me regret it.",
                    "We're not doing this.",
                    "Say what you came to say or move.",
                    "I've said all I'm saying.",
                    "You know what you did.",
                    "Not in front of people.",
                    "Whatever it is, it's too late for it.",
                    "I'd cross the road but I got here first.",
                    "Don't smile at me.",
                    "There's nothing left to talk about.",
                });
                reply = Pick(Answer(seed, b.Id), new[]
                {
                    "Suits me.",
                    "That's how it is, then.",
                    "Right.",
                    "Have it your way. You always do.",
                    "I wasn't going to.",
                    "Fine.",
                    "One of us has to be the bigger, and it won't be you.",
                    "As you like.",
                    "I'll be here when you've calmed down.",
                    "Understood.",
                    "You'll come round. You always come round.",
                    "Then we're done.",
                    "Suit yourself.",
                    "That's a shame. That's genuinely a shame.",
                });
            }
            else if (aInjured)
            {
                opener = Pick(seed, new[]
                {
                    "It's not healing. I've stopped pretending it is.",
                    "Can't lift with it. Can't do the work either.",
                    "It wakes me. That's the worst of it.",
                    "Doctor wants money I haven't got.",
                    "I've been strapping it up and hoping.",
                    "You can smell it going bad. I'm not imagining that.",
                    "Every step. Every single step.",
                    "I've been doing it one-handed a fortnight now.",
                    "They'll not keep me on if I can't carry.",
                    "It was nothing. A week ago it was nothing.",
                    "I daren't stop. If I stop I don't start again.",
                    "It's worse in the cold. It's always worse in the cold.",
                    "I'd have it looked at if looking at was free.",
                    "Don't. Don't touch it.",
                });
                reply = Pick(Answer(seed, b.Id), new[]
                {
                    "Get it seen to before it goes bad.",
                    "You said that last week.",
                    "There's a woman on Copper Row does it cheap.",
                    "You'll lose the arm being proud.",
                    "How much do you need?",
                    "Sit down, at least. Sit down.",
                    "My father did the same and he never worked again.",
                    "That's not a wound any more, that's a decision.",
                    "Let me see it. — No, properly.",
                    "You've been saying it's fine since Easter.",
                    "Take the day. The work'll still be there.",
                    "I'd not let a dog go on like that.",
                    "There's no shame in it costing money.",
                    "Promise me you'll go this week.",
                });
            }
            else if (priceLevel > 1.12)
            {
                opener = Pick(seed, new[]
                {
                    "Bread's gone up again. Again.",
                    "Everything's dearer and nobody will say why.",
                    "I paid what I paid last month and got less of it.",
                    "Have you seen what they want for coal?",
                    "Same basket, half the basket.",
                    "I stopped buying it. That's my answer to it.",
                    "The little ones are the ones that get you. Penny here, penny there.",
                    "It's not the price. It's that they say it like it's normal.",
                    "My rent's the same, my wages are the same, and yet.",
                    "There's no shortage. I've seen the store rooms.",
                    "Somebody's making that money. It's not us.",
                    "Twice this month. Twice.",
                    "I asked why and got a shrug for my trouble.",
                    "I've started keeping a list. It's not cheering reading.",
                });
                reply = Pick(Answer(seed, b.Id), new[]
                {
                    "It's the deliveries. Ask anyone who takes one.",
                    "My money's the same money it was.",
                    "You'll get used to it. We always do.",
                    "There's men getting rich off that shrug.",
                    "Wait till the winter.",
                    "It's the same everywhere. That's what they tell me, anyway.",
                    "I've gone back to the market. Costs me an hour, saves me a shilling.",
                    "Nobody's putting wages up to match, funny that.",
                    "My mother said the same in her day. Doesn't help.",
                    "You should see what they charge across the water.",
                    "Complain to who? That's the trouble.",
                    "I buy less and eat less and there we are.",
                    "It'll settle. It usually settles.",
                    "Don't get me started.",
                });
            }
            else if (prosperity < 0.35)
            {
                opener = Pick(seed, new[]
                {
                    "Nobody's spending. You can feel it on the street.",
                    "Third quiet week. I've started counting them.",
                    "I've had four people in since I opened.",
                    "You can hear the clock in my shop. That's how quiet.",
                    "Even the market's thin.",
                    "I've laid the boy off. I hated doing it.",
                    "Half these shutters weren't down last year.",
                    "There's no work at the docks. None.",
                    "People are walking past looking, not coming in.",
                    "I'll give it till the spring and then I don't know.",
                    "It's gone quiet in a way that doesn't feel temporary.",
                    "Nobody's got it to spend, that's the truth of it.",
                    "I've started taking payment in bits.",
                    "It's the waiting I can't stand.",
                });
                reply = Pick(Answer(seed, b.Id), new[]
                {
                    "It'll turn. It always turns.",
                    "Says who? I've not seen it turn yet.",
                    "Same for everybody. If that helps, which it doesn't.",
                    "Give it till the season changes.",
                    "I've been saying that for six months.",
                    "You've weathered worse than this.",
                    "There's still money on this street. It's just not moving.",
                    "My takings are down a third and I'm one of the lucky ones.",
                    "It's not you. Don't let it be you.",
                    "Hold on. That's all any of us can do.",
                    "There'll be work when the boats come back.",
                    "I'd not shut. Once you shut you don't open.",
                    "Everybody's saying it. That's how I know it's real.",
                    "Come round Sunday. We'll not talk about money.",
                });
            }
            else if (now.Hour >= 21 || now.Hour < 5)
            {
                opener = Pick(seed, new[]
                {
                    "You're out late.",
                    "Long shift?",
                    "You'll catch your death standing about.",
                    "Nothing good happens at this hour.",
                    "Couldn't sleep either?",
                    "It's a different street after eleven.",
                    "You're the third person I've passed. On a Tuesday.",
                    "Quiet, isn't it. Properly quiet.",
                    "I like it now. Nobody wants anything.",
                    "Watch the corner. It's dark since the lamp went.",
                    "Off home?",
                    "You're keeping strange hours lately.",
                    "That's the second time round the block for me.",
                    "Cold gets in at this hour.",
                });
                reply = Pick(Answer(seed, b.Id), new[]
                {
                    "It's the only quiet part of the day.",
                    "Someone has to be.",
                    "Nearly. Nearly.",
                    "I'll sleep when the bill's paid.",
                    "Couldn't settle. You know how it is.",
                    "Walking helps. Don't ask me why.",
                    "Work. What else.",
                    "I've stopped trying to sleep before two.",
                    "Nowhere to be, that's the trouble.",
                    "Same as you, by the look of it.",
                    "It's the only time I get to think.",
                    "Half an hour and I'm in.",
                    "You take care going back.",
                    "Aye. Goodnight to you.",
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
                    "That's the rain coming, that is.",
                    "Your lad's got tall.",
                    "Have you a minute? No, it'll keep.",
                    "I've been meaning to catch you.",
                    "Did the roof hold?",
                    "You look better than you did.",
                    "Any word from your brother?",
                    "They've dug the road up again.",
                    "I've got that thing you asked about, when you want it.",
                    "You're the fourth person to say that to me today.",
                });
                reply = Pick(Answer(seed, b.Id), new[]
                {
                    "Same as ever.",
                    "Better this week, thanks for asking.",
                    "Don't ask me about the landlord.",
                    "If the weather holds.",
                    "Can't complain. Well. I could.",
                    "She's asking after you, as it happens.",
                    "Not so bad. You?",
                    "Ask me tomorrow and you'll get a different answer.",
                    "It held. Just about.",
                    "I'll come by for it Friday.",
                    "Getting on with it, you know.",
                    "Mustn't grumble.",
                    "There's always something, isn't there.",
                    "Aye, well. It passes.",
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

        /// The seed for the SECOND half of an exchange.
        ///
        /// This used to be `seed + 1`, which sounds harmless and is not.
        /// Every bank is the same length, so opener[i] was always followed by
        /// reply[i+1] — fourteen banks of fourteen lines produced fourteen
        /// fixed conversations rather than a hundred and ninety-six, and no
        /// amount of writing more lines would have changed that. BarkGen
        /// found it by counting distinct PAIRS instead of distinct lines,
        /// which is the number a listener actually experiences.
        ///
        /// The seed for the reply — mixed with WHO IS REPLYING.
        ///
        /// This took three attempts and the first two were both wrong in ways
        /// that only counting distinct CONVERSATIONS could see:
        ///
        ///   `seed + 1`    — fourteen banks of fourteen gave fourteen fixed
        ///                   conversations. opener[i] always met reply[i+1].
        ///   `seed * 7 + 3` — WORSE. Seven divides fourteen, so the reply
        ///                   index took two values and every band collapsed
        ///                   from fourteen replies to two.
        ///   `seed * 97`   — still fourteen conversations, because both
        ///                   indices were functions of ONE number, and a
        ///                   bijection is a bijection however prime you make
        ///                   it.
        ///
        /// The actual fix is a second independent input, and there is an
        /// obvious one: the person answering. The same remark now gets a
        /// different answer from a different neighbour, which is what it
        /// should have been doing all along.
        ///
        /// FNV-1a rather than string.GetHashCode, which is randomised per
        /// process on .NET Core — the same save would have produced different
        /// conversations on each launch, and every deterministic test in this
        /// repo would have been quietly lying.
        static int Answer(int seed, string replierId) =>
            seed * 97 + 31 + (int)(Hash(replierId) % 9973);

        static uint Hash(string s)
        {
            uint h = 2166136261;
            if (s != null)
                foreach (char c in s) { h ^= c; h *= 16777619; }
            return h;
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
