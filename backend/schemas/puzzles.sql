CREATE TABLE
  public.puzzles (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY NOT NULL,
    puzzle_id INTEGER NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    GROUPS jsonb NOT NULL,
    author TEXT NOT NULL,
    CONSTRAINT puzzles_pkey PRIMARY KEY (id),
    CONSTRAINT puzzles_date_key UNIQUE (date)
  ) TABLESPACE pg_default;