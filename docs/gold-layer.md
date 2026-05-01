# Gold Layer

La capa Gold resume la telemetria limpia de Silver en indicadores listos para dashboards historicos y lectura de negocio.

## Diferencia entre Silver y Gold

Silver mantiene una fila por evento aceptado:

```text
data/silver/telemetry_clean.csv
```

Gold agrupa esas filas por minuto, equipo, sitio y linea:

```text
data/gold/equipment_minute_summary.csv
```

## Que responde Gold

La capa Gold permite responder preguntas como:

- cuantas lecturas llegaron por minuto
- cual fue la temperatura promedio y maxima
- cual fue la vibracion promedio y maxima
- cual fue la presion minima de lubricacion
- cuantas anomalias hubo
- cuantos eventos warning o critical hubo
- cual fue la latencia promedio del pipeline
- cual fue el nivel de riesgo dominante del minuto

## Como ejecutarlo

Primero debe existir la capa Silver:

```bash
python3 -m processing.batch.silver_transform
```

Luego se construye Gold:

```bash
python3 -m processing.batch.gold_transform
```

Salidas generadas:

```text
data/gold/equipment_minute_summary.csv
data/gold/gold_quality_report.json
```

## Para que sirve

Gold es la capa adecuada para:

- dashboard historico
- metricas ejecutivas
- reportes por equipo
- comparacion entre ventanas de tiempo
- carga futura hacia Power BI, Grafana o una tabla analitica cloud

## Uso en dashboard

El dashboard Streamlit lee esta capa desde:

```text
GOLD_SUMMARY_PATH=/app/data/gold/equipment_minute_summary.csv
GOLD_REPORT_PATH=/app/data/gold/gold_quality_report.json
```

En Docker Compose, `data/gold` se monta como volumen de solo lectura dentro del dashboard.
