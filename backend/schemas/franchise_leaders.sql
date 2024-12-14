CREATE TABLE franchise_leaders(
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    team_id integer NOT NULL,
    team_name text NOT NULL,
    pts integer,
    pts_person_id integer,
    pts_player text,
    ast integer,
    ast_person_id integer,
    ast_player text,
    reb integer,
    reb_person_id integer,
    reb_player text,
    blk integer,
    blk_person_id integer,
    blk_player text,
    stl integer,
    stl_person_id integer,
    stl_player text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Add a unique constraint on team_id to ensure one record per team
ALTER TABLE franchise_leaders
    ADD CONSTRAINT unique_team_id UNIQUE (team_id);

-- Create an index on team_id for faster lookups
CREATE INDEX idx_franchise_leaders_team_id ON franchise_leaders(team_id);

