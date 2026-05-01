# Silver Layer

La capa Silver es la version limpia y tabular de la telemetria aceptada.

## Diferencia entre Bronze y Silver

Bronze conserva los eventos como llegaron desde la ingesta:

```text
data/bronze/raw_telemetry.ndjson
```

Silver transforma esos eventos en una tabla mas facil de analizar:

```text
data/silver/telemetry_clean.csv
```

## Que agrega Silver

La transformacion:

- aplana el JSON del evento en columnas
- separa fecha y minuto del evento
- calcula `ingestion_latency_ms`
- marca eventos anomalos con `is_anomaly`
- marca problemas de calidad con `is_quality_issue`
- marca lecturas faltantes de caudal con `is_flow_missing`
- deriva `risk_level` como `normal`, `warning` o `critical`
- elimina duplicados por `event_id`
- genera un reporte de calidad

## Como ejecutarlo

Con datos en `data/bronze/raw_telemetry.ndjson`:

```bash
python3 -m processing.batch.silver_transform
```

Salidas generadas:

```text
data/silver/telemetry_clean.csv
data/silver/quality_report.json
```

## Para que sirve

Silver deja los datos preparados para:

- analisis historico
- calculo de KPIs
- generacion de capa Gold
- dashboards ejecutivos
- carga futura a Spark, Databricks o un data lake cloud
