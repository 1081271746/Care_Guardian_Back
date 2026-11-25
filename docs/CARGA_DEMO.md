# Carga HTTP de demostración

No se reconstruye CareGuardian, no se insertan usuarios ni se ejecuta SQL.
El script reutiliza los esquemas y rutas existentes. No usa Groq.

## Vista previa sin conexión

Desde la raíz del backend, con sus dependencias instaladas:

```sh
python -m scripts.seed_demo
```

Predeterminados: 6 pacientes y sus asignaciones automáticas al creador,
18 medicamentos, 12 citas, 84 síntomas (14 por paciente), 24 notas y 6 alertas
manuales. Los registros se distribuyen entre los pacientes. Son datos ficticios,
etiquetados “(demo)” y con un marcador `CG-DEMO-…`; los medicamentos no son
prescripciones.

## Aplicar una carga

Configura `SEED_BASE_URL`, `SEED_EMAIL` y `SEED_PASSWORD` mediante el gestor
de secretos. Nunca publiques sus valores ni los pases en la línea de comandos.
La URL es la raíz real del backend, sin `/auth/login`, consulta ni credenciales.
La cuenta debe existir, estar activa y tener los permisos correspondientes.

```sh
python -m scripts.seed_demo --apply --confirm-production
```

Si la cuenta todavía no existe, agrega `--create-account` (y opcionalmente
`--account-name "Nombre visible"`): se registra con `POST /users/` solo cuando
el inicio de sesión responde 401. Nunca se cambia la contraseña de una cuenta existente.

`--confirm-production` autoriza escrituras fuera de localhost; revisa el
destino antes de usarlo. El comando predeterminado no escribe nada.
Para cambiar cantidades: `--patients 6 --medications 18 --appointments 12
--symptoms 84 --notes 24 --alerts 6`. Todas aceptan 0–1000. Una carga de
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
Síntomas y notas usan el campo opcional `fecha_registro` de la API para
repartirse en las últimas cuatro semanas (nunca en el futuro); así las gráficas
de Evolución tienen mediciones reales almacenadas. Citas y medicamentos usan
sus fechas programadas/de inicio.

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
sin mostrar `DATABASE_URL`. La carga se probó contra un backend local con
PostgreSQL (creación, reejecución sin duplicados y lectura tras reiniciar el
proceso); no se ejecutó contra producción.
