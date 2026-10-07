from SeedEngine import (
    DIVISION_CRITERIA,
    LEAGUE_LEADER_CRITERIA,
    compute_division_seeding,
    compute_league_seeding,
    rank_teams,
)


class FakeTeam:
    """Minimal Team-like stand-in: no Sleeper API, no pandas, no metrics."""

    def __init__(self, roster_id, division=None, wins=0, division_seed=0,
                 cew=0.0, division_record=(0, 0)):
        self.roster_id = roster_id
        self.division = division
        self.wins = wins
        self.division_seed = division_seed
        self._cew = cew
        self._division_record = division_record
        self._h2h = {}

    def getH2hRecord(self, other_team_id):
        return self._h2h.get(other_team_id, -1)

    def getDivisionRecord(self):
        return self._division_record

    def getCEW(self):
        return self._cew


def set_result(winner, loser):
    """Record a single head-to-head game between two FakeTeams."""
    winner._h2h[loser.roster_id] = 1.0
    loser._h2h[winner.roster_id] = 0.0


def test_h2h_cycle_falls_through_as_a_group():
    a = FakeTeam(1, wins=5, division_record=(3, 1))
    b = FakeTeam(2, wins=5, division_record=(2, 2))
    c = FakeTeam(3, wins=5, division_record=(1, 3))
    set_result(winner=a, loser=b)
    set_result(winner=b, loser=c)
    set_result(winner=c, loser=a)

    ranked = rank_teams([a, b, c], DIVISION_CRITERIA)

    assert ranked == [a, b, c]


def test_clean_sweep_winner_isolated_then_remaining_three_recurse():
    d = FakeTeam(1, wins=5, division_record=(0, 0), cew=0.0)
    a = FakeTeam(2, wins=5, division_record=(0, 0), cew=3.0)
    b = FakeTeam(3, wins=5, division_record=(0, 0), cew=2.0)
    c = FakeTeam(4, wins=5, division_record=(0, 0), cew=1.0)

    set_result(winner=d, loser=a)
    set_result(winner=d, loser=b)
    set_result(winner=d, loser=c)
    set_result(winner=a, loser=b)
    set_result(winner=b, loser=c)
    set_result(winner=c, loser=a)

    ranked = rank_teams([d, a, b, c], DIVISION_CRITERIA)

    assert ranked[0] is d
    assert ranked[1:] == [a, b, c]


def test_incomplete_h2h_data_blocks_sweep_verdict():
    x = FakeTeam(1, wins=5, division_record=(2, 0), cew=5.0)
    y = FakeTeam(2, wins=5, division_record=(1, 1), cew=3.0)
    z = FakeTeam(3, wins=5, division_record=(0, 2), cew=1.0)
    set_result(winner=x, loser=y)
    # x and z never played each other - x cannot be ruled a sweep winner

    ranked = rank_teams([x, y, z], DIVISION_CRITERIA)

    assert ranked == [x, y, z]


def test_division_leader_outranks_higher_win_non_leader():
    a_leader = FakeTeam(1, division="A", wins=5, division_seed=1, cew=1.0)
    a2 = FakeTeam(2, division="A", wins=3, division_seed=2, cew=1.0)
    b_leader = FakeTeam(3, division="B", wins=10, division_seed=1, cew=1.0)
    b2 = FakeTeam(4, division="B", wins=8, division_seed=2, cew=1.0)

    teams = {t.roster_id: t for t in (a_leader, a2, b_leader, b2)}
    compute_league_seeding(teams)

    assert a_leader.league_seed < b2.league_seed
    assert b_leader.league_seed < a_leader.league_seed
    assert {a_leader.league_seed, b_leader.league_seed} == {1, 2}


def test_zero_weeks_played_cew_does_not_crash_comparison():
    played = FakeTeam(1, wins=5, division_record=(0, 0), cew=0.8)
    never_played = FakeTeam(2, wins=5, division_record=(0, 0), cew=None)

    ranked = rank_teams([played, never_played], DIVISION_CRITERIA)

    assert ranked == [played, never_played]


def test_exhausted_criteria_falls_back_to_roster_id():
    high_id = FakeTeam(9, wins=5, division_record=(1, 1), cew=1.0)
    low_id = FakeTeam(2, wins=5, division_record=(1, 1), cew=1.0)

    ranked = rank_teams([high_id, low_id], DIVISION_CRITERIA)

    assert ranked == [low_id, high_id]


def test_per_division_sampling_respects_own_division_seed_order():
    a_leader = FakeTeam(1, division="A", wins=10, division_seed=1)
    a2 = FakeTeam(2, division="A", wins=2, division_seed=2)
    a3 = FakeTeam(3, division="A", wins=9, division_seed=3)
    b_leader = FakeTeam(4, division="B", wins=8, division_seed=1)
    b2 = FakeTeam(5, division="B", wins=5, division_seed=2)

    teams = {t.roster_id: t for t in (a_leader, a2, a3, b_leader, b2)}
    compute_league_seeding(teams)

    # a3 has far more wins than a2, but is division A's own #3 seed and
    # must never be assigned a league seed ahead of A's own #2 (a2).
    assert a2.league_seed < a3.league_seed
