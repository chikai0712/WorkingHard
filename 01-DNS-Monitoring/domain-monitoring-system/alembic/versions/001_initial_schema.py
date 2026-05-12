"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2026-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create domains table
    op.create_table(
        'domains',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('expected_ips', postgresql.ARRAY(postgresql.INET()), nullable=False),
        sa.Column('expected_ns', postgresql.ARRAY(sa.String(length=255)), nullable=False),
        sa.Column('keyword', sa.String(length=500), nullable=True),
        sa.Column('check_interval', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_domains_domain'), 'domains', ['domain'], unique=True)
    
    # Create nameservers table
    op.create_table(
        'nameservers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('isp_name', sa.String(length=100), nullable=False),
        sa.Column('dns_server', postgresql.INET(), nullable=False),
        sa.Column('is_healthy', sa.Boolean(), nullable=True),
        sa.Column('last_check', sa.TIMESTAMP(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dns_server')
    )
    op.create_index(op.f('ix_nameservers_country_code'), 'nameservers', ['country_code'], unique=False)
    
    # Create monitoring_events table
    op.create_table(
        'monitoring_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_events_domain_id'), 'monitoring_events', ['domain_id'], unique=False)
    op.create_index(op.f('ix_monitoring_events_timestamp'), 'monitoring_events', ['timestamp'], unique=False)
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('alert_level', sa.String(length=10), nullable=False),
        sa.Column('root_cause', sa.String(length=100), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('first_seen', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_seen', sa.TIMESTAMP(), nullable=True),
        sa.Column('notified_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_domain_id'), 'alerts', ['domain_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_alerts_domain_id'), table_name='alerts')
    op.drop_table('alerts')
    op.drop_index(op.f('ix_monitoring_events_timestamp'), table_name='monitoring_events')
    op.drop_index(op.f('ix_monitoring_events_domain_id'), table_name='monitoring_events')
    op.drop_table('monitoring_events')
    op.drop_index(op.f('ix_nameservers_country_code'), table_name='nameservers')
    op.drop_table('nameservers')
    op.drop_index(op.f('ix_domains_domain'), table_name='domains')
    op.drop_table('domains')

