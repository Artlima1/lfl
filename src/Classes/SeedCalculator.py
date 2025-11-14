from functools import cmp_to_key


class SeedCalculator:
    """
    Handles seeding calculations for fantasy league teams.
    Computes both division and league-wide seeding based on:
    1. Win-loss record
    2. Head-to-head record
    3. Division record (for division seeding)
    4. Division seed (for league seeding)
    5. Expected wins (tiebreaker)
    """

    def __init__(self):
        pass

    @staticmethod
    def _division_comp(t1, t2):
        """
        Comparison function for division seeding.

        Tiebreaker order:
        1. Wins
        2. Head-to-head record
        3. Division record
        4. Expected wins
        """
        if t1.wins > t2.wins:
            return 1
        elif t1.wins < t2.wins:
            return -1
       
        h2h = t1.getH2hRecord(t2.roster_id)
        print(t1.name, t2.name, h2h)
        if h2h > 0.5:
            return 1
        elif 0 <= h2h < 0.5:
            return -1

        div_rec1 = t1.getDivisionRecord()
        div_rec2 = t2.getDivisionRecord()
        if div_rec1 > div_rec2:
            return 1
        elif div_rec1 < div_rec2:
            return -1
        
        expw1 = t1.to_dict().get("expw", None)
        expw2 = t2.to_dict().get("expw", None)
        if expw1 > expw2:
            return 1
        elif expw1 < expw2:
            return -1
        return 0

    @staticmethod
    def _league_comp(t1, t2):
        """
        Comparison function for league seeding.

        Tiebreaker order:
        1. Wins
        2. Division seed (lower is better)
        3. Head-to-head record
        4. Expected wins
        """
        if t1.wins > t2.wins:
            return 1
        elif t1.wins < t2.wins:
            return -1
        
        if t1.division_seed < t2.division_seed:
            return 1
        elif t1.division_seed > t2.division_seed:
            return -1
        
        h2h = t1.getH2hRecord(t2.roster_id)
        if h2h > 0.5:
            return 1
        elif 0 <= h2h < 0.5:
            return -1

        expw1 = t1.to_dict().get("expw", None)
        expw2 = t2.to_dict().get("expw", None)
        if expw1 > expw2:
            return 1
        elif expw1 < expw2:
            return -1
        
        return 0

    def calculate_and_update_seeding(self, teams):
        """
        Compute both division and league seeding for teams.
        Directly modifies the team objects by setting their division_seed
        and league_seed attributes.

        Args:
            teams: List or dict of Team objects
        """
        # Convert to list if dict
        if isinstance(teams, dict):
            teams_list = list(teams.values())
        else:
            teams_list = teams

        # Step 1: Group teams by division and compute division seeding
        divisions = {}
        for team in teams_list:
            if team.division:
                if team.division not in divisions:
                    divisions[team.division] = []
                divisions[team.division].append(team)

        for division_name, div_teams in divisions.items():
            # Sort using the division comparison function
            div_teams.sort(key=cmp_to_key(SeedCalculator._division_comp), reverse=True)
            # Assign division seeds directly to team objects
            for i, team in enumerate(div_teams):
                team.division_seed = i + 1

        # Step 2: Compute league seeding
        teams_list.sort(key=cmp_to_key(SeedCalculator._league_comp), reverse=True)
        # Assign league seeds directly to team objects
        for i, team in enumerate(teams_list):
            team.league_seed = i + 1
