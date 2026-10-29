"""Tests for the Open-Meteo client and CSV writer (no network)."""

import csv

import pytest

import fetch_rainfall
from fetch_rainfall import summarize_daily_precip, write_csv


def test_write_csv_rows_and_header(tmp_path):
    daily = {
        "time": ["2024-08-31", "2024-09-01"],
        "precipitation_sum": [120.5, 80.0],
        "rain_sum": [120.5, 80.0],
        "precipitation_hours": [20.0, 14.0],
    }
    out = tmp_path / "nested" / "rain.csv"
    n = write_csv(daily, out)
    assert n == 2
    rows = list(csv.reader(out.open(encoding="utf-8")))
    assert rows[0] == ["date", "precipitation_sum_mm", "rain_sum_mm", "precipitation_hours"]
    assert rows[1] == ["2024-08-31", "120.5", "120.5", "20.0"]


def test_write_csv_handles_short_series(tmp_path):
    daily = {"time": ["2024-08-31", "2024-09-01"], "precipitation_sum": [1.0]}
    out = tmp_path / "rain.csv"
    assert write_csv(daily, out) == 2
    rows = list(csv.reader(out.open(encoding="utf-8")))
    assert rows[2] == ["2024-09-01", "", "", ""]


def test_summarize_daily_precip_skips_none():
    daily = {
        "time": ["2024-08-31", "2024-09-01", "2024-09-02"],
        "precipitation_sum": [10.0, None, 5.5],
    }
    n, total = summarize_daily_precip(daily)
    assert n == 3
    assert total == pytest.approx(15.5)


def test_summarize_daily_precip_empty():
    assert summarize_daily_precip({}) == (0, 0.0)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_open_meteo_sends_expected_params(monkeypatch):
    calls = {}

    def fake_get(url, params, timeout):
        calls.update(url=url, params=params, timeout=timeout)
        return _FakeResponse({"daily": {"time": []}})

    monkeypatch.setattr(fetch_rainfall.requests, "get", fake_get)
    out = fetch_rainfall.fetch_open_meteo(16.51, 80.63, "2024-08-25", "2024-09-15")

    assert out == {"daily": {"time": []}}
    assert calls["url"] == fetch_rainfall.ARCHIVE_URL
    assert calls["params"]["latitude"] == 16.51
    assert calls["params"]["longitude"] == 80.63
    assert calls["params"]["start_date"] == "2024-08-25"
    assert calls["params"]["end_date"] == "2024-09-15"
    assert "precipitation_sum" in calls["params"]["daily"]
    assert calls["params"]["timezone"] == "Asia/Kolkata"
