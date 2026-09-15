from functools import cmp_to_key
from abc import ABC, abstractmethod


# ============================================================================
# SEED CRITERIA CLASSES
# ============================================================================

class SeedCriteria(ABC):
    """
    Base class for seeding criteria.
    Each criteria defines a single comparison rule between two teams.
    """

    @staticmethod
    @abstractmethod
    def calculate(t1, t2):
        """
        Compare two teams based on a specific criterion.

        Args:
            t1: First team object
            t2: Second team object

        Returns:
            1 if t1 is better than t2
            -1 if t2 is better than t1
            0 if they are tied on this criterion
        """
        pass


class RecordCriteria(SeedCriteria):
    """Compare teams by their win-loss record."""

    @staticmethod
    def calculate(t1, t2):
        if t1.wins > t2.wins:
            return 1
        elif t1.wins < t2.wins:
            return -1
        return 0


class H2HCriteria(SeedCriteria):
    """Compare teams by their head-to-head record."""

    @staticmethod
    def calculate(t1, t2):
        h2h = t1.getH2hRecord(t2.roster_id)
        print(t1.name, t2.name, h2h)
        if h2h > 0.5:
            return 1
        elif 0 <= h2h < 0.5:
            return -1
        return 0


class DivisionRecordCriteria(SeedCriteria):
    """Compare teams by their division record."""

    @staticmethod
    def calculate(t1, t2):
        div_rec1 = t1.getDivisionRecord()
        div_rec2 = t2.getDivisionRecord()
        div_perc1 = div_rec1[0] / (div_rec1[0] + div_rec1[1]) if (div_rec1[0] + div_rec1[1]) > 0 else 0
        div_perc2 = div_rec2[0] / (div_rec2[0] + div_rec2[1]) if (div_rec2[0] + div_rec2[1]) > 0 else 0
        if div_perc1 > div_perc2:
            return 1
        elif div_perc1 < div_perc2:
            return -1
        return 0


class ExpectedWinsCriteria(SeedCriteria):
    """Compare teams by their expected wins."""

    @staticmethod
    def calculate(t1, t2):
        expw1 = t1.to_dict().get("CEW", None)
        expw2 = t2.to_dict().get("CEW", None)
        if expw1 > expw2:
            return 1
        elif expw1 < expw2:
            return -1
        return 0


class DivisionSeedCriteria(SeedCriteria):
    """Compare teams by their division seed (lower is better)."""

    @staticmethod
    def calculate(t1, t2):
        if t1.division_seed < t2.division_seed:
            return 1
        elif t1.division_seed > t2.division_seed:
            return -1
        return 0


class SameDivisionCriteria(SeedCriteria):
    """
    Special criteria: Only applies if teams are in the same division.
    Uses their division seed to break ties.
    """

    @staticmethod
    def calculate(t1, t2):
        # Only apply if teams are in the same division
        if t1.division == t2.division:
            if t1.division_seed < t2.division_seed:
                return 1
            elif t1.division_seed > t2.division_seed:
                return -1
        return 0


class DivisionLeaderCriteria(SeedCriteria):
    """
    Special criteria: Prioritize teams that are first in their division.
    Only applies when one team is #1 seed and the other is not.
    """

    @staticmethod
    def calculate(t1, t2):
        # Only apply if exactly one team is #1 seed in their division
        if t1.division_seed == 1 or t2.division_seed == 1:
            if t1.division_seed == 1 and t2.division_seed != 1:
                return 1
            elif t1.division_seed != 1 and t2.division_seed == 1:
                return -1
        return 0


# ============================================================================
# SEEDER CLASSES
# ============================================================================

class Seeder(ABC):
    """
    Base class for seeding systems.
    Uses a chain of SeedCriteria to compare teams.
    """

    def __init__(self, criteria_chain=None):
        """
        Initialize seeder with a chain of criteria.

        Args:
            criteria_chain: List of SeedCriteria classes to apply in order
        """
        self.criteria_chain = criteria_chain if criteria_chain else []

    def _compare(self, t1, t2):
        """
        Compare two teams using the criteria chain.
        Iterates through criteria until one returns a non-zero result.

        Args:
            t1: First team object
            t2: Second team object

        Returns:
            1 if t1 is better, -1 if t2 is better, 0 if tied
        """
        for criteria in self.criteria_chain:
            result = criteria.calculate(t1, t2)
            if result != 0:
                return result
        return 0

    @abstractmethod
    def calculate_and_update_seeding(self, teams):
        """
        Calculate seeding and update team objects.
        Must be implemented by subclasses.
        """
        pass


class DivisionSeeder(Seeder):
    """
    Abstract base class for division seeding.
    Provides generic implementation for calculating division seeds.
    Subclasses should define their own criteria chain.
    """

    def calculate_and_update_seeding(self, teams):
        """
        Calculate division seeding for all teams.
        Groups teams by division and assigns division_seed to each team.

        Args:
            teams: List or dict of Team objects
        """
        # Convert to list if dict
        if isinstance(teams, dict):
            teams_list = list(teams.values())
        else:
            teams_list = teams

        # Group teams by division
        divisions = {}
        for team in teams_list:
            if team.division:
                if team.division not in divisions:
                    divisions[team.division] = []
                divisions[team.division].append(team)

        # Sort each division and assign seeds
        for div_teams in divisions.values():
            div_teams.sort(key=cmp_to_key(self._compare), reverse=True)
            for i, team in enumerate(div_teams):
                team.division_seed = i + 1


class LFLDivisionSeeder(DivisionSeeder):
    """
    LFL-specific division seeder.

    Tiebreaker order:
    1. Record (wins)
    2. Head-to-head record
    3. Division record
    4. Expected wins
    """

    def __init__(self):
        super().__init__(criteria_chain=[
            RecordCriteria,
            H2HCriteria,
            DivisionRecordCriteria,
            ExpectedWinsCriteria
        ])


class LeagueSeeder(Seeder):
    """
    Abstract base class for league-wide seeding.
    Provides generic implementation for calculating league seeds.
    Subclasses should define their own criteria chain.
    """

    def calculate_and_update_seeding(self, teams):
        """
        Calculate league seeding for all teams.
        Assigns league_seed to each team.

        Note: Requires division_seed to be set first (run DivisionSeeder first).

        Args:
            teams: List or dict of Team objects
        """
        # Convert to list if dict
        if isinstance(teams, dict):
            teams_list = list(teams.values())
        else:
            teams_list = teams

        # Sort teams and assign league seeds
        teams_list.sort(key=cmp_to_key(self._compare), reverse=True)
        for i, team in enumerate(teams_list):
            team.league_seed = i + 1


class LFLLeagueSeeder(LeagueSeeder):
    """
    LFL-specific league seeder.

    Tiebreaker order:
    1. Record (wins)
    2. If same division: use division seed
    3. If one is #1 in division: prioritize division winners
    4. Head-to-head record
    5. Expected wins
    """

    def __init__(self):
        super().__init__(criteria_chain=[
            RecordCriteria,
            SameDivisionCriteria,
            DivisionLeaderCriteria,
            H2HCriteria,
            ExpectedWinsCriteria
        ])


# ============================================================================
# SEED ENGINE
# ============================================================================

class SeedEngine:
    """
    Generic seed engine that orchestrates division and league seeding.
    Accepts any DivisionSeeder and LeagueSeeder implementations.
    """

    def __init__(self, division_seeder=None, league_seeder=None):
        """
        Initialize the SeedEngine with custom seeders.

        Args:
            division_seeder: DivisionSeeder instance
            league_seeder: LeagueSeeder instance
        """
        self.division_seeder = division_seeder
        self.league_seeder = league_seeder

    def calculate_and_update_seeding(self, teams):
        """
        Compute both division and league seeding for teams.
        Directly modifies the team objects by setting their division_seed
        and league_seed attributes.

        Args:
            teams: List or dict of Team objects
        """
        # First calculate division seeding
        self.division_seeder.calculate_and_update_seeding(teams)

        # Then calculate league seeding (depends on division seeds)
        self.league_seeder.calculate_and_update_seeding(teams)
