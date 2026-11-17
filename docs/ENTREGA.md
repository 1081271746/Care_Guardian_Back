# Auditoría y entrega

## Estado de partida

Base: `main`, commit `39e77ffc51c25f87c54288e7213c04ca9d41d806`.
Solo existía `main`; no había pull requests abiertos ni cerrados al iniciar.
La copia clonada no tenía modificaciones pendientes.

Existían usuarios/login JWT, pacientes/asignaciones, síntomas, medicamentos,
citas, notas, alertas automáticas y manuales, análisis histórico por reglas y un
dashboard. Los scripts `test_*.py` originales imprimen simulaciones o consultan
una base configurada; no constituían una suite de aserciones aislada.

Faltaban evolución completa, servicio Groq, persistencia de resúmenes y
consentimientos, manifiesto de dependencias, migraciones y configuración Railway.
El frontend ya tenía ruta Evolución, pero solo mostraba “evolucion works!”.

## Cambios

- Se conserva el motor de reglas y el contrato de `/analysis/patients/{id}`.
- Nuevo servicio de agregación, cronología multiorigen y métricas verificables.
- Servicio independiente Groq por API oficial, timeout, esquema y validación.
- Persistencia de resúmenes, consentimiento y reservas de cuota en PostgreSQL.
- Dependencia común de autorización por objeto en los routers clínicos existentes:
  cierra accesos cruzados que antes permitían pacientes, medicamentos y citas.
- El listado de pacientes ahora solo muestra asignados. Creación con autoasignación.
- Usuarios: acceso autenticado a uno mismo, sin escalamiento de rol desde registro
  público ni desde actualización de perfil.
- CORS explícito, respuestas privadas `no-store`, health y cierre del engine.
- Docker, Railway, migraciones aditivas y ejemplos sin credenciales reales.

Mapa de archivos:

| Área | Archivos |
|---|---|
| Evolución | `app/routers/evolution.py`, `app/services/evolution.py`, `app/schemas/evolution.py` |
| Groq | `app/services/groq_analysis.py` |
| Persistencia | `app/models/evolution_analysis.py`, `migrations/`, `alembic.ini` |
| Seguridad/configuración | `app/core/access.py`, `app/core/dependencies.py`, `app/routers/patient.py`, `app/routers/user.py`, `app/main.py`, `app/database/connection.py` |
| Verificación | `tests/` |
| Despliegue/documentación | `Dockerfile`, `.dockerignore`, `railway.toml`, `.env.example`, `requirements*.txt`, `.gitignore`, `README.md`, este documento |

## Verificación y límites

Se ejecutaron 29 pruebas con SQLite y 29 con PostgreSQL 16 local UTF-8:
estadísticas reales de fixtures aislados, fechas inclusivas, datos vacíos, acceso
por asignación, consentimiento, clave ausente, respuestas de Groq válidas e
inválidas, fallos HTTP/conexión/timeout, cuota y conservación de migraciones.
Las llamadas a Groq se simulan; no se ha enviado información sanitaria a Groq.
Los datos de prueba no se usan para poblar la aplicación ni simular historiales.

Las advertencias de Pydantic Config heredado y `datetime.utcnow` corresponden a
modelos/esquemas anteriores; no se hizo una actualización masiva de esos archivos.

El historial contiene la eliminación de un `.env` que antes estuvo versionado.
No se recuperó ni se mostró su contenido. Las credenciales que hayan estado en ese
archivo deben considerarse expuestas y rotarse por sus proveedores, incluso si el
archivo ya no aparece en la rama actual. No se reescribe el historial Git.

Esta entrega prepara Railway, pero no acredita un despliegue de producción.
No se accedió ni se modificó una base de datos remota. La política de conservación,
los acuerdos de procesamiento y la autorización real deben configurarse antes
del uso con datos sensibles. La reserva de cuota se valida en PostgreSQL; SQLite
se utiliza solo para pruebas rápidas y no ofrece las mismas garantías de bloqueo.
