# Resultados de Demo Local

Ultima ejecucion documentada: 2026-04-28.

## Configuracion

- equipo simulado: `sag-mill-01`
- sitio: `concentradora-norte`
- linea: `linea-a`
- frecuencia del simulador: `2.0` segundos
- tasa de error simulada: `SIMULATOR_DATA_ERROR_RATE=0.03`
- capas generadas: Bronze, Silver y Gold

## Resultado Silver

| Metrica | Valor |
| --- | ---: |
| registros de entrada | 3712 |
| registros de salida | 3712 |
| duplicados omitidos | 0 |
| registros malformados omitidos | 0 |
| eventos anomalos | 147 |
| eventos con problema de calidad | 203 |
| eventos con caudal faltante | 56 |

## Resultado Gold

| Metrica | Valor |
| --- | ---: |
| filas Silver procesadas | 3712 |
| ventanas Gold generadas | 126 |
| filas malformadas omitidas | 0 |
| eventos anomalos agregados | 147 |
| eventos warning agregados | 48 |
| eventos critical agregados | 91 |

## Lectura para portafolio

Esta ejecucion demuestra:

- ingesta continua desde un simulador industrial
- validacion de contrato de datos
- rechazo controlado de mensajes defectuosos
- persistencia raw para trazabilidad
- transformacion Bronze -> Silver -> Gold
- resumen historico por minuto y equipo
- dashboard operacional e historico

## Como regenerar resultados

```bash
source .venv/bin/activate
python3 -m processing.batch.silver_transform
python3 -m processing.batch.gold_transform
python3 -m pytest
```
