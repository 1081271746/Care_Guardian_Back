"""Verify the configured Groq key and model end to end, without patient data.

Usage (locally or inside Railway with `railway run`):

    python -m scripts.check_groq

Sends two synthetic facts through the exact production code path
(`generate_analysis`) and prints only the outcome; never the key.
"""
import sys

from fastapi import HTTPException

from app.services.groq_analysis import generate_analysis

SYNTHETIC = {
    "periodo": {"desde": None, "hasta": None},
    "hechos": {
        "prueba_dolor": "Dolor (0–10): 2 mediciones; promedio 3; primera 2; última 4. (dato sintético)",
        "prueba_sueno": "Sueño (0–10): 2 mediciones; promedio 7; primera 7; última 7. (dato sintético)",
    },
}


def main() -> int:
    try:
        result = generate_analysis(SYNTHETIC)
    except HTTPException as error:
        print(f"Groq NO disponible: HTTP {error.status_code} · {error.detail}")
        return 1
    print("Groq respondió correctamente con salida validada:")
    for line in result["resumen"]:
        print(f"  - {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
