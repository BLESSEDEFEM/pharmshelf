from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Product  # noqa: F401  — registers the table


@pytest.fixture(scope="session")
def test_engine():
    """One engine for the whole run. Creates the schema, drops it at the end."""
    assert settings.test_database_url, "TEST_DATABASE_URL is not set in .env"
    assert settings.test_database_url != settings.database_url, (
        "TEST_DATABASE_URL must point at a different database from DATABASE_URL"
    )

    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(test_engine):
    """Empty the tables and reset the id counter AFTER every test."""
    yield
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE products RESTART IDENTITY CASCADE"))


@pytest.fixture
def db_session(test_engine):
    """A raw session, for tests that call crud/ directly with no HTTP."""
    TestSession = sessionmaker(bind=test_engine, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine):
    """A test client whose every request gets a FRESH session on the test branch."""
    TestSession = sessionmaker(bind=test_engine, expire_on_commit=False)

    def override_get_db():
        db = TestSession()          # ⭐ NEW session per request. See sub-step 12.2.
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_product(client, *, name="Test Drug", quantity=10, price="100.00", days_out=30):
    """Create a product through the API, with an expiry RELATIVE to today."""
    return client.post("/products", json={
        "name": name,
        "quantity": quantity,
        "price": price,
        "expiry_date": str(date.today() + timedelta(days=days_out)),
    })
