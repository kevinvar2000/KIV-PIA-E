import pytest
from Model.User import User

def test_create_customer_valid():
    user = User("", "", None).create_customer("John Doe", "john@example.com")
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.role.name == "CUSTOMER"
    assert user.id is not None
    assert user.created_at is not None
    assert user.languages == []

def test_create_customer_invalid_name():
    with pytest.raises(ValueError) as excinfo:
        User("", "", None).create_customer("", "john@example.com")

