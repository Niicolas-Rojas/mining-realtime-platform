# Roadmap

## Fase 1 - Vertical slice local

- simulador MQTT operativo
- ingesta con persistencia raw en PostgreSQL
- copia bronze en archivos NDJSON
- documentacion base y `docker compose`

## Fase 2 - Procesamiento streaming

- normalizacion de esquema
- contrato de evento y validacion en ingesta
- dead-letter para mensajes invalidos
- metricas de aceptacion, rechazo y latencia de ingesta
- enriquecimiento de eventos
- derivacion a capa silver local
- derivacion a capa gold local por minuto y equipo
- primeras reglas de calidad

## Fase 3 - Serving y dashboards

- FastAPI para consultas recientes
- dashboard operacional en tiempo real
- primeras alertas por umbrales

## Fase 4 - Cloud y analitica

- object storage estilo data lake
- procesamiento con Spark o Databricks
- modelado gold para analitica
- Power BI o Grafana para historico

## Fase 5 - Operacion profesional

- CI/CD
- monitoreo y logs estructurados
- IaC con Terraform
- narrativa before/after del impacto logrado
