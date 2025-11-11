from src.Team import WeekPerformance
from itertools import combinations

class Metric:
    def __init__(self, weeks: WeekPerformance):
        self.value = self.compute(weeks)

    def compute(self, weeks: WeekPerformance):
        pass

    def getValue(self):
        return self.value

class AverageMetric(Metric):
    def compute(self, weeks: WeekPerformance):
        points = [week.getPoints() for week in weeks]
        return sum(points.get) / len(points) if points else 0

class StdDevMetric(Metric):
    def compute(self, weeks: WeekPerformance):
        points = [week.getPoints() for week in weeks]
        mean = sum(points) / len(points)
        variance = sum((x - mean) ** 2 for x in points) / len(points)
        return variance ** 0.5
    
class ExpectedWinsMetric(Metric):
     def compute(self, weeks: WeekPerformance):
        winProbs = [week.getWinProb() for week in weeks]
        return sum(winProbs)
    
class ProbNWins(Metric):
    def compute(self, weeks: WeekPerformance):
        winProbs = [week.getWinProb() for week in weeks]
        week_indices = list(range(len(weeks)))

        prob_n_wins = [0.0] * (len(weeks) + 1)

        w_combinations = []
        for n in range(len(week_indices) + 1):
            w_combinations += list(combinations(week_indices, n))

        for scenario in w_combinations:
            n_wins = len(scenario)

            wins_prob = 1.0
            for idx in scenario:
                wins_prob *= winProbs[idx]

            losses_prob = 1.0
            for idx in week_indices:
                if idx not in scenario:
                    losses_prob *= (1 - winProbs[idx])

            scenario_prob = wins_prob * losses_prob

            prob_n_wins[n_wins] += scenario_prob

        return prob_n_wins