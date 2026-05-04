"""prompt template advisor wiring

Revision ID: 20260504_0040
Revises: 20260504_0039
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260504_0040'
down_revision = '20260504_0039'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('prompt_templates', sa.Column('assistant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('prompt_templates', sa.Column('required_plan', sa.String(length=50), nullable=False, server_default='free'))
    op.add_column('prompt_templates', sa.Column('visibility', sa.String(length=30), nullable=False, server_default='system'))
    op.create_index(op.f('ix_prompt_templates_assistant_id'), 'prompt_templates', ['assistant_id'], unique=False)
    op.create_foreign_key('fk_prompt_templates_assistant_id_assistant_profiles', 'prompt_templates', 'assistant_profiles', ['assistant_id'], ['id'], ondelete='SET NULL')
    op.alter_column('prompt_templates', 'required_plan', server_default=None)
    op.alter_column('prompt_templates', 'visibility', server_default=None)

def downgrade() -> None:
    op.drop_constraint('fk_prompt_templates_assistant_id_assistant_profiles', 'prompt_templates', type_='foreignkey')
    op.drop_index(op.f('ix_prompt_templates_assistant_id'), table_name='prompt_templates')
    op.drop_column('prompt_templates', 'visibility')
    op.drop_column('prompt_templates', 'required_plan')
    op.drop_column('prompt_templates', 'assistant_id')
