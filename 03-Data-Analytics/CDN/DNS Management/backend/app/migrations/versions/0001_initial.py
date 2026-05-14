"""Initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.models.provider import ProviderSlug, ProviderType
from app.models.sync_job import SyncStatus

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    provider_type_enum = sa.Enum(ProviderType, name="providertype")
    provider_slug_enum = sa.Enum(ProviderSlug, name="providerslug")
    sync_status_enum = sa.Enum(SyncStatus, name="syncstatus")

    provider_type_enum.create(op.get_bind(), checkfirst=True)
    provider_slug_enum.create(op.get_bind(), checkfirst=True)
    sync_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", provider_slug_enum, nullable=False, unique=True),
        sa.Column("provider_type", provider_type_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id", ondelete="CASCADE")),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("api_secret", sa.Text(), nullable=True),
        sa.Column("extra_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_accounts_id", "accounts", ["id"])

    op.create_table(
        "domains",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("nameservers", sa.JSON(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), server_default=sa.false()),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_domains_name", "domains", ["name"])

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="CASCADE")),
        sa.Column("provider_slug", sa.String(length=50), nullable=False),
        sa.Column("status", sync_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sync_jobs")
    op.drop_index("ix_domains_name", table_name="domains")
    op.drop_table("domains")
    op.drop_index("ix_accounts_id", table_name="accounts")
    op.drop_table("accounts")
    op.drop_table("providers")

    bind = op.get_bind()
    sa.Enum(SyncStatus, name="syncstatus").drop(bind, checkfirst=True)
    sa.Enum(ProviderSlug, name="providerslug").drop(bind, checkfirst=True)
    sa.Enum(ProviderType, name="providertype").drop(bind, checkfirst=True)

