from datetime import date, datetime, time

from backend.utils import pdf_generator


def test_format_value_none_and_numbers():
    assert pdf_generator.format_value(None) == ""
    assert pdf_generator.format_value(123) == "123"


def test_format_date_variants():
    d = date(2026, 8, 27)
    dt = datetime(2026, 8, 27, 15, 30)
    assert pdf_generator.format_date(d) == "27-08-2026"
    assert pdf_generator.format_date(dt) == "27-08-2026"
    assert pdf_generator.format_date("raw") == "raw"


def test_format_time_variants():
    t = time(9, 5)
    dt = datetime(2026, 8, 27, 9, 5)
    assert pdf_generator.format_time(t) == "09:05"
    assert pdf_generator.format_time(dt) == "09:05"
    assert pdf_generator.format_time(None) == ""


def test_format_datetime():
    dt = datetime(2026, 8, 27, 9, 5)
    assert pdf_generator.format_datetime(dt) == "27-08-2026 09:05"
    assert pdf_generator.format_datetime(None) == ""
