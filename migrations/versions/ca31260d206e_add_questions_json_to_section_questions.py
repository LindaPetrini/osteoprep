"""add_questions_json_to_section_questions

Revision ID: ca31260d206e
Revises: f9d56859adcc
Create Date: 2026-03-02 07:41:48.661821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca31260d206e'
down_revision: Union[str, Sequence[str], None] = 'f9d56859adcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add questions_json column to section_questions
    with op.batch_alter_table('section_questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('questions_json', sa.Text(), nullable=True))

    # Clear old single-question rows — they will be regenerated with 2-3 questions
    op.execute("DELETE FROM section_questions")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('section_questions', schema=None) as batch_op:
        batch_op.drop_column('questions_json')
