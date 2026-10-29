"""Tests for DEM download helpers (no network, no API key)."""

import pytest

from download_dem import redact, stream_to_file


def test_stream_to_file_writes_and_counts(tmp_path):
    out = tmp_path / "dem" / "bbox.tif"
    assert stream_to_file([b"ab", b"", b"cde"], out) == 5
    assert out.read_bytes() == b"abcde"
    assert not (tmp_path / "dem" / "bbox.tif.part").exists()


def test_stream_to_file_leaves_nothing_on_interrupt(tmp_path):
    out = tmp_path / "bbox.tif"

    def broken():
        yield b"partial"
        raise OSError("connection reset")

    with pytest.raises(OSError):
        stream_to_file(broken(), out)
    assert list(tmp_path.iterdir()) == []


def test_redact_hides_api_key():
    msg = "GET https://portal.opentopography.org/API/globaldem?API_Key=abc123 failed"
    assert "abc123" not in redact(msg, "abc123")
    assert redact("no key here", "") == "no key here"
