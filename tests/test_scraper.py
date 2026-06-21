"""Tests del parser y de la lógica de estado.

El parser se testea contra un HTML de fixture que replica el formato "sucio"
del CMS del consulado (zero-width spaces y palabras partidas), para que un
futuro rediseño de la web rompa el test antes que la producción.
"""
from pathlib import Path

import pytest

from idu_monitor.scraper import determine_status, extract_idu_numbers, parse_html

FIXTURE = Path(__file__).parent / "fixtures" / "idu_page.html"


@pytest.fixture
def html():
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_html_extrae_primer_rango(html):
    data = parse_html(html)
    assert data["desde"] == "NW-2024-055880"
    assert data["hasta"] == "NW-2024-067240"
    assert data["mes"] == "Mayo 2026"
    assert "timestamp" in data


def test_parse_html_sin_tabla_falla():
    with pytest.raises(ValueError):
        parse_html("<html><body><p>sin tabla</p></body></html>")


def test_extract_idu_numbers():
    assert extract_idu_numbers("NW-2024-110693") == 110693
    with pytest.raises(ValueError):
        extract_idu_numbers("no-es-un-idu")


@pytest.mark.parametrize(
    "my_idu,desde,hasta,esperado",
    [
        ("NW-2024-060000", "NW-2024-055880", "NW-2024-067240", "AL FIN NOS TOCA A NOSOTROS!!!!"),
        ("NW-2024-110693", "NW-2024-055880", "NW-2024-067240", "Hay que esperar..."),
        ("NW-2024-110693", "NW-2024-085000", "NW-2024-095000", "YA FALTA POCO!!"),
    ],
)
def test_determine_status(my_idu, desde, hasta, esperado):
    assert determine_status(my_idu, desde, hasta) == esperado
