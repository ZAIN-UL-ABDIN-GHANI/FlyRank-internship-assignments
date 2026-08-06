from app.session_store import append, get_history, reset


def test_append_and_get_history_roundtrip_in_order(tmp_path):
    db_path = str(tmp_path / "sessions.db")

    append("s1", "user", "add caching", db_path=db_path)
    append("s1", "assistant", "what should be cached?", db_path=db_path)
    append("s1", "user", "GET /users responses", db_path=db_path)

    history = get_history("s1", db_path=db_path)
    assert history == [
        {"role": "user", "content": "add caching"},
        {"role": "assistant", "content": "what should be cached?"},
        {"role": "user", "content": "GET /users responses"},
    ]


def test_sessions_are_isolated_from_each_other(tmp_path):
    db_path = str(tmp_path / "sessions.db")

    append("s1", "user", "message for session one", db_path=db_path)
    append("s2", "user", "message for session two", db_path=db_path)

    assert get_history("s1", db_path=db_path) == [{"role": "user", "content": "message for session one"}]
    assert get_history("s2", db_path=db_path) == [{"role": "user", "content": "message for session two"}]


def test_reset_clears_only_that_session(tmp_path):
    db_path = str(tmp_path / "sessions.db")

    append("s1", "user", "keep me safe from reset of s2", db_path=db_path)
    append("s2", "user", "will be cleared", db_path=db_path)

    reset("s2", db_path=db_path)

    assert get_history("s2", db_path=db_path) == []
    assert len(get_history("s1", db_path=db_path)) == 1


def test_get_history_on_unknown_session_returns_empty_list(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    assert get_history("never-used", db_path=db_path) == []
