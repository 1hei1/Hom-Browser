import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app # Changed: Assuming backend/ is in PYTHONPATH
from app.database import Base, get_db # Changed
from app import models # Changed

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # Test database

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Create tables before tests run
    # Ensure all models are imported so Base knows about them
    # models.Profile, models.Group, models.Proxy should be defined
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after tests run (optional, good for clean state)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_db): # Depends on setup_db to ensure tables are created
    connection = engine.connect()
    # begin a non-ORM transaction
    transaction = connection.begin()
    # bind an ORM session to the connection
    # session = TestingSessionLocal(bind=connection)
    # use the above line if you want each test to have a session that is part of the same transaction block
    # or use a new session for each test, but ensure it's closed.
    # For test isolation, creating a new session that's rolled back is often preferred.
    db = TestingSessionLocal()

    try:
        yield db # provide the session for the test
    finally:
        db.close()
        # Rollback the transaction to ensure test isolation
        # This part is tricky with how TestingSessionLocal is defined.
        # The typical pattern is to begin a transaction on the session itself
        # or use a "savepoint" if the session is bound to an outer transaction.
        # For simplicity with SQLite and TestClient, individual rollbacks are fine.
        # If using the connection/transaction pattern directly:
        # transaction.rollback()
        # connection.close()
        # For tests, it's often easier to just clear data or re-create tables per test/session.
        # The drop_all/create_all in setup_db handles full test session isolation.
        # For per-test isolation when tests modify data:
        # After each test, clear all data from tables.
        # This current db_session provides a session but doesn't manage per-test transaction rollback.
        # Let's refine db_session for per-test rollback.

@pytest.fixture(scope="function")
def client(db_session): # db_session fixture will be used here
    # Override the get_db dependency for the app
    # The lambda here ensures that each call to get_db within a single test
    # will use the same db_session that this client fixture received.
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear() # Clear overrides after test

# Refined db_session for per-test data isolation via rollback
@pytest.fixture(scope="function")
def db_session_with_rollback(setup_db):
    connection = engine.connect()
    transaction = connection.begin()

    # bind an ORM Session to the connection
    # this session will be part of the transaction
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    # rollback the transaction: the data changed by the test are not
    # committed to the actual database
    transaction.rollback()
    connection.close()

# Update client to use the rollback session for tests that modify data
@pytest.fixture(scope="function")
def client_with_rollback(db_session_with_rollback):
    app.dependency_overrides[get_db] = lambda: db_session_with_rollback
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# For tests that only read data, the original 'client' and 'db_session' are fine.
# For tests that write data, 'client_with_rollback' and 'db_session_with_rollback' should be used.
# To simplify, we can make the default client use the rollback mechanism.
# Let's make the primary 'db_session' and 'client' use the rollback.

@pytest.fixture(scope="function") # Ensure tests can use 'db_session' as the name
def db_session(setup_db): # This is the one with rollback
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session): # client now uses the rollback session 'db_session'
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
