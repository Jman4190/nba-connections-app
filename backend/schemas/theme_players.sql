CREATE TABLE theme_players(
    theme_id integer REFERENCES new_themes(theme_id),
    player_name text NOT NULL,
    player_id integer,
    additional_info jsonb,
    PRIMARY KEY (theme_id, player_name)
);

