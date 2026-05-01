# Plan de Demo Azure

## Recomendacion

Si tienes disponible el mes gratis de Azure, si conviene usarlo para este proyecto. La mejor forma es hacer una demo cloud acotada, documentada y apagada al terminar.

Segun la pagina oficial de Azure, la cuenta gratuita para nuevos clientes puede incluir credito de USD 200 por 30 dias, servicios gratis por 12 meses y servicios siempre gratis. Aun asi, conviene trabajar con presupuesto, alertas y un resource group desechable.

## Objetivo de la demo cloud

Demostrar que la arquitectura local puede llevarse a cloud:

```text
simulador
-> Event Hubs
-> procesamiento / consumer
-> Data Lake Bronze
-> Silver / Gold
-> dashboard o Power BI
-> observabilidad
```

## Alcance recomendado

Primera version Azure:

- Event Hubs para ingesta
- Storage Account con contenedores `bronze`, `silver`, `gold`
- un consumer en Python ejecutado localmente o en Container Apps
- screenshots de metricas y archivos generados
- documentacion de costos y limpieza

Segunda version Azure:

- Container App para el simulador
- Container App o Azure Function para ingesta
- Application Insights
- dashboard conectado a resultados cloud

## Control de costos

Checklist antes de desplegar:

- usar una region unica
- crear resource group exclusivo
- configurar presupuesto bajo
- no usar recursos premium
- evitar Databricks al inicio si no es necesario
- apagar o eliminar recursos al terminar

Checklist al terminar:

```bash
az group delete --name <resource-group> --yes
```

## Screenshots sugeridos

Guardar capturas en:

```text
docs/assets/screenshots/
```

Capturas recomendadas:

- resource group con recursos creados
- Event Hubs con mensajes entrantes
- Storage Account con carpetas Bronze/Silver/Gold
- logs del consumer
- dashboard final
- costo estimado o presupuesto

## Resultado esperado para portafolio

La historia final debe decir:

> Disene una plataforma local end-to-end y luego valide su migracion conceptual a Azure usando Event Hubs, Data Lake, procesamiento Python y observabilidad basica, con una ejecucion temporal controlada para evitar costos innecesarios.
