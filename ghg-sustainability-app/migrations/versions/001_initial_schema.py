"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for full-text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # Create criteria table
    op.create_table(
        'criteria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('criteria_number', sa.Integer(), nullable=False),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=False),
        sa.Column('subcategory', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('example', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_criteria_id'), 'criteria', ['id'], unique=False)
    op.create_index(op.f('ix_criteria_number'), 'criteria', ['criteria_number'], unique=True)
    op.create_index(op.f('ix_criteria_scope'), 'criteria', ['scope'], unique=False)

    # Create reason_codes table
    op.create_table(
        'reason_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reason_codes_id'), 'reason_codes', ['id'], unique=False)
    op.create_index(op.f('ix_reason_codes_code'), 'reason_codes', ['code'], unique=True)
    op.create_index(op.f('ix_reason_codes_category'), 'reason_codes', ['category'], unique=False)

    # Create formulas table
    op.create_table(
        'formulas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=False),
        sa.Column('formula_text', sa.Text(), nullable=False),
        sa.Column('formula_expression', sa.String(length=500), nullable=True),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('example', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_formulas_id'), 'formulas', ['id'], unique=False)
    op.create_index(op.f('ix_formulas_scope'), 'formulas', ['scope'], unique=False)
    op.create_index(op.f('ix_formulas_category'), 'formulas', ['category'], unique=False)

    # Create ecoinvent table
    op.create_table(
        'ecoinvent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('factor_name', sa.String(length=500), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=False),
        sa.Column('subcategory', sa.String(length=255), nullable=True),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('emission_factor', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=100), nullable=False),
        sa.Column('gwp', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('search_text', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ecoinvent_id'), 'ecoinvent', ['id'], unique=False)
    op.create_index(op.f('ix_ecoinvent_category'), 'ecoinvent', ['category'], unique=False)
    op.create_index(op.f('ix_ecoinvent_subcategory'), 'ecoinvent', ['subcategory'], unique=False)
    op.create_index(op.f('ix_ecoinvent_scope'), 'ecoinvent', ['scope'], unique=False)
    op.create_index(op.f('ix_ecoinvent_region'), 'ecoinvent', ['region'], unique=False)
    op.create_index(op.f('ix_ecoinvent_year'), 'ecoinvent', ['year'], unique=False)
    op.create_index('idx_ecoinvent_category_scope', 'ecoinvent', ['category', 'scope'], unique=False)
    # Create GIN index for full-text search
    op.create_index(
        'idx_ecoinvent_search',
        'ecoinvent',
        ['search_text'],
        unique=False,
        postgresql_using='gin',
        postgresql_ops={'search_text': 'gin_trgm_ops'}
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(length=255), nullable=False),
        sa.Column('organization_name', sa.String(length=255), nullable=False),
        sa.Column('reporting_year', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_by_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('total_scope1', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_scope2', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_scope3', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_emissions', sa.Float(), nullable=True, server_default='0.0'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_organization_name'), 'projects', ['organization_name'], unique=False)
    op.create_index(op.f('ix_projects_reporting_year'), 'projects', ['reporting_year'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)

    # Create project_data table
    op.create_table(
        'project_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=False),
        sa.Column('activity_data', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('has_evidence', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('entered_by', sa.Integer(), nullable=True),
        sa.Column('entered_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['criteria_id'], ['criteria.id'], ),
        sa.ForeignKeyConstraint(['entered_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_data_id'), 'project_data', ['id'], unique=False)
    op.create_index(op.f('ix_project_data_project_id'), 'project_data', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_data_criteria_id'), 'project_data', ['criteria_id'], unique=False)

    # Create calculations table
    op.create_table(
        'calculations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=False),
        sa.Column('project_data_id', sa.Integer(), nullable=False),
        sa.Column('activity_data', sa.Float(), nullable=False),
        sa.Column('emission_factor', sa.Float(), nullable=False),
        sa.Column('emission_factor_source', sa.String(length=255), nullable=True),
        sa.Column('gwp', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('unit_conversion', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('emissions_kg', sa.Float(), nullable=False),
        sa.Column('emissions_tco2e', sa.Float(), nullable=False),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=False),
        sa.Column('formula_used', sa.String(length=255), nullable=True),
        sa.Column('calculation_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('calculated_by', sa.Integer(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['calculated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['criteria_id'], ['criteria.id'], ),
        sa.ForeignKeyConstraint(['project_data_id'], ['project_data.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calculations_id'), 'calculations', ['id'], unique=False)
    op.create_index(op.f('ix_calculations_project_id'), 'calculations', ['project_id'], unique=False)
    op.create_index(op.f('ix_calculations_criteria_id'), 'calculations', ['criteria_id'], unique=False)
    op.create_index(op.f('ix_calculations_project_data_id'), 'calculations', ['project_data_id'], unique=False)
    op.create_index(op.f('ix_calculations_scope'), 'calculations', ['scope'], unique=False)

    # Create reviews table
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=False),
        sa.Column('reason_code_id', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('suggestions', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['reason_code_id'], ['reason_codes.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_id'), 'reviews', ['id'], unique=False)
    op.create_index(op.f('ix_reviews_project_id'), 'reviews', ['project_id'], unique=False)

    # Create approvals table
    op.create_table(
        'approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approvals_id'), 'approvals', ['id'], unique=False)
    op.create_index(op.f('ix_approvals_project_id'), 'approvals', ['project_id'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_role', sa.String(length=10), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('reason_code', sa.String(length=50), nullable=True),
        sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_project_id'), 'audit_logs', ['project_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_to_status'), 'audit_logs', ['to_status'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)

    # Create evidence table
    op.create_table(
        'evidence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['criteria_id'], ['criteria.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_project_id'), 'evidence', ['project_id'], unique=False)
    op.create_index(op.f('ix_evidence_criteria_id'), 'evidence', ['criteria_id'], unique=False)


def downgrade() -> None:
    op.drop_table('evidence')
    op.drop_table('audit_logs')
    op.drop_table('approvals')
    op.drop_table('reviews')
    op.drop_table('calculations')
    op.drop_table('project_data')
    op.drop_table('projects')
    op.drop_table('ecoinvent')
    op.drop_table('formulas')
    op.drop_table('reason_codes')
    op.drop_table('criteria')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
