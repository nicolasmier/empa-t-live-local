"""eventos: inicio_directo (marca de cada entrada a En directo)

Revision ID: b7e4c1a90f23
Revises: f56667d53efd
Create Date: 2026-07-22 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e4c1a90f23'
down_revision = 'f56667d53efd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('eventos', sa.Column('inicio_directo', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('eventos', 'inicio_directo')
