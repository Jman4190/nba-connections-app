CREATE TABLE common_player_info(
    player_id integer PRIMARY KEY,
    first_name varchar,
    last_name varchar,
    display_first_last varchar,
    display_last_comma_first varchar,
    display_fi_last varchar,
    player_slug varchar,
    birthdate date,
    school varchar,
    country varchar,
    last_affiliation varchar,
    height varchar,
    weight integer,
    season_exp integer,
    jersey varchar,
    position varchar,
    roster_status boolean,
    team_id integer,
    team_name varchar,
    team_abbreviation varchar,
    team_code varchar,
    team_city varchar,
    playercode varchar,
    from_year integer,
    to_year integer,
    dleague_flag boolean,
    nba_flag boolean,
    games_played_flag boolean,
    draft_year integer,
    draft_round integer,
    draft_number integer
);
