.PHONY: dev install bump-version-minor bump-version-patch format-backend
dev:
	@set -e; \
	trap 'printf "\n↪ shutting down…\n"; kill 0' INT TERM; \
	npm run dev & \
	(cd api && poetry run ./manage.py runserver) & \
	wait || true

install:
	@set -e; \
	npm install; \
	(cd api && poetry lock && poetry install)

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
	(cd api && poetry run black .);