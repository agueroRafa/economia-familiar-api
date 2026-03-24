# Economia Familiar by AguerattiSoft

API REST para gestionar economia familiar:

- Login y registro de usuarios
- Gastos mensuales
- Deudas
- Ingresos (incluyendo comisiones)
- Eventos y compromisos
- Asignacion de items a cada usuario
- Carga de fotos/tickets/comprobantes
- Dashboard con balance general

## Requisitos

- Python 3.10+

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion

```bash
uvicorn app.main:app --reload
```

Swagger:

- http://127.0.0.1:8000/docs

## Frontend rapido (sin dependencias)

Se incluye un frontend funcional en `web/` pensado para usar hoy mismo sin instalar Node.

### Opcion 1: abrir directo

Abrir `web/index.html` en el navegador.

### Opcion 2: servirlo local con Python

```bash
python -m http.server 5500 -d web
```

Luego abrir:

- http://127.0.0.1:5500

### Configuracion frontend

1. En la UI, colocar `Base URL API` (por ejemplo `http://127.0.0.1:8000`).
2. Registrar ambos usuarios.
3. Hacer login y operar gastos/deudas/ingresos/eventos/adjuntos.

### Deploy rapido del frontend

Como es estatico, se puede subir la carpeta `web/` a:

- Netlify (drag & drop)
- Vercel (Static)
- GitHub Pages

## Flujo recomendado

1. Registrar 2 usuarios (`/auth/register`), uno para cada uno.
2. Iniciar sesion con `/auth/login`.
3. Copiar el `access_token` y usarlo como `Bearer Token` en Swagger.
4. Crear gastos, deudas, ingresos y eventos.
5. Subir tickets/fotos en endpoints de attachments.
6. Consultar resumen en `/dashboard`.

## Endpoints principales

- `POST /auth/register`
- `POST /auth/login`
- `GET /users/me`
- `POST/GET/DELETE /expenses`
- `POST/GET/DELETE /debts`
- `POST/GET/DELETE /incomes`
- `POST/GET/DELETE /events`
- `POST /expenses/{id}/attachments`
- `POST /debts/{id}/attachments`
- `POST /incomes/{id}/attachments`
- `GET /attachments`
- `GET /dashboard`

## Notas

- La base de datos SQLite se crea automaticamente como `economia_familiar.db`.
- Los archivos se guardan en `uploads/`.
- Para produccion, cambia `SECRET_KEY` en `app/auth.py` y restringe CORS.

## Deploy hoy mismo (rapido)

### 1) Backend en Render (Docker)

1. Subi esta carpeta a un repo en GitHub.
2. En Render: **New +** -> **Web Service** -> conectar repo.
3. Elegi `Docker` (usa `Dockerfile` del proyecto).
4. Deploy.
5. Vas a obtener una URL tipo:
   - `https://economia-familiar-api.onrender.com`

Prueba:
- `https://TU-URL/docs`

### 2) Frontend en Netlify

1. Entrar a Netlify -> **Add new site** -> **Deploy manually**.
2. Arrastrar la carpeta `web/`.
3. Abrir la URL que te da Netlify.
4. En la app, en `Base URL API`, poner la URL del backend de Render.

Con esto ya queda funcionando online para ambos celulares.

---

## APK Android (WebView) para ambos telefonos

Se incluye un proyecto Android en:

- `android-app/`

### Paso a paso

1. Abrir Android Studio.
2. `Open` -> seleccionar carpeta `android-app`.
3. Esperar `Gradle Sync`.
4. Editar archivo:
   - `android-app/app/src/main/java/com/aguerattisoft/economiafamiliar/MainActivity.java`
   - Reemplazar `APP_URL` por la URL del frontend (Netlify).
5. Build:
   - `Build` -> `Build Bundle(s) / APK(s)` -> `Build APK(s)`.
6. Ubicacion del APK:
   - `android-app/app/build/outputs/apk/debug/app-debug.apk`

### Instalar en los dos telefonos

1. Pasar el APK por WhatsApp/Drive/Telegram o cable.
2. En cada Android: permitir "Instalar apps desconocidas".
3. Instalar el APK.

---

## Recomendacion para produccion real

- Migrar de SQLite a PostgreSQL (Render lo soporta).
- Guardar adjuntos en storage externo (S3/Cloudinary) en vez de disco local.
- Agregar recuperacion de password y notificaciones push.
