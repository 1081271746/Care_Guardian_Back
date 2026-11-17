"""Non-destructive baseline: create missing original tables, keep existing data."""
from alembic import op
from app.database.base import Base
from app.models import patient, user, patient_caregiver, medication, appointment
from app.models import symptom_record, caregiver_note, alert

revision = "001_existing"
down_revision = None


def upgrade():
    tables = [t for t in Base.metadata.sorted_tables if t.name != "evolution_analyses"]
    Base.metadata.create_all(op.get_bind(), tables=tables, checkfirst=True)


def downgrade():
    raise RuntimeError("No se elimina el esquema existente; restaura una copia de seguridad")
