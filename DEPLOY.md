# Despliegue en la web (vos y tu esposa)

La app tiene **dos piezas** que se publican por separado:

| Pieza | Qué es | Dónde conviene alojarla |
|--------|--------|-------------------------|
| **Frontend** | Carpeta `web/` (HTML/CSS/JS, sin Node) | **Netlify** o **Cloudflare Pages** (gratis, HTTPS, fácil) |
| **Backend** | API FastAPI (`app/`) | **Render** (Docker ya incluido), **Railway**, **Fly.io**, etc. |

Ambos entran desde el navegador con una URL cada uno. La web llama a la API por HTTPS; por eso hay que configurar **CORS** en el backend con la URL exacta del frontend.

---

## 1. Backend en Render (recomendado con tu `Dockerfile`)

1. Subí el proyecto a **GitHub** (si aún no está).
2. En [Render](https://render.com): **New +** → **Web Service** → conectá el repo.
3. Configuración típica:
   - **Environment**: Docker (usa el `Dockerfile` de la raíz).
   - **Port**: Render inyecta `PORT`; el `Dockerfile` ya usa `uvicorn ... --port ${PORT}`.
4. **Variables de entorno** (Environment):

   | Variable | Valor |
   |----------|--------|
   | `SECRET_KEY` | Una cadena larga y aleatoria (no la compartas). Ej.: `openssl rand -hex 32` en tu PC. |
   | `CORS_ORIGINS` | La URL pública del frontend, **sin barra final**. Ej.: `https://TU-SITIO.netlify.app` |
   | `DATABASE_URL` | *(Opcional)* Por defecto usa SQLite en el disco del contenedor. Ver nota abajo. |
   | `UPLOADS_DIR` | *(Opcional)* Si usás disco persistente, por ej. `/data/uploads`. |

5. **Deploy**. Anotá la URL pública de la API, por ejemplo:  
   `https://economia-familiar-api.onrender.com`

### Nota sobre SQLite y adjuntos

En muchos planes gratuitos el **disco del contenedor no es permanente**: un reinicio o redeploy puede borrar `economia_familiar.db` y la carpeta `uploads`. Para uso real entre dos personas:

- **Opción A**: En Render, **Persistent Disk** montado (por ejemplo en `/data`) y entonces:
  - `DATABASE_URL=sqlite:////data/economia_familiar.db` (cuatro barras tras `sqlite:` en URLs absolutas)
  - `UPLOADS_DIR=/data/uploads`
- **Opción B**: Más adelante, migrar a **PostgreSQL** (Render ofrece DB gestionada) y almacenamiento de archivos en S3 u otro bucket.

El código ya lee `DATABASE_URL` y `UPLOADS_DIR` desde el entorno.

---

## 2. Frontend en Netlify

1. En [Netlify](https://netlify.com): **Add new site** → **Import an existing project** (GitHub) o **Deploy manually** (arrastrar carpeta).
2. Si usás Git: directorio de publicación **`web`**, o dejá el `netlify.toml` del repo (ya apunta `publish = "web"`).
3. Tras el deploy, obtenés una URL tipo `https://algo.netlify.app`.
4. Editá **`web/config.js`** en el repo y poné la URL del backend:

   ```javascript
   window.__API_BASE_URL__ = "https://TU-API.onrender.com";
   ```

   Volvé a desplegar el sitio (push o redeploy en Netlify).

5. En **Render**, actualizá `CORS_ORIGINS` con la URL exacta del sitio Netlify (incluido `https://`, sin `/` al final).

6. **Registro**: cada uno (vos y tu esposa) puede **Registrarse** con su email desde la misma web; comparten la misma base de datos y el mismo calendario/eventos según diseño actual de la API.

Si en el navegador quedó guardada una Base URL vieja en “Configuracion API”, borrá datos del sitio o usá ventana privada la primera vez.

---

## 3. Comprobar

- API: `https://TU-API.onrender.com/docs` (Swagger).
- Web: abrir Netlify, login, crear un evento y subir un adjunto.

---

## Alternativas rápidas

- **Frontend**: [Cloudflare Pages](https://pages.cloudflare.com/) (subir carpeta `web/` o conectar Git).
- **Backend**: [Railway](https://railway.app/) o [Fly.io](https://fly.io/) con el mismo `Dockerfile` y las mismas variables.

Si querés un solo dominio tipo `familia.com`, se puede poner el frontend en `app.familia.com` y la API en `api.familia.com` con DNS en el mismo proveedor; es un paso extra de dominio personalizado en Netlify y Render.

---

## PostgreSQL en Render + migraciones (3 pasos)

Ya quedó preparada la configuración para usar tu instancia de Render.

### Paso 1: conexión por `DATABASE_URL`

- Se agregó `.env` con tu URL externa:
  - `postgresql://bdd_economia_familiar_api_user:KoIODGJ8vM4ZHRjcBR1Q33FmT1Z8Zsnp@dpg-d7f4citckfvc739slfu0-a.oregon-postgres.render.com/bdd_economia_familiar_api`
- El backend ahora carga variables desde `.env` automáticamente.
- En Render (servicio web), configurá esa misma URL en la variable `DATABASE_URL`.

### Paso 2: migración inicial con Alembic

Se agregó estructura de Alembic:

- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/0001_initial_schema.py`

Comandos:

```bash
pip install -r requirements.txt
alembic upgrade head
```

Esto crea las tablas de usuarios, gastos, deudas, ingresos, eventos y adjuntos en PostgreSQL.

### Paso 3: dejar producción usando migraciones

Para producción en Render, definí:

- `AUTO_CREATE_TABLES=false`

Así evitás que la app dependa de `Base.metadata.create_all()` en runtime y el esquema queda controlado por Alembic.
