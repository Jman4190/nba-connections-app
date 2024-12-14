CREATE TABLE league_leaders(
    id serial PRIMARY KEY,
    player_id integer,
    rank integer,
    player varchar(255),
    team varchar(50),
    gp integer,
    min numeric(5, 1),
    fgm numeric(5, 1),
    fga numeric(5, 1),
    fg_pct numeric(4, 3),
    fg3m numeric(5, 1),
    fg3a numeric(5, 1),
    fg3_pct numeric(4, 3),
    ftm numeric(5, 1),
    fta numeric(5, 1),
    ft_pct numeric(4, 3),
    oreb numeric(5, 1),
    dreb numeric(5, 1),
    reb numeric(5, 1),
    ast numeric(5, 1),
    stl numeric(5, 1),
    blk numeric(5, 1),
    tov numeric(5, 1),
    pf numeric(5, 1),
    pts numeric(5, 1),
    eff numeric(5, 1),
    ast_tov numeric(5, 2),
    stl_tov numeric(5, 2),
    season varchar(7),
    stat_category varchar(10)
);

-- Create an index on the season and stat_category columns for faster queries
CREATE INDEX idx_season_stat_category ON league_leaders(season, stat_category);

-- Create an index on the player_id for faster lookups
CREATE INDEX idx_player_id ON league_leaders(player_id);

