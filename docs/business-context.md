# Business Context

## Problema operacional

Las operaciones mineras dependen de telemetria continua para anticipar fallas, reaccionar frente a condiciones de riesgo y mantener la continuidad del proceso. En muchos escenarios, esos datos quedan repartidos entre sistemas, planillas y visualizaciones aisladas, lo que dificulta responder con velocidad.

Consecuencias tipicas:

- deteccion tardia de desviaciones
- consolidacion manual de informacion
- baja trazabilidad de eventos
- dificultad para construir historico confiable
- menor capacidad de priorizar mantenimiento

## Propuesta de solucion

La plataforma centraliza telemetria operacional desde un flujo event-driven. Parte desde la simulacion de sensores y llega a capas de almacenamiento y consumo que permiten operar en tiempo real y analizar tendencias historicas.

## Caso de uso inicial

El caso de uso base es el monitoreo de un molino SAG. Se prioriza este equipo porque concentra criticidad operacional, alto costo de detencion y variables con comportamiento dinamico.

Variables incluidas en la primera version:

- temperatura
- vibracion
- presion de lubricacion
- rpm
- amperaje
- potencia
- caudal
- estado operacional
- calidad del dato

## Resultado esperado

La solucion debe permitir:

- capturar telemetria en vivo
- tener una capa raw trazable
- preparar una base para alertas y dashboards
- demostrar criterio de arquitectura cloud y streaming

## Audiencia del proyecto

Este proyecto esta orientado a recruiters, hiring managers y lideres tecnicos que quieran evaluar:

- capacidad de disenar una plataforma end-to-end
- manejo de herramientas de datos modernas
- entendimiento de contexto industrial
- criterio para documentar y medir impacto
