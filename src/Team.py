from src.Metrics import AverageMetric, StdDevMetric, ExpectedWinsMetric, ProbNWins

class WeekPerformance:
    def __init__(self, week, points, rank, adversary_points, adversary_rank):
        self.week = week
        self.points = points
        self.rank = rank
        self.winProb = (12-rank)/11
        self.adversary_points = adversary_points
        self.adversary_rank = adversary_rank
        self.win = points > adversary_points

    def getPoints(self):
        return self.points
    def getWinProb(self):       
        return self.winProb
    def getWeek(self):
        return self.week
    def getRank(self):
        return self.rank
    

class Team:
    def __init__(self, team_name, roster_id, division, seed):
        self.name = team_name
        self.short_name = team_name.split().str[1]
        self.division = division
        self.roster_id = roster_id
        self.seed = seed

        self.weekly_scores = []
        self.wins = 0
        self.avg = 0
        self.std = 0
        self.expw = 0
        self.probNWins = 0

    def insert_week(self, week: WeekPerformance):
        self.weekly_scores.append(week)
        if week.win:
            self.wins += 1
        self.weekly_scores.sort(key=lambda x: x.getWeek())


    def calculate_metrics(self):
        self.avg = AverageMetric(self.weekly_scores)
        self.std = StdDevMetric(self.weekly_scores)
        self.expw = ExpectedWinsMetric(self.weekly_scores)
        self.probNWins = ProbNWins(self.weekly_scores)


    def getPoints(self):
        return [week.getPoints() for week in self.weekly_scores]
    
    def getRanks(self):
        return [week.getRank() for week in self.weekly_scores]
    
    def getProbNWins(self):
        return self.probNWins.getValue()

    def to_dict(self):
        return {
            "name": self.name,
            "short_name": self.short_name,
            "division": self.division,
            "roster_id": self.roster_id,
            "seed": self.seed,
            "wins": self.wins,
            "avg": self.avg.getValue(),
            "std": self.std.getValue(),
            "expw": self.expw.getValue()
        }
