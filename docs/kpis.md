# KPIs

## Sala de control

La sala de control es la vista ejecutiva y operacional del proyecto. Su objetivo no es mostrar todos los datos disponibles, sino responder rapido:

- si el molino SAG esta estable, en advertencia o critico
- que variable explica el riesgo: temperatura, vibracion, lubricacion, anomalia o calidad del dato
- si la plataforma de datos esta recibiendo, validando y persistiendo eventos con confianza
- que resumen historico deja la capa Oro para explicar la demo de portafolio

Por eso las graficas deben separar unidades, mostrar umbrales y reducir ruido visual. Una buena sala de control dice mucho con pocas senales.

## KPIs tecnicos

- `event_ingestion_latency_ms`
  Tiempo entre `event_ts` y persistencia raw.
  Disponible en `/api/v1/pipeline/metrics`.

- `events_ingested_per_minute`
  Volumen efectivo de mensajes recibidos y almacenados.
  Disponible en `/api/v1/pipeline/metrics`.

- `ingestion_error_rate`
  Porcentaje de mensajes rechazados o fallidos.
  Disponible en `/api/v1/pipeline/metrics`.
  Se puede observar configurando `SIMULATOR_DATA_ERROR_RATE`.

- `invalid_events_dead_lettered`
  Mensajes rechazados por JSON invalido o incumplimiento del contrato.
  Disponible en `/api/v1/pipeline/metrics`.

- `mqtt_publish_success_rate`
  Mensajes publicados versus intentados por el simulador.

- `bronze_write_success_rate`
  Persistencia correcta en archivos raw.
  Pendiente de instrumentacion explicita.

## KPIs operacionales simulados

- `anomaly_events_detected`
  Conteo de eventos con `anomaly_score` sobre umbral.

- `high_temperature_incidents`
  Lecturas con temperatura sobre limite operativo.

- `low_lubrication_pressure_incidents`
  Eventos con presion bajo rango esperado.

- `equipment_unstable_windows`
  Periodos donde coexisten vibracion alta y drift de potencia.

## KPIs de portafolio

- tiempo para levantar el entorno local
- cobertura del vertical slice
- claridad de la documentacion tecnica
- facilidad para extender hacia silver/gold y dashboards
- cantidad de registros generados en silver
- registros descartados por duplicados o malformacion en silver
- cantidad de ventanas generadas en gold
- eventos anomalos, warning y critical agregados en gold
