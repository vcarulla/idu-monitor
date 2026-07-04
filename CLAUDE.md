# CLAUDE.md — idu-monitor

Scraper que vigila las habilitaciones de IDU (Ley de Memoria Democrática) del Consulado
de España en Buenos Aires. Corre por **cron diario en GitHub Actions**, y si el rango
habilitado cambia avisa por **Telegram**. Python puro, ~220 líneas. Sin DB, sin web.

Código: `src/idu_monitor/scraper.py` · Estado: `data/state.json` · Tests: `tests/`.

## Antes de diagnosticar "no funciona": `git fetch`

El cron **commitea `data/state.json` y `data/last_run.txt` de vuelta al repo cada día**
(`chore: actualiza estado IDU [skip ci]`). Tu clon local queda atrás de `origin/main`
enseguida. Siempre `git fetch origin` y mirar `origin/main` antes de concluir nada.

- **`last_run.txt`** = liveness real (cambia en cada corrida). Si está fresco, el monitor corre.
- **`timestamp` de `state.json`** = solo cambia cuando cambia `hasta` (el rango avanzó).
  Un timestamp viejo NO es un bug: significa que el consulado no movió la cola desde entonces.
- Ver corridas: `gh run list --workflow monitor.yml`.

## Cómo funciona el parseo (gotchas del CMS)

El CMS del consulado inserta **zero-width spaces y espacios dentro de las palabras**
(`D esde`, `M ay​o`, `de julio`). Por eso `clean_text()` y las regex de `parse_ranges`
limpian agresivo. La tabla se identifica por contenido (`"NW-"`), no por clase CSS
(la clase cambia con cada rediseño del sitio). La web **apila** los meses (no borra los
viejos), así que `select_current` toma el rango de mayor `hasta`.

## Reglas

- **Push directo a `main`**, sin PRs ni required checks (soy solo dev).
- Commits **sin coautor ni firma** `Co-Authored-By`/`Generated with`.
- **Pre-push hook** corre `ruff` + `pytest` y aborta el push si fallan. Activar una vez
  por clon: `git config core.hooksPath .githooks`.
- El workflow `monitor.yml` corre `pytest` antes de scrapear: no notificar sobre código roto.

## Comandos

```bash
source venv/bin/activate            # deps de dev en venv/
PYTHONPATH=src python -m idu_monitor  # corrida completa (necesita .env con BOT_TOKEN/CHAT_ID/MY_IDU)
pytest -q                           # tests del parser (usan HTML de fixture)
ruff check .                        # lint
```

Config por entorno (ver `.env.example`): `BOT_TOKEN`, `CHAT_ID`, `MY_IDU`, `STATE_DIR`,
`IDU_URL`. En CI vienen de Settings → Secrets/Variables.
