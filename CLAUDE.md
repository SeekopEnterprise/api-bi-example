# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup y ejecución

Entorno virtual e instalación de dependencias:

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

Variables de entorno requeridas (archivo `.env` en la raíz):
`EMAIL_USER`, `PWD_USER`, `CLIENT_ID`, `SECRET_KEY`, `MARCA`.

Cada script en [src/](src/) es un punto de entrada independiente y ejecutable:

```powershell
python src/app.py           # Indicadores BI nacional (lectura, log de totales)
python src/app20.py         # Indicadores20 + ingesta a MySQL (sicopdb.analisisdiariobdc)
python src/funnel.py        # Funnel detalle (versión async con aiohttp)
python src/funnelGeneral.py # Funnel v8 detalle general
python src/apprtqc.py       # Quickcount QA → exporta CSV para conteo de registros
```

No existen tests ni linters configurados; no hay build step.

## Arquitectura

Cliente Python que consume APIs REST de SEEKOP (`api.sicopweb.com`). El repo es una **colección de ejemplos copy-paste** que muestran cómo consumir distintos endpoints de las APIs de datos. Cada script en `src/` es **intencionalmente autónomo** — duplica `get_access_token`, las clases de credenciales y el loop de paginación a propósito, para que cualquiera pueda copiar un archivo aislado a otro proyecto sin arrastrar dependencias internas. **No refactorizar a módulos compartidos.** Al corregir bugs o mejorar patrones comunes, propagar el cambio a todos los scripts relevantes.

**Flujo común a todos los scripts:**

1. `load_dotenv()` + `get_env_var()` para credenciales.
2. `get_access_token(UserCredentials, ClientCredentials)` → POST a `URL_AUTH_ENDPOINT` (`/auth/v3/token`), regresa bearer token.
3. POST al `URL_ENDPOINT_SERVICE` (varía por script) con `Authorization: Bearer <token>` y payload JSON que incluye `fbyfechaini`, `fbyfechafin`, `frecuencia`, `gby` y `page`.
4. **Paginación por encabezados de respuesta:**
   - `x-sicop-api-pages` → total de páginas.
   - `x-sicop-api-current-page` → página actual.
   - Loop `while current_page < total_pages` incrementando `page` en el payload.
5. Procesamiento (logging de totales, inserción a MySQL, escritura CSV, etc.).

**Diferencias clave por script:**

- [src/app.py](src/app.py) — endpoint `/bi/prod/indicadores/{MARCA}/nacional`; agrega totales (`prospectos`, `prospectospiso`, `leads`) y calcula fecha máxima recibida.
- [src/app20.py](src/app20.py) — endpoint `/bi/prod/indicadores20/{MARCA}/nacional`; **persiste a MySQL local** (`sicopdb.analisisdiariobdc`). Lee credenciales DB de `$HOME/.mysql/prod.conf` (formato `key=value`). Hace `TRUNCATE` antes de insertar por lotes con `cursor.executemany`.
- [src/funnel.py](src/funnel.py) — endpoint `/funnel/prod/indicadores/nacional/detalle`; usa `aiohttp` para descargar páginas **concurrentemente** (única implementación async del repo).
- [src/funnelGeneral.py](src/funnelGeneral.py) — endpoint `/funnel/v8/indicadores/nacional/detalle/general`.
- [src/apprtqc.py](src/apprtqc.py) — endpoint **QA** `/bi/qa/rt/quickcount/{MARCA}`; exporta CSV para verificar número de registros.

**Convenciones:**

- Fechas en los payloads van como strings `YYYYMMDD` (no ISO).
- El parámetro `gby` controla la dimensionalidad de agrupación; los nombres de campo en la respuesta JSON deben coincidir con las columnas esperadas (en `app20.py`, los `%(campo)s` del INSERT mapean directo a las llaves del dict de cada fila).
- Logging vía `logging.basicConfig(level=INFO)`; los scripts imprimen tiempo total al final.
