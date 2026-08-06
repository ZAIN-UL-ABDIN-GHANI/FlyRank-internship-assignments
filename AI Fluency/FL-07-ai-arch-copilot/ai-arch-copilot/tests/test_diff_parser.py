import pytest

from app.diff_parser import format_files_for_review, looks_like_unified_diff, parse_unified_diff

VALID_MULTI_FILE_DIFF = """diff --git a/db.py b/db.py
index 83db48f..bf269f4 100644
--- a/db.py
+++ b/db.py
@@ -1,3 +1,3 @@
 def get_user(user_id):
-    query = "SELECT * FROM users WHERE id=" + user_id
+    query = f"SELECT * FROM users WHERE id={user_id}"
     return db.execute(query)
diff --git a/utils.py b/utils.py
index 1111111..2222222 100644
--- a/utils.py
+++ b/utils.py
@@ -10,1 +10,3 @@ def helper():
     pass
+
+def another():
"""


def test_looks_like_unified_diff_detects_git_diff():
    assert looks_like_unified_diff(VALID_MULTI_FILE_DIFF) is True


def test_looks_like_unified_diff_rejects_plain_code():
    plain_code = "def add(a, b):\n    return a + b\n"
    assert looks_like_unified_diff(plain_code) is False


def test_parse_unified_diff_extracts_each_file():
    files = parse_unified_diff(VALID_MULTI_FILE_DIFF)
    filenames = [f["filename"] for f in files]
    assert filenames == ["db.py", "utils.py"]
    assert "SELECT * FROM users WHERE id={user_id}" in files[0]["content"]
    assert "def another():" in files[1]["content"]


def test_parse_unified_diff_raises_value_error_on_malformed_diff():
    malformed = "--- a/x.py\n+++ b/x.py\n@@ -1,5 +1,5 @@\nnot a real hunk line\n"
    with pytest.raises(ValueError):
        parse_unified_diff(malformed)


def test_format_files_for_review_marks_file_boundaries():
    files = [
        {"filename": "a.py", "content": "print('a')"},
        {"filename": "b.py", "content": "print('b')"},
    ]
    formatted = format_files_for_review(files)
    assert "=== FILE: a.py ===" in formatted
    assert "=== FILE: b.py ===" in formatted
    assert formatted.index("a.py") < formatted.index("b.py")
