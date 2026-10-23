.PHONY: install test run worker web build

install:
	python3.12 -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt

test:
	.venv/bin/python -m pytest -q

run:
	cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000

worker:
	cd backend && ../.venv/bin/python -m app.worker

web:
	cd frontend && npm install && npm run dev

build:
	cd frontend && npm run build
