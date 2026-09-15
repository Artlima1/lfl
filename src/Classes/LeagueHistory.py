import requests as rq
import json
import pandas as pd


class LeagueHistory:
    MAX_WEEKS = 25  # safety cap; loop stops earlier at first empty matchups response

    def __init__(self, from_json=None, current_season_games=None):
        with open(from_json, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.previous_leagues = config.get('previous_league_ids', [])

        # owner_id -> { adversary_owner_id -> {"games": int, "wins": int} }
        self._h2h = {}

        for entry in self.previous_leagues:
            self._accumulate(self._fetch_season_games(entry['league_id']))

        if current_season_games:
            self._accumulate(current_season_games)

    def _fetch_season_games(self, league_id):
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
                owner1 = roster_to_owner.get(p1['roster_id'])
                owner2 = roster_to_owner.get(p2['roster_id'])
                if owner1 is None or owner2 is None:
                    continue
                win1 = p1['points'] > p2['points']
                games.append({"owner_id": owner1, "adversary_owner_id": owner2, "win": win1})
                games.append({"owner_id": owner2, "adversary_owner_id": owner1, "win": not win1})

            week += 1
        return games

    def _accumulate(self, games):
        for g in games:
            bucket = self._h2h.setdefault(g['owner_id'], {}) \
                              .setdefault(g['adversary_owner_id'], {"games": 0, "wins": 0})
            bucket['games'] += 1
            if g['win']:
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
