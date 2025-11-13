from Classes.Metrics import Metric, AverageMetric, StdDevMetric, ExpectedWinsMetric, ProbNWins

class WeekPerformance:
    def __init__(self, week, points, rank, adversary_points, adversary_rank):
        self.week = week
        self.points = points
        self.rank = rank
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
        winProbs = [(12-week.rank)/11 for week in weeks]

        self.metrics["avg"] = AverageMetric(values=points)
        self.metrics["std"] = StdDevMetric(values=points)
        self.metrics["expw"] = ExpectedWinsMetric(values=winProbs)
        self.metrics["probNWins"] = ProbNWins(values=winProbs)

    def to_dict(self):
        return {k: v.compute() for k, v in self.metrics.items()}

class Team:
    def __init__(self, team_name, roster_id, division, seed):
        self.name = team_name
        self.short_name = team_name.split()[1]
        self.division = division
        self.roster_id = roster_id
        self.seed = seed
        self.wins = 0
        self.losses = 0

        self._metrics_manager = MetricsManager()

        self._weekly_scores = []

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
        return {
            "name": self.name,
            "short_name": self.short_name,
            "division": self.division,
            "roster_id": self.roster_id,
            "seed": self.seed,
            "wins": self.wins,
            "losses": self.losses,
            **self._metrics_manager.to_dict()
        }
