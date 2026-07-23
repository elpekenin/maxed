CREATE TABLE IF NOT EXISTS "Maxed" (
    id INTEGER PRIMARY KEY NOT NULL,

    user_id INTEGER NOT NULL,
    pokedex INTEGER NOT NULL,

    shadow INTEGER NOT NULL,
    legacy INTEGER NOT NULL,

    count INTEGER NOT NULL,

    CHECK (count >= 0),
    CHECK (shadow IN (0, 1)),
    CHECK (legacy IN (0, 1)),

    CONSTRAINT different UNIQUE (user_id, pokedex, shadow, legacy)
) STRICT;
