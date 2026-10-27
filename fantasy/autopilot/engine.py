"""Per-league logic: read the league's rules, then plan (and maybe apply) moves."""

import re
import time
from collections import Counter

from . import fantasypros as fp
from .lineup import EMPTY, SLOT_ELIGIBILITY, optimize, starter_slots
from .rankings import IdMap, RankList, load_fp_to_sleeper, norm_name
from .waivers import faab_bid, plan_stream, plan_upgrades

SKILL = ("QB", "RB", "WR", "TE")
UNRANKED = 999      # player missing from the ECR list
UNAVAILABLE = 5000  # bye / injured: only start him if there is literally nobody else
FAAB = 2            # Sleeper settings.waiver_type


class Session:
    """Shared, per-run data: Sleeper state + player db, cached ECR lists."""

    def __init__(self, read, write, cache_dir, now=None):
        self.read, self.write = read, write
        self.now = time.time() if now is None else now
        self.state = read.state()
        self.players = read.players()
        self.idmap = IdMap(self.players, load_fp_to_sleeper(cache_dir))
        self._lists = {}

    def ranks(self, slug):
        if slug not in self._lists:
            self._lists[slug] = RankList(fp.fetch(slug), self.idmap, self.now)
        return self._lists[slug]


def _pos_rank_number(pos_rank):
    m = re.search(r"(\d+)$", pos_rank or "")
    return int(m.group(1)) if m else None


def superflex_template(op_list, players):
    """Overall rank of the Nth QB/RB/WR/TE in the weekly superflex ECR.

    FantasyPros has no rest-of-season superflex list, and its ROS overall list
    is 1QB-flavoured (QBs ranked low). Mapping ROS positional ranks through
    this template puts QBs back at superflex value.
    """
    by_pos = {p: [] for p in SKILL}
    for sid, r in op_list.by_id.items():
        pos = (players.get(sid) or {}).get("position")
        if pos in by_pos and not r.bye:
            by_pos[pos].append(r.rank)
    return {p: sorted(v) for p, v in by_pos.items() if v}


def template_value(template, pos, n):
    ranks = template.get(pos)
    if not ranks or n is None:
        return None
    if n <= len(ranks):
        return ranks[n - 1]
    tail = ranks[-10:]
    step = max(1.0, (tail[-1] - tail[0]) / max(1, len(tail) - 1))
    return ranks[-1] + step * (n - len(ranks))


class League:
    def __init__(self, session, data, user_id, cfg):
        self.s, self.data, self.cfg = session, data, cfg
        self.id, self.name = data["league_id"], data.get("name", data["league_id"])
        self.slots = starter_slots(data.get("roster_positions") or [])
        self.fmt = fp.scoring_format(data.get("scoring_settings") or {})
        self.qb_premium = "SUPER_FLEX" in self.slots or self.slots.count("QB") >= 2
        self.settings = data.get("settings") or {}
        self.faab = self.settings.get("waiver_type") == FAAB
        self.rosters = session.read.rosters(self.id)
        self.roster = next((r for r in self.rosters if r.get("owner_id") == user_id
                            or user_id in (r.get("co_owners") or [])), None)
        self.lines, self.errors = [], 0

    # ---- player helpers -------------------------------------------------
    def player(self, pid):
        return self.s.players.get(pid) or {}

    def pos(self, pid):
        return self.player(pid).get("position") or "?"

    def positions(self, pid):
        p = self.player(pid)
        return set(p.get("fantasy_positions") or [p.get("position")])

    def team(self, pid):
        return pid if self.pos(pid) == "DEF" else self.player(pid).get("team")

    def label(self, pid, rank=None):
        if pid == EMPTY:
            return "(empty)"
        p = self.player(pid)
        name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or pid
        tag = f"{self.pos(pid)} {self.team(pid) or 'FA'}"
        if rank is not None:
            tag += f", {rank.pos_rank} / #{rank.rank}" if hasattr(rank, "pos_rank") else f", #{rank:g}"
        return f"{name} ({tag})"

    def active_players(self):
        r = self.roster
        hidden = set(r.get("reserve") or []) | set(r.get("taxi") or [])
        return [p for p in (r.get("players") or []) if p not in hidden]

    def weekly_list(self, pos):
        if pos == "K":
            return self.s.ranks(fp.WEEKLY_K)
        if pos == "DEF":
            return self.s.ranks(fp.WEEKLY_DST)
        if pos not in SKILL:
            return None
        if self.qb_premium:  # one list ranking QBs against RB/WR/TE
            return self.s.ranks(fp.WEEKLY_OP[self.fmt])
        return self.s.ranks(fp.WEEKLY_QB if pos == "QB" else fp.WEEKLY_FLEX[self.fmt])

    def weekly_rank(self, pid):
        lst = self.weekly_list(self.pos(pid))
        return lst.get(pid) if lst else None

    def never_drop(self):
        wanted = {str(x) for x in self.cfg["never_drop"]}
        names = {norm_name(x) for x in wanted}
        return {pid for pid in (self.roster.get("players") or [])
                if pid in wanted or norm_name(self.player(pid).get("full_name")) in names}

    # ---- lineup ---------------------------------------------------------
    def plan_lineup(self):
        main = self.weekly_list("QB" if self.qb_premium else "RB")
        week = int(self.s.state["week"])
        if main.week != week:
            self.lines.append(f"- Lineup skipped: FantasyPros weekly ECR is for week {main.week}, "
                              f"Sleeper is on week {week}.")
            return None
        positions = {p for s in self.slots for p in SLOT_ELIGIBILITY.get(s, ())}
        kickoff = {}
        for p in positions:
            kickoff.update(self.weekly_list(p).team_kickoff)
        now = self.s.now

        def status(pid):
            r = self.weekly_rank(pid)
            ko = (r.kickoff if r else None) or kickoff.get(self.team(pid))
            locked = bool(r and r.started) or bool(ko and ko <= now)
            injury = self.player(pid).get("injury_status")
            if injury in self.cfg["bench_statuses"]:
                why = injury
            elif (r and r.bye) or self.team(pid) not in kickoff:
                why = "bye/no game"
            else:
                why = None
            return r, locked, why

        info = {pid: status(pid) for pid in set(self.active_players()) | set(self.roster.get("starters") or [])
                if pid != EMPTY}
        bonus = self.cfg["superflex_qb_bonus"]

        def cost(pid, slot):
            if not self.positions(pid) & SLOT_ELIGIBILITY[slot]:
                return None
            r, _, why = info[pid]
            c = (r.rank if r else UNRANKED) + (UNAVAILABLE if why else 0)
            if slot == "SUPER_FLEX" and "QB" in self.positions(pid):
                c -= bonus
            return c

        locked = {pid for pid, (_, lk, _) in info.items() if lk}
        result = optimize(self.slots, self.roster.get("starters") or [], self.active_players(), cost, locked)
        result.info = info
        return result

    def report_lineup(self, result):
        if result is None:
            return
        def desc(pid):
            r, _, why = result.info[pid]
            return self.label(pid, r) + (f" [{why}]" if why else "")

        before = [p for p in (self.roster.get("starters") or []) if p != EMPTY]
        after = [p for p in result.starters if p != EMPTY]
        if not result.changes:
            self.lines.append(f"- Lineup already optimal for week {self.s.state['week']}.")
        else:
            benched = [desc(p) for p in before if p not in after]
            started = [f"**{desc(p)}**" for p in after if p not in before]
            if benched:
                self.lines.append(f"- Bench: {', '.join(benched)}")
            if started:
                self.lines.append(f"- Start: {', '.join(started)}")
            lineup = " · ".join(f"{slot} {self.label(pid).split(' (')[0]}"
                                for slot, pid in zip(self.slots, result.starters))
            self.lines.append(f"- New lineup: {lineup}")
        if result.locked:
            self.lines.append(f"- Locked (game started): {', '.join(self.label(p) for p in result.locked)}")
        bad = [pid for pid in result.starters
               if pid != EMPTY and result.info[pid][2] and pid not in result.locked]
        for pid in bad:
            self.lines.append(f"- ⚠️ Starting {self.label(pid)} [{result.info[pid][2]}]: no healthy option left.")

    # ---- waivers --------------------------------------------------------
    def minimums(self):
        c = Counter(self.slots)
        mins = {"QB": c["QB"] + c["SUPER_FLEX"], "RB": c["RB"], "WR": c["WR"], "TE": c["TE"],
                "K": c["K"], "DEF": c["DEF"]}
        if self.qb_premium:
            mins["QB"] += 1  # bye-week / injury cover when you start two QBs
        for p in ("RB", "WR"):
            mins[p] += 1 if mins[p] else 0
        mins.update(self.cfg["min_roster"])
        return mins

    def max_depth(self):
        """Past this many healthy players at a position, extra ones barely help (a 4th QB)."""
        c = Counter(self.slots)
        return {"QB": c["QB"] + c["SUPER_FLEX"] + 1, "TE": c["TE"] + 1}

    def plan_waivers(self):
        my_rid = self.roster["roster_id"]
        rostered = set()
        for r in self.rosters:
            rostered |= set(r.get("players") or []) | set(r.get("reserve") or []) | set(r.get("taxi") or [])
        pending = []
        if self.s.write:
            try:
                pending = [t for t in self.s.write.pending_waivers(self.id)
                           if my_rid in (t.get("roster_ids") or [])]
            except RuntimeError as e:
                self.lines.append(f"- ⚠️ Couldn't read your pending claims ({e}); duplicates are possible.")
        pending_adds = {pid for t in pending for pid in (t.get("adds") or {})}
        pending_drops = {pid for t in pending for pid in (t.get("drops") or {})}
        if pending:
            self.lines.append(f"- {len(pending)} claim(s) already pending; not repeating them.")

        ros = self.s.ranks(fp.ROS_OVERALL[self.fmt])
        template = superflex_template(self.weekly_list("QB"), self.s.players) if self.qb_premium else None

        def value(pid):
            pos, r = self.pos(pid), ros.get(pid)
            if pos not in SKILL or r is None:
                return None
            return template_value(template, pos, _pos_rank_number(r.pos_rank)) if template else r.rank

        keep = self.never_drop()

        def drop_value(pid):
            if pid in keep or self.pos(pid) not in SKILL:
                return None
            v = value(pid)
            if v is None and ros.get(pid) is None and self.weekly_rank(pid) is None:
                return UNRANKED  # in neither ROS nor weekly ECR: safe to cut
            return v

        mine = self.active_players()
        relevant = {p for s in self.slots for p in SLOT_ELIGIBILITY.get(s, ())} & set(SKILL)
        fas = [pid for pid in ros.by_id if pid not in rostered and pid not in pending_adds
               and self.pos(pid) in relevant and self.player(pid).get("team")]

        def ros_cost(pid, slot):
            if not self.positions(pid) & SLOT_ELIGIBILITY[slot]:
                return None
            v = value(pid)
            return UNRANKED if v is None else v

        core = set(optimize(self.slots, [], mine, ros_cost).starters) - {EMPTY}
        limit = sum(1 for s in self.data.get("roster_positions") or [] if s not in ("IR", "TAXI"))
        claims = plan_upgrades(free_agents=fas, my_players=mine, value=value, drop_value=drop_value,
                               position=self.pos, protected=core, minimums=self.minimums(),
                               roster_limit=limit, max_claims=self.cfg["max_claims"],
                               min_gain=self.cfg["min_gain"], blocked_drops=pending_drops,
                               max_depth=self.max_depth(),
                               healthy=lambda p: self.player(p).get("injury_status") not in self.cfg["bench_statuses"])
        if self.cfg["stream_k_def"]:
            claims += self._plan_streams(rostered | pending_adds, mine, pending_drops, keep,
                                         open_spot=limit - len(mine) - sum(c.drop is None for c in claims) > 0)
        self._set_bids(claims)
        return claims

    def _plan_streams(self, unavailable, mine, pending_drops, keep, open_spot):
        out = []
        for pos, slug in (("K", fp.WEEKLY_K), ("DEF", fp.WEEKLY_DST)):
            if pos not in self.slots:
                continue
            wl = self.s.ranks(slug)
            first = wl.first_kickoff()
            if not first or first <= self.s.now:
                self.lines.append(f"- {pos} streaming skipped: next week's {pos} ECR isn't out yet.")
                continue

            def wv(pid, wl=wl):
                r = wl.get(pid)
                return None if r is None or r.bye else r.rank

            fas = [pid for pid in wl.by_id if pid not in unavailable]
            my = [p for p in mine if self.pos(p) == pos and p not in pending_drops and p not in keep]
            claim = plan_stream(free_agents=fas, mine=my, value=wv, margin=self.cfg["stream_margin"],
                                open_spot=open_spot)
            if claim and claim.drop:
                # Never give away a top-12 K/DEF for one good week (e.g. to cover his bye),
                # unless the streamer is also the better pick for the rest of the season.
                ros = self.s.ranks(fp.ROS_K if pos == "K" else fp.ROS_DST)

                def ros_num(pid, ros=ros):
                    r = ros.get(pid)
                    n = _pos_rank_number(r.pos_rank) if r else None
                    return n or 999

                if ros_num(claim.drop) <= 12 and ros_num(claim.add) >= ros_num(claim.drop):
                    self.lines.append(f"- Keeping {self.label(claim.drop)} ({pos}{ros_num(claim.drop)} rest of "
                                      f"season) rather than dropping him for a one-week {pos} stream.")
                    claim = None
            if claim:
                out.append(claim)
        return out

    def _set_bids(self, claims):
        if not self.faab:
            return
        budget = (self.settings.get("waiver_budget") or 0) - ((self.roster.get("settings") or {})
                                                              .get("waiver_budget_used") or 0)
        min_bid = self.settings.get("waiver_bid_min") or 0
        for c in claims:
            if c.kind == "upgrade":
                c.bid = faab_bid(c.add_value, budget, self.cfg["faab_tiers"], min_bid)
            else:
                c.bid = min_bid if budget >= min_bid else None
        if any(c.bid is None for c in claims):
            self.lines.append("- ⚠️ Not enough FAAB left for some claims; skipped them.")
            claims[:] = [c for c in claims if c.bid is not None]

    def report_waivers(self, claims):
        if not claims:
            self.lines.append("- No waiver claims worth making.")
            return
        if self.redact:
            self.lines.append(f"- {len(claims)} waiver claim(s) planned (details hidden in public logs).")
            return
        unit = "ROS, SF-adjusted" if self.qb_premium else "ROS"
        for c in claims:
            add = self.label(c.add, c.add_value)
            drop = f"drop {self.label(c.drop, c.drop_value)}" if c.drop else "no drop (open roster spot)"
            bid = f", bid ${c.bid}" if c.bid is not None else ""
            what = f"{unit} value" if c.kind == "upgrade" else "this week's ECR"
            self.lines.append(f"- Claim **{add}**, {drop}{bid} _(by {what})_")

    # ---- driver ---------------------------------------------------------
    def describe(self):
        flags = [self.fmt, "superflex" if "SUPER_FLEX" in self.slots else
                 ("2QB" if self.qb_premium else "1QB"), "FAAB" if self.faab else "waiver priority"]
        scoring = self.data.get("scoring_settings") or {}
        if scoring.get("bonus_rec_te") or (scoring.get("pass_td") or 4) >= 6:
            flags.append("custom scoring (TE premium / 6pt pass TD): ECR is an approximation")
        return f"### {self.name}\n_{' · '.join(flags)} · slots: {' '.join(self.slots)}_"

    def run(self, task, apply, redact):
        self.redact = redact
        self.lines.append(self.describe())
        if self.roster is None:
            self.lines.append("- You don't own a roster in this league; skipped.")
            return self.lines
        if self.data.get("status") != "in_season":
            self.lines.append(f"- League status is `{self.data.get('status')}`; nothing to do.")
            return self.lines
        if task in ("lineup", "all"):
            if self.settings.get("best_ball"):
                self.lines.append("- Best ball league: Sleeper picks the lineup.")
            else:
                self._step("lineup", apply and self.cfg["auto_lineup"], self.plan_lineup,
                           self.report_lineup, self._apply_lineup)
        if task in ("waivers", "all"):
            self._step("waivers", apply and self.cfg["auto_waivers"], self.plan_waivers,
                       self.report_waivers, self._apply_waivers)
        return self.lines

    def _step(self, name, apply, plan, report, do_apply):
        try:
            result = plan()
            report(result)
            if apply and result:
                do_apply(result)
        except Exception as e:  # keep going with the other leagues
            self.errors += 1
            self.lines.append(f"- ❌ {name} failed: {e}")

    def _apply_lineup(self, result):
        if not result.changes:
            return
        self.s.write.set_starters(self.id, self.roster["roster_id"], result.starters)
        self.lines.append("- ✅ Lineup saved to Sleeper.")

    def _apply_waivers(self, claims):
        for n, c in enumerate(claims, 1):
            who = f"#{n}" if self.redact else self.label(c.add)
            try:
                self.s.write.submit_waiver_claim(self.id, self.roster["roster_id"], c.add, c.drop,
                                                 c.bid if self.faab else None)
                self.lines.append(f"- ✅ Claim {who} submitted.")
            except RuntimeError as e:
                self.errors += 1
                self.lines.append(f"- ❌ Claim {who} failed: {e}")
