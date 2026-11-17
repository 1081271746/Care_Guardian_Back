"""Add consent audit, quota attempts and verified summaries."""
from alembic import op
import sqlalchemy as sa

revision = "002_evolution"
down_revision = "001_existing"


def upgrade():
    op.create_table(
        "evolution_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_version", sa.String(30), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
    )
    for column in ("patient_id", "user_id", "created_at"):
        op.create_index(f"ix_evolution_analyses_{column}", "evolution_analyses", [column])


def downgrade():
    raise RuntimeError("La reversión eliminaría resúmenes y consentimientos; requiere un plan de conservación")
