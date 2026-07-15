-- Generates 100,000 rows so a sequential scan vs index scan
-- comparison is actually meaningful.
INSERT INTO items (name, description, price)
SELECT
    'item_' || g,
    'seeded row number ' || g,
    (random() * 500)::numeric(10, 2)
FROM generate_series(1, 100000) AS g;
