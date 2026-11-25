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
