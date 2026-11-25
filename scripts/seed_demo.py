"""Run with python -m scripts.seed_demo. Defaults to an offline dry run."""
import argparse
import json
import os
import sys
from .seed_http import SeedClient, SeedError, validate_url
from .seed_payloads import DEFAULT_COUNTS, validate_namespace
from .seed_runner import run_seed, validate_counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Crear registros mediante la API")
    parser.add_argument("--confirm-production", action="store_true", help="Autorizar escrituras en un servidor no local")
    parser.add_argument("--namespace", default="carlos-demo-v1")
    parser.add_argument("--create-account", action="store_true",
                        help="Registrar SEED_EMAIL mediante POST /users/ si todavía no existe")
    parser.add_argument("--account-name", default="Carlos (cuenta demo)")
    for key, default in DEFAULT_COUNTS.items():
        parser.add_argument("--" + key, type=int, default=default)
    args = parser.parse_args(argv)
    counts = {key: getattr(args, key) for key in DEFAULT_COUNTS}
    client = None
    try:
        validate_counts(counts)
        validate_namespace(args.namespace)
        if not args.apply:
            print(json.dumps({"mode": "dry-run", "counts": counts,
                              "assignments": counts["patients"]}, ensure_ascii=False))
            return 0
        url = os.getenv("SEED_BASE_URL", "")
        local = validate_url(url)
        if not local and not args.confirm_production:
            raise SeedError("El servidor no es local; revisa el destino y usa --confirm-production")
        client = SeedClient(url, os.getenv("SEED_EMAIL", ""), os.getenv("SEED_PASSWORD", ""))
        account = client.ensure_account(args.account_name) if args.create_account else "existing"
        result = run_seed(client, counts, args.namespace)
        result["account"] = account
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (SeedError, ValueError) as error:
        print(f"Carga detenida: {error}", file=sys.stderr)
        return 1
    except Exception:
        # Never print library errors that may contain request credentials.
        print("Carga detenida por un error inesperado; verifica los registros remotos antes de reintentar.", file=sys.stderr)
        return 1
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
