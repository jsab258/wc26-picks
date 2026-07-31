using System;
using System.Collections.Generic;
using System.Linq;

namespace Ledger.Core
{
    /// The living economy (roadmap M7, agency-model dimension raised to 85 by
    /// the player). The district is not a backdrop that pays out a fixed number
    /// every morning — it is a place with a finite amount of money in it, and
    /// everything you do to it changes how much.
    ///
    /// THE LOOP THAT MAKES THIS WORTH BUILDING: squeezing the street makes the
    /// street poorer. Poorer people spend less in your bar. So the racket that
    /// pays you dirty money at night quietly costs you clean money in the
    /// morning, and past a point it costs more than it pays. That is a real
    /// decision with no correct answer, and it is expressed entirely through
    /// people — which satisfies the project's two scope filters at once: this
    /// non-social system exists to give the social system stakes, and the
    /// decision ripples instead of becoming a chore.
    ///
    /// LEGIBILITY IS THE HARD REQUIREMENT. Nothing here surfaces as a
    /// percentage. Prices going up is Vesna saying the deliveries cost more.
    /// Prosperity falling is a regular drinking at home. If a number cannot be
    /// said as somebody's circumstance, it does not get shown at all.
    ///
    /// It is deliberately gentle at the start: a campaign that squeezes nothing
    /// sits at a takings factor of 1.0 and behaves exactly as it did before this
    /// file existed. The economy only bites once the player starts taking.

    /// Somebody who brings a business the things it sells. A person, with a
    /// name and an opinion of you — not a supply-chain node.
    public class Supplier
    {
        public string Id;
        public string Name;
        /// What they bring, in the words a person would use: "the drink",
        /// "the stock", "the produce".
        public string Goods;
        /// Which business they keep stocked ("bar" is the bar itself; null
        /// matches nothing — FactorFor(null) means the district as a whole).
        public string ServesBusinessId;
        /// Charged weekly, not daily — a delivery is an event, not a drip.
        public int PricePerWeek = 90;
        /// -1..1. Falls when the street they also serve gets squeezed, and when
        /// being seen at your door becomes a liability.
        public double Standing;
        /// Below the refusal floor they stop coming. Recoverable, at a price.
        public bool Refusing;
        public int LastPaidDay = -1;
        /// Days in a row they have arrived and not been paid.
        public int Unpaid;
        /// What they charged last time, so the game can notice when it changes
        /// and say so — a price rise the player never hears about is a tax.
        public int LastPrice;
    }

    /// One thing that happened to the district's money today, phrased as a
    /// person's circumstance. The UI prints these verbatim.
    public class EconomyEvent
    {
        public string Kind;      // supply | price | prosperity | supplier | refusal
        public string Text;
        public int Amount;

        public EconomyEvent(string kind, string text, int amount = 0)
        {
            Kind = kind; Text = text; Amount = amount;
        }
    }

    public class Economy
    {
        // ---- the two numbers that matter ----

        /// How much money the district's people have, 0..1. Half is ordinary.
        public double Prosperity = 0.5;
        /// What things cost, 1.0 = ordinary. Rises with squeeze and supply costs.
        public double PriceLevel = 1.0;

        /// How hard the player is currently taking from this street, 0..1.
        /// Recomputed every day from what the rackets actually earn.
        public double Squeeze { get; private set; }

        public readonly List<Supplier> Suppliers = new List<Supplier>();

        // ---- tuning (public so the balance lab can sweep it) ----

        /// Daily racket income at which the street is being squeezed as hard as
        /// it can be. Set from the shipped rackets' combined take.
        public double SqueezeFullAt = 180.0;
        public double BaseProsperity = 0.55;
        public double SqueezeCostsProsperity = 0.45;
        public double HeatCostsProsperity = 0.20;
        /// Money you put back into the street: crew cuts and front wages. The
        /// generous-cut policy is not charity — it is economic policy.
        public double WagesLiftProsperity = 0.30;
        public double WageFullAt = 120.0;
        /// Prosperity and prices move over a week, never overnight. A player
        /// must be able to feel a decision before its consequence lands.
        public double DriftPerDay = 0.12;
        public double SqueezeRaisesPrices = 0.35;
        public double SupplyRaisesPrices = 0.15;

        /// Deliberately small. Over a three-week campaign at maximum squeeze
        /// these cost a supplier about a third of his goodwill — enough that he
        /// charges you more and you can hear him doing it, nowhere near enough
        /// that squeezing the street automatically costs you your deliveries.
        public double SqueezeCostsSupplierStanding = 0.02;
        public double HeatCostsSupplierStanding = 0.015;
        /// A supplier who has come to dislike you charges what he can get away
        /// with. This is where a squeezed street reaches a player who has money:
        /// not by cutting him off, by costing him more.
        public double DislikeRaisesPrice = 0.6;

        /// Set so that paying on time OUTWEIGHS the worst drift a squeezed,
        /// watched street can apply (0.02 + 0.015 daily is 0.245 a week). That
        /// is the balance the design wants: a supplier is lost by neglect, never
        /// by the neighbourhood getting harder — the neighbourhood only makes
        /// him dearer.
        public double PaymentBuysStanding = 0.28;

        public double SupplierRefusalFloor = -0.5;
        public double SupplierRecoveryPrice = 2.5;   // multiple of a week's price
        /// A business nobody will supply still limps along on what's left in the
        /// cellar; it does not go to zero, because zero is not a decision.
        public double StarvedFactor = 0.45;

        public double MinTakingsFactor = 0.35;
        public double MaxTakingsFactor = 1.35;

        // ---- what the rest of the game reads ----

        /// The multiplier the daily close applies to the bar and every front.
        /// Neutral at 1.0, which is exactly where an unsqueezed campaign sits.
        public double TakingsFactor =>
            Clamp((0.5 + Prosperity) * (1.0 - 0.5 * (PriceLevel - 1.0)),
                  MinTakingsFactor, MaxTakingsFactor);

        /// Per-business, because a front nobody will deliver to earns less than
        /// one that is stocked, however rich the street is.
        ///
        /// null means THE DISTRICT AS A WHOLE, never "whichever supplier has a
        /// null id". That distinction bit once: the bar's drayman was authored
        /// with ServesBusinessId = null, so this lookup matched him and his
        /// refusal starved every racket in every district — decision 9 coupled
        /// to the bar's cellar instead of the street (audit 2026-07-27).
        public double FactorFor(string businessId)
        {
            if (businessId == null) return TakingsFactor;
            var s = SupplierFor(businessId);
            return TakingsFactor * (s != null && s.Refusing ? StarvedFactor : 1.0);
        }

        /// What this week's delivery costs: the street's price level, plus
        /// whatever he thinks he can add for having stopped liking you.
        public int DeliveryPrice(Supplier s) =>
            s == null ? 0 : (int)Math.Round(
                s.PricePerWeek * PriceLevel * (1.0 + DislikeRaisesPrice * Math.Max(0, -s.Standing)));

        public Supplier SupplierFor(string businessId) =>
            Suppliers.FirstOrDefault(s => s.ServesBusinessId == businessId);

        public Supplier SupplierNamed(string id) =>
            Suppliers.FirstOrDefault(s => s.Id == id);

        // ---- the day ----

        /// Settles the district's money for one day. Called from the daily close
        /// AFTER the rackets have earned, so squeeze reflects what actually
        /// happened rather than what was established on paper.
        public List<EconomyEvent> DailyTick(GameTime now, Wallet wallet,
            double racketIncomeToday, double wagesPaidToday, double heat)
        {
            var events = new List<EconomyEvent>();

            Squeeze = Clamp(racketIncomeToday / Math.Max(1.0, SqueezeFullAt), 0.0, 1.0);
            double wages = Clamp(wagesPaidToday / Math.Max(1.0, WageFullAt), 0.0, 1.0);

            double prosperityTarget = Clamp(
                BaseProsperity
                - SqueezeCostsProsperity * Squeeze
                - HeatCostsProsperity * Clamp(heat, 0, 1)
                + WagesLiftProsperity * wages, 0.05, 0.95);

            double priceTarget = 1.0
                + SqueezeRaisesPrices * Squeeze
                + SupplyRaisesPrices * SupplyStrain();

            double beforeProsperity = Prosperity, beforePrice = PriceLevel;
            Prosperity += (prosperityTarget - Prosperity) * DriftPerDay;
            PriceLevel += (priceTarget - PriceLevel) * DriftPerDay;

            // Weekly deliveries. A supplier arrives, is paid or is not, and
            // forms an opinion about it either way.
            foreach (var s in Suppliers)
            {
                if (s.LastPaidDay >= 0 && now.Day - s.LastPaidDay < 7) continue;
                if (s.Refusing) continue;

                int price = DeliveryPrice(s);
                if (wallet != null && wallet.Spend(price, dirtyOk: true))
                {
                    bool dearer = price > s.LastPrice && s.LastPrice > 0;
                    s.LastPaidDay = now.Day;
                    s.LastPrice = price;
                    s.Unpaid = 0;
                    s.Standing = Clamp(s.Standing + PaymentBuysStanding, -1, 1);
                    events.Add(new EconomyEvent("supply",
                        dearer
                            ? $"{s.Name} brings {s.Goods} and asks £{price} for it now. He doesn't explain the difference."
                            : $"{s.Name} brings {s.Goods} and takes £{price} for it.", price));
                }
                else
                {
                    s.Unpaid++;
                    s.Standing = Clamp(s.Standing - 0.25, -1, 1);
                    events.Add(new EconomyEvent("supplier",
                        s.Unpaid == 1
                            ? $"{s.Name} brings {s.Goods} and leaves without being paid. He says nothing about it, which is worse."
                            : $"{s.Name} asks, for the {Ordinal(s.Unpaid)} time, about the money for {s.Goods}."));
                }
            }

            // Being squeezed is not something a supplier is insulated from — they
            // sell to this street too, and they hear who is taxing it. But it is
            // a DRIFT, not a countdown: a man who is paid every Thursday does not
            // walk out because the neighbourhood got poorer. He puts his price up
            // (see DeliveryPrice) and keeps coming. What loses a supplier is
            // neglect, which is the player's own decision and nobody else's.
            foreach (var s in Suppliers)
            {
                if (s.Refusing) continue;
                double pressure = SqueezeCostsSupplierStanding * Squeeze
                                + HeatCostsSupplierStanding * Clamp(heat, 0, 1);
                if (pressure > 0) s.Standing = Clamp(s.Standing - pressure, -1, 1);
                if (s.Standing <= SupplierRefusalFloor)
                {
                    s.Refusing = true;
                    events.Add(new EconomyEvent("refusal",
                        $"{s.Name} doesn't come. Word is he's found somewhere quieter to sell {s.Goods}."));
                }
            }

            // Only report the district's mood when it has actually moved enough
            // for a person to notice — otherwise this line becomes wallpaper.
            var mood = MoodLine(beforeProsperity, beforePrice);
            if (mood != null) events.Add(new EconomyEvent("prosperity", mood));

            return events;
        }

        /// Make it right with a supplier who has stopped coming. Expensive on
        /// purpose: the cheap moment to keep him was every week before this one.
        public bool MakeAmends(Supplier s, Wallet wallet, GameTime now, out string line)
        {
            line = null;
            if (s == null) return false;
            if (!s.Refusing)
            {
                line = $"{s.Name} is still coming. There is nothing to fix yet.";
                return false;
            }
            int price = (int)Math.Round(DeliveryPrice(s) * SupplierRecoveryPrice);
            if (wallet == null || !wallet.Spend(price, dirtyOk: true))
            {
                line = $"{s.Name} names a figure — £{price} — and waits. You don't have it.";
                return false;
            }
            s.Refusing = false;
            s.Standing = 0.1;
            s.Unpaid = 0;
            s.LastPaidDay = now.Day;
            line = $"{s.Name} takes the £{price} without counting it. {s.Goods.Substring(0, 1).ToUpperInvariant()}{s.Goods.Substring(1)} starts arriving again on Thursday.";
            return true;
        }

        /// How much of the district's supply is strained — refusing suppliers and
        /// unpaid ones both push prices up, because both mean scarcity.
        double SupplyStrain()
        {
            if (Suppliers.Count == 0) return 0;
            double strain = 0;
            foreach (var s in Suppliers)
                strain += s.Refusing ? 1.0 : Math.Min(1.0, s.Unpaid * 0.4);
            return strain / Suppliers.Count;
        }

        /// The district's state as somebody's circumstance. Never a number.
        string MoodLine(double beforeProsperity, double beforePrice)
        {
            const double Notice = 0.012;
            bool poorer = Prosperity < beforeProsperity - Notice;
            bool richer = Prosperity > beforeProsperity + Notice;
            bool dearer = PriceLevel > beforePrice + Notice;

            if (dearer && poorer)
                return "Two regulars drank at home tonight. The corner shop has put its prices up again, and everyone knows why.";
            if (poorer)
                return "The bar was quiet. Not empty — quiet, in the way a street gets when nobody has anything spare.";
            if (dearer)
                return "Prices went up on Hook Street this week. Nobody blamed you out loud.";
            if (richer)
                return "Somebody bought a round for the whole bar tonight. It has been a while since anyone could.";
            return null;
        }

        public string StatusLine() =>
            $"street: {ProsperityWord()}, prices {PriceWord()}" +
            (Suppliers.Any(s => s.Refusing) ? ", supply short" : "");

        public string ProsperityWord() =>
            Prosperity >= 0.65 ? "comfortable" : Prosperity >= 0.45 ? "getting by"
            : Prosperity >= 0.28 ? "tight" : "hurting";

        public string PriceWord() =>
            PriceLevel >= 1.25 ? "steep" : PriceLevel >= 1.10 ? "up" : "ordinary";

        static string Ordinal(int n) =>
            n == 2 ? "second" : n == 3 ? "third" : n == 4 ? "fourth" : n + "th";

        static double Clamp(double v, double lo, double hi) => v < lo ? lo : v > hi ? hi : v;

        // ---- persistence (P5: the city's state is the save file) ----

        public Dictionary<string, object> Capture()
        {
            var suppliers = new List<object>();
            foreach (var s in Suppliers)
                suppliers.Add(new Dictionary<string, object>
                {
                    { "id", s.Id }, { "standing", s.Standing }, { "refusing", s.Refusing },
                    { "lastPaidDay", s.LastPaidDay }, { "unpaid", s.Unpaid },
                    { "lastPrice", s.LastPrice },   // the "he charges more now" baseline (audit 2026-07-27)
                });
            return new Dictionary<string, object>
            {
                { "prosperity", Prosperity }, { "priceLevel", PriceLevel },
                { "squeeze", Squeeze }, { "suppliers", suppliers },
            };
        }

        public void Restore(Dictionary<string, object> data)
        {
            if (data == null) return;
            Prosperity = Clamp(GetD(data, "prosperity", 0.5), 0.0, 1.0);
            PriceLevel = Clamp(GetD(data, "priceLevel", 1.0), 0.5, 3.0);
            Squeeze = Clamp(GetD(data, "squeeze", 0.0), 0.0, 1.0);

            var list = MiniJson.GetList(data, "suppliers");
            if (list == null) return;
            foreach (var raw in list)
            {
                var o = MiniJson.AsObject(raw);
                if (o == null) continue;
                var s = SupplierNamed(MiniJson.GetString(o, "id"));
                if (s == null) continue;
                s.Standing = Clamp(GetD(o, "standing", 0.0), -1, 1);
                s.Refusing = o.TryGetValue("refusing", out var r) && r is bool b && b;
                s.LastPaidDay = MiniJson.GetInt(o, "lastPaidDay");
                s.Unpaid = MiniJson.GetInt(o, "unpaid");
                s.LastPrice = MiniJson.GetInt(o, "lastPrice");
            }
        }

        static double GetD(Dictionary<string, object> o, string key, double fallback)
        {
            if (o == null || !o.TryGetValue(key, out var v) || v == null) return fallback;
            if (v is double d) return d;
            if (v is long l) return l;
            if (v is int i) return i;
            return double.TryParse(Convert.ToString(v,
                System.Globalization.CultureInfo.InvariantCulture),
                System.Globalization.NumberStyles.Float,
                System.Globalization.CultureInfo.InvariantCulture, out var p) ? p : fallback;
        }
    }
}
