# Architecture Overview

## Current slice

```text
simulator -> mqtt -> ingestion -> postgres raw + bronze ndjson
                              -> dead-letter ndjson
                              -> rejected_telemetry
bronze ndjson -> processing batch -> silver csv
silver csv -> processing batch -> gold csv
postgres -> api -> dashboard
```

## Design principles

- servicios pequenos y desacoplados
- contratos de evento simples y versionables
- persistencia raw antes de transformaciones complejas
- rechazo trazable de mensajes invalidos
- metricas consultables desde API para medir confiabilidad
- separacion entre datos crudos y datos limpios para analitica
- capa gold para indicadores resumidos por ventana de tiempo
- facilidad de extension hacia cloud

## Near-term evolution

```text
simulator
-> mqtt
-> ingestion
-> event backbone
-> stream processing
-> silver/gold
-> api
-> dashboards
-> observability
```
