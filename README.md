# Mining Realtime Platform

Plataforma de monitoreo operacional minero en tiempo real, pensada como proyecto de portafolio con enfoque cloud-first y criterio de arquitectura de datos productiva.

## Objetivo

Simular la telemetria de un equipo critico, inicialmente un molino SAG, para recorrer el flujo completo:

- generacion de eventos
- transporte por MQTT
- ingesta desacoplada
- persistencia raw en PostgreSQL y capa bronze
- procesamiento posterior hacia silver/gold
- exposicion operativa y analitica
- observabilidad tecnica

## Primer alcance implementado

Este primer corte deja operativo el vertical slice minimo del sistema:

1. `simulator`: genera telemetria realista y la publica en MQTT.
2. `ingestion`: consume los eventos, los persiste en PostgreSQL y replica una copia cruda en `data/bronze/`.
3. `api`: expone salud, telemetria reciente, metricas y alertas activas.
4. `dashboard`: muestra un tablero Streamlit para inspeccion visual.
5. `compose.yml`: orquesta broker MQTT, base de datos y los servicios Python.

## Arquitectura inicial

```text
simulator
-> MQTT broker
-> ingestion
-> PostgreSQL raw_telemetry
-> API FastAPI
-> Streamlit dashboard
-> bronze NDJSON
```

Arquitectura objetivo de mediano plazo:

```text
Sensor Simulator
-> MQTT Broker
-> Streaming Ingestion Service
-> Event Backbone
-> Bronze
-> Stream Processing
-> Silver / Gold
-> Alert Engine
-> API / Serving Layer
-> Dashboards
-> Monitoring
```

## Estructura del repositorio

```text
api/                FastAPI y serving layer
dashboards/         Grafana, Streamlit y Power BI
data/               Capas bronze, silver, gold y muestras
docs/               Contexto, roadmap, KPIs y arquitectura
infrastructure/     Docker, scripts y Terraform
ingestion/          Servicio consumidor de MQTT
observability/      Prometheus, Grafana y logging
processing/         Transformaciones batch/streaming
simulator/          Generador de telemetria industrial
```

## Variables de entorno

Duplica `.env.example` como `.env` si quieres personalizar valores.

Variables principales:

- `MQTT_BROKER_HOST`
- `MQTT_BROKER_PORT`
- `MQTT_TOPIC`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `SIMULATOR_INTERVAL_SECONDS`
- `SIMULATOR_DATA_ERROR_RATE`
- `BRONZE_OUTPUT_PATH`
- `DEAD_LETTER_OUTPUT_PATH`
- `GOLD_SUMMARY_PATH`
- `GOLD_REPORT_PATH`

## Levantar el entorno

```bash
docker compose up --build
```

Tambien existe un script para preparar la demo local completa:

```bash
./infrastructure/scripts/run-local-demo.sh
```

El script ejecuta pruebas, levanta servicios, espera la API y genera las capas Silver y Gold.

Servicios incluidos:

- `mqtt`: broker Eclipse Mosquitto
- `postgres`: almacenamiento raw
- `simulator`: publicador de telemetria
- `ingestion`: consumidor y persistencia
- `api`: consulta operativa de eventos recientes
- `dashboard`: visualizacion inicial en Streamlit

## Verificacion rapida

Cuando el stack este arriba:

```bash
docker compose logs simulator
docker compose logs ingestion
docker compose exec postgres psql -U mining -d mining_rt -c "select count(*) from raw_telemetry;"
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/telemetry/recent
curl http://localhost:8000/api/v1/metrics/summary
curl http://localhost:8000/api/v1/pipeline/metrics
curl http://localhost:8000/api/v1/alerts/active
curl http://localhost:8000/api/v1/telemetry/trends
```

Tambien deberian aparecer archivos NDJSON en `data/bronze/`.
Tambien deberias poder abrir `http://localhost:8501`.
Para que la pestana historica del dashboard muestre Gold, ejecuta primero los scripts Silver y Gold.

## Datos simulados

Cada evento representa una lectura operacional de un molino SAG con campos como:

- `equipment_id`
- `site`
- `line`
- `event_id`
- `event_ts`
- `operational_state`
- `temperature_c`
- `vibration_mm_s`
- `lubrication_pressure_bar`
- `rpm`
- `amperage_a`
- `power_kw`
- `flow_m3_h`
- `anomaly_score`
- `quality_flag`

El simulador ya incorpora:

- operacion normal
- drift gradual
- picos anomalos ocasionales
- lecturas faltantes controladas
- flags de calidad
- errores de datos configurables para probar dead-letter y tasa de error

## Documentacion

- [Master plan](docs/project-master-plan.md)
- [Business context](docs/business-context.md)
- [Event contract](docs/event-contract.md)
- [KPIs](docs/kpis.md)
- [Roadmap](docs/roadmap.md)
- [Runbook](docs/runbook.md)
- [Demo results](docs/demo-results.md)
- [Silver layer](docs/silver-layer.md)
- [Gold layer](docs/gold-layer.md)
- [Architecture overview](docs/architecture/overview.md)
- [Azure architecture](docs/architecture/azure-architecture.md)
- [Azure demo plan](docs/azure-demo.md)

## Siguientes pasos sugeridos

1. Ejecutar una demo temporal en Azure con Event Hubs y Data Lake.
2. Agregar observabilidad cloud con Application Insights.
3. Preparar screenshots y narrativa final de portafolio.
4. Incorporar Terraform/Bicep para despliegue reproducible.

## Como funciona hoy

1. `simulator` genera un evento JSON cada pocos segundos con variables como temperatura, vibracion, presion, potencia y estado operacional.
2. En una fraccion configurable, `simulator` publica mensajes defectuosos para probar validacion y dead-letter.
3. Ese evento viaja por MQTT en el topic `mining/sag-mill/telemetry`.
4. `ingestion` se suscribe a ese topic, recibe el mensaje y hace dos cosas:
   - valida el contrato minimo del evento
   - lo guarda completo en PostgreSQL, en la tabla `raw_telemetry`
   - lo replica a un archivo NDJSON en `data/bronze/`
   - envia mensajes invalidos a `data/dead_letter/`
5. `api` consulta PostgreSQL y entrega una vista simple para inspeccionar las ultimas lecturas desde tu navegador o con `curl`.
6. `api` tambien resume una ventana reciente y calcula alertas activas para convertir eventos crudos en indicadores operacionales.
7. `api` expone metricas del pipeline para medir eventos aceptados, rechazados, tasa de error y latencia.
8. `dashboard` consume la API y te deja revisar salud, metricas, alertas, confiabilidad del pipeline y ultimos eventos desde el navegador.
9. La API tambien expone tendencias y latencia de ingesta para observar el comportamiento del pipeline en el tiempo.
10. `processing` puede transformar bronze en una capa silver tabular para analisis.
11. `processing` tambien puede generar una capa gold con resumen por minuto y equipo.

## Como probarlo en Debian

### 1. Instalar prerequisitos

Necesitas Docker Engine y Docker Compose plugin.

```bash
sudo apt update
sudo apt install docker.io docker-compose-v2 curl
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Despues de agregar tu usuario al grupo `docker`, cierra sesion y vuelve a entrar.

### 2. Levantar el proyecto

```bash
cd /home/nico/Proyectos-Github/mining-realtime-platform
docker compose up --build
```

### 3. Confirmar que esta corriendo

En otra terminal:

```bash
docker compose ps
docker compose logs simulator --tail 20
docker compose logs ingestion --tail 20
docker compose logs api --tail 20
```

### 4. Probar la API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/telemetry/recent | python3 -m json.tool
curl "http://localhost:8000/api/v1/telemetry/recent?limit=5" | python3 -m json.tool
curl "http://localhost:8000/api/v1/metrics/summary?window=50" | python3 -m json.tool
curl "http://localhost:8000/api/v1/pipeline/metrics" | python3 -m json.tool
curl "http://localhost:8000/api/v1/alerts/active?limit=10" | python3 -m json.tool
curl "http://localhost:8000/api/v1/telemetry/trends?window=80" | python3 -m json.tool
```

### 5. Probar la base de datos

```bash
docker compose exec postgres psql -U mining -d mining_rt -c "select count(*) from raw_telemetry;"
docker compose exec postgres psql -U mining -d mining_rt -c "select event_id, operational_state, event_ts from raw_telemetry order by id desc limit 5;"
```

### 6. Probar la capa bronze

```bash
tail -n 5 data/bronze/raw_telemetry.ndjson
```

### 7. Revisar mensajes rechazados

```bash
tail -n 5 data/dead_letter/rejected_telemetry.ndjson
```

Si el archivo no existe, no se han rechazado mensajes durante la ejecucion actual.

### 8. Construir la capa silver

```bash
python3 -m processing.batch.silver_transform
head -5 data/silver/telemetry_clean.csv
cat data/silver/quality_report.json
```

### 9. Construir la capa gold

```bash
python3 -m processing.batch.gold_transform
head -5 data/gold/equipment_minute_summary.csv
cat data/gold/gold_quality_report.json
```

### 10. Probar el dashboard

Abre en tu navegador:

```text
http://localhost:8501
```

## Que mirar mientras aprendes

- Si `simulator` falla, piensa en el rol de un productor de eventos.
- Si `ingestion` falla, piensa en desacoplamiento y persistencia raw.
- Si `api` responde vacio, revisa primero si PostgreSQL realmente tiene filas.
- Si `bronze` crece pero la API no muestra datos, el problema probablemente esta entre ingestion y PostgreSQL.
- Si `metrics/summary` muestra que suben `warning_events` o `avg_anomaly_score`, ya estas pasando de observacion tecnica a lectura operacional.
- Si `alerts/active` comienza a listar eventos, ya tienes la base de un motor de alertas por reglas.
- Si aumenta `avg_ingestion_latency_ms`, ya puedes empezar a hablar de performance del pipeline y no solo de contenido del dato.
- Si `pipeline/metrics` muestra rechazos, ya puedes hablar de calidad de datos y confiabilidad de ingesta.
- Si la pestana `Historical` muestra ventanas Gold, ya tienes una demo local con lectura operacional y analitica historica.
