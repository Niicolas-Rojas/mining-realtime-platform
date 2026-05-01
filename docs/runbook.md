# Runbook Operacional

Este runbook resume acciones de diagnostico para operar la demo local de la plataforma.

## Flujo esperado

```text
simulator -> mqtt -> ingestion -> postgres + bronze
                               -> rejected_telemetry + dead_letter
bronze -> silver -> gold
api -> dashboard
```

## Comandos base

Levantar servicios:

```bash
docker compose up --build
```

Construir capas analiticas:

```bash
python3 -m processing.batch.silver_transform
python3 -m processing.batch.gold_transform
```

Ejecutar pruebas:

```bash
python3 -m pytest
```

## Si el dashboard no muestra datos

1. Confirmar que los contenedores esten activos:

```bash
docker compose ps
```

2. Revisar logs del simulador e ingesta:

```bash
docker compose logs simulator --tail 50
docker compose logs ingestion --tail 50
```

3. Confirmar datos en PostgreSQL:

```bash
docker compose exec postgres psql -U mining -d mining_rt -c "select count(*) from raw_telemetry;"
```

4. Confirmar API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/telemetry/recent
```

## Si aumenta la tasa de error

1. Revisar metrica del pipeline:

```bash
curl http://localhost:8000/api/v1/pipeline/metrics
```

2. Revisar mensajes rechazados:

```bash
tail -n 20 data/dead_letter/rejected_telemetry.ndjson
```

3. Confirmar tasa configurada del simulador:

```text
SIMULATOR_DATA_ERROR_RATE=0.03
```

Una tasa alta puede ser intencional para demo. Para una operacion mas estable, usar 0.01 a 0.03.

## Si no aparece la vista historica

La vista historica usa Gold. Generar primero Silver y luego Gold:

```bash
python3 -m processing.batch.silver_transform
python3 -m processing.batch.gold_transform
```

Confirmar archivos:

```bash
ls -lh data/silver data/gold
```

## Si la latencia sube

1. Revisar latencia expuesta por API:

```bash
curl http://localhost:8000/api/v1/pipeline/metrics
```

2. Revisar uso de contenedores:

```bash
docker stats
```

3. Revisar si PostgreSQL esta respondiendo:

```bash
docker compose exec postgres psql -U mining -d mining_rt -c "select now();"
```

## Si se quiere reiniciar la demo

Detener servicios:

```bash
docker compose down
```

Detener y borrar volumen de PostgreSQL:

```bash
docker compose down -v
```

Nota: borrar el volumen elimina los datos guardados en PostgreSQL. Los archivos en `data/bronze`, `data/silver`, `data/gold` y `data/dead_letter` quedan en el repositorio local salvo que se eliminen manualmente.
