import os
import importlib
import uuid
import pytest
from datetime import datetime


os.environ["DATABASE_HOST"] = os.getenv("TEST_DATABASE_HOST", "127.0.0.1")
os.environ["DATABASE_USER"] = os.getenv("TEST_DATABASE_USER", "pia_user")
os.environ["DATABASE_PASSWORD"] = os.getenv("TEST_DATABASE_PASSWORD", "pia_password")
os.environ["DATABASE_NAME"] = os.getenv("TEST_DATABASE_NAME", "pia_db")


def _reload_db_and_project_modules():
    import models.db as db_module
    importlib.reload(db_module)

    import models.Project as project_module
    importlib.reload(project_module)

    return db_module.db, project_module


@pytest.fixture(scope="module")
def ctx():
    db, project_module = _reload_db_and_project_modules()

    db.connect()
    assert db.connection is not None, (
        "Could not connect to MySQL. "
        "If running pytest on host, DATABASE_HOST must be 127.0.0.1 and MySQL must be published on port 3306. "
        "If running inside docker network, DATABASE_HOST should be mysql."
    )

    yield {"db": db, "Project": project_module.Project, "ProjectState": project_module.ProjectState}

    try:
        db.close()
    except Exception:
        pass


@pytest.fixture()
def created_ids(ctx):
    """
    Track all rows created by tests and delete only those.
    Order matters because of FK constraints:
      - Projects references Users (customerId/translators), so delete Projects first.
    """
    db = ctx["db"]
    ids = {
        "project_ids": [],
        "user_ids": [],
    }
    yield ids

    # Cleanup projects first
    for pid in ids["project_ids"]:
        try:
            db.execute_query("DELETE FROM Feedbacks WHERE projectId = %s", (pid,))
        except Exception:
            pass
        db.execute_query("DELETE FROM Projects WHERE id = %s", (pid,))

    # Then users
    for uid in ids["user_ids"]:
        db.execute_query("DELETE FROM Users WHERE id = %s", (uid,))


def _insert_user(db, user_id: str, name: str, email: str, role: str):
    """
    Minimal insert into Users to satisfy FK constraints.
    Assumes Users table contains: (id, name, email, password, role, created_at)
    """
    db.execute_query(
        "INSERT INTO Users (id, name, email, password, role, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, name, email, "integration_dummy_hash", role, datetime.utcnow()),
    )


def _select_project_row(db, project_id: str):
    rows = db.execute_query("SELECT * FROM Projects WHERE id = %s", (project_id,))
    return rows[0] if rows else None


def test_project_create_project_persists_row(ctx, created_ids):
    db = ctx["db"]
    Project = ctx["Project"]
    ProjectState = ctx["ProjectState"]

    customer_id = str(uuid.uuid4())
    _insert_user(db, customer_id, "it_customer", "it_customer@example.com", "customer")
    created_ids["user_ids"].append(customer_id)

    created = Project.create_project(
        customer_id=customer_id,
        project_name="IT Project Creation",
        description="Integration storage test",
        language="en",
        original_file=b"integration-bytes-123",
    )
    created_ids["project_ids"].append(created.id)

    row = _select_project_row(db, created.id)
    assert row is not None, "Expected inserted project row to exist in DB"
    assert row["id"] == created.id
    assert row["name"] == "IT Project Creation"
    assert row["description"] == "Integration storage test"
    assert row["customerId"] == customer_id
    assert row["translatorId"] is None
    assert row["languageCode"] == "en"
    assert row["originalFile"] == "integration-bytes-123"
    assert row["translatedFile"] is None
    assert row["state"] == ProjectState.CREATED.value


def test_project_assign_translator_persists_update(ctx, created_ids):
    db = ctx["db"]
    Project = ctx["Project"]
    ProjectState = ctx["ProjectState"]

    customer_id = str(uuid.uuid4())
    translator_id = str(uuid.uuid4())

    _insert_user(db, customer_id, "it_customer2", "it_customer2@example.com", "customer")
    _insert_user(db, translator_id, "it_translator", "it_translator@example.com", "translator")

    created_ids["user_ids"].extend([customer_id, translator_id])

    created = Project.create_project(
        customer_id=customer_id,
        project_name="IT Assignment",
        description="Integration assignment test",
        language="de",
        original_file=b"integration-bytes-456",
    )
    created_ids["project_ids"].append(created.id)

    Project.assign_translator(created.id, translator_id)

    row = _select_project_row(db, created.id)
    assert row is not None, "Expected project row to exist in DB after assignment"
    assert row["translatorId"] == translator_id
    assert row["state"] == ProjectState.ASSIGNED.value
