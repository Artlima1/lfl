import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests as rq
import json

from Classes.Team import Team, WeekPerformance

class FantasyLeague:
    def __init__(self, from_json=None, league_id=None, seeding=None, divisions=None):
        if from_json:
            # Load configuration from JSON file
            with open(from_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.league_id = config.get('league_id')
            seeding = config.get('seeding')
            divisions = config.get('divisions')
        else:
            self.league_id = league_id

        self.teams = {}
        self.retrieve_teams(seeding, divisions)
        self.retrieve_scoring()

    def retrieve_teams(self, seeding, divisions):
        # Fetch users data
        response = rq.get('https://api.sleeper.app/v1/league/{}/users'.format(self.league_id))
        users_data = json.loads(response.text)

        # Fetch rosters data
        response = rq.get('https://api.sleeper.app/v1/league/{}/rosters'.format(self.league_id))
        rosters_data = json.loads(response.text)

        # Create a mapping of owner_id to roster_id
        owner_to_roster = {}
        for roster in rosters_data:
            owner_to_roster[roster['owner_id']] = roster['roster_id']

        # Create mappings from seeding and divisions config
        seed_map = {}
        if seeding:
            for seed_entry in seeding:
                seed_map[seed_entry['short_name']] = seed_entry['seed']

        division_by_team = {}
        if divisions:
            for division in divisions:
                for team_name in division['team_names']:
                    division_by_team[team_name] = division['name']

        # Create Team objects indexed by roster_id
        teams = {}
        for user in users_data:
            user_id = user['user_id']
            team_name = user.get('metadata', {}).get('team_name')
            roster_id = owner_to_roster.get(user_id)

            if roster_id:
                # Extract short_name (second word of team name)
                short_name = team_name.split()[1] if len(team_name.split()) > 1 else team_name

                # Get seed and division from config
                seed = seed_map.get(short_name)
                division = division_by_team.get(short_name)

                team = Team(team_name, roster_id, division, seed)
                teams[roster_id] = team

        self.teams = teams

        # Create division_map: division -> [roster_ids]
        self.division_map = {}
        if divisions:
            for division in divisions:
                division_name = division['name']
                self.division_map[division_name] = []

                # Find roster_ids for teams in this division
                for team in teams.values():
                    if team.division == division_name:
                        self.division_map[division_name].append(team.roster_id)

    def retrieve_scoring(self):
        # Get current week
        response = rq.get('https://api.sleeper.app/v1/state/nfl')
        data = json.loads(response.text)
        self.current_week = data['week']

        # Retrieve scoring data for each week
        for week in range(1, self.current_week):
            response = rq.get('https://api.sleeper.app/v1/league/{}/matchups/{}'.format(self.league_id, week))
            week_data = json.loads(response.text)

            # Collect all performances for this week to calculate ranks
            week_performances = []
            for team_performance in week_data:
                roster_id = team_performance["roster_id"]
                points = team_performance["points"]
                matchup_id = team_performance["matchup_id"]
                week_performances.append({
                    "roster_id": roster_id,
                    "points": points,
                    "matchup_id": matchup_id
                })

            # Sort by points to determine ranks
            week_performances.sort(key=lambda x: x["points"], reverse=True)

            # Assign ranks to each performance
            for rank, perf in enumerate(week_performances, start=1):
                perf["rank"] = rank

            # Create a mapping of matchup_id to performances
            matchup_map = {}
            for perf in week_performances:
                matchup_id = perf["matchup_id"]
                if matchup_id not in matchup_map:
                    matchup_map[matchup_id] = []
                matchup_map[matchup_id].append(perf)

            # Assign ranks and create WeekPerformance objects with opponent data
            for perf in week_performances:
                roster_id = perf["roster_id"]
                points = perf["points"]
                rank = perf["rank"]
                matchup_id = perf["matchup_id"]

                # Find opponent in the same matchup
                opponent = None
                for other_perf in matchup_map[matchup_id]:
                    if other_perf["roster_id"] != roster_id:
                        opponent = other_perf
                        break

                # Get opponent data
                adversary_points = opponent["points"] if opponent else None
                adversary_rank = opponent["rank"] if opponent else None

                team = self.teams.get(roster_id)
                if team:
                    week_perf = WeekPerformance(week, points, rank, adversary_points, adversary_rank)
                    team.insert_week(week_perf)

    def getTeamsData(self):
        teamsData=[]
        for team in self.teams.values():
            teamsData.append(team.to_dict())
        return teamsData
    
    def getCurrentWeek(self):
        return self.current_week

    def getWeekScores(self, week):
        week_scores = []
        for team in self.teams.values():
            week_scores.append({
                "short_name": team.short_name,
                **team.getWeek(week)
            })
        return week_scores

    def getTeamScores(self, short_name):
        for team in self.teams.values():
            if team.short_name == short_name:
                return team.getPoints()
        return []

    def getScoringDf(self):
        data = []
        for week in range(1, self.current_week):
            data.extend([
                {"week": week,**score}
                for score in self.getWeekScores(week)
            ])
        return pd.DataFrame(data)
    
    def getTeamsDf(self):
        return pd.DataFrame(self.getTeamsData())