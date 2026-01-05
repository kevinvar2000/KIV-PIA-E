import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.User import User, UserRole

# ---------------------------
# UserRole.from_string tests
# ---------------------------

def test_userrole_from_string_valid():
    assert UserRole.from_string("administrator") == UserRole.ADMINISTRATOR
    assert UserRole.from_string("ADMINISTRATOR") == UserRole.ADMINISTRATOR
    assert UserRole.from_string(" customer ") == UserRole.CUSTOMER
    assert UserRole.from_string("translator") == UserRole.TRANSLATOR


def test_userrole_from_string_invalid_type():
    with pytest.raises(TypeError):
        UserRole.from_string(123)


def test_userrole_from_string_unknown_value():
    with pytest.raises(ValueError):
        UserRole.from_string("unknown")


# ---------------------------
# create_customer tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_create_customer_success(mock_query):
    mock_query.return_value = True

    user = User.create_customer("Alice", "alice@example.com", "hashed")

    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.role == UserRole.CUSTOMER
    mock_query.assert_called_once()


@patch("models.User.db.execute_query")
def test_create_customer_invalid_name(mock_query):
    with pytest.raises(ValueError):
        User.create_customer("", "mail@test.com", "hashed")


@patch("models.User.db.execute_query")
def test_create_customer_invalid_email(mock_query):
    with pytest.raises(ValueError):
        User.create_customer("User", "invalid-email", "hashed")


# ---------------------------
# create_translator tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_create_translator_success(mock_query):
    mock_query.return_value = True
    langs = ["en", "de"]

    user = User.create_translator("Bob", "bob@example.com", "hashed", langs)

    assert user.role == UserRole.TRANSLATOR
    assert user.languages == ["en", "de"]
    assert mock_query.call_count == 1 + len(langs)  # one insert + languages inserts


@patch("models.User.db.execute_query")
def test_create_translator_invalid_name(mock_query):
    with pytest.raises(ValueError):
        User.create_translator("", "bob@example.com", "hashed", ["en"])


@patch("models.User.db.execute_query")
def test_create_translator_invalid_email(mock_query):
    with pytest.raises(ValueError):
        User.create_translator("Bob", "invalid", "hashed", ["en"])


# ---------------------------
# get_user_by_name tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_get_user_by_name_found(mock_query):
    mock_query.return_value = [
        {"id": "1", "name": "Alice", "email": "a@test.com", "password": "pw", "role": "customer", "created_at": datetime.utcnow()}
    ]

    result = User.get_user_by_name("Alice")

    assert result["name"] == "Alice"
    mock_query.assert_called_once()


@patch("models.User.db.execute_query")
def test_get_user_by_name_not_found(mock_query):
    mock_query.return_value = []

    result = User.get_user_by_name("Missing")

    assert result is None


# ---------------------------
# set_languages tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_set_languages_success(mock_query):
    user = User("Test", "test@test.com", UserRole.TRANSLATOR)

    user.set_languages(["en", "sk"])

    assert user.languages == ["en", "sk"]
    assert mock_query.call_count == 2  # inserts


@patch("models.User.db.execute_query")
def test_set_languages_invalid(mock_query):
    user = User("X", "x@test.com", UserRole.TRANSLATOR)

    with pytest.raises(ValueError):
        user.set_languages("invalid")


# ---------------------------
# get_languages tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_get_languages(mock_query):
    user = User("Test", "test@test.com", UserRole.TRANSLATOR)
    user.id = "1234"

    mock_query.return_value = [
        {"language": "en"},
        {"language": "cz"},
    ]

    result = user.get_languages()

    assert result == ["en", "cz"]
    mock_query.assert_called_once()


# ---------------------------
# get_all_users tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_get_all_users(mock_query):
    mock_query.return_value = [
        {
            "id": "1",
            "name": "A",
            "email": "a@test.com",
            "role": "customer",
            "created_at": datetime.utcnow(),
        },
        {
            "id": "2",
            "name": "B",
            "email": "b@test.com",
            "role": "translator",
            "created_at": datetime.utcnow(),
        }
    ]

    users = User.get_all_users()

    assert len(users) == 2
    assert users[0].name == "A"
    assert users[1].role == UserRole.TRANSLATOR


# ---------------------------
# get_user_by_id tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_get_user_by_id_found(mock_query):
    mock_query.return_value = [
        {
            "id": "123",
            "name": "User1",
            "email": "u@test.com",
            "password": "pw",
            "role": "customer",
            "created_at": datetime.utcnow(),
        }
    ]

    user = User.get_user_by_id("123")

    assert user.name == "User1"
    assert user.role == UserRole.CUSTOMER
    mock_query.assert_called_once()


@patch("models.User.db.execute_query")
def test_get_user_by_id_not_found(mock_query):
    mock_query.return_value = []

    user = User.get_user_by_id("missing")

    assert user is None


# ---------------------------
# get_translators_by_language tests
# ---------------------------

@patch("models.User.db.execute_query")
def test_get_translators_by_language(mock_query):
    mock_query.return_value = [
        {
            "id": "999",
            "name": "Trans",
            "email": "t@test.com",
            "role": "translator",
            "created_at": datetime.utcnow(),
        }
    ]

    translators = User.get_translators_by_language("en")

    assert len(translators) == 1
    assert translators[0].role == UserRole.TRANSLATOR
    mock_query.assert_called_once()
