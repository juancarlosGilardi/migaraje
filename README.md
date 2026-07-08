# MiGaraje

La bitácora inteligente de tu auto: mantenimiento por marca/modelo, kilometraje, facturas
(PDF y XML SUNAT) y papeles del auto y del conductor (SOAT, revisión técnica, impuesto
vehicular y brevete), con reglas peruanas nativas.

**Mockup / pitch:** https://juancarlosgilardi.github.io/migaraje/

## Stack

- **Frontend** (`frontend/`): React 18 + Vite + TypeScript + Tailwind 4 + PWA (vite-plugin-pwa)
- **Backend** (`backend/`): FastAPI + SQLAlchemy 2 + Alembic (SQLite en dev, PostgreSQL en prod)

## Desarrollo local

```bash
# Backend (puerto 8000)
cd backend
py -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/uvicorn app.main:app --port 8000 --reload

# Frontend (puerto 5173)
cd frontend
npm install
npm run dev
```

Abrir http://localhost:5173 — la documentación de la API queda en http://localhost:8000/docs
