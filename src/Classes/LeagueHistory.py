import requests as rq
import json
import pandas as pd


class LeagueHistory:
    MAX_WEEKS = 25  # safety cap; loop stops earlier at first empty matchups response
    DEFAULT_PLAYOFF_WEEK_START = 15

    def __init__(self, from_json=None, current_season_games=None):
        with open(from_json, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.previous_leagues = config.get('previous_league_ids', [])

        # owner_id -> { adversary_owner_id -> {"games": int, "wins": int} }
        self._h2h = {}
        # single-direction match records: year, week, playoff, team_a/b_owner, team_a/b_points
        self._games = []

        for entry in self.previous_leagues:
            games = self._fetch_season_games(entry)
            self._games.extend(games)
            self._accumulate(games)

        if current_season_games:
            self._games.extend(current_season_games)
            self._accumulate(current_season_games)

    def _fetch_playoff_week_start(self, league_id):
        response = rq.get('https://api.sleeper.app/v1/league/{}'.format(league_id))
        data = json.loads(response.text)
        return data.get('settings', {}).get('playoff_week_start', self.DEFAULT_PLAYOFF_WEEK_START)

    def _fetch_season_games(self, entry):
        league_id = entry['league_id']
        year = entry['year']
        playoff_week_start = self._fetch_playoff_week_start(league_id)

        response = rq.get('https://api.sleeper.app/v1/league/{}/rosters'.format(league_id))
        rosters_data = json.loads(response.text)
        roster_to_owner = {r['roster_id']: r['owner_id'] for r in rosters_data}

        games = []
        week = 1
        while week <= self.MAX_WEEKS:
            response = rq.get('https://api.sleeper.app/v1/league/{}/matchups/{}'.format(league_id, week))
            week_data = json.loads(response.text)
            if not week_data:
                break

            matchup_map = {}
            for perf in week_data:
                matchup_map.setdefault(perf['matchup_id'], []).append(perf)

            for perfs in matchup_map.values():
                if len(perfs) != 2:
                    continue
                p1, p2 = perfs
                owner_a = roster_to_owner.get(p1['roster_id'])
                owner_b = roster_to_owner.get(p2['roster_id'])
                if owner_a is None or owner_b is None:
                    continue
                games.append({
                    "year": year,
                    "week": week,
                    "playoff": week >= playoff_week_start,
                    "team_a_owner": owner_a,
                    "team_b_owner": owner_b,
                    "team_a_points": p1['points'],
                    "team_b_points": p2['points'],
                })

            week += 1
        return games

    def _accumulate(self, games):
        for g in games:
            a, b = g['team_a_owner'], g['team_b_owner']
            a_win = g['team_a_points'] > g['team_b_points']
            self._bump(a, b, a_win)
            self._bump(b, a, not a_win)

    def _bump(self, owner_id, adversary_owner_id, win):
        bucket = self._h2h.setdefault(owner_id, {}) \
                          .setdefault(adversary_owner_id, {"games": 0, "wins": 0})
        bucket['games'] += 1
        if win:
            bucket['wins'] += 1

    def getAllTimeH2hDf(self, current_teams_df):
        active = current_teams_df[['owner_id', 'short_name']].to_dict('records')
        rows = []
        for team in active:
            row = {"Team": team['short_name']}
            for adv in active:
                bucket = self._h2h.get(team['owner_id'], {}).get(adv['owner_id'])
                if not bucket or bucket['games'] == 0:
                    row[f"vs {adv['short_name']}"] = "-"
                else:
                    wins = bucket['wins']
                    losses = bucket['games'] - wins
                    row[f"vs {adv['short_name']}"] = f"{wins}-{losses}"
            rows.append(row)
        return pd.DataFrame(rows)

    def getMatchesBetween(self, owner_a, owner_b):
        """Return every match between two owners, in chronological order,
        with points always oriented as (points for owner_a, points for owner_b)."""
        pair = {owner_a, owner_b}
        matches = []
        for g in self._games:
            if {g['team_a_owner'], g['team_b_owner']} != pair:
                continue
            if g['team_a_owner'] == owner_a:
                points_a, points_b = g['team_a_points'], g['team_b_points']
            else:
                points_a, points_b = g['team_b_points'], g['team_a_points']
            matches.append({
                "year": g['year'],
                "week": g['week'],
                "playoff": g['playoff'],
                "points_a": points_a,
                "points_b": points_b,
            })
        matches.sort(key=lambda m: (m['year'], m['week']))
        return matches
