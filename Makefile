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
test-backend:
	cd backend && pytest
