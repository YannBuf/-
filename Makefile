.PHONY: setup dev backend frontend test lint clean

setup:
	docker compose up -d postgres redis
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker compose up

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

clean:
	docker compose down -v
	rm -rf backend/__pycache__ frontend/.next