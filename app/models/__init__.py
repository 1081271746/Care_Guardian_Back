"""Import every model so ``Base.metadata`` is complete wherever it is used."""
from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.caregiver_note import CaregiverNote
from app.models.evolution_analysis import EvolutionAnalysis
from app.models.medication import Medication
from app.models.patient import Patient
from app.models.patient_caregiver import PatientCaregiver
from app.models.symptom_record import SymptomRecord
from app.models.user import User

__all__ = [
    "User", "Patient", "PatientCaregiver", "Medication", "Appointment",
    "SymptomRecord", "CaregiverNote", "Alert", "EvolutionAnalysis",
]
