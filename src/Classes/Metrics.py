from itertools import combinations

class Metric:
    def __init__(self, values:list):
        self.values = values

    def compute(self):
        pass

class AverageMetric(Metric):
    def compute(self):
        return sum(self.values) / len(self.values) if self.values else 0

class StdDevMetric(Metric):
    def compute(self):
        mean = sum(self.values) / len(self.values)
        variance = sum((x - mean) ** 2 for x in self.values) / len(self.values)
        return variance ** 0.5

class ExpectedWinsMetric(Metric):
     def compute(self):
        return sum(self.values)

class ProbNWins(Metric):
    def compute(self):
        week_indices = list(range(len(self.values)))

        prob_n_wins = [0.0] * (len(self.values) + 1)

        w_combinations = []
        for n in range(len(week_indices) + 1):
            w_combinations += list(combinations(week_indices, n))

        for scenario in w_combinations:
            n_wins = len(scenario)
            wins_prob = 1.0
            for idx in scenario:
                wins_prob *= self.values[idx]
            losses_prob = 1.0
            for idx in week_indices:
                if idx not in scenario:
                    losses_prob *= (1 - self.values[idx])

            scenario_prob = wins_prob * losses_prob
            prob_n_wins[n_wins] += scenario_prob

        return prob_n_wins