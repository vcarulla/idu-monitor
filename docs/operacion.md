# Operación

## Cómo funciona

1. El cron diario (`monitor.yml`) descarga la web del consulado y extrae el primer
   rango "Desde NW-… hasta NW-…" de la tabla.
2. Compara el `hasta` con el guardado en `data/state.json`.
3. Si cambió, envía un mensaje a Telegram y guarda el nuevo estado.
4. Siempre actualiza `data/last_run.txt` (heartbeat) y commitea los cambios al repo.

## Decisiones de diseño

- **Identificación de la tabla por contenido, no por clase CSS.** El CMS del consulado
  ya rompió el scraper una vez al rediseñar la página (cambió URL, clase de tabla y metió
  caracteres invisibles en el texto). Buscar la tabla que contiene `NW-` y limpiar el
  texto antes de parsear lo hace resistente a esos cambios.
- **Tests con fixture "sucio".** `tests/fixtures/idu_page.html` replica los zero-width
  spaces y palabras partidas (`D esde`, `M ay​o`). Si la web vuelve a cambiar de forma
  incompatible, conviene refrescar el fixture con el HTML real.
- **GitHub Actions en vez de un contenedor con scheduler externo.** Sin servidor que
  mantener; el estado persiste commiteándolo al repo.

## Caveat del cron (importante)

GitHub deshabilita automáticamente los workflows `schedule` tras ~60 días sin actividad
del repositorio. Los commits hechos por el bot con `GITHUB_TOKEN` no siempre cuentan como
actividad. Opciones si el monitor se apaga:

1. Re-habilitarlo manualmente desde la pestaña **Actions** (un clic).
2. Empujar cualquier commit cada tanto.
3. Hacer que el paso "Commit state" empuje con un Personal Access Token (PAT) en vez del
   `GITHUB_TOKEN` por defecto: esos pushes sí reinician el contador de 60 días.

## Probar a mano

Desde la pestaña Actions → workflow "monitor/idu" → **Run workflow** (`workflow_dispatch`).
