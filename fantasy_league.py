from FantasyLeague import FantasyLeague

league_id = 1238157874098618368

seeding = [
    {"short_name": "Roludos", "seed": 1},
    {"short_name": "Flyers", "seed": 2},
    {"short_name": "SuperBowlers", "seed": 3},
    {"short_name": "JetEagles", "seed": 4},
    {"short_name": "Gamblers", "seed": 5},
    {"short_name": "Farmers", "seed": 6},
    {"short_name": "Pombos", "seed": 7},
    {"short_name": "Quasars", "seed": 8},
    {"short_name": "Vetter's", "seed": 9},
    {"short_name": "Spartans", "seed": 10},
    {"short_name": "CottonPickers", "seed": 11},
    {"short_name": "Foxes", "seed": 12}
]

divisions = [
    {
        "name": "COMI",
        "team_names": ["Quasars", "Spartans", "Gamblers", "Flyers"]
    },
    {
        "name": "SEU",
        "team_names": ["JetEagles", "Roludos", "Vetter's", "Foxes"]
    },
    {
        "name": "PAI",
        "team_names": ["SuperBowlers", "CottonPickers", "Pombos", "Farmers"]
    },
]

league = FantasyLeague(league_id, custom_seeding=seeding, custom_divisions=divisions)
league.compile_league_data()
league.export_charts()