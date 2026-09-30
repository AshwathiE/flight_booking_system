from datetime import date, datetime, time
import sys
import types

# Create lightweight stubs for reportlab modules used in pdf_generator
pkg = types.ModuleType("reportlab")
lib = types.ModuleType("reportlab.lib")
pagesizes = types.ModuleType("reportlab.lib.pagesizes")
pagesizes.letter = (612, 792)
platypus = types.ModuleType("reportlab.platypus")
platypus.SimpleDocTemplate = object
platypus.Paragraph = object
platypus.Spacer = object
platypus.Table = object
platypus.TableStyle = object
styles_mod = types.ModuleType("reportlab.lib.styles")
styles_mod.getSampleStyleSheet = lambda: {"Heading1": None}
styles_mod.ParagraphStyle = type("ParagraphStyle", (), {})
colors = types.ModuleType("reportlab.lib.colors")
colors.HexColor = lambda code: code

sys.modules["reportlab"] = pkg
sys.modules["reportlab.lib"] = lib
sys.modules["reportlab.lib.pagesizes"] = pagesizes
sys.modules["reportlab.platypus"] = platypus
sys.modules["reportlab.lib.styles"] = styles_mod
sys.modules["reportlab.lib.colors"] = colors

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
