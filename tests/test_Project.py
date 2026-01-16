# tests/test_project.py

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.Project import Project, ProjectState


# ---------------------------
# Constructor tests
# ---------------------------

def test_project_init_sets_defaults():
    project = Project(customer_id="cust1", translator_id="trans1", language="en", original_file=b"data")

    assert isinstance(project.id, str)
    assert project.customer_id == "cust1"
    assert project.translator_id == "trans1"
    assert project.language == "en"
    assert project.original_file == b"data"
    assert project.translated_file is None
    assert project.state == ProjectState.CREATED
    assert isinstance(project.created_at, datetime)
    assert project.feedback is None


# ---------------------------
# create_project tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_create_project_success(mock_execute):
    mock_execute.return_value = 1
    customer_id = "cust123"
    project_name = "Test project"
    description = "Description"
    language = "en"
    original_file = b"file-bytes"

    project = Project.create_project(customer_id, project_name, description, language, original_file)

    assert project.customer_id == customer_id
    assert project.language == language
    assert project.original_file == original_file
    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "INSERT INTO Projects" in args[0]
    assert args[1][1] == project_name
    assert args[1][2] == description
    assert args[1][3] == customer_id
    assert args[1][5] == language
    assert args[1][6] == original_file
    assert args[1][8] == project.state.value


@patch("models.Project.db.execute_query")
def test_create_project_failure_raises(mock_execute):
    mock_execute.return_value = None

    with pytest.raises(ValueError, match="Failed to create project"):
        Project.create_project("cust123", "P", "D", "en", b"file")


# ---------------------------
# get_by_user_id tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_by_user_id_uses_role_and_from_result(mock_execute):
    mock_execute.return_value = [{"id": "p1"}]
    fake_projects = ["project1"]
    with patch.object(Project, "from_result", return_value=fake_projects) as mock_from:
        result = Project.get_by_user_id("user123", "customerId")

    assert result == fake_projects
    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "WHERE customerId = %s" in args[0]
    assert args[1] == ("user123",)
    mock_from.assert_called_once_with(mock_execute.return_value)


# ---------------------------
# assign_translator tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_assign_translator_success(mock_execute):
    Project.assign_translator("proj123", "trans123")
    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "UPDATE Projects SET translatorId = %s, state = %s WHERE id = %s" in args[0]
    assert args[1][0] == "trans123"
    assert args[1][1] == ProjectState.ASSIGNED.value
    assert args[1][2] == "proj123"


@patch("models.Project.db.execute_query")
def test_assign_translator_invalid_project_id(mock_execute):
    with pytest.raises(ValueError):
        Project.assign_translator("", "trans123")
    with pytest.raises(ValueError):
        Project.assign_translator(None, "trans123")


@patch("models.Project.db.execute_query")
def test_assign_translator_invalid_translator_id(mock_execute):
    with pytest.raises(ValueError):
        Project.assign_translator("proj123", "")
    with pytest.raises(ValueError):
        Project.assign_translator("proj123", None)


# ---------------------------
# get_all tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_all_uses_from_result(mock_execute):
    mock_execute.return_value = [{"id": "p1"}]
    fake_projects = ["p1"]
    with patch.object(Project, "from_result", return_value=fake_projects) as mock_from:
        result = Project.get_all()

    assert result == fake_projects
    mock_execute.assert_called_once_with("SELECT * FROM Projects")
    mock_from.assert_called_once_with(mock_execute.return_value)


# ---------------------------
# get_by_id tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_by_id_returns_none_when_not_found(mock_execute):
    mock_execute.return_value = []

    result = Project.get_by_id("missing")

    assert result is None
    mock_execute.assert_called_once()


@patch("models.Project.db.execute_query")
def test_get_by_id_returns_first_project(mock_execute):
    mock_execute.return_value = [{"id": "p1"}]
    fake_project = MagicMock()
    with patch.object(Project, "from_result", return_value=[fake_project]) as mock_from:
        result = Project.get_by_id("p1")

    assert result is fake_project
    mock_execute.assert_called_once()
    mock_from.assert_called_once_with(mock_execute.return_value)


# ---------------------------
# update_state tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_update_state_success(mock_execute):
    mock_execute.return_value = 1

    Project.update_state("proj123", ProjectState.APPROVED.value)

    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "UPDATE Projects SET state = %s WHERE id = %s" in args[0]
    assert args[1] == (ProjectState.APPROVED.value, "proj123")


@patch("models.Project.db.execute_query")
def test_update_state_failure_raises(mock_execute):
    mock_execute.return_value = 0

    with pytest.raises(ValueError, match="Failed to update project status"):
        Project.update_state("proj123", ProjectState.REJECTED.value)


# ---------------------------
# get_state tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_state_success(mock_execute):
    mock_execute.return_value = [{"state": "CREATED"}]

    state = Project.get_state("proj123")

    assert state == ProjectState.CREATED
    mock_execute.assert_called_once()


@patch("models.Project.db.execute_query")
def test_get_state_project_not_found_raises(mock_execute):
    mock_execute.return_value = []

    with pytest.raises(ValueError, match="Project not found"):
        Project.get_state("proj123")


# ---------------------------
# save_feedback tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_save_feedback_success(mock_execute):
    mock_execute.return_value = 1

    Project.save_feedback("proj123", "Great job")

    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "INSERT INTO Feedbacks" in args[0]
    assert args[1][0] == "proj123"
    assert args[1][1] == "Great job"


@patch("models.Project.db.execute_query")
def test_save_feedback_failure_raises(mock_execute):
    mock_execute.return_value = 0

    with pytest.raises(ValueError, match="Failed to save feedback"):
        Project.save_feedback("proj123", "Bad job")


# ---------------------------
# get_feedback tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_feedback_success(mock_execute):
    mock_execute.return_value = [{"text": "Latest feedback"}]

    text = Project.get_feedback("proj123")

    assert text == "Latest feedback"
    mock_execute.assert_called_once()


@patch("models.Project.db.execute_query")
def test_get_feedback_not_found_raises(mock_execute):
    mock_execute.return_value = []

    with pytest.raises(ValueError, match="Feedback not found"):
        Project.get_feedback("proj123")


# ---------------------------
# update_feedback tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_update_feedback_success(mock_execute):
    mock_execute.return_value = 1

    Project.update_feedback("proj123", "Updated feedback")

    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "UPDATE Feedbacks SET text = %s, createdAt = %s WHERE projectId = %s" in args[0]
    assert args[1][0] == "Updated feedback"
    assert args[1][2] == "proj123"


@patch("models.Project.db.execute_query")
def test_update_feedback_failure_raises(mock_execute):
    mock_execute.return_value = 0

    with pytest.raises(ValueError, match="Failed to update feedback"):
        Project.update_feedback("proj123", "Updated feedback")


# ---------------------------
# save_translated_file tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_save_translated_file_failure_none_raises(mock_execute):
    mock_execute.return_value = None

    with pytest.raises(ValueError, match="Failed to save translated file"):
        Project.save_translated_file("proj123", b"data")


@patch("models.Project.db.execute_query")
def test_save_translated_file_zero_rows_ok(mock_execute):
    mock_execute.return_value = 0

    # Should not raise
    Project.save_translated_file("proj123", b"data")

    mock_execute.assert_called_once()


@patch("models.Project.db.execute_query")
def test_save_translated_file_success(mock_execute):
    mock_execute.return_value = 1

    # Should not raise
    Project.save_translated_file("proj123", b"data")

    mock_execute.assert_called_once()


# ---------------------------
# get_original_file tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_original_file_success(mock_execute):
    mock_execute.return_value = [{"originalFile": b"orig"}]

    data = Project.get_original_file("proj123")

    assert data == b"orig"
    mock_execute.assert_called_once()


@patch("models.Project.db.execute_query")
def test_get_original_file_not_found_raises(mock_execute):
    mock_execute.return_value = []

    with pytest.raises(ValueError, match="Project not found"):
        Project.get_original_file("proj123")


# ---------------------------
# get_translated_file tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_translated_file_success(mock_execute):
    mock_execute.return_value = [{"translatedFile": b"trans"}]

    data = Project.get_translated_file("proj123")

    assert data == b"trans"
    mock_execute.assert_called_once()


@patch("models.Project.db.execute_query")
def test_get_translated_file_not_found_raises(mock_execute):
    mock_execute.return_value = []

    with pytest.raises(ValueError, match="Project not found"):
        Project.get_translated_file("proj123")


# ---------------------------
# get_by_customer_id tests
# ---------------------------

@patch("models.Project.db.execute_query")
def test_get_by_customer_id_uses_from_result(mock_execute):
    mock_execute.return_value = [{"id": "p1"}]
    fake_projects = ["p1"]
    with patch.object(Project, "from_result", return_value=fake_projects) as mock_from:
        result = Project.get_by_customer_id("cust123")

    assert result == fake_projects
    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert "WHERE customerId = %s" in args[0]
    assert args[1] == ("cust123",)
    mock_from.assert_called_once_with(mock_execute.return_value)


# ---------------------------
# from_result tests
# ---------------------------

def test_from_result_full_row_mapping():
    created = datetime(2024, 1, 1, 12, 0, 0)
    row = {
        "id": "p1",
        "customerId": "cust1",
        "translatorId": "trans1",
        "languageCode": "en",
        "originalFile": b"orig",
        "name": "Project 1",
        "description": "Desc",
        "translatedFile": b"trans",
        "state": "APPROVED",
        "createdAt": created,
    }

    projects = Project.from_result([row])

    assert len(projects) == 1
    p = projects[0]
    assert p.id == "p1"
    assert p.customer_id == "cust1"
    assert p.translator_id == "trans1"
    assert p.language == "en"
    assert p.original_file == b"orig"
    assert p.name == "Project 1"
    assert p.description == "Desc"
    assert p.translated_file == b"trans"
    assert p.state == ProjectState.APPROVED
    assert p.created_at == created


def test_from_result_missing_and_invalid_values():
    row = {
        "customerId": None,
        "translatorId": None,
        "languageCode": None,
        "originalFile": None,
        "translatedFile": None,
        "state": "INVALID",
        "createdAt": None,
    }

    projects = Project.from_result([row])

    assert len(projects) == 1
    p = projects[0]
    assert p.customer_id == ""
    assert p.language == ""
    assert p.translator_id is None
    assert p.original_file is None
    assert p.translated_file is None
    assert p.state == ProjectState.CREATED
    assert isinstance(p.created_at, datetime)
