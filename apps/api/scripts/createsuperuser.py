from getpass import getpass

from repo_db import User, create_engine, create_session_factory
from sqlalchemy import select

from api.modules.auth.service import register_user
from api.settings import Settings


def main() -> None:
    settings = Settings()
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    email = input("Email: ").strip().lower()
    name = input("Name (optional): ").strip()
    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")
    if not email:
        raise ValueError("Email is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if password != confirmation:
        raise ValueError("Passwords do not match.")

    with factory() as database:
        user = database.scalar(select(User).where(User.email == email))
        if user:
            user.role = "admin"
            if name:
                user.name = name
            database.commit()
            print(f"Admin user ready: {user.email}. Existing password was not changed.")
        else:
            user = register_user(
                database,
                email=email,
                name=name or email,
                password=password,
                role="admin",
            )
            print(f"Admin user ready: {user.email}")
    engine.dispose()


if __name__ == "__main__":
    main()
