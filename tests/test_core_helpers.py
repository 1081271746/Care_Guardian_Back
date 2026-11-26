from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, ValidationError

from app.core.time import app_timezone, as_utc, local_today, utc_now
from app.schemas.common import BirthDate, OptionalText, PastTimestamp, Phone, Text


def test_utc_now_is_aware():
    assert utc_now().tzinfo is not None


def test_local_today_uses_configured_zone(monkeypatch):
    monkeypatch.setenv("APP_TIMEZONE", "Pacific/Kiritimati")  # UTC+14
    ahead = local_today()
    monkeypatch.setenv("APP_TIMEZONE", "Pacific/Pago_Pago")  # UTC-11
    behind = local_today()
    assert (ahead - behind).days in (1, 2)


def test_invalid_zone_is_rejected():
    with pytest.raises(ValueError):
        app_timezone("Nowhere/Invalid")


def test_as_utc_handles_naive_and_aware_values():
    assert as_utc(datetime(2026, 1, 1, 5)).tzinfo == timezone.utc
    bogota = datetime(2026, 1, 1, 0, tzinfo=timezone(timedelta(hours=-5)))
    assert as_utc(bogota).hour == 5


class Sample(BaseModel):
    name: Text(10)
    note: OptionalText(5) = None
    phone: Phone = None
    born: BirthDate = date(1950, 1, 1)
    seen: PastTimestamp = None


@pytest.mark.parametrize("payload", [
    {"name": "  "}, {"name": "x" * 11}, {"name": "ok", "note": "123456"},
    {"name": "ok", "phone": "abc"}, {"name": "ok", "born": "1800-01-01"},
    {"name": "ok", "seen": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
    {"name": "bad\x07"},
])
def test_shared_types_reject_invalid_values(payload):
    with pytest.raises(ValidationError):
        Sample(**payload)


def test_shared_types_normalize_values():
    sample = Sample(name="  Ana ", note="  ", phone=" +57 300 1234567 ")
    assert sample.name == "Ana" and sample.note is None and sample.phone == "+57 300 1234567"
