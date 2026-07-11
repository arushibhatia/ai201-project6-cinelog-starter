"""
tests/test_watchlist.py — CineLog (feature/watchlist branch)

Tests for the watchlist service, following the same patterns as
tests/test_collection.py.
"""

import pytest
from app import create_app, db
from models import User
from services.watchlist_service import add_to_watchlist, get_watchlist
from services.collection_service import FilmNotFoundError


@pytest.fixture
def app():
    """Create an isolated test app with an in-memory database."""
    app = create_app(config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app):
    """A user to use in tests."""
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()
        return user.id


# ── Nonexistent film ─────────────────────────────────────────────────────────

def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """
    Adding a film_id that doesn't exist in the database should raise
    FilmNotFoundError, not a database integrity error.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)


# ── get_watchlist sort order ─────────────────────────────────────────────────

def test_get_watchlist_returns_newest_first(app, sample_user):
    """
    get_watchlist() should return films sorted by date_added descending
    (most recently added first), not alphabetically.
    """
    with app.app_context():
        from datetime import datetime, timezone, timedelta
        from models import Film, WatchlistEntry

        film_a = Film(title="Alien", year=1979, genre="Horror")
        film_b = Film(title="Blade Runner", year=1982, genre="Sci-Fi")
        db.session.add_all([film_a, film_b])
        db.session.commit()

        earlier = datetime.now(timezone.utc) - timedelta(days=5)
        later = datetime.now(timezone.utc)

        # Alphabetically, "Alien" would sort before "Blade Runner" — but
        # "Alien" was added later, so it should come first by date_added.
        entry_a = WatchlistEntry(user_id=sample_user, film_id=film_a.id, date_added=later)
        entry_b = WatchlistEntry(user_id=sample_user, film_id=film_b.id, date_added=earlier)
        db.session.add_all([entry_a, entry_b])
        db.session.commit()

        watchlist = get_watchlist(sample_user)
        titles = [f["title"] for f in watchlist]

        assert titles[0] == "Alien"
        assert titles[1] == "Blade Runner"
