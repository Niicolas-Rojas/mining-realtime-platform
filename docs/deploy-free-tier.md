# Guía de Deploy — Versión Gratuita (Demo Pública)

## Arquitectura del deploy

```
GitHub Actions (Lun/Jue)
  ├── Simulator  ──MQTT/TLS──►  HiveMQ Cloud (free)
  └── Ingestion  ──SQL/SSL──►   Supabase PostgreSQL (free)
                                      │
                              Render — API FastAPI (free, duerme)
                                      │
                         Streamlit Cloud — Dashboard (free, hiberna sin visitas)
```

Los datos persisten en Supabase entre corridas. La API despierta en ~30
segundos cuando alguien la visita. El dashboard Streamlit puede hibernar tras
periodos sin visitas; para portafolio se recomienda un wake-up con navegador
real desde GitHub Actions.

---

## Paso 1 — Supabase (PostgreSQL en la nube)

### 1.1 Crear proyecto

1. Ir a [supabase.com](https://supabase.com) → **Start your project** → crear cuenta con GitHub
2. **New Project**
   - Organization: (la que crea por defecto)
   - Name: `mining-platform`
   - Database Password: anotar esta contraseña (la necesitas después)
   - Region: elegir el más cercano (ej. South America - São Paulo)
3. Esperar ~2 minutos a que el proyecto se inicialice

### 1.2 Obtener credenciales

1. En el sidebar: **Project Settings** → **Database**
2. Bajar hasta **Connection parameters** y anotar:
   - Host: `db.XXXXXXXXXXXXXXXX.supabase.co`
   - Port: `5432`
   - Database name: `postgres`
   - User: `postgres`
   - Password: (la que pusiste al crear)
3. En **Connection string** seleccionar modo **URI** y copiarla como referencia

### 1.3 Verificar conexión (opcional)

```bash
psql "postgresql://postgres:TU_PASSWORD@db.XXXX.supabase.co:5432/postgres?sslmode=require"
```

Si aparece el prompt `postgres=#` todo está bien. Escribir `\q` para salir.

---

## Paso 2 — HiveMQ Cloud (MQTT Broker)

### 2.1 Crear cluster

1. Ir a [console.hivemq.cloud](https://console.hivemq.cloud) → crear cuenta
2. **Create Cluster** → elegir **Free** (Serverless)
3. Anotar la URL del cluster: `XXXXXXXXXXXXXXXX.s2.eu.hivemq.cloud`

### 2.2 Crear credenciales

1. En el cluster creado → **Access Management** → **Credentials**
2. **Add Credential**:
   - Username: `mining-platform`
   - Password: crear una contraseña segura y anotarla
3. Los permisos de subscribe/publish quedan habilitados por defecto

### 2.3 Datos a anotar

```
MQTT_BROKER_HOST = XXXXXXXXXXXXXXXX.s2.eu.hivemq.cloud
MQTT_BROKER_PORT = 8883
MQTT_USERNAME    = mining-platform
MQTT_PASSWORD    = tu-password
MQTT_USE_TLS     = true
MQTT_TOPIC       = mining/sag-mill/telemetry
```

### 2.4 Verificar conexión (opcional, necesita mosquitto_clients instalado)

```bash
mosquitto_pub \
  -h XXXXXXXXXXXXXXXX.s2.eu.hivemq.cloud \
  -p 8883 \
  --capath /etc/ssl/certs \
  -u mining-platform \
  -P tu-password \
  -t mining/sag-mill/telemetry \
  -m '{"test": true}'
```

---

## Paso 3 — GitHub Secrets

Los secretos permiten que el workflow `simulate.yml` use las credenciales
reales sin exponerlas en el código.

1. Ir al repositorio en GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** — crear uno por uno los siguientes:

| Secret Name | Valor |
|-------------|-------|
| `MQTT_BROKER_HOST` | URL del cluster HiveMQ |
| `MQTT_BROKER_PORT` | `8883` |
| `MQTT_USERNAME` | Username de HiveMQ |
| `MQTT_PASSWORD` | Password de HiveMQ |
| `MQTT_USE_TLS` | `true` |
| `POSTGRES_HOST` | Host de Supabase (`db.XXXX.supabase.co`) |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_DB` | `postgres` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | Password de Supabase |

> **Nota:** El topic MQTT está configurado como variable, no secret.
> Ir a **Variables** → **New repository variable** → `MQTT_TOPIC` = `mining/sag-mill/telemetry`

---

## Paso 4 — Primera corrida del simulador (prueba manual)

Antes de esperar el schedule automático, disparar el workflow manualmente
para verificar que todo funciona.

1. Ir al repositorio → **Actions**
2. En el sidebar: **scheduled-simulator**
3. **Run workflow** → en `duration_seconds` poner `120` (2 minutos para probar)
4. Hacer clic en **Run workflow**
5. Observar el progreso en tiempo real:
   - El step "Start ingestion service in background" debe conectarse al broker
   - El step "Run simulator" debe mostrar eventos publicados
   - El step "Run processor" debe mostrar silver/gold generados y rows escritos en postgres
6. Al terminar, verificar en Supabase:
   - **Table Editor** → buscar `raw_telemetry` → debe tener filas
   - Buscar `gold_summary` → debe tener filas

Si el workflow pasa verde en todos los steps, la infraestructura está lista.

---

## Paso 5 — Render (API FastAPI)

### 5.1 Crear cuenta y conectar repo

1. Ir a [render.com](https://render.com) → **Get Started for Free** → entrar con GitHub
2. **New** → **Web Service**
3. **Connect a repository** → buscar `mining-realtime-platform` → **Connect**

### 5.2 Configurar el servicio

Render debería detectar el `render.yaml` automáticamente. Si no:

- **Name:** `mining-api`
- **Region:** Oregon (US West) — el más cercano a Supabase São Paulo está en US East, pero cualquiera funciona
- **Branch:** `main`
- **Root Directory:** (dejar vacío — se usa render.yaml)
- **Build Command:** (vacío — usa Dockerfile)
- **Start Command:** (vacío — usa Dockerfile CMD)
- **Instance Type:** **Free**

### 5.3 Agregar variables de entorno

En el servicio creado → **Environment** → agregar:

| Key | Value |
|-----|-------|
| `POSTGRES_HOST` | Host de Supabase |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_DB` | `postgres` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | Password de Supabase |
| `POSTGRES_SSLMODE` | `require` |

### 5.4 Hacer el primer deploy

1. **Deploy** → esperar que construya la imagen Docker (~3-5 minutos)
2. Una vez en estado **Live**, anotar la URL: `https://mining-api-4dp3.onrender.com`
3. Probar: abrir `https://mining-api-4dp3.onrender.com/health` en el navegador
   - Debe responder: `{"status":"ok","service":"api"}`
4. Probar endpoint de datos: `https://mining-api-4dp3.onrender.com/api/v1/telemetry/recent`

> **Importante:** La primera vez que llames a la API después de un período
> de inactividad, puede tardar 30-50 segundos en despertar (cold start del
> free tier). Esto es normal.

---

## Paso 6 — Streamlit Community Cloud (Dashboard)

### 6.1 Crear cuenta

1. Ir a [share.streamlit.io](https://share.streamlit.io) → **Sign in with GitHub**
2. Dar acceso a los repositorios cuando lo pida

### 6.2 Crear la app

1. **New app**
2. **Repository:** `Niicolas-Rojas/mining-realtime-platform`
3. **Branch:** `main`
4. **Main file path:** `dashboards/streamlit/app.py`
5. **App URL:** elegir algo como `mining-realtime-platform` (quedará como `mining-realtime-platform.streamlit.app`)

### 6.3 Configurar secrets

Antes de hacer deploy, agregar el secret de la API:

1. En la configuración de la app → **Secrets**
2. Pegar el contenido:

```toml
API_BASE_URL = "https://mining-api-4dp3.onrender.com"
```

3. Hacer clic en **Save**

### 6.4 Deploy

1. **Deploy!** → esperar ~2-3 minutos
2. La app quedará disponible en: `https://mining-realtime-platform.streamlit.app`
3. Verificar que las tabs cargan datos (si la corrida del simulador fue exitosa)

> **Nota sobre el gold layer:** La tab "Historical Gold" puede aparecer vacía
> la primera vez si el workflow del simulador aún no corrió suficientes eventos.
> Correr el workflow nuevamente con `duration_seconds=600` para poblar datos.

> **Nota sobre Streamlit:** Community Cloud puede hibernar la app despues de
> periodos sin visitas. Para portafolio, mantener un workflow separado en el
> repo del sitio personal que abra la app con navegador real y presione el
> boton de wake-up si aparece. Un `curl` simple puede no despertar la app.

---

## Paso 7 — Verificación completa del sistema

Checklist para confirmar que todo funciona end-to-end:

```
[ ] Workflow simulate.yml corre sin errores en GitHub Actions
[ ] raw_telemetry tiene filas en Supabase Table Editor
[ ] gold_summary tiene filas en Supabase Table Editor
[ ] https://mining-api-4dp3.onrender.com/health responde ok
[ ] https://mining-api-4dp3.onrender.com/api/v1/metrics/summary responde con datos
[ ] https://mining-realtime-platform.streamlit.app carga sin errores
[ ] Tab "Control" muestra gráficos con datos reales
[ ] Tab "Pipeline" muestra eventos aceptados/rechazados
[ ] Tab "Historical Gold" muestra datos históricos
[ ] Tab "Risk & Alerts" muestra alertas si las hay
```

Si algo falla:
- API no conecta a Supabase → revisar `POSTGRES_SSLMODE=require` y las credenciales en Render
- Dashboard no conecta a API → revisar `API_BASE_URL` en Streamlit secrets (sin barra al final)
- Workflow falla en ingestion → revisar `MQTT_USE_TLS=true` y credenciales de HiveMQ

---

## Paso 8 — Schedule automático

El workflow ya está configurado para correr automáticamente los **lunes y jueves
a las 10:00 UTC** (07:00 hora Chile en verano, 06:00 en invierno).

Para ajustar el horario, editar `.github/workflows/simulate.yml`:

```yaml
schedule:
  - cron: "0 13 * * 1,4"  # 10:00 hora Chile en horario de verano (UTC-3)
```

GitHub Actions usa UTC. Si se necesita una hora exacta en Chile durante todo
el año, revisar el cron cuando cambie el horario de verano/invierno.

Para aumentar la duración de cada corrida (más datos generados):
- Ir a Actions → scheduled-simulator → Run workflow
- Cambiar `duration_seconds` a `1800` (30 minutos = ~900 eventos)

---

## Paso 9 — Agregar el proyecto al portafolio web

### 9.1 Información a tener lista antes de editar

- URL del dashboard: `https://mining-realtime-platform.streamlit.app`
- URL del repo: `https://github.com/Niicolas-Rojas/mining-realtime-platform`
- Stack a mencionar: Python, MQTT, PostgreSQL, FastAPI, Streamlit, Docker, GitHub Actions

### 9.2 Cambios en `index.html`

**A) Actualizar hero stats** — buscar la sección con los números del hero y cambiar:

```html
<!-- ANTES -->
<div class="hero-stat-number">2</div>
<div class="hero-stat-label">Proyectos destacados</div>

<div class="hero-stat-number">1</div>
<div class="hero-stat-label">Demo pública activa</div>

<!-- DESPUÉS -->
<div class="hero-stat-number">3</div>
<div class="hero-stat-label">Proyectos destacados</div>

<div class="hero-stat-number">2</div>
<div class="hero-stat-label">Demos públicas activas</div>
```

**B) Agregar la tarjeta del nuevo proyecto** — en la sección de proyectos,
después de la tarjeta del ETL Minería Chile, agregar:

```html
<div class="project-card">
  <div class="project-header">
    <div class="project-badge">Demo pública activa</div>
    <h3 class="project-title">Mining Realtime Platform</h3>
  </div>

  <p class="project-description">
    Plataforma de monitoreo operacional en tiempo real para equipos mineros
    (molino SAG). Arquitectura orientada a eventos: simulador de telemetría →
    MQTT → ingesta con validación → PostgreSQL → API → dashboard operacional.
    Pipeline continuo con capas bronze/silver/gold y observabilidad con
    Prometheus y Grafana.
  </p>

  <ul class="project-highlights">
    <li>Ingesta continua de telemetría con detección de anomalías y dead-letter</li>
    <li>Capas de datos bronze/silver/gold con transformaciones batch</li>
    <li>API FastAPI con 7 endpoints + métricas Prometheus</li>
    <li>Dashboard operacional en vivo (Streamlit) con auto-refresh</li>
    <li>Deploy gratuito: Supabase + Render + Streamlit Cloud + HiveMQ</li>
    <li>Simulación automatizada 2x/semana con GitHub Actions</li>
  </ul>

  <div class="project-tech">
    <span class="tech-tag">Python</span>
    <span class="tech-tag">MQTT</span>
    <span class="tech-tag">PostgreSQL</span>
    <span class="tech-tag">FastAPI</span>
    <span class="tech-tag">Streamlit</span>
    <span class="tech-tag">Docker</span>
    <span class="tech-tag">GitHub Actions</span>
    <span class="tech-tag">Prometheus</span>
  </div>

  <div class="project-links">
    <a href="https://mining-realtime-platform.streamlit.app" target="_blank"
       class="btn btn-primary">Ver demo</a>
    <a href="https://github.com/Niicolas-Rojas/mining-realtime-platform"
       target="_blank" class="btn btn-secondary">Ver código</a>
  </div>
</div>
```

> **Nota:** Verificar los nombres exactos de las clases CSS en tu `index.html`
> actual (project-card, project-badge, tech-tag, etc.) y ajustar si difieren.

### 9.3 Actualizar la sección de proyectos en el hero

Si hay un callout o descripción debajo del hero que menciona los proyectos,
actualizar el texto para incluir el tercer proyecto.

### 9.4 Commit y push

```bash
cd c:\Users\nicor\OneDrive\Documentos\GitHub\Niicolas-Rojas.github.io
git add index.html
git commit -m "add mining-realtime-platform to portfolio"
git push
```

GitHub Pages publica automáticamente en 1-2 minutos.

---

## Resumen de URLs finales

| Servicio | URL |
|----------|-----|
| Dashboard Streamlit | `https://mining-realtime-platform.streamlit.app` |
| API (despierta en ~30s) | `https://mining-api-4dp3.onrender.com` |
| API Health | `https://mining-api-4dp3.onrender.com/health` |
| API Docs (Swagger) | `https://mining-api-4dp3.onrender.com/docs` |
| Portafolio | `https://niicolas-rojas.github.io` |
| Repo | `https://github.com/Niicolas-Rojas/mining-realtime-platform` |

---

## Costos (todo gratuito)

| Servicio | Plan | Límites del free tier |
|----------|------|-----------------------|
| Supabase | Free | 500 MB storage, 2 proyectos |
| HiveMQ Cloud | Free Serverless | 100 conexiones, tráfico limitado |
| Render | Free | 750h/mes, duerme a los 15min |
| Streamlit Cloud | Free | Apps publicas gratis, hibernan sin visitas |
| GitHub Actions | Free | 2.000 min/mes (suficiente para ~20 corridas de 10min) |

**Costo total mensual: $0**
