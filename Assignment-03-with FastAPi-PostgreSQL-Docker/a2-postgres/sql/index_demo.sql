-- Run this BEFORE creating the index — expect a Seq Scan:
EXPLAIN ANALYZE SELECT * FROM tasks WHERE title = 'Learn FastAPI';

-- Now add the index:
CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks (title);

-- Run the same query again — expect an Index Scan and a lower
-- execution time:
EXPLAIN ANALYZE SELECT * FROM tasks WHERE title = 'Learn FastAPI';
