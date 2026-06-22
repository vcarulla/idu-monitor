"""Tests del parser y de la lógica de estado.

El parser se testea contra un HTML de fixture que replica el formato "sucio"
del CMS del consulado (zero-width spaces y palabras partidas), para que un
futuro rediseño de la web rompa el test antes que la producción.
"""
from pathlib import Path

import pytest

from idu_monitor.scraper import (
    determine_status,
    extract_idu_numbers,
    parse_html,
    parse_ranges,
    select_current,
)

FIXTURE = Path(__file__).parent / "fixtures" / "idu_page.html"


@pytest.fixture
def html():
    return FIXTURE.read_text(encoding="utf-8")


def test_parse_ranges_extrae_todas_las_filas(html):
    ranges = parse_ranges(html)
    assert len(ranges) == 2
    assert ranges[0]["mes"] == "Mayo 2026"
    assert ranges[1] == {
        "desde": "NW-2024-067241",
        "hasta": "NW-2024-080072",
        "mes": "Julio 2026",
    }


def test_select_current_elige_el_hasta_mas_alto(html):
    current = select_current(parse_ranges(html))
    # Julio (080072) gana sobre Mayo (067240) aunque Mayo va primero en la tabla.
    assert current["hasta"] == "NW-2024-080072"
    assert current["mes"] == "Julio 2026"


def test_parse_html_reporta_el_rango_mas_avanzado(html):
    data = parse_html(html)
    assert data["hasta"] == "NW-2024-080072"
    assert data["mes"] == "Julio 2026"
    assert "timestamp" in data
    assert len(data["ranges"]) == 2


def test_parse_ranges_sin_tabla_falla():
    with pytest.raises(ValueError):
        parse_ranges("<html><body><p>sin tabla</p></body></html>")


def test_extract_idu_numbers():
    assert extract_idu_numbers("NW-2024-110693") == 110693
    with pytest.raises(ValueError):
        extract_idu_numbers("no-es-un-idu")


def test_determine_status_idu_en_algun_rango():
    ranges = [
        {"desde": "NW-2024-055880", "hasta": "NW-2024-067240", "mes": "Mayo 2026"},
        {"desde": "NW-2024-067241", "hasta": "NW-2024-080072", "mes": "Julio 2026"},
    ]
    assert determine_status("NW-2024-070000", ranges) == "AL FIN NOS TOCA A NOSOTROS!!!!"
    assert determine_status("NW-2024-110693", ranges) == "Hay que esperar..."


def test_determine_status_ya_falta_poco():
    ranges = [{"desde": "NW-2024-085000", "hasta": "NW-2024-095000", "mes": "X 2026"}]
    assert determine_status("NW-2024-110693", ranges) == "YA FALTA POCO!!"
