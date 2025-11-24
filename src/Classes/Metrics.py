from itertools import combinations

class Metric:
    def __init__(self, values:list):
        if len(values) == 0:
            return
        self.value = self.compute(values)

    def compute(self, values):
        pass

class AverageMetric(Metric):
    def compute(self, values):
        return sum(values) / len(values) if values else 0
    
class MedianMetric(Metric):
    def compute(self, values):  
        size = len(values)
        if size == 1:
            return values[0]
        ordered = sorted(values)
        center_index = (size//2)
        return ordered[center_index] if size%2==1 else (ordered[center_index-1] + ordered[center_index])/2
    
class StdDevMetric(Metric):
    def compute(self, values):
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

class ExpectedWinsMetric(Metric):
     def compute(self, values):
        return sum(values)

class ProbNWins(Metric):
    def compute(self, values):
        week_indices = list(range(len(values)))

        prob_n_wins = [0.0] * (len(values) + 1)

        w_combinations = []
        for n in range(len(week_indices) + 1):
            w_combinations += list(combinations(week_indices, n))

        for scenario in w_combinations:
            n_wins = len(scenario)
            wins_prob = 1.0
            for idx in scenario:
                wins_prob *= values[idx]
            losses_prob = 1.0
            for idx in week_indices:
                if idx not in scenario:
                    losses_prob *= (1 - values[idx])

            scenario_prob = wins_prob * losses_prob
            prob_n_wins[n_wins] += scenario_prob

        return prob_n_wins