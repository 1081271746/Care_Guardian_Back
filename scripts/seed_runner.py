"""Reconcile remote demo markers; do not use local state as persistence."""
from .seed_http import SeedError
from .seed_payloads import DEFAULT_COUNTS, IDENTITY_FIELDS, patient_payload, resource_payload, validate_namespace


def validate_counts(counts):
    if set(counts) != set(DEFAULT_COUNTS):
        raise SeedError("Categorías de carga inválidas")
    if any(type(n) is not int or not 0 <= n <= 1000 for n in counts.values()):
        raise SeedError("Las cantidades deben ser enteros entre 0 y 1000")
    if not counts["patients"] and any(n for key, n in counts.items() if key != "patients"):
        raise SeedError("Se necesita al menos un paciente para crear registros relacionados")


def collection(value):
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise SeedError("La API no devolvió la colección esperada")
    return value


def unique_match(rows, field, value):
    found = [r for r in rows if r.get(field) == value]
    if len(found) > 1:
        raise SeedError("Hay marcadores duplicados; revisa la carga antes de continuar")
    return found[0] if found else None


def run_seed(client, counts, namespace="carlos-demo-v1", log=print):
    validate_counts(counts)
    validate_namespace(namespace)
    report = {key: {"created": 0, "existing": 0, "verified": 0} for key in counts}
    existing = collection(client.request("GET", "/patients/"))
    patients = []
    for index in range(counts["patients"]):
        payload = patient_payload(namespace, index)
        record = unique_match(existing, "documento", payload["documento"])
        if record and not record.get("activo", True):
            raise SeedError("Un paciente de demostración está inactivo; no se modificó")
        if record is None:
            record = client.request("POST", "/patients/", payload)
            report["patients"]["created"] += 1
        else:
            report["patients"]["existing"] += 1
        if not isinstance(record, dict) or not isinstance(record.get("id"), int):
            raise SeedError("La API no devolvió el identificador del paciente")
        patients.append(record)
    # Re-read patients in a new HTTP request; POST responses alone are not verification.
    saved = collection(client.request("GET", "/patients/"))
    for patient in patients:
        match = unique_match(saved, "documento", patient["documento"])
        if match is None or match.get("id") != patient["id"]:
            raise SeedError("No fue posible verificar el paciente creado")
        caregivers = collection(client.request("GET", f"/patients/{patient['id']}/caregivers"))
        if not caregivers:
            raise SeedError("El paciente no tiene cuidadores asignados")
        report["patients"]["verified"] += 1
    for resource, field in IDENTITY_FIELDS.items():
        for patient_index, patient in enumerate(patients):
            path = f"/{resource}/patients/{patient['id']}"
            rows = collection(client.request("GET", path))
            expected = []
            for index in range(patient_index, counts[resource], len(patients)):
                payload = resource_payload(namespace, resource, index)
                value = payload[field]
                expected.append(value)
                if unique_match(rows, field, value) is None:
                    record = client.request("POST", path, payload)
                    if not isinstance(record, dict) or record.get("patient_id") != patient["id"]:
                        raise SeedError("La respuesta no coincide con la relación esperada")
                    rows.append(record)
                    report[resource]["created"] += 1
                    log(f"{resource}: registro creado")
                else:
                    report[resource]["existing"] += 1
            saved = collection(client.request("GET", path))
            for value in expected:
                match = unique_match(saved, field, value)
                if match is None or match.get("patient_id") != patient["id"]:
                    raise SeedError("No fue posible verificar un registro mediante una nueva consulta")
                report[resource]["verified"] += 1
    report["assignments"] = {"verified": len(patients)}
    return report
