# CareGuardian · API (backend)

Sistema de acompañamiento y seguimiento para cuidadores de adultos mayores.
Este repositorio contiene la API REST (FastAPI + PostgreSQL + Groq). La interfaz
web está en [Care_Guardian_Front](https://github.com/1081271746/Care_Guardian_Front).

## Acceso de demostración

| Campo | Valor |
|---|---|
| Correo | `carlos@careguardian.com` |
| Contraseña | `CareGuardian123` |

Es una **cuenta de demostración** con pacientes ficticios. No registres datos
reales de personas con ella: cualquiera que lea este README puede iniciar sesión.
Si la cuenta todavía no existe en un entorno, créala con el procedimiento de
[carga de datos de demostración](#carga-segura-de-datos-de-demostración)
(`--create-account`).

> La IA de CareGuardian es una herramienta de apoyo al seguimiento. No
> diagnostica, no recomienda medicamentos ni cambia dosis y no sustituye a un
> profesional de la salud.

## Contenido

1. [Arquitectura](#arquitectura)
2. [Tecnologías](#tecnologías)
3. [Estructura de carpetas](#estructura-de-carpetas)
4. [Instalación y ejecución local](#instalación-y-ejecución-local)
5. [Variables de entorno](#variables-de-entorno)
6. [Autenticación y permisos](#autenticación-y-permisos)
7. [Endpoints](#endpoints)
8. [Base de datos y migraciones](#base-de-datos-y-migraciones)
9. [Integración con Groq](#integración-con-groq)
10. [Módulo de evolución](#módulo-de-evolución)
11. [Pruebas](#pruebas)
12. [Despliegue en Railway](#despliegue-en-railway)
13. [Carga segura de datos de demostración](#carga-segura-de-datos-de-demostración)
14. [Seguridad](#seguridad)

## Arquitectura

```text
Navegador ──► Frontend Angular (SSR, Node/Express)
                 │  /api/*  (proxy del mismo origen; el navegador nunca ve la URL interna)
                 ▼
             API FastAPI ──► PostgreSQL (Railway, volumen persistente)
                 │
                 └──► Groq (solo backend, solo con consentimiento y datos minimizados)
```

- Cada petición privada lleva un JWT (`Authorization: Bearer`).
- Todo recurso clínico pertenece a un paciente; una dependencia global
  (`app/core/access.py`) comprueba que el usuario esté asignado al paciente
  antes de ejecutar cualquier ruta con `patient_id` o con el id de un registro.
- Las reglas de riesgo (síntomas, notas, historial) son deterministas y locales.
  Groq solo se usa en **Evolución → Resumen con IA**.

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.13 | Lenguaje |
| FastAPI | API REST y OpenAPI (`/docs`) |
| SQLAlchemy 2 | ORM |
| Pydantic 2 | Validación de entrada/salida |
| Alembic | Migraciones no destructivas |
| PostgreSQL 16 | Persistencia |
| HTTPX | Cliente HTTP hacia Groq |
| PyJWT + pwdlib (Argon2) | Tokens y contraseñas |
| pytest | Pruebas (SQLite o PostgreSQL desechable) |

## Estructura de carpetas

```text
app/
  core/        access.py (permisos por paciente), dependencies.py (JWT),
               security.py (hash/tokens), time.py (UTC y zona del cuidador)
  database/    base declarativa y conexión
  models/      tablas SQLAlchemy (users, patients, patient_caregivers, medications,
               appointments, symptom_records, caregiver_notes, alerts, evolution_analyses)
  schemas/     validación Pydantic (common.py contiene tipos compartidos)
  routers/     auth, users, patients, medications, appointments, symptoms, notes,
               alerts, analysis, dashboard, evolution
  services/    reglas de riesgo, generador de alertas, resumen del panel,
               evolución y cliente de Groq
migrations/    Alembic (001 base, 002 análisis IA, 003 índices y período)
scripts/       carga de demostración por HTTP (seed_demo.py)
tests/         pruebas automatizadas
docs/          notas de entrega y carga
```

## Instalación y ejecución local

Requisitos: Python 3.13 y PostgreSQL 14 o superior.

```sh
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # completa los valores (ver tabla siguiente)
createdb careguardian                # o crea la base desde pgAdmin
alembic upgrade head                 # crea/actualiza tablas sin borrar datos
uvicorn app.main:app --reload --port 8000
```

- Documentación interactiva: <http://localhost:8000/docs>
- Salud: <http://localhost:8000/health> → `{"status":"ok","database":"ok"}`

Para generar un `SECRET_KEY` seguro:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB`. Se aceptan `postgres://` y `postgresql://` (Railway). Alternativa heredada: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. |
| `SECRET_KEY` | Sí | Mínimo 32 caracteres. La API no arranca sin ella. Cambiarla cierra todas las sesiones. |
| `CORS_ORIGINS` | Sí en producción | Orígenes permitidos separados por comas, p. ej. `https://careguardian-front.up.railway.app`. Con el proxy `/api` del frontend el navegador no llama a la API directamente, pero se mantiene por seguridad. |
| `GROQ_API_KEY` | Para IA | Clave de Groq. Sin ella, Evolución muestra “servicio no disponible” y nunca simula resultados. |
| `GROQ_MODEL` | Para IA | `openai/gpt-oss-20b` (soporta salida estructurada estricta). |
| `GROQ_TIMEOUT_SECONDS` | No | 1–120, por defecto `30`. |
| `GROQ_REQUESTS_PER_MINUTE` | No | Límite de análisis por cuidador y minuto, por defecto `10`. |
| `APP_TIMEZONE` | No | Zona IANA del calendario de los cuidadores, por defecto `America/Bogota`. Define “hoy”, las citas próximas y los límites de los períodos. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Duración del JWT (5–1440), por defecto `60`. |
| `ALLOW_PUBLIC_REGISTRATION` | No | `true` por defecto. `false` desactiva `POST /users/`. |
| `LOGIN_MAX_FAILURES` / `LOGIN_WINDOW_SECONDS` | No | Intentos fallidos por correo antes de responder `429` (por defecto 8 en 900 s; por dirección, 5 veces más). |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_RECYCLE_SECONDS` | No | Pool de conexiones a PostgreSQL (5 / 5 / 1800). |
| `LOG_LEVEL` | No | `INFO` por defecto. |
| `PORT` | Railway | Lo define Railway; localmente `8000`. |

Nunca subas `.env` al repositorio (está en `.gitignore`).

## Autenticación y permisos

1. `POST /users/` registra un cuidador (`nombre`, `email`, `password` de 8+
   caracteres con letras y números). El rol siempre es `cuidador`.
2. `POST /auth/login` devuelve `access_token`, `token_type` y `expires_in`.
3. El frontend envía `Authorization: Bearer <token>` en cada petición.
4. `GET /auth/me` devuelve el perfil y cuántos pacientes tiene asignados.

| Situación | Respuesta |
|---|---|
| Sin token, token mal formado, firmado con otra clave, sin `sub` | `401` + `WWW-Authenticate: Bearer` |
| Token expirado | `401` “Tu sesión expiró; inicia sesión nuevamente” |
| Usuario desactivado | `403` |
| Paciente no asignado (exista o no) | `403` (no se revela si existe) |
| Registro inexistente | `404` |

Quien crea un paciente queda asignado automáticamente. Otros cuidadores se
agregan desde `POST /patients/{id}/caregivers` por correo. Solo el autor puede
editar o eliminar sus notas; el resto del equipo puede leerlas.

## Endpoints

Todas las rutas (excepto `/`, `/health`, `/auth/login` y `POST /users/`) exigen token.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/login` | Iniciar sesión |
| GET | `/auth/me` | Perfil del usuario autenticado |
| POST | `/users/` | Registrar cuidador |
| GET/PUT/DELETE | `/users/{id}` | Cuenta propia |
| PUT | `/users/{id}/password` | Cambiar contraseña (requiere la actual) |
| GET/POST | `/patients/` | Listar (`?q=`, `?activos=`) / crear |
| GET/PUT | `/patients/{id}` | Consultar / actualizar |
| DELETE | `/patients/{id}` | **Desactivar** (el historial se conserva) |
| GET/POST | `/patients/{id}/caregivers` | Equipo de cuidado / asignar por `email` |
| DELETE | `/patients/{id}/caregivers/{user_id}` | Desasignar (siempre queda al menos uno) |
| GET/POST | `/medications/patients/{id}` | Listar (`?activos=`) / registrar |
| GET/PUT/DELETE | `/medications/{id}` | Consultar / actualizar / suspender |
| GET/POST | `/appointments/patients/{id}` | Listar (`?proximas=true`) / crear |
| GET/PUT/DELETE | `/appointments/{id}` | Consultar / actualizar / eliminar |
| GET/POST | `/symptoms/patients/{id}` | Historial paginado (`limit`, `offset`) / registrar |
| GET/PUT/DELETE | `/symptoms/{id}` | Consultar / corregir / desactivar |
| GET/POST | `/notes/patients/{id}` | Historial paginado / crear |
| GET/PUT/DELETE | `/notes/{id}` | Consultar / editar (autor) / desactivar (autor) |
| GET/POST | `/alerts/patients/{id}` | Activas (`?incluir_cerradas=`, `?nivel=`) / alerta manual |
| GET/PUT/DELETE | `/alerts/{id}` | Consultar / cambiar estado / descartar |
| GET | `/analysis/patients/{id}` | Análisis por reglas de los últimos 10 registros |
| GET | `/dashboard/summary` | Indicadores de todos los pacientes asignados |
| GET | `/dashboard/patients/{id}` | Panel de un paciente |
| GET | `/evolution/ai-status` | ¿Está configurada la IA? (sin secretos) |
| GET | `/evolution/patients/{id}` | Estadísticas, gráficas e historial (`?desde=&hasta=`) |
| GET/POST | `/evolution/patients/{id}/analyses` | Resúmenes guardados / generar con Groq |
| GET | `/evolution/patients/{id}/analyses/{analysis_id}` | Un resumen guardado |
| GET | `/health` | Estado de la API y de PostgreSQL |

Valores permitidos:

- Citas `estado`: `pendiente`, `confirmada`, `completada`, `cancelada`.
- Síntomas `nivel_gravedad`: `bajo`, `moderado`, `grave`; `nivel_dolor` y
  `calidad_sueno` 0–10; `temperatura` 30–45 °C; `fecha_registro` opcional (nunca futura).
- Alertas `nivel`: `bajo`, `medio`, `alto`; `estado`: `pendiente`, `en_revision`,
  `atendida`, `descartada` (las dos últimas cierran la alerta).
- Medicamentos `hora` en formato `HH:MM`; `fecha_fin` ≥ `fecha_inicio`.

## Base de datos y migraciones

```sh
alembic upgrade head      # aplicar (idempotente; se puede ejecutar varias veces)
alembic current           # revisión aplicada
```

| Revisión | Cambios |
|---|---|
| `001_existing` | Crea las tablas originales que falten; no toca las existentes. |
| `002_evolution` | Tabla `evolution_analyses` (consentimiento, modelo, estado, resultado). |
| `003_indexes_period` | Índices por `patient_id`, índice único de asignaciones (se omite si ya hay duplicados, sin borrarlos) y columnas `period_start`, `period_end`, `error`. |

Reglas del proyecto:

- Las migraciones solo **agregan** (tablas, columnas anulables, índices).
  `downgrade` está bloqueado a propósito para no perder datos.
- Railway ejecuta `alembic upgrade head` como `preDeployCommand` antes de cada despliegue.
- Las fechas/horas se guardan en UTC (`timestamptz`). La zona de los
  cuidadores (`APP_TIMEZONE`) solo se usa para calcular días de calendario.
- Pacientes, medicamentos, síntomas, notas y alertas se **desactivan** en lugar
  de borrarse, para que el historial y la evolución sigan completos.

## Integración con Groq

Archivo: `app/services/groq_analysis.py`. Modelo: `openai/gpt-oss-20b`.

Recorrido real:

1. El cuidador elige un paciente y un período en **Evolución**.
2. La API consulta PostgreSQL (síntomas, medicamentos, citas, notas y alertas del período).
3. `app/services/evolution.py` calcula estadísticas y redacta **hechos verificados**
   (frases cortas con conteos y promedios). No incluye nombres, documentos,
   fechas exactas, textos de notas ni observaciones; las categorías libres
   que no son conocidas se cuentan como “otro”.
4. El cuidador marca la casilla de consentimiento. El backend exige
   `consentimiento: true` y `version_consentimiento: "groq-minimized-v1"`
   (validado en Pydantic, no solo en Angular).
5. Se registra el intento en `evolution_analyses` (estado `pending`) y se aplica
   el límite por minuto con un bloqueo de fila en PostgreSQL.
6. Se llama a `https://api.groq.com/openai/v1/chat/completions` con salida
   estructurada estricta (`json_schema`, `strict: true`): Groq solo puede
   devolver **identificadores** de hechos. Si Groq rechaza el modo estricto, se
   reintenta una vez en modo flexible.
7. El servidor valida el JSON con Pydantic (`extra="forbid"`) y que cada
   identificador exista; si algo no cuadra, el intento queda `failed` y no se muestra nada.
8. Se guarda el resultado (`completed`) con fecha, período, modelo y versión del consentimiento.
9. El frontend muestra el resultado guardado y el historial desde `GET .../analyses`.

Errores (nunca se reenvía el cuerpo de Groq ni la clave):

| Caso | Respuesta |
|---|---|
| Sin `GROQ_API_KEY`/`GROQ_MODEL` | `503` “El análisis IA no está configurado” |
| Menos de dos mediciones de un indicador | `422` |
| Límite propio por minuto | `429` + `Retry-After: 60` |
| Límite de Groq | `429` + `Retry-After` de Groq (máx. 300 s) |
| Clave inválida / modelo inexistente | `503` con mensaje accionable |
| Tiempo agotado | `504` |
| Respuesta inválida o error del proveedor | `502` |

Comprobar la configuración sin exponer secretos: `GET /evolution/ai-status`.

## Módulo de evolución

`GET /evolution/patients/{id}?desde=AAAA-MM-DD&hasta=AAAA-MM-DD` devuelve:

- `totales`: registros por tipo en el período.
- `metricas`: para dolor, sueño y temperatura — cantidad, promedio, primera y
  última medición, diferencia y `puntos` (solo mediciones reales, en orden cronológico).
- `categorias`: conteos de gravedad, apetito y ánimo.
- `historial`: línea de tiempo (síntomas, notas, alertas, citas por fecha
  programada y medicamentos por fecha de inicio), de la más reciente a la más antigua.
- `datos_suficientes`: hay al menos dos mediciones de un mismo indicador.
- `zona_horaria`: zona usada para los límites del período.

Decisiones:

- Los días del filtro son días del calendario del cuidador (`APP_TIMEZONE`):
  un registro a las 21:00 en Bogotá pertenece a ese día aunque en UTC ya sea el siguiente.
- No se interpolan mediciones faltantes; las gráficas espacian los puntos según el tiempo real.
- La diferencia entre la primera y la última medición se presenta como tal,
  nunca como “tendencia clínica”.
- Máximo 2000 registros por tipo y período; si se supera, la API pide un período más corto.

## Pruebas

```sh
pip install -r requirements-dev.txt
python -m pytest -q                                   # SQLite en memoria
TEST_DATABASE_URL=postgresql+psycopg://USER@127.0.0.1:5432/careguardian_test \
  python -m pytest -q                                 # PostgreSQL local desechable
```

- `TEST_DATABASE_URL` debe ser local y contener “test” en el nombre; la suite se niega a usar otra base.
- Groq siempre se simula con `unittest.mock`: no se necesita ni se usa una clave real.
- Cobertura: autenticación, permisos (matriz por recurso), pacientes y equipo,
  medicamentos, citas, síntomas, notas, alertas, panel, evolución (zonas horarias,
  límites, categorías), Groq (éxito, minimización, cuotas, errores, reintento),
  migraciones sobre un esquema heredado en PostgreSQL, persistencia tras abrir
  un motor nuevo y la carga de demostración.
- GitHub Actions (`.github/workflows/tests.yml`) ejecuta migraciones dos veces y la suite en PostgreSQL 16.

## Despliegue en Railway

El servicio se construye con el `Dockerfile` (usuario sin privilegios, `uvicorn`
con `--proxy-headers`). `railway.toml` define:

- `preDeployCommand = alembic upgrade head` (migraciones aditivas).
- `healthcheckPath = /health` (falla con 503 si PostgreSQL no responde).

Pasos:

1. En el proyecto de Railway, el servicio PostgreSQL debe mantener su **volumen
   persistente** (no lo elimines ni lo recrees).
2. En el servicio del backend, variables:
   - `DATABASE_URL` = referencia `${{Postgres.DATABASE_URL}}`
   - `SECRET_KEY` = valor aleatorio de 48+ caracteres. La API **se niega a
     arrancar** con el valor que quedó publicado en el historial del repositorio
     (`careguardian_super_secret_key_2026`); si Railway lo usa, cámbialo antes de
     desplegar (las sesiones abiertas se cerrarán, es lo esperado).
   - `CORS_ORIGINS` = URL pública del frontend
   - `GROQ_API_KEY`, `GROQ_MODEL=openai/gpt-oss-20b`
   - opcionales: `GROQ_TIMEOUT_SECONDS`, `GROQ_REQUESTS_PER_MINUTE`, `APP_TIMEZONE`
3. Despliega la rama (o fusiona el PR en `main`). Railway construirá la imagen,
   ejecutará las migraciones y comprobará `/health`.
4. Verifica: `GET https://<backend>/health` y, con sesión, `GET /evolution/ai-status`.
5. En el frontend, `API_BASE_URL` debe apuntar a la URL del backend (privada
   `http://<servicio>.railway.internal:<puerto>` o pública `https://...`).

## Carga segura de datos de demostración

Script: `python -m scripts.seed_demo`. Usa **solo la API HTTP** (los mismos
endpoints autenticados que el frontend); nunca abre la base de datos ni ejecuta SQL.

Qué crea por defecto (todo ficticio y marcado “(demo)” + un marcador `CG-DEMO-…`):

| Recurso | Cantidad | Detalle |
|---|---|---|
| Pacientes | 6 | Asignados automáticamente a la cuenta que ejecuta la carga |
| Medicamentos | 18 | Suplementos genéricos “(demo)”, sin indicación clínica |
| Citas | 12 | Próximas, en una sede ficticia |
| Síntomas | 84 | 14 por paciente, repartidos en las últimas 4 semanas |
| Notas | 24 | Observaciones cotidianas ficticias |
| Alertas manuales | 6 | Niveles bajo/medio |

Algunas notas pueden generar alertas automáticas (por ejemplo “durmió poco”),
igual que en el uso real.

```sh
# 1) Vista previa: no se conecta a nada
python -m scripts.seed_demo

# 2) Local
export SEED_BASE_URL=http://127.0.0.1:8000
export SEED_EMAIL=carlos@careguardian.com
export SEED_PASSWORD=CareGuardian123
python -m scripts.seed_demo --apply --create-account

# 3) Producción (solo con autorización explícita, revisando antes el destino)
export SEED_BASE_URL=https://<backend>.up.railway.app
python -m scripts.seed_demo --apply --create-account --confirm-production
```

- Idempotente: reejecutar con el mismo `--namespace` (por defecto `carlos-demo-v1`)
  reconcilia los registros existentes y no duplica nada.
- No borra, modifica ni desactiva datos existentes; solo hace `GET` y `POST`.
- `--create-account` registra la cuenta mediante `POST /users/` únicamente si el
  inicio de sesión falla con 401; si el correo existe con otra contraseña, se detiene.
- Tras la carga relee cada registro mediante una nueva consulta HTTP.
- Como los datos se guardan a través de la API desplegada, quedan en el
  PostgreSQL persistente de Railway y siguen ahí después de reiniciar el backend.

Más detalle en [`docs/CARGA_DEMO.md`](docs/CARGA_DEMO.md).

## Seguridad

- Contraseñas con Argon2; mismo coste de verificación para correos inexistentes.
- Límite de intentos fallidos de inicio de sesión (`429` + `Retry-After`).
- Cambiar la contraseña invalida todos los tokens emitidos antes.
- JWT HS256 con `exp`, `iat` y `sub` obligatorios.
- Permisos por paciente en todas las rutas (dependencia global + comprobación explícita).
- Errores de base de datos traducidos a `409`/`503` sin SQL ni datos.
- Cabeceras `Cache-Control: private, no-store` y `X-Content-Type-Options: nosniff`.
- Logs sin cuerpos de Groq, tokens, ni URLs de peticiones salientes.
- `.env` está ignorado. **Importante:** el historial antiguo del repositorio
  contiene un `.env` con un `SECRET_KEY` y una contraseña de base de datos de
  desarrollo. Si alguno de esos valores se usó en Railway, rótalo.
- La cuenta de demostración es pública por diseño: úsala solo con datos ficticios.
