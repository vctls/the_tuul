.PHONY: dev install bump-version-minor bump-version-patch format-backend run-api test-api
dev:
	@set -e; \
	trap 'printf "\n↪ shutting down…\n"; kill 0' INT TERM; \
	npm run dev & \
	poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload & \
	wait || true

install:
	@set -e; \
	npm install; \
	poetry lock && poetry install

bump-version-minor:
	@set -e; \
	# Uses "version" command in package.json to bump python version
	npm version minor;

bump-version-patch:
	@set -e; \
	# Uses "version" command in package.json to bump python version
	npm version patch;

format-backend:
	@set -e; \
	poetry run black api/;

run-api:
	@set -e; \
	poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload;

test-api:
	@set -e; \
	poetry run python -c "from api.main import app; print('✅ FastAPI app loads successfully')";