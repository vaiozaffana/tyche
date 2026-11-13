"""Create the authentication tables without replacing existing template data."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    if "User" not in existing:
        op.create_table(
            "User",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("email", sa.Text(), nullable=False),
            sa.Column("emailVerified", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("image", sa.Text()),
            sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updatedAt", sa.DateTime(), nullable=False),
            sa.Column("role", sa.Text()),
            sa.Column("banned", sa.Boolean()),
            sa.Column("banReason", sa.Text()),
            sa.Column("banExpires", sa.DateTime()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("User_email_key", "User", ["email"], unique=True)

    if "Account" not in existing:
        op.create_table(
            "Account",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("accountId", sa.Text(), nullable=False),
            sa.Column("providerId", sa.Text(), nullable=False),
            sa.Column("userId", sa.Text(), nullable=False),
            sa.Column("accessToken", sa.Text()),
            sa.Column("refreshToken", sa.Text()),
            sa.Column("idToken", sa.Text()),
            sa.Column("accessTokenExpiresAt", sa.DateTime()),
            sa.Column("refreshTokenExpiresAt", sa.DateTime()),
            sa.Column("scope", sa.Text()),
            sa.Column("password", sa.Text()),
            sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updatedAt", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["userId"], ["User.id"], ondelete="CASCADE", onupdate="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if "Session" not in existing:
        op.create_table(
            "Session",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("expiresAt", sa.DateTime(), nullable=False),
            sa.Column("token", sa.Text(), nullable=False),
            sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updatedAt", sa.DateTime(), nullable=False),
            sa.Column("ipAddress", sa.Text()),
            sa.Column("userAgent", sa.Text()),
            sa.Column("userId", sa.Text(), nullable=False),
            sa.Column("impersonatedBy", sa.Text()),
            sa.ForeignKeyConstraint(
                ["userId"], ["User.id"], ondelete="CASCADE", onupdate="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("Session_token_key", "Session", ["token"], unique=True)

    if "Verification" not in existing:
        op.create_table(
            "Verification",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("identifier", sa.Text(), nullable=False),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("expiresAt", sa.DateTime(), nullable=False),
            sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("updatedAt", sa.DateTime()),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    # shortcut: this baseline may adopt existing tables; use an explicit reset migration for drops.
    pass
