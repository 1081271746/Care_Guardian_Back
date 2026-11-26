from types import SimpleNamespace

from app.services.historical_analysis import analyze_patient_history
from app.services.note_analysis import analyze_caregiver_note
from app.services.risk_analysis import analyze_symptoms


def test_original_historical_rules():
    records = [
        SimpleNamespace(calidad_sueno=8, nivel_dolor=2, temperatura=36.5, apetito="normal", estado_animo="estable"),
        SimpleNamespace(calidad_sueno=4, nivel_dolor=7, temperatura=38.2, apetito="bajo", estado_animo="decaído"),
    ]
    result = analyze_patient_history(records)
    assert result.registros_analizados == 2
    assert result.nivel == "alto"
    assert result.score == 9
    assert analyze_patient_history([]).registros_analizados == 0


def test_original_risk_rules():
    result = analyze_symptoms(SimpleNamespace(
        nivel_dolor=6, temperatura=37.8, calidad_sueno=4, apetito="bajo",
        estado_animo="estable", nivel_gravedad="moderado",
    ))
    assert result.score == 6
    assert result.nivel == "medio"


def test_original_notes_rules():
    result = analyze_caregiver_note("No quiso comer y durmió mal. Está triste.")
    assert result.score == 6
    assert "Alteración del sueño" in result.factores
