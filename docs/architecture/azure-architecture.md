# Arquitectura Azure Propuesta

Esta arquitectura traduce la demo local a servicios administrados de Azure para evidenciar criterio cloud.

## Arquitectura logica

```text
Simulator Container
-> Azure Event Hubs
-> Azure Function / Container App consumer
-> Azure Data Lake Storage Gen2 Bronze
-> Batch/Streaming Processing
-> Azure Data Lake Storage Gen2 Silver/Gold
-> Azure Database for PostgreSQL or serving API
-> Dashboard / Power BI
-> Application Insights + Log Analytics
```

## Servicios sugeridos

| Componente local | Equivalente Azure |
| --- | --- |
| stream local | Azure Event Hubs |
| `data/bronze` | Azure Data Lake Storage Gen2 Bronze |
| `processing/batch` | Azure Container Apps Job, Azure Functions o Databricks |
| PostgreSQL local | Azure Database for PostgreSQL Flexible Server |
| FastAPI | Azure Container Apps |
| Streamlit dashboard | Azure Container Apps o demo local conectada a datos cloud |
| logs locales | Application Insights / Log Analytics |

## Estrategia recomendada para el mes gratis

Usar Azure para una demo temporal y controlada:

1. Crear un resource group exclusivo.
2. Desplegar Event Hubs, Storage Account y un servicio de procesamiento liviano.
3. Ejecutar el simulador durante una ventana corta.
4. Capturar screenshots de recursos, metricas, archivos y logs.
5. Exportar resultados a `docs/assets/screenshots/`.
6. Eliminar el resource group al terminar.

## Por que no dejarlo prendido

El objetivo de portafolio es demostrar arquitectura y ejecucion, no mantener una carga 24/7 pagando recursos. Una demo temporal con evidencia, costos estimados y limpieza posterior es suficiente y profesional.

## Evidencia esperada

- diagrama de arquitectura Azure
- screenshots de Event Hubs recibiendo eventos
- screenshots de Storage/Data Lake con Bronze/Silver/Gold
- logs de procesamiento
- dashboard o Power BI usando resultados
- nota de costos y limpieza de recursos
