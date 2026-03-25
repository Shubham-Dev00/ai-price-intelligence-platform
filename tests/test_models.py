from app.models import User


def test_password_hashing():
    user = User(full_name="A", email="a@example.com")
    user.set_password("secret123")
    assert user.password_hash != "secret123"
    assert user.check_password("secret123") is True
