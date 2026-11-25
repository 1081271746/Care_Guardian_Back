"""Unit tests for the deterministic rule services (no database, no AI)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.historical_analysis import analyze_patient_history
from app.services.note_analysis import analyze_caregiver_note
from app.services.risk_analysis import analyze_symptoms


def symptom(**values):
    base = dict(nivel_dolor=None, temperatura=None, calidad_sueno=None, apetito=None,
                estado_animo=None, nivel_gravedad="bajo")
    return SimpleNamespace(**{**base, **values})


@pytest.mark.parametrize("values,level", [
    ({}, "bajo"),
    ({"nivel_dolor": 5, "calidad_sueno": 4, "apetito": "bajo"}, "medio"),
    ({"nivel_dolor": 9, "temperatura": 39.1, "nivel_gravedad": "grave"}, "alto"),
])
def test_symptom_risk_levels(values, level):
    assert analyze_symptoms(symptom(**values)).nivel == level


def test_symptom_risk_is_case_insensitive():
    result = analyze_symptoms(symptom(apetito="MUY BAJO", estado_animo="Decaído"))
    assert "Apetito muy bajo" in result.factores
    assert "Estado de ánimo decaído" in result.factores


def test_history_orders_by_date_before_comparing():
    start = datetime(2026, 11, 1, tzinfo=timezone.utc)
    newest_first = [
        SimpleNamespace(fecha_registro=start + timedelta(days=2), calidad_sueno=3, nivel_dolor=8,
                        temperatura=None, apetito=None, estado_animo=None),
        SimpleNamespace(fecha_registro=start, calidad_sueno=8, nivel_dolor=2,
                        temperatura=None, apetito=None, estado_animo=None),
    ]
    result = analyze_patient_history(newest_first)
    assert "Se observa un deterioro importante en la calidad del sueño." in result.tendencias
    assert "Se observa un aumento importante del nivel de dolor." in result.tendencias


def test_history_with_single_record_has_no_trends():
    result = analyze_patient_history([symptom(fecha_registro=datetime.now(timezone.utc), nivel_dolor=3)])
    assert result.tendencias == []
    assert result.nivel == "bajo"


@pytest.mark.parametrize("text,factor", [
    ("Se despertó varias veces", "Alteración del sueño"),
    ("Está desorientado y no reconoce a su hija", "Posible desorientación o confusión"),
    ("Tiene fiebre desde la tarde", "Posible fiebre o temperatura elevada"),
])
def test_note_patterns(text, factor):
    assert factor in analyze_caregiver_note(text).factores


def test_neutral_note_has_no_factors():
    result = analyze_caregiver_note("Caminamos por el parque y almorzó completo.")
    assert result.factores == [] and result.nivel == "bajo"
