# MiGaraje — Documento de continuación

> Léeme primero si retomas este proyecto en una sesión nueva. Resume el estado exacto al 2026-07-08, la arquitectura, cómo desplegar, qué falta y los problemas del entorno ya resueltos (para no volver a perder tiempo en ellos).

**App en producción:** https://migaraje.192.64.87.241.nip.io
**Mockup / pitch del concurso:** https://juancarlosgilardi.github.io/migaraje/
**Repo:** https://github.com/juancarlosGilardi/migaraje (público)

---

## 1. Qué es esto

PWA de mantenimiento vehicular para el mercado peruano: garaje multi-auto, plan de mantenimiento por marca/modelo, historial de servicios con lectura automática de facturas XML SUNAT, y un módulo "Papeles" con las reglas peruanas de SOAT/revisión técnica/impuesto vehicular/brevete. Nace de un mockup presentado a un concurso; el roadmap del propio mockup ya está 100% implementado (ver sección 4 para lo que sigue quedando fuera).

## 2. Estado actual — todo lo construido

| Fase | Qué hace | Archivos clave |
|---|---|---|
| **F0** | Monorepo, FastAPI, React+Vite+TS+Tailwind4, PWA instalable | `backend/app/main.py`, `frontend/vite.config.ts` |
| **F1** | Registro/login JWT, garaje (CRUD vehículos), registro de kilometraje | `routers/auth.py`, `routers/vehicles.py`, `screens/Garage.tsx` |
| **F2** | Despliegue en **VPS propio** (no Netlify/Render/Neon — ver sección 3) | ver sección 5 |
| **F3** | Plan de mantenimiento + ficha técnica (aceite, llantas, batería) por marca/modelo | `services/plan_progress.py`, `seeds/templates.json`, `screens/VehicleDetail.tsx` |
| **F4** | Historial de servicios + subida de facturas PDF/XML + parser UBL 2.1 SUNAT | `services/sunat_parser.py`, `routers/services.py`, `screens/History.tsx`, `screens/UploadInvoice.tsx` |
| **F5** | Papeles: SOAT, revisión técnica (CITV), impuesto vehicular, brevete, con reglas peruanas verificadas | `services/peru_rules.py`, `routers/drivers.py`, `routers/documents.py`, `screens/Papeles.tsx` |
| **F6** | Recordatorio de km anti-spam + alertas consolidadas + caché offline real | `services/reminders.py`, `services/alerts.py`, `routers/alerts.py`, `components/AlertsBanner.tsx`, `components/OfflineBanner.tsx` |
| **Catálogo marcas/modelos** | BD propia (383 marcas, 5,365 modelos) importada de NHTSA + agregados curados para Perú (Hilux, Creta, etc.) | `services/vehicle_catalog.py`, `seeds/import_vehicle_catalog.py`, `seeds/catalog_additions.json`, `components/Combobox.tsx` |
| **Catálogo de componentes** | 23 componentes mantenibles con intervalos reales (feedback de un contacto de talleres de Lima) | `seeds/maintenance_components.py`, endpoint `GET /api/catalog/components` |

**Tests: 80/80 pasando** (`cd backend && .venv/Scripts/python.exe -m pytest tests/ -q`).

Migraciones de Alembic en orden (todas aplicadas en producción):
```
6c1007562d69  initial tables: users, vehicles, odometer_logs
361154c5d5a0  add plan_items and vehicle spec_json
fe2184c9d622  add service_records and service_files
8b19094b857b  add catalog_makes and catalog_models
aacbed75e3de  add drivers and legal_documents (papeles)
19f5ee674319  add maintenance_components catalog  ← head
```

## 3. Arquitectura

- **Backend**: FastAPI + SQLAlchemy 2 (estilo `Mapped`/`mapped_column`) + Alembic + PyJWT + bcrypt + lxml (parser XML) + httpx (llamadas externas). SQLite en desarrollo local, **MySQL en producción** (driver `pymysql`).
- **Frontend**: React 18 + Vite + TypeScript + Tailwind 4 (tokens en `frontend/src/index.css` con `@theme`, ej. `--color-cyan`, `--color-card`) + TanStack Query + React Router + `vite-plugin-pwa`.
- **Despliegue**: **NO usa Netlify/Render/Neon** — se abandonó esa vía por fricción (ver memoria de Claude si quieres el detalle). Todo corre en un VPS propio compartido con otros proyectos del usuario:
  - Alias SSH ya configurado en la laptop de desarrollo: `ssh vps-facturape`
  - Backend: `/opt/migaraje/backend` (venv propio), servicio **systemd** `migaraje-api`, escucha en `127.0.0.1:8103`
  - Frontend: build estático en `/var/www/migaraje`, servido por **nginx**
  - Dominio: `migaraje.192.64.87.241.nip.io` (servicio **nip.io** — wildcard DNS gratis que resuelve `algo.<IP>.nip.io` a esa IP, sin necesidad de comprar dominio ni crear cuenta)
  - SSL: certbot / Let's Encrypt, renovación automática
  - Base de datos: MySQL 8 compartido del VPS, con BD y usuario propios (`migaraje` / `migaraje_user`)
  - El `.env` de producción vive **solo en el VPS** (`/opt/migaraje/backend/.env`, no versionado) con `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`

## 4. Qué falta — priorizado

### A. Brechas reales entre el mockup (demo del concurso) y la app construida
El roadmap "semanas 1-4" del mockup está 100% cumplido, pero dos cosas que se **mostraron en la animación de la demo** nunca se construyeron (el propio mockup ya las marcaba como "v1.1", no MVP, pero si el jurado prueba la app real notará la diferencia):

1. **Kilometraje por foto (OCR)** — hoy solo hay entrada manual de km. Para implementarlo bien: NO usar Tesseract (lee mal los 7-segmentos de pantallas digitales y los rodillos análogos a medio girar); usar un modelo de visión (ej. la API de Claude con salida estructurada) que reciba la foto y devuelva el número con nivel de confianza, y el usuario siempre confirma antes de guardar.
2. **SOAT/CITV desde XML/boleta** — hoy `PUT /api/vehicles/{id}/documents/{soat|citv}` solo acepta fecha manual. El parser de facturas (`sunat_parser.py`, ya funcional para servicios de mantenimiento) podría extenderse para reconocer pólizas de seguro/certificados de inspección y autocompletar la fecha de vencimiento.

### B. Post-MVP ya anotado en el roadmap del mockup (nunca prometido, pero valioso)
3. Web Push real (hoy los "recordatorios" son banners in-app en `AlertsBanner.tsx`, no notificaciones push del sistema operativo)
4. Dashboard de gastos por auto y por año
5. Exportar historial a PDF (para reventa del auto)
6. Papeletas por placa + récord del conductor (SAT/MTC)
7. Recalls de INDECOPI según marca/modelo
8. Revisión anual del kit GNV/GLP (autos a gas)

### C. Ideas nuevas de la investigación de la API NHTSA (no estaban en el mockup original)
Investigado y confirmado con datos reales, nada implementado aún:
- **Decodificación de VIN** (`vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{VIN}`): autocompletar marca/modelo/año/motor a partir del número de chasis al agregar un auto. Limitación: como NHTSA es una base de EE.UU., decodifica mal VINs de autos fabricados solo para otros mercados (ej. Hilux).
- **Recalls y quejas de NHTSA** (`api.nhtsa.gov/recalls/recallsByVehicle`, `/complaints/complaintsByVehicle`): dato complementario a los recalls de INDECOPI (punto B.7), solo cubre modelos compartidos con el mercado de EE.UU.

### D. Feedback de talleres — pendiente de especificar
Un contacto del usuario quiere promocionar la app en talleres de mecánica de Lima. Ya se atendió su primer feedback (catálogo de 23 componentes mantenibles, punto ya resuelto). **Falta preguntarle específicamente** qué necesitaría un taller para adoptar la app — ideas no confirmadas a explorar en la próxima conversación con él:
- ¿El taller necesita una cuenta/vista propia para registrar el servicio que le hizo a un cliente directamente (en vez de que el dueño del auto suba la factura)?
- ¿Le sirve que la app le sugiera repuestos/servicios pendientes cuando un cliente llega (a partir del plan de mantenimiento)?
- ¿Necesita reportes o algo exportable para su propio negocio?

**No implementar nada de esto sin antes confirmar con el usuario** qué le respondió el contacto — es una decisión de producto, no técnica.

## 5. Cómo desplegar (comandos exactos, reutilizables)

Patrón usado en cada fase — backend primero, frontend después:

```bash
# 1. Commit y push
cd "C:\Users\juanc\Claude Proyectos\Automóviles"
git add -A && git commit -m "..." && git push origin master

# 2. Backend: pull + instalar deps + migrar + reiniciar
ssh vps-facturape "cd /opt/migaraje && git pull origin master"
ssh vps-facturape "cd /opt/migaraje/backend && venv/bin/pip install -r requirements.txt && venv/bin/alembic upgrade head"
ssh vps-facturape "systemctl restart migaraje-api && sleep 2 && curl -s http://127.0.0.1:8103/api/health"

# 3. Frontend: build con la URL de producción (.env.production) + subir
cd frontend
npm run build
scp -r dist/* vps-facturape:/var/www/migaraje/
```

**Antes de generar una migración nueva**, confirma que no exista `backend/.env` local apuntando a otra base (residuo de pruebas viejas) — si lo hay, Alembic comparará contra esa BD en vez de SQLite y puede meter sintaxis no portable (`now()` de Postgres en vez de `CURRENT_TIMESTAMP`). Revisa siempre el archivo de migración generado antes de aplicarlo.

**Datos que solo existen en Python, no en Alembic** (como el catálogo de 23 componentes o el de marcas/modelos): si necesitas re-sembrarlos en producción sin recrear la tabla, hazlo con un script que importe desde el módulo compartido (`app/seeds/maintenance_components.py`, `app/seeds/import_vehicle_catalog.py`), corrido en el VPS vía SSH.

## 6. Verificación local antes de desplegar

```bash
# Backend
cd backend
.venv/Scripts/python.exe -m pytest tests/ -q   # deben pasar 80/80 (o más, si agregaste)

# Frontend
cd frontend
npx tsc --noEmit    # chequeo de tipos, debe salir sin output
npm run build        # build de producción
```

Para probar la UI real en el navegador contra el backend de **producción** desde el entorno local (útil para verificar features que dependen de servicios externos, ver gotcha #3 abajo):
1. `npm run preview` sirve el build de `dist/` con el service worker real en `http://localhost:4173` (dev normal con `npm run dev` NO genera el service worker)
2. Agrega temporalmente `http://localhost:4173` a `CORS_ORIGINS` en `/opt/migaraje/backend/.env` del VPS y reinicia el servicio
3. Prueba con Claude Preview (`mcp__Claude_Preview__*`)
4. **Revierte el CORS_ORIGINS** a solo el dominio de producción antes de terminar

## 7. Gotchas del entorno de desarrollo (ya resueltos una vez, no perder tiempo de nuevo)

1. **curl con tildes en `-d '...'` da 400 "error parsing the body"** — no es bug del backend, es la codificación de la terminal de Windows/Git Bash corrompiendo el texto al pasarlo. Solución: generar el JSON con Python (`encoding='utf-8'`) a un archivo en el scratchpad y usar `curl --data-binary @archivo.json`.
2. **`python -m json.tool` sobre un pipe de curl muestra texto con tildes mal codificadas** (mojibake tipo `sintÃ©tico`) — tampoco es un bug real, es el codepage de la consola. Verificar guardando la respuesta a un archivo y leyendo los bytes crudos si hay duda.
3. **Python/httpx en esta laptop no puede verificar certificados SSL de servicios externos** (`CERTIFICATE_VERIFY_FAILED` incluso con `certifi` actualizado) — parece inspección TLS de la red/antivirus local. El **VPS (Linux) no tiene este problema**. Cualquier feature que llame una API externa (como NHTSA) debe probarse ejecutando el código en el VPS, no en local.
4. **`curl` a HTTPS externo desde Windows a veces falla con error de revocación de certificado** — usar `curl --ssl-no-revoke`.
5. **`uvicorn --reload` deja procesos zombis** en el puerto 8000 de sesiones anteriores, que no se actualizan con el código nuevo aunque parezca que reiniciaste. Si un endpoint nuevo da 404 inesperado: `Get-NetTCPConnection -LocalPort 8000` (PowerShell) para ver qué proceso tiene el puerto de verdad, matar TODOS los `python`/`uvicorn` con `Get-Process python,uvicorn | Stop-Process -Force`, y arrancar limpio.
6. **Claude Preview: `preview_resize` con `preset: "desktop"` puede dejar el viewport en 0x0** en este entorno, causando bounding boxes falsos (ancho 0, posiciones negativas) que parecen bugs de layout pero no lo son. Usar `width`/`height` explícitos en vez del preset.
7. **`JSON.stringify(el.getBoundingClientRect())` da `{}` vacío** (quirk de serialización de `DOMRect` — sus propiedades son accessors en el prototipo, no propias). Extraer manualmente: `{x: r.x, y: r.y, width: r.width, height: r.height}`.
8. **`preview_screenshot` a veces da timeout** sin motivo aparente — usar `preview_snapshot` (árbol de accesibilidad) en su lugar, es más confiable en este entorno.
9. **El service worker de la PWA puede dejar a un usuario "atascado" en una versión vieja** tras un deploy — ya arreglado (`main.tsx` usa `virtual:pwa-register` con `registerSW({immediate:true})`, que se autoactualiza y recarga solo). Si el usuario reporta que no ve cambios nuevos después de un deploy, dile que borre los datos del sitio en su navegador una vez (instrucciones ya dadas: Chrome → ícono de candado → Configuración del sitio → Borrar y restablecer).

## 8. Convenciones del proyecto

- **Idioma**: identificadores y código en inglés, texto de UI y mensajes de error en español (tuteo neutro peruano, no rioplatense).
- **Backend**: patrón de ownership `_get_owned_vehicle(vehicle_id, user, db)` en cada router que toca recursos del usuario (ver `routers/vehicles.py`, replicado en `plan.py`, `documents.py`). Lógica de negocio pura (sin DB) en `services/` — ver `peru_rules.py`, `plan_progress.py`, `reminders.py` como referencia de estilo (funciones puras, testeables sin fixtures de BD).
- **Frontend**: pantallas en `screens/`, componentes reutilizables en `components/`. `Combobox.tsx` es el patrón para cualquier selector con búsqueda + texto libre (ya usado para marca/modelo de auto y componentes de mantenimiento) — reutilízalo antes de construir un selector nuevo.
- **Tests**: cada fase nueva necesita tests de la lógica pura (`services/`) y de los endpoints (ownership, casos válidos/inválidos, aislamiento entre usuarios). `tests/conftest.py` tiene los fixtures `client` y `auth_headers`; si agregas una tabla con datos semilla (como `maintenance_components`), el seed debe vivir en un módulo Python importable tanto por la migración de Alembic como por `conftest.py` (los tests no corren migraciones, solo `Base.metadata.create_all`).
- **Migraciones**: siempre revisar el `server_default` de columnas `created_at` autogenerado — debe ser portable entre SQLite/MySQL (`CURRENT_TIMESTAMP`, con o sin paréntesis, ambos funcionan), nunca sintaxis específica de un solo dialecto.
- **Commits**: mensaje descriptivo multilínea con viñetas resumiendo qué cambió en backend/frontend/tests, terminando con `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

## 9. Accesos (referencia, sin secretos)

- Repo GitHub: `juancarlosGilardi/migaraje` (público) — el usuario ya tiene sesión de `gh` autenticada en esta laptop.
- VPS: `ssh vps-facturape` ya configurado (clave en `~/.ssh/`), es un servidor **compartido con otros proyectos del usuario** — tener cuidado de no tocar nada fuera de `/opt/migaraje` y `/var/www/migaraje`, ni otros `sites-available`/servicios systemd.
- Usuario de prueba en producción: `juancarlos.gilardi@gmail.com` (contraseña conocida por el usuario, no se documenta aquí por ser un repo público).
- Variables sensibles (`DATABASE_URL`, `SECRET_KEY`, contraseña de MySQL) viven solo en `/opt/migaraje/backend/.env` en el VPS — nunca comitear ese archivo.
