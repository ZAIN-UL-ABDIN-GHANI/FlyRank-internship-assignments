INSERT INTO tasks (title, done)
SELECT v.title, FALSE
FROM (VALUES
    ('Learn FastAPI'),
    ('Learn PostgreSQL'),
    ('Finish Assignment')
) AS v(title)
WHERE NOT EXISTS (SELECT 1 FROM tasks);
