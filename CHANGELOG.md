# Cambios

## 1.1.0 — 2026-11-25

### Agregado
- `GET /auth/me`, `PUT /users/{id}/password`, `GET /dashboard/summary`,
  `GET /evolution/ai-status`, `GET /evolution/patients/{id}/analyses/{analysis_id}`.
- Asignación y desasignación de cuidadores por correo.
- `fecha_registro` opcional en síntomas y notas; `edad` en pacientes; `vigente` en medicamentos;
  autor de notas y síntomas.
- Migración `003_indexes_period` (índices, unicidad de asignaciones, período de los análisis).
- Límite de intentos de inicio de sesión, `X-Request-ID`, manejador genérico de errores.

### Cambiado
- `DELETE` de pacientes y medicamentos desactiva en lugar de borrar.
- Los `POST` de creación responden `201`.
- Períodos de Evolución y “hoy” calculados en `APP_TIMEZONE`.
- Errores de Groq clasificados con precisión (`429`, `503`, `504`, `502`).

### Corregido
- Alertas falsas por menciones negadas en notas.
- `500` por correos o documentos duplicados.
- Alertas automáticas guardadas fuera de la transacción del registro.

### Seguridad
- La API no arranca con el `SECRET_KEY` publicado en el historial ni con `CORS_ORIGINS=*`.
- Cambiar la contraseña revoca los tokens anteriores.
