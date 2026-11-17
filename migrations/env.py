from alembic import context
from app.database.connection import engine
from app.database.base import Base
from app.models import patient, user, patient_caregiver, medication, appointment
from app.models import symptom_record, caregiver_note, alert, evolution_analysis

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata,
                      compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
