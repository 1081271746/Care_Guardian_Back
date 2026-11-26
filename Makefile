# Atajos de desarrollo. Requieren el entorno virtual activo y un .env local.
.PHONY: install run migrate test test-pg coverage seed-preview

install:
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload --port 8000

migrate:
	alembic upgrade head

test:
	python -m pytest -q

# Requiere TEST_DATABASE_URL apuntando a una base local desechable con "test" en el nombre.
test-pg:
	@test -n "$$TEST_DATABASE_URL" || (echo "Define TEST_DATABASE_URL" && exit 1)
	python -m pytest -q

coverage:
	python -m pytest -q --cov=app --cov=scripts --cov-report=term-missing:skip-covered

seed-preview:
	python -m scripts.seed_demo
