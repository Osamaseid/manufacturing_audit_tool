import os
import tempfile

import pytest

from analayzer import calculate_idle_time
from file_parser import parse_file
from utils import normalize_timestamp
from validator import validate_file
from sample_data import generate_sample


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(content):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
    f.write(content)
    f.close()
    return f.name


# ---------------------------------------------------------------------------
# utils.normalize_timestamp
# ---------------------------------------------------------------------------

def test_timestamp_iso():
    assert normalize_timestamp("2024-01-01T10:00:00") is not None

def test_timestamp_unix_int():
    assert normalize_timestamp("1700000000") is not None

def test_timestamp_unix_float():
    assert normalize_timestamp("1700000000.5") is not None

def test_timestamp_unix_negative():
    # Negative Unix epoch (pre-1970) must not crash
    assert normalize_timestamp("-3600") is not None

def test_timestamp_garbage():
    assert normalize_timestamp("NOT_A_DATE") is None

def test_timestamp_empty():
    assert normalize_timestamp("") is None

def test_timestamp_whitespace():
    assert normalize_timestamp("   ") is None


# ---------------------------------------------------------------------------
# analayzer.calculate_idle_time
# ---------------------------------------------------------------------------

def test_idle_empty_list():
    assert calculate_idle_time([]) == 0.0

def test_idle_all_idle():
    data = [{"status": "IDLE"}] * 4
    assert calculate_idle_time(data) == 100.0

def test_idle_no_idle():
    data = [{"status": "RUNNING"}] * 4
    assert calculate_idle_time(data) == 0.0

def test_idle_mixed():
    data = [{"status": "IDLE"}, {"status": "RUNNING"},
            {"status": "IDLE"}, {"status": "RUNNING"}]
    assert calculate_idle_time(data) == 50.0

def test_idle_with_broken():
    # BROKEN counts toward total, diluting idle %
    data = [{"status": "IDLE"}, {"status": "BROKEN"}]
    assert calculate_idle_time(data) == 50.0

def test_idle_all_broken_no_zero_division():
    # 100% downtime must not raise ZeroDivisionError
    data = [{"status": "BROKEN"}] * 10
    assert calculate_idle_time(data) == 0.0


# ---------------------------------------------------------------------------
# file_parser.parse_file
# ---------------------------------------------------------------------------

def test_parse_valid_rows():
    path = _write_csv("timestamp,status\n2024-01-01T10:00:00,RUNNING\n2024-01-01T10:01:00,IDLE\n")
    try:
        data, skipped = parse_file(path)
        assert len(data) == 2 and skipped == 0
    finally:
        os.unlink(path)

def test_parse_skips_bad_timestamp():
    path = _write_csv("timestamp,status\nNOT_A_DATE,RUNNING\n2024-01-01T10:00:00,IDLE\n")
    try:
        data, skipped = parse_file(path)
        assert len(data) == 1 and skipped == 1
    finally:
        os.unlink(path)

def test_parse_skips_unknown_status():
    path = _write_csv("timestamp,status\n2024-01-01T10:00:00,UNKNOWN\n")
    try:
        data, skipped = parse_file(path)
        assert len(data) == 0 and skipped == 1
    finally:
        os.unlink(path)

def test_parse_accepts_broken_status():
    path = _write_csv("timestamp,status\n2024-01-01T10:00:00,BROKEN\n")
    try:
        data, skipped = parse_file(path)
        assert len(data) == 1 and skipped == 0
    finally:
        os.unlink(path)

def test_parse_mixed_timestamp_formats():
    path = _write_csv("timestamp,status\n1700000000,RUNNING\n2024-01-01T10:00:00,IDLE\n")
    try:
        data, skipped = parse_file(path)
        assert len(data) == 2 and skipped == 0
    finally:
        os.unlink(path)

def test_parse_missing_status_column_no_crash():
    # Row has only one column — must skip, not crash
    path = _write_csv("timestamp,status\n2024-01-01T10:00:00\n")
    try:
        data, skipped = parse_file(path)
        assert len(data) == 0 and skipped == 1
    finally:
        os.unlink(path)

def test_parse_all_malformed_no_crash():
    path = _write_csv("timestamp,status\nBAD,BAD\n,\nNOT_A_DATE,UNKNOWN\n")
    try:
        data, skipped = parse_file(path)
        assert len(data) == 0 and skipped == 3
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# validator.validate_file
# ---------------------------------------------------------------------------

def test_validate_valid_file():
    path = _write_csv("timestamp,status\n2024-01-01T10:00:00,RUNNING\n")
    try:
        valid, msg = validate_file(path)
        assert valid is True
    finally:
        os.unlink(path)

def test_validate_missing_column():
    path = _write_csv("timestamp\n2024-01-01T10:00:00\n")
    try:
        valid, msg = validate_file(path)
        assert valid is False
        assert "status" in msg
    finally:
        os.unlink(path)

def test_validate_data_gaps_reported():
    path = _write_csv("timestamp,status\n,RUNNING\n2024-01-01T10:00:00,\n")
    try:
        valid, msg = validate_file(path)
        assert valid is False
        assert "gap" in msg.lower() or "missing" in msg.lower()
    finally:
        os.unlink(path)

def test_validate_file_not_found():
    valid, msg = validate_file("nonexistent_file_xyz.csv")
    assert valid is False
    assert "not found" in msg.lower() or "error" in msg.lower()


# ---------------------------------------------------------------------------
# End-to-end: 10,000-row file with >=5% malformed data must not crash
# ---------------------------------------------------------------------------

def test_end_to_end_10k_resilience(tmp_path):
    csv_path = str(tmp_path / "test_sample.csv")
    generate_sample(file_name=csv_path, rows=10000, malformed_pct=0.05)

    # Must not raise
    data, skipped = parse_file(csv_path)

    total = len(data) + skipped
    assert total == 10000, "Row count mismatch"
    assert skipped >= 400, f"Expected >=5% malformed rows skipped, got {skipped}"
    assert len(data) > 0, "No valid rows parsed"

    idle_pct = calculate_idle_time(data)
    assert 0.0 <= idle_pct <= 100.0, f"Idle % out of range: {idle_pct}"
