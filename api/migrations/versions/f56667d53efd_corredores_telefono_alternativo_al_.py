"""corredores: telefono alternativo al email, email nullable

Revision ID: f56667d53efd
Revises: 61715d2c2096
Create Date: 2026-07-19 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f56667d53efd'
down_revision = '61715d2c2096'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('corredores', sa.Column('telefono', sa.String(length=30), nullable=True))
    op.create_unique_constraint('uq_corredores_telefono', 'corredores', ['telefono'])
    op.alter_column('corredores', 'email',
               existing_type=sa.String(length=255),
               nullable=True)
    op.create_check_constraint(
        'ck_corredores_email_o_telefono',
        'corredores',
        'email IS NOT NULL OR telefono IS NOT NULL',
    )


def downgrade() -> None:
    op.drop_constraint('ck_corredores_email_o_telefono', 'corredores', type_='check')
    op.alter_column('corredores', 'email',
               existing_type=sa.String(length=255),
               nullable=False)
    op.drop_constraint('uq_corredores_telefono', 'corredores', type_='unique')
    op.drop_column('corredores', 'telefono')
