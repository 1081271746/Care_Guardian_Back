"""Add lookup indexes, a unique caregiver assignment and analysis period columns.

Non-destructive: only CREATE INDEX / ADD COLUMN. Existing rows are untouched.
If duplicated caregiver assignments already exist, the unique index is skipped
(and reported) instead of deleting anything.
"""
import logging

from alembic import op
import sqlalchemy as sa

revision = "003_indexes_period"
down_revision = "002_evolution"

logger = logging.getLogger("alembic.runtime.migration")

PATIENT_TABLES = ("medications", "appointments", "symptom_records", "caregiver_notes", "alerts")


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in PATIENT_TABLES:
        op.create_index(f"ix_{table}_patient_id", table, ["patient_id"], if_not_exists=True)
    op.create_index("ix_patient_caregivers_user_id", "patient_caregivers", ["user_id"], if_not_exists=True)

    duplicates = bind.execute(sa.text(
        "SELECT COUNT(*) FROM (SELECT patient_id, user_id FROM patient_caregivers "
        "GROUP BY patient_id, user_id HAVING COUNT(*) > 1) AS repeated"
    )).scalar()
    if duplicates:
        logger.warning(
            "Se omitió uq_patient_caregivers_patient_user: hay %s asignaciones repetidas. "
            "Revísalas manualmente; la migración no borra datos.", duplicates,
        )
    else:
        op.create_index("uq_patient_caregivers_patient_user", "patient_caregivers",
                        ["patient_id", "user_id"], unique=True, if_not_exists=True)

    existing = {column["name"] for column in inspector.get_columns("evolution_analyses")}
    with op.batch_alter_table("evolution_analyses") as batch:
        if "period_start" not in existing:
            batch.add_column(sa.Column("period_start", sa.Date(), nullable=True))
        if "period_end" not in existing:
            batch.add_column(sa.Column("period_end", sa.Date(), nullable=True))
        if "error" not in existing:
            batch.add_column(sa.Column("error", sa.String(200), nullable=True))


def downgrade():
    raise RuntimeError("Esta migración solo agrega índices y columnas; no se revierte automáticamente")
