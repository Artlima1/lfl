from Metrics import MedianMetric, AverageMetric, StdDevMetric, ExpectedWinsMetric, ProbNWins

class WeekPerformance:
    def __init__(self, week, points, rank, division_game, adversary_id, adversary_points, adversary_rank):
        self.week = week
        self.points = points
        self.rank = rank
        self.division_game = division_game
        self.adversary_id = adversary_id
        self.adversary_points = adversary_points
        self.adversary_rank = adversary_rank
        self.win = points > adversary_points
    
    def to_dict(self):
        return {
            "week": self.week,
            "points": self.points,
            "rank": self.rank,
            "adversary_points": self.adversary_points,
            "adversary_rank": self.adversary_rank,
            "win": self.win
        }
    

class MetricsManager:
    def __init__(self):
        self.weeks = []
        self.metrics = {}

    def update(self, weeks: list[WeekPerformance]):
        points = [week.points for week in weeks]
        cewProbs = [(12-week.rank)/11 for week in weeks]
        sewProbs = [(week.adversary_rank-1)/11 for week in weeks]

        self.metrics["avg"] = AverageMetric(values=points)
        self.metrics["std"] = StdDevMetric(values=points)
        self.metrics["med"] = MedianMetric(values=points)
        self.metrics["last5"] = AverageMetric(values=points[-5:])
        self.metrics["CEW"] = ExpectedWinsMetric(values=cewProbs)
        self.metrics["SEW"] = ExpectedWinsMetric(values=sewProbs)
        self.metrics["probNWins"] = ProbNWins(values=cewProbs)

    def to_dict(self):
        return {k: v.value for k, v in self.metrics.items()}

class Team:
    def __init__(self, team_name, roster_id, division):
        self.name = team_name
        self.short_name = team_name.split()[1]
        self.division = division
        self.roster_id = roster_id

        self.wins = 0
        self.losses = 0
        self.league_seed = 0
        self.division_seed = 0

        self._metrics_manager = MetricsManager()
        self._weekly_scores = []

    def getDivisionRecord(self):
        division_wins = 0
        division_losses = 0
        for week in self._weekly_scores:
            if week.division_game:
                if week.win:
                    division_wins += 1
                else:
                    division_losses += 1
        return (division_wins,division_losses)

    def getH2hRecord(self, other_team_id):
        h2h_wins = 0
        h2h_games = 0
        for week in self._weekly_scores:
            if week.adversary_id == other_team_id:
                h2h_games += 1
                if week.win:
                    h2h_wins += 1
        if h2h_games == 0:
            return -1
        return (h2h_wins / h2h_games)

    def insert_week(self, week: WeekPerformance):
        self._weekly_scores.append(week)
        if week.win:
            self.wins += 1
        else:
            self.losses += 1
        self._weekly_scores.sort(key=lambda x: x.week)
        self._metrics_manager.update(self._weekly_scores)

    def getWeek(self, week):
        if week <= len(self._weekly_scores):
            return self._weekly_scores[week - 1].to_dict()
        return None

    def getPoints(self):
        return [week.points for week in self._weekly_scores]
    
    def getRanks(self):
        return [week.rank for week in self._weekly_scores]

    def to_dict(self):
        rec = self.getDivisionRecord()
        return {
            "name": self.name,
            "short_name": self.short_name,
            "division": self.division,
            "roster_id": self.roster_id,
            "seed": self.league_seed,
            "division_seed": self.division_seed,
            "wins": self.wins,
            "losses": self.losses,
            "record": f"{self.wins}-{self.losses}",
            "division_record": f"{rec[0]}-{rec[1]}",
            **self._metrics_manager.to_dict()
        }
