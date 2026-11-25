from unittest.mock import patch

import httpx

from scripts import check_groq

URL = "https://api.groq.com/openai/v1/chat/completions"


def test_check_reports_success_without_printing_the_key(capsys, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_only_value")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    ok = httpx.Response(200, request=httpx.Request("POST", URL), json={
        "choices": [{"message": {"content": '{"resumen":["prueba_dolor"],"revisar":[]}'}}]})
    with patch("app.services.groq_analysis.GroqHTTPClient.post", return_value=ok):
        assert check_groq.main() == 0
    out = capsys.readouterr().out
    assert "correctamente" in out and "gsk_test_only_value" not in out


def test_check_reports_missing_configuration(capsys, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert check_groq.main() == 1
    assert "503" in capsys.readouterr().out
