# Carga HTTP de demostración

No se reconstruye CareGuardian, no se insertan usuarios ni se ejecuta SQL.
El script reutiliza los esquemas y rutas existentes. No usa Groq.

## Vista previa sin conexión

Desde la raíz del backend, con sus dependencias instaladas:

```sh
python -m scripts.seed_demo
```

Predeterminados: 10 pacientes y sus asignaciones automáticas al creador,
20 medicamentos, 20 citas, 30 síntomas, 20 notas y 30 alertas manuales.
Los registros se distribuyen entre los pacientes. Son datos ficticios,
claramente identificados; los medicamentos no son prescripciones.

## Aplicar una carga

Configura `SEED_BASE_URL`, `SEED_EMAIL` y `SEED_PASSWORD` mediante el gestor
de secretos. Nunca publiques sus valores ni los pases en la línea de comandos.
La URL es la raíz real del backend, sin `/auth/login`, consulta ni credenciales.
La cuenta debe existir, estar activa y tener los permisos correspondientes.

```sh
python -m scripts.seed_demo --apply --confirm-production
```

`--confirm-production` autoriza escrituras fuera de localhost; revisa el
destino antes de usarlo. El comando predeterminado no escribe nada.
Para cambiar cantidades: `--patients 10 --medications 20 --appointments 20
--symptoms 30 --notes 20 --alerts 30`. Todas aceptan 0–1000. Una carga de
registros relacionados requiere pacientes.

Mantén `--namespace carlos-demo-v1` entre ejecuciones para reconciliar los
mismos registros mediante marcadores remotos. Cambiarlo crea otro conjunto.
Ejecuta una sola instancia a la vez: la API no tiene claves de idempotencia
ni restricciones únicas para todos los tipos de registros; no se promete
idempotencia ante escritores concurrentes. No borres, edites ni desactives
manualmente los marcadores si quieres reutilizarlos para reconciliación.

## Rutas y comprobaciones

- `POST /auth/login`: autenticación; renovación una vez si una operación devuelve 401.
- `GET/POST /patients/`: búsqueda por documento ficticio estable y creación.
- `GET /patients/{id}/caregivers`: comprueba la asignación automática.
- `GET/POST /medications/patients/{id}`: medicamentos.
- `GET/POST /appointments/patients/{id}`: citas.
- `GET/POST /symptoms/patients/{id}`: síntomas.
- `GET/POST /notes/patients/{id}`: notas.
- `GET/POST /alerts/patients/{id}`: alertas manuales.

Cada categoría informa `created`, `existing` y `verified`. La verificación
reconsulta la API y comprueba las relaciones, no se limita a creer el POST.
Un fallo detiene la carga con código distinto de cero; las operaciones
anteriores pueden haber quedado guardadas. No hay rollback ni borrados.
Un timeout en POST no se reintenta automáticamente: reejecuta el comando
con el mismo namespace para consultar primero lo que quedó guardado.
Los mensajes de error excluyen cuerpos de respuesta y credenciales.

La API puede generar alertas adicionales al crear síntomas o notas:
el conteo configurado de alertas corresponde solo a las manuales marcadas.
No se inventa una fecha histórica para síntomas o notas: sus endpoints
actuales asignan la fecha de registro en el servidor. Citas y medicamentos
sí admiten fechas programadas/de inicio.

## Verificación y límites

```sh
python -m pytest tests -q
```

Hay pruebas de esquemas, límites de fechas, normalización UTC, errores HTTP,
renovación de sesión, ejecución repetida e integración con rutas reales.
Las pruebas usan exclusivamente la base desechable configurada por la suite;
el cargador utiliza exclusivamente HTTP y no abre bases locales ni remotas.

Una relectura HTTP confirma que los registros son recuperables desde la API.
No demuestra por sí sola que el despliegue use PostgreSQL de Railway:
eso debe verificarse en la configuración y logs del despliegue autorizado,
sin mostrar `DATABASE_URL`. Esta entrega no ejecutó carga en producción,
no comprobó persistencia en Railway y no cambió despliegues ni migraciones.
La rama debe revisarse e integrarse antes de desplegar.
