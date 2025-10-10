import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests as rq
import json
import math
import seaborn as sns
from scipy.interpolate import make_interp_spline
from itertools import combinations

from Charts import LeagueBoxPlot, LeaguePerformanceChart, LeagueExpWChart, LeagueProbChart

def expected_value(values, weights):
    values = np.asarray(values)
    weights = np.asarray(weights)
    return (values * weights).sum()

class FantasyLeague:
    def __init__(self, league_id, custom_seeding=None, custom_divisions=None):
        self.league_id = league_id
        self.custom_seeding = custom_seeding
        self.custom_divisions = custom_divisions

    def retrieve_teams(self):
        response = rq.get('https://api.sleeper.app/v1/league/{}/users'.format(self.league_id))
        data = json.loads(response.text)
        users_df = pd.DataFrame(data)
        users_df = pd.concat([users_df, users_df["metadata"].apply(pd.Series)], axis=1)
        users_df = users_df.drop(columns=users_df.columns.difference(['user_id','display_name', 'team_name']), axis=1)
        users_df['team_name'] = users_df['team_name'].fillna(users_df['display_name'])
        users_df

        response = rq.get('https://api.sleeper.app/v1/league/{}/rosters'.format(self.league_id))
        data = json.loads(response.text)
        rosters_df = pd.DataFrame(data)
        rosters_df = pd.concat([rosters_df, rosters_df["settings"].apply(pd.Series)], axis=1)
        rosters_df = rosters_df.drop(columns=rosters_df.columns.difference(['wins','roster_id', 'owner_id']), axis=1)

        teams_df = users_df.rename(columns={"user_id": "owner_id"})
        teams_df = pd.merge(rosters_df, teams_df, on="owner_id")
        teams_df['short_name'] = teams_df['team_name'].str.split().str[1]
        self.teams_df = teams_df


    def retrieve_current_week(self):
        response = rq.get('https://api.sleeper.app/v1/state/nfl')
        data = json.loads(response.text)
        self.current_week = data['week']

    def retrieve_scoring(self):
        scores_data = []

        for week in range(1, self.current_week):
            response = rq.get('https://api.sleeper.app/v1/league/{}/matchups/{}'.format(self.league_id, week))
            data = json.loads(response.text)
            for team_performance in data:
                scores_data.append({"roster_id": team_performance["roster_id"], "week": week, "points": team_performance["points"]})

        self.scores_df = pd.DataFrame(scores_data)

    def calculate_probabilities(self):
        self.scores_df['rank'] = self.scores_df.groupby('week')['points'].rank(ascending=False, method='min').astype(int)
        self.scores_df['win_prob'] = self.scores_df["rank"].apply(lambda x: (len(self.teams_df) - x) / (len(self.teams_df) - 1))

        sample_list = range(1, self.current_week)
        w_combinations = list()
        for n in range(len(sample_list) + 1):
            w_combinations += list(combinations(sample_list, n))

        scenarios_prob = []
        for roster_id in self.teams_df['roster_id']:
            for scenario in w_combinations:
                wins_prob = self.scores_df[(self.scores_df['roster_id'] == roster_id) & (self.scores_df['week'].isin(scenario))]['win_prob'].prod() 
                losses_prob = self.scores_df[(self.scores_df['roster_id'] == roster_id) & ~self.scores_df['week'].isin(scenario)]['win_prob'].apply(lambda x: 1-x).prod()
                scenario_prob = wins_prob * losses_prob
                scenarios_prob.append({"roster_id": roster_id, "scenario": scenario, "n_wins": len(scenario), "prob": scenario_prob})

        prob_df = pd.DataFrame(scenarios_prob) 
        prob_df = prob_df.groupby(['roster_id', 'n_wins'])['prob'].sum().reset_index()
        self.prob_df = prob_df
    
    def calculate_metrics(self):
        metrics_df = self.scores_df.groupby('roster_id')['points'].agg(['mean', 'std']).reset_index()
        metrics_df.columns = ['roster_id', 'avg', 'std']

        # Calculate expected wins
        exp_w_df = self.prob_df.groupby('roster_id').apply(lambda g: expected_value(g['n_wins'], g['prob']))
        exp_w_df = exp_w_df.reset_index()
        exp_w_df.columns = ['roster_id', 'exp_w']

        self.metrics_df = metrics_df.merge(exp_w_df, on='roster_id')


    def compile_league_data(self):
        self.retrieve_current_week()
        self.retrieve_teams()
        self.retrieve_scoring()
        self.calculate_probabilities()
        self.calculate_metrics()

        league_df = self.teams_df.merge(self.metrics_df, on='roster_id')
        league_df["delta_w"] = league_df["exp_w"] - league_df["wins"]

        if self.custom_seeding:
            seeding_df = pd.DataFrame(self.custom_seeding)
            league_df = league_df.merge(seeding_df, on='short_name')
            league_df = league_df.sort_values(by=['seed'])
        else:
            league_df = league_df.sort_values(by=[["wins", "avg"]], ascending=False)
            league_df["seed"] = league_df.index + 1

        self.league_df = league_df

        self.charts = [
            LeagueBoxPlot(self.scores_df, league_df, filename=f'output/boxplot_w{self.current_week}.png'),
            LeaguePerformanceChart(league_df, filename=f'output/performance_chart_w{self.current_week}.png'),
            LeagueExpWChart(league_df, filename=f'output/expw_chart_w{self.current_week}.png')
        ]

        if(self.custom_divisions):
            for division in self.custom_divisions:
                chart = LeagueProbChart(self.prob_df, league_df, division["team_names"], f"output/prob_chart_{division["name"]}_w{self.current_week}")
                self.charts.append(chart)

    def get_league_df(self):
        return self.league_df

    def get_scores_data(self):
        return self.scores_df
    
    def get_probability_data(self):
        return self.prob_df

    def export_charts(self):
        for chart in self.charts:
            chart.export()

    