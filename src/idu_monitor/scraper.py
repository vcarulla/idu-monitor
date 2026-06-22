#!/usr/bin/env python3
"""Scrapea la web del consulado y avisa por Telegram cuando cambia el rango de IDU."""
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Carga opcional de .env para desarrollo local. En CI las variables vienen del entorno.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Configuración (todo por entorno; nada de secretos hardcodeados) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
MY_IDU = os.environ.get("MY_IDU", "NW-2024-110693")
STATE_DIR = Path(os.environ.get("STATE_DIR", "data"))
STATE_FILE = STATE_DIR / "state.json"
URL = os.environ.get(
    "IDU_URL",
    "https://www.exteriores.gob.es/Consulados/buenosaires/es/ServiciosConsulares/"
    "Paginas/IDUs-Ley-de-Memoria-Democratica.aspx",
)


def clean_text(s):
    """Normaliza el texto del sitio (quita zero-width spaces y colapsa espacios).

    El CMS del consulado inserta caracteres invisibles (​) y espacios dentro de las
    palabras (ej: 'D esde', 'M ay​o'), así que hay que limpiar antes de parsear.
    """
    s = s.replace("​", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def extract_idu_numbers(idu_string):
    """Extrae el número de un IDU (ej: NW-2024-XXXXXX -> XXXXXX)."""
    match = re.search(r"NW-\d+-(\d+)", idu_string)
    if match:
        return int(match.group(1))
    raise ValueError(f"No se pudo parsear el IDU: {idu_string}")


def parse_ranges(html):
    """Extrae TODOS los rangos de IDU de la tabla (la web apila los meses, no los borra).

    Separado de la descarga para poder testearlo con HTML de fixture.
    Devuelve una lista de dicts {desde, hasta, mes} en el orden en que aparecen.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Identificamos la tabla por su contenido (la clase del CMS cambia con cada rediseño).
    table = None
    for t in soup.find_all("table"):
        if "NW-" in t.get_text():
            table = t
            break
    if not table:
        raise ValueError("No se encontró la tabla de habilitaciones")

    ranges = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        # Texto sin espacios para tolerar palabras partidas (ej: 'D esde').
        row_nospace = clean_text(row.get_text(" ")).replace(" ", "")
        match = re.search(r"[Dd]esde(NW-\d+-\d+)hasta(NW-\d+-\d+)", row_nospace)
        if not match:
            continue
        desde, hasta = match.group(1), match.group(2)

        mes = "Desconocido"
        mes_text = clean_text(cells[0].get_text(" "))
        mes_match = re.search(
            r"([A-Za-záéíóúñÁÉÍÓÚÑ][A-Za-záéíóúñÁÉÍÓÚÑ ]*?)\s*(\d{4})", mes_text
        )
        if mes_match:
            mes = f"{mes_match.group(1).replace(' ', '')} {mes_match.group(2)}"

        ranges.append({"desde": desde, "hasta": hasta, "mes": mes})

    if not ranges:
        raise ValueError("No se encontró el rango de IDU en la tabla")
    return ranges


def select_current(ranges):
    """Devuelve el rango más avanzado: el de mayor 'hasta'.

    La web lista meses ya pasados además de los próximos, así que la primera fila puede
    estar atrasada. El 'hasta' más alto es hasta dónde llegó realmente la cola.
    """
    return max(ranges, key=lambda r: extract_idu_numbers(r["hasta"]))


def parse_html(html):
    """Devuelve el rango más avanzado con timestamp, más la lista completa de rangos."""
    ranges = parse_ranges(html)
    current = dict(select_current(ranges))
    current["timestamp"] = datetime.now(UTC).isoformat()
    current["ranges"] = ranges
    return current


def scrape_website():
    """Descarga el sitio y devuelve el rango de IDU habilitado."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()
    return parse_html(response.content)


def determine_status(my_idu, ranges):
    """Determina el estado evaluando el IDU contra TODOS los rangos publicados."""
    my_num = extract_idu_numbers(my_idu)

    for r in ranges:
        if extract_idu_numbers(r["desde"]) <= my_num <= extract_idu_numbers(r["hasta"]):
            return "AL FIN NOS TOCA A NOSOTROS!!!!"

    max_hasta = max(extract_idu_numbers(r["hasta"]) for r in ranges)
    if max_hasta >= 90000:
        return "YA FALTA POCO!!"
    return "Hay que esperar..."


def load_state():
    """Carga el estado anterior del archivo."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
                return data if data else None
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def save_state(data):
    """Guarda el estado actual."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def send_telegram_message(message):
    """Envía un mensaje a Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Falta BOT_TOKEN o CHAT_ID en el entorno; no se puede enviar.")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Mensaje enviado a Telegram")
        return True
    except Exception as e:
        print(f"❌ Error al enviar mensaje: {e}")
        return False


def main():
    print(f"🔍 Scrappeando {URL}...")

    current_data = scrape_website()
    print("✅ Datos obtenidos:")
    print(f"   Mes:   {current_data['mes']}")
    print(f"   Desde: {current_data['desde']}")
    print(f"   Hasta: {current_data['hasta']}")

    previous_data = load_state()

    status = determine_status(MY_IDU, current_data["ranges"])
    current_data["status"] = status
    print(f"📊 Tu IDU ({MY_IDU}): {status}")

    if previous_data is None:
        print("📝 Primera ejecución, guardando estado...")
        save_state(current_data)
        return

    if previous_data["hasta"] == current_data["hasta"]:
        print("⏭️  No hay cambios desde la última verificación. No se envía mensaje.")
        return

    print("🔄 ¡CAMBIO DETECTADO!")
    print(f"   Antes: hasta {previous_data['hasta']}")
    print(f"   Ahora: hasta {current_data['hasta']}")

    message = f"""
<b>🚨 ACTUALIZACIÓN IDU - Ley de Memoria Democrática</b>

<b>Próxima habilitación – {current_data['mes']}:</b>
Desde: {current_data['desde']}
Hasta: {current_data['hasta']}

<b>Tu IDU ({MY_IDU}):</b>
<b>{status}</b>

<i>Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>
""".strip()

    if send_telegram_message(message):
        save_state(current_data)
    else:
        print("⚠️  No se guardó el estado por error en el envío")


if __name__ == "__main__":
    main()
