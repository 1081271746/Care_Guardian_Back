# Auditoría del backend — noviembre de 2026

## Estado inicial (`main`)

- FastAPI + SQLAlchemy 2 + PostgreSQL + Alembic, con integración Groq ya
  declarada y 55 pruebas automatizadas que pasaban.
- Permisos por paciente aplicados con una dependencia global.
- Evolución y Groq funcionales en lo básico (consentimiento, minimización y
  validación de la respuesta ya existían).

## Problemas detectados y corrección

| # | Prioridad | Problema | Corrección |
|---|---|---|---|
| 1 | Alta | `DELETE /patients/{id}` borraba en cascada todo el historial clínico y los análisis IA. | Ahora desactiva al paciente; su historial queda en modo solo lectura. |
| 2 | Alta | Un `.env` con `SECRET_KEY` y contraseña de BD de desarrollo quedó en el historial de Git. | La API se niega a arrancar con ese `SECRET_KEY`; README pide rotarlo. |
| 3 | Alta | Los días de los filtros de Evolución se cortaban en UTC: registros nocturnos en Colombia cambiaban de día y las citas se mostraban 5 h antes. | `APP_TIMEZONE` (por defecto `America/Bogota`) o la zona del navegador. |
| 4 | Alta | “No tiene fiebre” o “sin dolor” en una nota generaban alertas. | Detección de negaciones en el análisis de notas. |
| 5 | Alta | Registro con correo repetido → error 500 de la base de datos. | `409` explícito; correos normalizados a minúsculas; login sin distinguir mayúsculas. |
| 6 | Media | Síntoma/nota y su alerta automática se guardaban en dos transacciones. | Una sola transacción. |
| 7 | Media | Alerta automática abierta no se actualizaba si una evaluación posterior era más grave. | Se escala el nivel (nunca se baja en silencio). |
| 8 | Media | Sin validación de texto vacío, formato `HH:MM`, rango de fechas, estados y niveles. | Tipos compartidos (`schemas/common.py`) y `Literal` para estados. |
| 9 | Media | Actualizaciones no permitían borrar campos opcionales y aceptaban `null` en obligatorios. | `exclude_unset` + comprobación de obligatorios. |
| 10 | Media | Errores de Groq mal clasificados (límite → 503, clave inválida → 502). | `429` con `Retry-After`, `503` para credencial/modelo, `504`, `502`; reintento único si Groq rechaza el modo estricto. |
| 11 | Media | Intentos de análisis podían quedar en `pending` ante errores inesperados. | Siempre se marcan `failed` con motivo seguro. |
| 12 | Media | Panel sin indicadores globales: solo existía el panel por paciente. | `GET /dashboard/summary` calculado en PostgreSQL. |
| 13 | Media | Sin índices en `patient_id` ni unicidad de asignaciones. | Migración 003 (aditiva e idempotente). |
| 14 | Media | Sin límite de intentos de inicio de sesión. | Límite por correo y por dirección (`429`). |
| 15 | Media | Los tokens seguían siendo válidos tras cambiar la contraseña (no existía el cambio). | `PUT /users/{id}/password` y revocación por huella del hash. |
| 16 | Baja | `datetime.utcnow` (obsoleto, sin zona) en los modelos. | `utc_now()` con zona. |
| 17 | Baja | Scripts sueltos `test_*.py` en la raíz usaban la base real. | Eliminados; cubiertos por pruebas con base desechable. |
| 18 | Baja | Sin `X-Request-ID`, sin manejador genérico de 500, sin `Referrer-Policy`/`X-Frame-Options`. | Agregados. |
| 19 | Baja | `DATABASE_URL` ausente producía una URL `None:None@None`. | Error claro al iniciar. |
| 20 | Baja | Carga de demostración: todos los síntomas con la fecha del momento de carga. | Fechas repartidas en 4 semanas con `fecha_registro` opcional (nunca futura). |

## Verificación

- 170 pruebas en PostgreSQL 16 local (168 + 2 exclusivas de PostgreSQL en SQLite), cobertura 94 %.
- `ruff check .` sin hallazgos.
- Migraciones aplicadas dos veces sobre una base vacía y sobre un esquema heredado con datos y asignaciones duplicadas (no se borra nada).
- Carga de demostración ejecutada contra un backend local: creación, segunda
  ejecución sin duplicados y lectura tras reiniciar el proceso.
- Groq: probado con respuestas simuladas (éxito, minimización, cuota, errores,
  reintento). **No se probó con una clave real** porque no había una disponible
  en este entorno; sin clave, la API responde `503` y no simula análisis.

## Pendiente de intervención manual

- Rotar `SECRET_KEY` en Railway si coincide con el valor publicado.
- Configurar `GROQ_API_KEY` y generar un análisis real desde Evolución para
  confirmar la conexión con la cuenta de Groq.
- Ejecutar la carga de demostración en producción solo tras revisar el destino.
