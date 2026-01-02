"""add_performance_indexes_to_projects

Revision ID: 1211414ef3fe
Revises: 001
Create Date: 2026-01-01 18:45:25.232743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1211414ef3fe'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes to timestamp columns for improved query performance
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])
    op.create_index('ix_projects_updated_at', 'projects', ['updated_at'])
    op.create_index('ix_projects_submitted_at', 'projects', ['submitted_at'])
    op.create_index('ix_projects_calculated_at', 'projects', ['calculated_at'])
    op.create_index('ix_projects_reviewed_at', 'projects', ['reviewed_at'])
    op.create_index('ix_projects_approved_at', 'projects', ['approved_at'])
    op.create_index('ix_projects_locked_at', 'projects', ['locked_at'])

    # Add composite indexes for common query patterns
    op.create_index('idx_project_status_year', 'projects', ['status', 'reporting_year'])
    op.create_index('idx_project_created_by_status', 'projects', ['created_by', 'status'])
    op.create_index('idx_project_status_created', 'projects', ['status', 'created_at'])


def downgrade() -> None:
    # Drop composite indexes
    op.drop_index('idx_project_status_created', 'projects')
    op.drop_index('idx_project_created_by_status', 'projects')
    op.drop_index('idx_project_status_year', 'projects')

    # Drop timestamp indexes
    op.drop_index('ix_projects_locked_at', 'projects')
    op.drop_index('ix_projects_approved_at', 'projects')
    op.drop_index('ix_projects_reviewed_at', 'projects')
    op.drop_index('ix_projects_calculated_at', 'projects')
    op.drop_index('ix_projects_submitted_at', 'projects')
    op.drop_index('ix_projects_updated_at', 'projects')
    op.drop_index('ix_projects_created_at', 'projects')
