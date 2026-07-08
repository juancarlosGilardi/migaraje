# MiGaraje

La bitácora inteligente de tu auto: mantenimiento por marca/modelo, kilometraje, facturas
(PDF y XML SUNAT) y papeles del auto y del conductor (SOAT, revisión técnica, impuesto
vehicular y brevete), con reglas peruanas nativas.

**Mockup / pitch:** https://juancarlosgilardi.github.io/migaraje/
**App en producción:** https://migaraje.192.64.87.241.nip.io

## Stack

- **Frontend** (`frontend/`): React 18 + Vite + TypeScript + Tailwind 4 + PWA (vite-plugin-pwa)
- **Backend** (`backend/`): FastAPI + SQLAlchemy 2 + Alembic
  - Desarrollo local: SQLite
  - Producción: MySQL 8 (VPS propio)

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

## Producción (VPS)

Desplegado en `/opt/migaraje` (backend, systemd `migaraje-api.service`, puerto interno 8103)
y `/var/www/migaraje` (frontend estático), servidos por nginx con SSL (Let's Encrypt) en el
dominio `migaraje.192.64.87.241.nip.io` (nip.io resuelve automáticamente al VPS, sin DNS propio).

### Actualizar el backend tras un cambio

```bash
ssh vps-facturape
cd /opt/migaraje
git pull origin master
cd backend
venv/bin/pip install -r requirements.txt
venv/bin/alembic upgrade head
systemctl restart migaraje-api
```

### Actualizar el frontend tras un cambio

```bash
# En la laptop
cd frontend
npm run build
scp -r dist/* vps-facturape:/var/www/migaraje/
```
