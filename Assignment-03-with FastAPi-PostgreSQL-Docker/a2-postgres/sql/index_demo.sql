-- Run this BEFORE creating the index — expect a Seq Scan:
EXPLAIN ANALYZE SELECT * FROM items WHERE name = 'item_54321';

-- Now add the index:
CREATE INDEX IF NOT EXISTS idx_items_name ON items (name);

-- Run the same query again — expect an Index Scan and a lower
-- execution time:
EXPLAIN ANALYZE SELECT * FROM items WHERE name = 'item_54321';
