# In-memory user store — replace with a real DB (e.g. SQLAlchemy + Postgres)
from typing import Optional

_users: dict[str, dict] = {}  # email -> {id, email, hashed_password}


def get_user_by_email(email: str) -> Optional[dict]:
    return _users.get(email)


def create_user(user_id: str, email: str, hashed_password: str) -> dict:
    user = {"id": user_id, "email": email, "hashed_password": hashed_password}
    _users[email] = user
    return user
