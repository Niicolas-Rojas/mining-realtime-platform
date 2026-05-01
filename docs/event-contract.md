# Telemetry Event Contract

Este contrato define la estructura minima aceptada por `ingestion` antes de persistir un evento en PostgreSQL y bronze.

## Version actual

- contrato: `telemetry_event.v1`
- productor inicial: `simulator`
- consumidor inicial: `ingestion`
- mensajes invalidos: `data/dead_letter/rejected_telemetry.ndjson`
- tabla de mensajes invalidos: `rejected_telemetry`

## Campos obligatorios

| Campo | Tipo | Regla |
| --- | --- | --- |
| `event_id` | string | UUID valido |
| `event_ts` | string | timestamp ISO-8601 con zona horaria |
| `equipment_id` | string | no vacio |
| `site` | string | no vacio |
| `line` | string | no vacio |
| `operational_state` | string | `running`, `warning`, `critical`, `stopped` o `maintenance` |
| `temperature_c` | number | entre -20 y 130 |
| `vibration_mm_s` | number | entre 0 y 25 |
| `lubrication_pressure_bar` | number | entre 0 y 10 |
| `rpm` | number | entre 0 y 30 |
| `amperage_a` | number | entre 0 y 2000 |
| `power_kw` | number | entre 0 y 20000 |
| `flow_m3_h` | number o null | entre 0 y 500; `null` representa lectura faltante |
| `anomaly_score` | number | entre 0 y 1 |
| `quality_flag` | string | `ok`, `partial` o `anomalous` |

## Comportamiento de ingesta

1. `ingestion` decodifica el mensaje MQTT como JSON.
2. Valida que sea un objeto y cumpla el contrato.
3. Si el evento es valido, lo persiste en `raw_telemetry` y escribe copia bronze.
4. Si el JSON o el contrato fallan, escribe el mensaje en `rejected_telemetry` y en dead-letter con:
   - timestamp de rechazo
   - razon del rechazo
   - topic MQTT
   - payload crudo
   - payload decodificado, cuando exista

## Simulacion de errores

El simulador puede publicar una fraccion configurable de mensajes defectuosos para probar la calidad del pipeline:

```text
SIMULATOR_DATA_ERROR_RATE=0.03
```

Ese valor representa aproximadamente un 3% de mensajes con problemas de datos. Los defectos simulados incluyen:

- JSON malformado
- campo obligatorio faltante
- tipo incorrecto en una medicion
- valor fuera de rango
- estado operacional invalido

Estos mensajes no deben llegar a Bronze/Silver/Gold. Deben quedar en `rejected_telemetry` y `data/dead_letter/`.

## Decisiones

- La capa bronze solo recibe eventos validos de contrato, pero conserva el payload completo.
- `flow_m3_h` permite `null` para simular lectura faltante sin rechazar el evento.
- Los rangos son amplios y operacionales, pensados para separar valores fisicamente imposibles de condiciones anormales validas.
- El dead-letter permite medir calidad de datos y recuperar evidencia sin detener el pipeline.
- La API expone `/api/v1/pipeline/metrics` para medir aceptados, rechazados, tasa de error y latencia.
