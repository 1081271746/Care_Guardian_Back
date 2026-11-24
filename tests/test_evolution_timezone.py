from datetime import datetime, timedelta, timezone

from app.services.evolution import utc


def test_naive_legacy_timestamps_are_interpreted_as_utc():
    value = datetime(2026, 11, 1, 12)
    assert utc(value).isoformat() == "2026-11-01T12:00:00+00:00"


def test_offsets_are_normalized_before_timeline_sorting():
    local = datetime(2026, 11, 1, 8, tzinfo=timezone(timedelta(hours=-5)))
    earlier = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    assert utc(local).isoformat() > utc(earlier).isoformat()
    assert utc(local).hour == 13
    assert utc(utc(local)) == utc(local)
