"""add_linda_content_columns

Revision ID: e7a3b1c2d4f5
Revises: ca31260d206e
Create Date: 2026-03-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a3b1c2d4f5'
down_revision: Union[str, Sequence[str], None] = 'ca31260d206e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('topics', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content_linda_it', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('content_linda_en', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('topics', schema=None) as batch_op:
        batch_op.drop_column('content_linda_en')
        batch_op.drop_column('content_linda_it')
