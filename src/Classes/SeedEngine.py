from abc import ABC, abstractmethod


# ============================================================================
# RANKING PRIMITIVES
# ============================================================================

class RankingCriterion(ABC):
    """
    A single ranking rule, applied to a group of currently-tied teams.
    """

    @abstractmethod
    def partition(self, teams) -> list:
        """
        Split a group of tied teams into ordered tied-subgroups.

        Args:
            teams: list of Team objects, all currently tied with each other

        Returns:
            list of lists of Team, best subgroup first. Subgroups of size 1
            are final; subgroups of size > 1 are still tied on this
            criterion and get recursed into with the remaining criteria.
        """
        raise NotImplementedError


class ValueCriterion(RankingCriterion):
    """
    Groups teams by a descending scalar key (e.g. wins, division win%, CEW).
    Teams with an equal key stay tied in the same subgroup.
    """

    def __init__(self, key_func, default=0.0):
        self.key_func = key_func
        self.default = default

    def partition(self, teams):
        keyed = [(self.key_func(team), team) for team in teams]
        keyed.sort(key=lambda pair: pair[0], reverse=True)

        groups = []
        for value, team in keyed:
            if groups and groups[-1][0] == value:
                groups[-1][1].append(team)
            else:
                groups.append((value, [team]))
        return [group for _, group in groups]


def classify_h2h_group(teams):
    """
    Classify each team in a tied group by its head-to-head record against
    every OTHER team in that same group.

    A team is a sweep winner only if it has complete head-to-head data
    (Team.getH2hRecord != -1) against every other team in the group AND
    beat (> 0.5) every one of them. Symmetric definition for a swept
    loser. Any team missing data against even one group member, or with
    a mixed/cyclic result, is undecided.

    Returns:
        (winners, undecided, losers) - lists of Team
    """
    winners, undecided, losers = [], [], []

    for team in teams:
        others = [other for other in teams if other is not team]
        records = [team.getH2hRecord(other.roster_id) for other in others]

        if any(record == -1 for record in records):
            undecided.append(team)
        elif all(record > 0.5 for record in records):
            winners.append(team)
        elif all(record < 0.5 for record in records):
            losers.append(team)
        else:
            undecided.append(team)

    return winners, undecided, losers


class H2HGroupCriterion(RankingCriterion):
    """Head-to-head tiebreak, evaluated across the whole tied group at once."""

    def partition(self, teams):
        winners, undecided, losers = classify_h2h_group(teams)
        return [group for group in (winners, undecided, losers) if group]


def rank_teams(teams, criteria):
    """
    Resolve a group of teams into a single fully-ordered list by applying
    `criteria` in order. Within each criterion's tied subgroups, recurse
    with the remaining criteria. When criteria are exhausted, falls back
    to a deterministic order by roster_id.

    Args:
        teams: list of Team objects to rank (assumed already tied going in)
        criteria: list of RankingCriterion to apply in order

    Returns:
        list of Team, best first
    """
    if len(teams) <= 1:
        return list(teams)

    if not criteria:
        return sorted(teams, key=lambda team: team.roster_id)

    groups = criteria[0].partition(teams)

    result = []
    for group in groups:
        if len(group) == 1:
            result.extend(group)
        else:
            result.extend(rank_teams(group, criteria[1:]))
    return result


# ============================================================================
# LFL CRITERIA CHAINS
# ============================================================================

def _division_win_pct(team):
    wins, losses = team.getDivisionRecord()
    total = wins + losses
    return wins / total if total > 0 else 0.0


def _cew(team):
    value = team.getCEW()
    return value if value is not None else 0.0


DIVISION_CRITERIA = [
    ValueCriterion(lambda team: team.wins),
    H2HGroupCriterion(),
    ValueCriterion(_division_win_pct),
    ValueCriterion(_cew),
]

LEAGUE_LEADER_CRITERIA = [
    ValueCriterion(lambda team: team.wins),
    H2HGroupCriterion(),
    ValueCriterion(_cew),
]


# ============================================================================
# DIVISION SEEDING
# ============================================================================

def compute_division_seeding(teams, criteria=DIVISION_CRITERIA):
    """
    Groups teams by division and assigns a 1-indexed division_seed to each
    team within its division. Teams with a falsy division are skipped.

    Args:
        teams: dict or list of Team objects
    """
    teams_list = list(teams.values()) if isinstance(teams, dict) else list(teams)

    divisions = {}
    for team in teams_list:
        if team.division:
            divisions.setdefault(team.division, []).append(team)

    for div_teams in divisions.values():
        ranked = rank_teams(div_teams, criteria)
        for i, team in enumerate(ranked):
            team.division_seed = i + 1


# ============================================================================
# LEAGUE SEEDING
# ============================================================================

def _sample_best_remaining_per_division(non_leaders, criteria):
    """
    Seeds non-leader teams by repeatedly comparing the current-best
    not-yet-seeded team from each division and picking the overall best
    candidate each round. Within a division, teams are only ever offered
    as a candidate in their own division_seed order (a division's #3 can
    never be picked before its own #2).

    Args:
        non_leaders: list of Team objects (division_seed != 1)
        criteria: list of RankingCriterion used to compare candidates

    Returns:
        list of Team, best (next seed) first
    """
    by_division = {}
    for team in non_leaders:
        by_division.setdefault(team.division, []).append(team)
    for div_teams in by_division.values():
        div_teams.sort(key=lambda team: team.division_seed)

    pointers = {division: 0 for division in by_division}
    result = []

    remaining = len(non_leaders)
    while remaining > 0:
        candidates = []
        for division, div_teams in by_division.items():
            pointer = pointers[division]
            if pointer < len(div_teams):
                candidates.append(div_teams[pointer])

        best = rank_teams(candidates, criteria)[0]
        result.append(best)
        pointers[best.division] += 1
        remaining -= 1

    return result


def compute_league_seeding(teams, leader_criteria=LEAGUE_LEADER_CRITERIA):
    """
    Assigns a 1-indexed league_seed to every team. Division leaders
    (division_seed == 1) always occupy the top seeds ahead of every
    non-leader. Requires division_seed to already be set on every team.

    Args:
        teams: dict or list of Team objects
    """
    teams_list = list(teams.values()) if isinstance(teams, dict) else list(teams)

    leaders = [team for team in teams_list if team.division_seed == 1]
    non_leaders = [team for team in teams_list if team.division_seed != 1]

    ordered_leaders = rank_teams(leaders, leader_criteria)
    ordered_non_leaders = _sample_best_remaining_per_division(non_leaders, leader_criteria)

    for i, team in enumerate(ordered_leaders + ordered_non_leaders):
        team.league_seed = i + 1


# ============================================================================
# PUBLIC FACADES (unchanged signatures, used by FantasyLeague.py)
# ============================================================================

class LFLDivisionSeeder:
    """
    LFL-specific division seeder.

    Tiebreaker order:
    1. Record (wins)
    2. Head-to-head record (evaluated across the whole tied group)
    3. Division record
    4. Expected wins (CEW)
    """

    def calculate_and_update_seeding(self, teams):
        compute_division_seeding(teams)


class LFLLeagueSeeder:
    """
    LFL-specific league seeder.

    Division leaders always rank ahead of non-leaders. Leaders are ranked
    among themselves by wins, then group head-to-head, then CEW. The rest
    are seeded by sampling the best remaining team from each division,
    using the same criteria, until everyone is seeded.
    """

    def calculate_and_update_seeding(self, teams):
        compute_league_seeding(teams)


class SeedEngine:
    """
    Orchestrates division and league seeding. Accepts any
    division_seeder/league_seeder implementing calculate_and_update_seeding.
    """

    def __init__(self, division_seeder=None, league_seeder=None):
        self.division_seeder = division_seeder
        self.league_seeder = league_seeder

    def calculate_and_update_seeding(self, teams):
        """
        Computes both division and league seeding for teams. Directly
        modifies the team objects by setting their division_seed and
        league_seed attributes.

        Args:
            teams: dict or list of Team objects
        """
        self.division_seeder.calculate_and_update_seeding(teams)
        self.league_seeder.calculate_and_update_seeding(teams)
