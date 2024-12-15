CREATE TABLE player_awards(
    id serial PRIMARY KEY,
    person_id integer NOT NULL,
    first_name varchar(50),
    last_name varchar(50),
    team varchar(50),
    description text,
    all_nba_team_number integer,
    season varchar(7),
    month integer,
    week integer,
    conference varchar(10),
    award_type varchar(50),
    subtype1 varchar(50),
    subtype2 varchar(50),
    subtype3 varchar(50),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_player_awards_person_id ON player_awards(person_id);

CREATE INDEX idx_player_awards_season ON player_awards(season);

