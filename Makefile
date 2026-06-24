.PHONY: generate-api check-api test-frontend test-backend ci-frontend ci-backend

# Export OpenAPI spec from backend and generate frontend types
generate-api:
	cd backend && python -m scripts.export_openapi ../openapi.json
	cd frontend && npm run generate:api

# CI check: regenerate everything and fail if there's a diff
check-api:
	cd backend && python -m scripts.export_openapi ../openapi.json
	cd frontend && npm run generate:api
	git diff --exit-code openapi.json frontend/src/lib/api/schema.gen.ts

# Frontend commands
test-frontend:
	cd frontend && npm test

ci-frontend:
	cd frontend && npm run ci

# Backend commands
# 専用テスト DB (audienceroom_test) に対して Docker 経由で実行する。
# dev DB (audienceroom) を汚染せず、本番 DB にも向かない。詳細は README 12.6。
TEST_DB_URL = postgresql+psycopg://app:app@db:5432/audienceroom_test

test-backend:
	docker compose up -d db
	docker compose exec -T db sh -c "psql -U app -d audienceroom -tAc \"SELECT 1 FROM pg_database WHERE datname='audienceroom_test'\" | grep -q 1 || createdb -U app audienceroom_test"
	docker compose run --rm \
		-e APP_ENV=test \
		-e DATABASE_URL=$(TEST_DB_URL) \
		backend sh -c "pip install -q pytest pytest-asyncio && pytest"
