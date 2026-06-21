# idu-monitor

Monitor de habilitaciones de IDU (Ley de Memoria Democrática) del Consulado de España
en Buenos Aires. Scrapea la web oficial una vez por día y, cuando el rango habilitado
cambia, avisa por Telegram.

## Estructura

```
src/idu_monitor/    Código del scraper (parse + estado + Telegram)
tests/              Tests del parser con HTML de fixture
data/state.json     Estado persistido entre corridas
docs/               Notas de diseño y operación
.github/workflows/  CI (lint + tests) y monitor (cron diario)
```

## Desarrollo local

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # completá BOT_TOKEN / CHAT_ID / MY_IDU
PYTHONPATH=src python -m idu_monitor
```

Tests y lint:

```bash
pytest
ruff check .
```

## Configuración

Todo por entorno (ver `.env.example`):

| Variable    | Descripción                                   |
|-------------|-----------------------------------------------|
| `BOT_TOKEN` | Token del bot de Telegram (**secreto**)       |
| `CHAT_ID`   | Chat/grupo donde se envían los avisos         |
| `MY_IDU`    | IDU a monitorear (default `NW-2024-110693`)   |
| `STATE_DIR` | Carpeta del `state.json` (default `data`)     |

## Producción (GitHub Actions)

El workflow `.github/workflows/monitor.yml` corre el monitor por cron diario y commitea
el `state.json` de vuelta al repo. Configurar en **Settings → Secrets and variables → Actions**:

- Secrets: `BOT_TOKEN`, `CHAT_ID`
- Variables: `MY_IDU`

> **Nota cron:** GitHub deshabilita los workflows `schedule` tras ~60 días sin actividad
> del repo, y los commits del propio bot no siempre reinician ese contador. Si el monitor
> se apaga, basta con re-habilitarlo desde la pestaña Actions o empujar cualquier commit.
> Ver `docs/operacion.md`.

El `Dockerfile` se mantiene solo para correr local; en producción manda Actions.
