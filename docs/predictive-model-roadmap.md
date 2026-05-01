# Predictive Maintenance — Master Plan

## 1. Vision del proyecto

Este proyecto es el tercer componente de una trilogia analitica orientada a
mineria. No es un ejercicio academico aislado: es la capa que cierra el ciclo
de datos de los dos proyectos anteriores, demostrando que los datos operacionales
no solo sirven para monitorear lo que pasa, sino para anticipar lo que va a pasar.

```
ETL Mineria Chile        Mining Realtime Platform      Predictive Maintenance
"Que paso?"         →   "Que esta pasando?"       →   "Que va a pasar?"
Analitica descriptiva    Analitica operacional          Analitica predictiva
Datos historicos         Telemetria en tiempo real      ML sobre flota industrial
```

La meta no es construir un modelo que funcione en un notebook. La meta es
construir una solucion que se pueda defender tecnica y operacionalmente, que
tenga metricas reales, que sea explicable, y que demuestre criterio de ingenieria
aplicada a la industria minera.

## 2. Objetivo general

Construir un modelo de machine learning que, dado el historial reciente de
telemetria de un equipo industrial, prediga si ese equipo va a fallar en las
proximas 24 horas, con suficiente anticipacion como para programar una
intervencion de mantenimiento planificada.

El proyecto debe mostrar:

- capacidad de definir un problema de negocio real y medible
- construccion de hipotesis verificables con datos
- feature engineering sobre series de tiempo industriales
- entrenamiento y evaluacion rigurosa de un modelo de clasificacion
- explicabilidad del modelo para uso operacional
- exposicion del modelo como servicio (API + dashboard)
- narrativa de impacto cuantificada

## 3. Problema de negocio que resuelve

### Situacion actual

Las operaciones mineras dependen de equipos rotativos criticos: molinos SAG,
bombas de impulsion, compresores, correas transportadoras. El modelo de
mantenimiento predominante en la industria es reactivo o basado en calendario:

- **Reactivo:** se interviene despues de la falla. Impacto maximo en produccion.
- **Preventivo por calendario:** se mantiene cada N horas sin considerar el
  estado real del equipo. Genera sobremantension o fallas entre ciclos.

### Impacto cuantificado del problema

| Situacion | Costo estimado |
|-----------|---------------|
| Detencion no planificada de molino SAG | USD 50.000-150.000 por hora |
| Reparacion de emergencia vs. planificada | 5x a 10x mas caro |
| Tiempo de diagnostico en campo | 2 a 6 horas por evento |
| Consolidacion manual de datos de sensores | 3 a 8 horas de ingenieria por incidente |

### Lo que la solucion propone

Centralizar la telemetria historica de la flota, identificar patrones previos
a fallas y generar predicciones de riesgo por equipo con 24 horas de anticipacion.
Esto permite transformar intervenciones de emergencia en mantenciones planificadas.

## 4. Caso de uso principal

### Dataset

Se usa el dataset publico **Azure Predictive Maintenance (Kaggle / Microsoft)**:
876.100 lecturas horarias de 100 maquinas durante 3 anos. Es el dataset de
referencia en la industria para este tipo de problema.

Descarga: `kaggle datasets download -d arnabbiswas1/microsoft-azure-predictive-maintenance`

### Variables del dataset

Telemetria por maquina (una lectura por hora):

- voltaje (V)
- velocidad de rotacion (RPM)
- presion (bar)
- vibracion (mm/s)
- timestamp y ID de maquina

Variables de contexto:

- historial de errores no criticos (5 tipos)
- registros de mantencion por componente (4 componentes)
- modelo del equipo (1 a 4)
- edad del equipo (anos)

### Tipos de falla a detectar

| Codigo | Descripcion | Analogia minera |
|--------|-------------|-----------------|
| comp   | Falla de componente mecanico | Desgaste en cuerpo del molino |
| heat   | Sobrecalentamiento del sistema | Falla termica en rodamiento SAG |
| replace| Desgaste que requiere reemplazo | Reemplazo de revestimiento |
| slider | Falla en mecanismo deslizante | Falla en sello de bomba |
| bearings| Falla en rodamientos | Rodamiento del eje principal |

### Comportamientos que el modelo debe detectar

- degradacion gradual del voltaje en las horas previas a la falla
- aumento de variabilidad en vibracion antes de falla mecanica
- caida sostenida de presion como precursor de falla hidraulica
- acumulacion de errores no criticos como senales tempranas
- patron de tiempo largo sin mantencion combinado con anomalia en sensor

### Hipotesis a verificar con los datos

1. El cambio de los sensores (tendencia, pendiente) predice mejor que el valor absoluto
2. Los errores no criticos son indicadores adelantados de fallas reales
3. El tiempo desde la ultima mantencion agrega poder predictivo
4. Equipos de mayor edad tienen distribuciones de falla distintas

Cada hipotesis se confirma o refuta cuantitativamente en el notebook de EDA
y en el analisis SHAP del modelo.

## 5. Senal profesional que debe transmitir

El proyecto debe verse como una solucion de ingenieria de datos aplicada a
industria, no como un notebook de Kaggle.

Debe transmitir:

- capacidad de estructurar un problema: situacion actual, problema, hipotesis,
  solucion, metricas de exito
- dominio de series de tiempo industriales y sus particularidades
- criterio en seleccion de algoritmos con justificacion tecnica
- manejo de datos desbalanceados (fallas son ~3.5% del dataset)
- explicabilidad del modelo para contexto operacional (SHAP)
- pensamiento de producto: el modelo expuesto como API y dashboard usables

No debe verse como:

- un notebook con accuracy alto pero sin narrativa de negocio
- un modelo sin metricas de impacto real
- una solucion que no explica sus predicciones
- un proyecto desconectado de los otros dos del portafolio

## 6. Relacion con los tips del portafolio

### Tip 1 - Mostrar proyectos reales

El dataset es real (Microsoft Azure, industria), el problema es real (costo
de fallas no planificadas en mineria), y la solucion es aplicable a operacion
real. No es un dataset de juguete.

### Tip 2 - Explicar el problema resuelto

Cada seccion del proyecto responde:

- que problema operacional se analiza (detenciones no planificadas)
- que arquitectura se eligio y por que (XGBoost + SHAP por explicabilidad)
- que resultados genera (% recall, horas de anticipacion)
- que impacto tendria en operacion real (mantenciones planificadas vs. emergencia)

### Tip 3 - Documentar bien

El proyecto debe incluir:

- README fuerte con metricas reales
- model card (documentacion del modelo)
- notebooks ejecutables y comentados
- definicion de features
- contexto de negocio separado del codigo

### Tip 4 - Usar herramientas del mundo real

- Python, pandas, scikit-learn, XGBoost — estandar de industria
- SHAP — explicabilidad exigida en entornos regulados e industriales
- FastAPI — serving de modelos en produccion
- Streamlit — visualizacion rapida para stakeholders
- Docker — despliegue reproducible

### Tip 5 - Publicarlo y hacerlo visible

El repositorio debe quedar publico con:

- demo activa en Streamlit Cloud
- API en Render
- enlace desde el portafolio personal
- mencion explicita de la trilogia con los otros dos proyectos

## 7. Arquitectura objetivo

Arquitectura logica:

```
Dataset historico (Kaggle)
-> Carga y merge de 5 archivos
-> Feature Engineering (rolling stats + errores + mantencion + metadata)
-> Particion temporal (train/test cronologico)
-> Entrenamiento XGBoost
-> Evaluacion (Recall, PR-AUC, anticipacion en horas)
-> Explicabilidad SHAP
-> Modelo serializado
-> API de inferencia
-> Dashboard operacional
```

Arquitectura tecnica:

```
data/raw/            (5 CSV del dataset)
src/data_loader.py   (carga y merge)
src/features.py      (feature engineering)
src/train.py         (entrenamiento CLI)
models/              (modelo serializado + feature names)
api/main.py          (FastAPI: POST /predict, GET /health)
dashboard/app.py     (Streamlit: 3 tabs)
notebooks/           (EDA, features, entrenamiento, evaluacion)
docs/                (model card, feature definitions, business context)
```

## 8. Stack recomendado

### Core de datos y modelo

- Python 3.11
- pandas, numpy
- scikit-learn (preprocesamiento, metricas, TimeSeriesSplit)
- XGBoost (modelo principal)
- SHAP (explicabilidad)
- joblib (serializacion del modelo)
- pyarrow (parquet para datos procesados)

### Visualizacion y exploracion

- matplotlib, seaborn (notebooks)
- plotly (dashboard interactivo)
- jupyter (notebooks)

### Serving

- FastAPI + Uvicorn (API de inferencia)
- Streamlit (dashboard operacional)

### Infraestructura

- Docker + Docker Compose
- GitHub Actions (CI: tests automaticos)
- Render (API en cloud)
- Streamlit Cloud (dashboard publico)

## 9. Capas del sistema

### 9.1 Capa de datos

Carga y union de los 5 archivos del dataset. Construccion del label:
para cada hora de telemetria, determinar si hay una falla en las proximas
24 horas. Resultado: un DataFrame con telemetria + label + tipo de falla.

### 9.2 Capa de features

Transformacion del dataset crudo en un vector de features por observacion:

- estadisticas de ventana (media, std, min, max) en 3h, 24h y 168h por sensor
- deltas entre valor actual y media de ventana (señal de cambio brusco)
- conteo de errores no criticos en ventana de 24h por tipo
- horas desde ultima mantencion por componente
- metadata de la maquina (modelo, edad)

Total: ~80 features por observacion.

### 9.3 Capa de entrenamiento

Particion temporal (80% train, 20% test, sin shuffle). Entrenamiento con
XGBoost y manejo de desbalance de clases (scale_pos_weight). Validacion
con TimeSeriesSplit para evitar data leakage.

### 9.4 Capa de evaluacion

Metricas de clasificacion (Recall, Precision, F1, ROC-AUC, PR-AUC) sobre
el conjunto de test. Metrica de negocio: cuantas horas antes de la falla
real emite el modelo su primera alerta.

### 9.5 Capa de explicabilidad

Analisis SHAP para identificar que features impulsan cada prediccion.
Genera el grafico de importancia global y la explicacion por prediccion
individual (waterfall). Permite responder: "por que el modelo predijo
falla en esta maquina en este momento".

### 9.6 Capa de serving

API FastAPI que acepta una ventana de telemetria reciente y retorna
probabilidad de falla, nivel de riesgo (low/medium/high/critical)
y recomendacion operacional. Latencia de inferencia < 100ms.

### 9.7 Capa de visualizacion

Dashboard Streamlit con tres pestanas:

- Predictor en vivo: gauge de probabilidad, nivel de riesgo, recomendacion
- Resultados del modelo: metricas, distribucion de datos, histogramas por sensor
- Contexto de negocio: narrativa del problema, tipos de falla, conexion con la trilogia

## 10. Dashboards esperados

### Dashboard operacional (tab Predictor en vivo)

Debe mostrar:

- gauge de probabilidad de falla en 24h (0% a 100%)
- nivel de riesgo: NORMAL / PRECAUCION / ALERTA / CRITICO
- recomendacion operacional segun el nivel
- historial reciente de predicciones para la maquina seleccionada
- inputs manuales de telemetria para consulta ad-hoc

### Dashboard de resultados del modelo (tab Metricas)

Debe mostrar:

- KPIs principales: Recall, Precision, ROC-AUC, anticipacion promedio en horas
- distribucion del dataset de test (balance de clases)
- histogramas de sensores por clase (normal vs. falla proxima)
- matriz de confusion interpretada
- importancia de features (SHAP global)

### Dashboard de contexto (tab Negocio)

Debe mostrar:

- descripcion del problema y su impacto economico
- tabla de tipos de falla con analogia a mineria
- diagrama de la trilogia de proyectos
- como se conecta con el sistema de monitoreo en tiempo real

## 11. KPIs y metricas del sistema

El proyecto debe medir resultados concretos. No basta con decir que funciona.

### Metricas tecnicas del modelo

| Metrica | Umbral minimo | Objetivo |
|---------|--------------|---------|
| Recall (clase falla) | >= 70% | >= 80% |
| Precision (clase falla) | >= 55% | >= 65% |
| ROC-AUC | >= 0.85 | >= 0.90 |
| PR-AUC | >= 0.50 | >= 0.65 |

### Metrica de negocio (la mas importante)

| Metrica | Umbral minimo | Objetivo |
|---------|--------------|---------|
| Anticipacion promedio antes de falla | >= 12 horas | >= 18 horas |
| % de fallas detectadas con >= 12h anticipacion | >= 60% | >= 75% |
| Latencia de inferencia (API) | < 500ms | < 100ms |

### Por que el Recall es la metrica principal

En mantenimiento predictivo, un falso negativo (falla no detectada) tiene
un costo operacional mucho mayor que un falso positivo (alarma sin falla real).
Un Recall del 70% significa que 7 de cada 10 fallas reales son anticipadas.
El costo de inspeccionar sin encontrar falla es bajo comparado con una
detencion no planificada.

## 12. Narrativa de impacto esperada

El proyecto deberia poder defender estas afirmaciones, respaldadas con
los numeros reales del dataset de test:

- El modelo detecta el X% de las fallas con mas de 12 horas de anticipacion,
  permitiendo programar mantenciones planificadas en lugar de responder emergencias
- Las features mas importantes son variabilidad de voltaje y presion minima
  en ventana de 24h, confirmando que los equipos anuncian su falla a traves
  de inestabilidad energética antes del evento critico
- El modelo procesa 100 maquinas simultaneamente con latencia de inferencia
  menor a 100ms, compatible con integracion en sistema de monitoreo en tiempo real
- En un escenario operacional real, transformar el 60% de las intervenciones
  de emergencia en mantenciones planificadas representaria una reduccion
  significativa en costos de reparacion y tiempo de detencion

## 13. Filosofia de mejora continua

El proyecto debe mostrar evolucion, no solo resultado final.

### Version 1

- carga del dataset y EDA completo
- feature engineering basico (rolling stats de telemetria)
- modelo XGBoost binario
- evaluacion con metricas estandar
- notebook ejecutable

### Version 2

- feature engineering completo (errores + mantencion + metadata)
- evaluacion con metrica de negocio (horas de anticipacion)
- analisis SHAP de importancia de features
- validacion de las 4 hipotesis planteadas

### Version 3

- API FastAPI con endpoint /predict
- dashboard Streamlit con tab de predictor en vivo
- Docker Compose para ejecutar todo localmente
- tests unitarios para features y API

### Version 4

- deploy publico en Render (API) y Streamlit Cloud (dashboard)
- README con metricas reales y narrativa de impacto
- model card completo
- integracion con el endpoint de telemetria del proyecto de monitoreo

### Version 5

- analisis de falsos negativos (que fallas no se detectaron y por que)
- ajuste de threshold segun costo operacional real
- documentacion de limitaciones y proximos pasos
- mencion en portafolio con metricas reales

## 14. Estructura documental obligatoria

El repositorio debe tener:

- README principal con metricas reales y demo
- model card (docs/model-card.md)
- definicion de features (docs/feature-definitions.md)
- contexto de negocio (docs/business-context.md)
- 4 notebooks ejecutables (EDA, features, entrenamiento, evaluacion)
- instrucciones de ejecucion (Docker y entorno virtual)

## 15. Contenido obligatorio del README

El README debe incluir en este orden:

- nombre del proyecto y descripcion en una linea
- problema de negocio (2-3 parrafos, con numeros de impacto)
- hipotesis planteada
- dataset utilizado (fuente, volumen, variables)
- arquitectura de la solucion (diagrama en texto)
- stack tecnico
- resultados: tabla con metricas reales (completar despues de entrenar)
- metrica de negocio principal: horas de anticipacion
- como ejecutarlo (docker compose up --build)
- link a la demo
- conexion con los otros dos proyectos del portafolio
- limitaciones del modelo
- proximos pasos

## 16. Lo que hace que el proyecto destaque en portafolio

Este proyecto destacara si logra combinar:

- un problema de negocio real con numeros de impacto defendibles
- hipotesis explicitas que se confirman o refutan con datos
- modelo explicable (SHAP) que un operador puede entender
- metrica de negocio concreta (horas de anticipacion) en lugar de solo accuracy
- conexion explicita con los otros dos proyectos de la trilogia
- demo publica funcionando

La clave no es tener el modelo con mejor accuracy. La clave es poder explicar
por que el modelo toma cada decision, cuanto anticipa las fallas, y que
impacto tendria eso en una operacion minera real.

## 17. Riesgos a evitar

- entrenar con datos futuros (shuffle en series de tiempo = data leakage)
- reportar solo accuracy cuando las clases estan desbalanceadas
- no tener metrica de negocio (anticipacion en horas)
- no explicar las predicciones (modelo caja negra no es aceptable en operacion)
- dashboard sin conexion a modelo real (demo falsa)
- README sin metricas reales (poner XX y olvidar completar)
- no mencionar las limitaciones del modelo

## 18. Criterios de exito

El proyecto se considerara bien logrado si al final:

- [ ] tiene flujo completo desde datos hasta prediccion en vivo
- [ ] Recall >= 70% en clase de falla en conjunto de test
- [ ] anticipa fallas con promedio >= 12 horas de anticipacion
- [ ] modelo explicado con SHAP (se puede decir que variables causaron la alerta)
- [ ] las 4 hipotesis estan respondidas con datos
- [ ] API funcionando con latencia < 500ms
- [ ] demo publica accesible desde el portafolio
- [ ] README con metricas reales completadas
- [ ] model card documentado
- [ ] trilogia mencionada explicitamente en el README

## 19. Checklist final de senal profesional

- [ ] Problema operacional bien definido con impacto cuantificado
- [ ] Hipotesis explicitas antes de ver los datos
- [ ] Dataset real de industria (no simulado ni de juguete)
- [ ] Feature engineering sobre series de tiempo (rolling stats, deltas)
- [ ] Particion temporal correcta (sin data leakage)
- [ ] Manejo de clases desbalanceadas
- [ ] Metricas adecuadas para datos desbalanceados (Recall, PR-AUC)
- [ ] Metrica de negocio (horas de anticipacion)
- [ ] Explicabilidad con SHAP
- [ ] API de inferencia funcional
- [ ] Dashboard operacional con demo publica
- [ ] README con metricas reales
- [ ] Model card documentado
- [ ] Conexion explicita con la trilogia de proyectos
- [ ] Deploy reproducible con Docker

## 20. Conclusion

La meta de este proyecto no es construir el mejor modelo de Kaggle. La meta
es demostrar que se puede tomar un problema operacional real de la industria
minera, plantear hipotesis verificables, construir una solucion con criterio
de ingenieria, medir su impacto, y explicarla de forma que un operador o un
gerente de mantenimiento pueda entenderla y confiar en ella.

Ese es exactamente el perfil que busca el Programa de Graduados de Codelco:
alguien que entiende tanto los datos como el contexto operacional en que se usan.

---

# Parte 2 — Guia de Implementacion

> Esta seccion contiene el detalle tecnico para construir el proyecto
> siguiendo el plan definido arriba. Disenada para ser usada con IA
> como guia de implementacion paso a paso.

---

## A. Dataset — Descarga y estructura

**Comando de descarga:**
```bash
pip install kaggle
kaggle datasets download -d arnabbiswas1/microsoft-azure-predictive-maintenance
unzip microsoft-azure-predictive-maintenance.zip -d data/raw/
```

**Archivos:**
```
data/raw/
├── PdM_telemetry.csv    # 876.100 filas — lecturas horarias por maquina
├── PdM_errors.csv       # 3.919 filas  — errores no criticos
├── PdM_maint.csv        # 3.286 filas  — registros de mantencion
├── PdM_failures.csv     # 761 filas    — eventos de falla reales
└── PdM_machines.csv     # 100 filas    — metadata (modelo, edad)
```

**Columnas de telemetria:** datetime, machineID, volt, rotate, pressure, vibration

**Columnas de fallas:** datetime, machineID, failure (comp/heat/replace/slider/bearings)

---

## B. Estructura del repositorio

```
sag-mill-predictive-maintenance/
├── data/
│   ├── raw/                          # CSV originales de Kaggle (no commitear)
│   └── processed/                    # features_train.parquet, features_test.parquet
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
├── src/
│   ├── data_loader.py                # carga y merge de archivos raw
│   ├── features.py                   # pipeline de feature engineering
│   ├── train.py                      # script de entrenamiento CLI
│   └── predict.py                    # funcion de inferencia
├── api/
│   ├── main.py                       # FastAPI endpoints
│   └── requirements.txt
├── dashboard/
│   ├── app.py                        # Streamlit 3 tabs
│   └── requirements.txt
├── models/
│   ├── predictive_model.pkl
│   └── feature_names.json
├── docs/
│   ├── model-card.md
│   ├── feature-definitions.md
│   └── business-context.md
├── tests/
├── .streamlit/secrets.toml.example
├── .gitignore
├── Dockerfile
├── compose.yml
├── requirements.txt
└── README.md
```

---

## C. requirements.txt

```
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
xgboost>=2.0
shap>=0.44
joblib>=1.3
pyarrow>=14.0
matplotlib>=3.7
seaborn>=0.12
plotly>=5.18
jupyter>=1.0
ipykernel>=6.0
```

**api/requirements.txt:**
```
fastapi>=0.110
uvicorn[standard]>=0.27
pydantic>=2.0
joblib>=1.3
numpy>=1.24
pandas>=2.0
scikit-learn>=1.3
xgboost>=2.0
```

**dashboard/requirements.txt:**
```
streamlit>=1.32
plotly>=5.18
pandas>=2.0
numpy>=1.24
requests>=2.31
shap>=0.44
joblib>=1.3
xgboost>=2.0
scikit-learn>=1.3
```

---

## D. src/data_loader.py

```python
from __future__ import annotations
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")


def load_raw_files() -> dict[str, pd.DataFrame]:
    return {
        "telemetry": pd.read_csv(RAW_DIR / "PdM_telemetry.csv", parse_dates=["datetime"]),
        "errors":    pd.read_csv(RAW_DIR / "PdM_errors.csv",    parse_dates=["datetime"]),
        "maint":     pd.read_csv(RAW_DIR / "PdM_maint.csv",     parse_dates=["datetime"]),
        "failures":  pd.read_csv(RAW_DIR / "PdM_failures.csv",  parse_dates=["datetime"]),
        "machines":  pd.read_csv(RAW_DIR / "PdM_machines.csv"),
    }


def build_label_column(
    telemetry: pd.DataFrame,
    failures: pd.DataFrame,
    horizon_hours: int = 24,
) -> pd.DataFrame:
    """
    Para cada fila de telemetria, label=1 si hay una falla en las proximas
    horizon_hours horas para esa maquina. Label=0 en caso contrario.
    """
    df = telemetry.copy().sort_values(["machineID", "datetime"])
    df["label"] = 0
    df["failure_type"] = "none"

    for machine_id in df["machineID"].unique():
        machine_failures = failures[failures["machineID"] == machine_id]
        machine_mask = df["machineID"] == machine_id

        for _, failure_row in machine_failures.iterrows():
            failure_time = failure_row["datetime"]
            window_start = failure_time - pd.Timedelta(hours=horizon_hours)
            in_window = (
                machine_mask
                & (df["datetime"] >= window_start)
                & (df["datetime"] < failure_time)
            )
            df.loc[in_window, "label"] = 1
            df.loc[in_window, "failure_type"] = failure_row["failure"]

    return df
```

---

## E. src/features.py

```python
from __future__ import annotations
import pandas as pd
import numpy as np

SENSOR_COLS  = ["volt", "rotate", "pressure", "vibration"]
WINDOWS      = [3, 24, 168]
ERROR_TYPES  = [f"error{i}" for i in range(1, 6)]
COMP_TYPES   = [f"comp{i}"  for i in range(1, 5)]


def build_telemetry_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df[["datetime", "machineID"] + SENSOR_COLS].copy()

    for window in WINDOWS:
        grp     = df.groupby("machineID")[SENSOR_COLS]
        rolling = grp.rolling(window=window, min_periods=1)

        for stat_name, stat_fn in [
            ("mean", rolling.mean),
            ("std",  rolling.std),
            ("min",  rolling.min),
            ("max",  rolling.max),
        ]:
            stat_df = stat_fn().reset_index(level=0, drop=True)
            for col in SENSOR_COLS:
                result[f"{col}_{stat_name}_{window}h"] = stat_df[col]

    for col in SENSOR_COLS:
        result[f"{col}_delta_3h"]  = result[col] - result[f"{col}_mean_3h"]
        result[f"{col}_delta_24h"] = result[col] - result[f"{col}_mean_24h"]

    return result


def build_error_features_fast(
    telemetry: pd.DataFrame,
    errors: pd.DataFrame,
    window_hours: int = 24,
) -> pd.DataFrame:
    """Version vectorizada con merge_asof."""
    tel = telemetry[["datetime", "machineID"]].copy()
    tel = tel.sort_values("datetime")

    for error_type in ERROR_TYPES:
        err = errors[errors["errorID"] == error_type].copy()
        err["_count"] = 1
        merged = pd.merge_asof(
            tel,
            err.sort_values("datetime")[["datetime", "machineID", "_count"]],
            on="datetime",
            by="machineID",
            tolerance=pd.Timedelta(hours=window_hours),
            direction="backward",
        )
        tel[f"errors_{error_type}_{window_hours}h"] = merged["_count"].fillna(0).values

    return tel.sort_index()


def build_maintenance_features(
    telemetry: pd.DataFrame,
    maint: pd.DataFrame,
) -> pd.DataFrame:
    result = telemetry[["datetime", "machineID"]].copy()

    for comp in COMP_TYPES:
        result[f"hours_since_{comp}"] = np.nan

    for machine_id in telemetry["machineID"].unique():
        machine_tel  = telemetry[telemetry["machineID"] == machine_id]
        machine_maint = maint[maint["machineID"] == machine_id]

        for comp in COMP_TYPES:
            comp_maint = machine_maint[machine_maint["comp"] == comp].sort_values("datetime")

            for idx, tel_row in machine_tel.iterrows():
                if comp_maint.empty:
                    result.loc[idx, f"hours_since_{comp}"] = 9999
                    continue
                past = comp_maint[comp_maint["datetime"] <= tel_row["datetime"]]
                if past.empty:
                    result.loc[idx, f"hours_since_{comp}"] = 9999
                else:
                    hours = (tel_row["datetime"] - past.iloc[-1]["datetime"]).total_seconds() / 3600
                    result.loc[idx, f"hours_since_{comp}"] = hours

    return result


def merge_all_features(
    telemetry_features: pd.DataFrame,
    error_features: pd.DataFrame,
    maint_features: pd.DataFrame,
    machines: pd.DataFrame,
    labels: pd.DataFrame,
) -> pd.DataFrame:
    df = labels[["datetime", "machineID", "label", "failure_type"]].copy()

    for block in [telemetry_features, error_features, maint_features]:
        cols = [c for c in block.columns if c not in ["datetime", "machineID"]]
        df = df.merge(block[["datetime", "machineID"] + cols], on=["datetime", "machineID"], how="left")

    df = df.merge(machines[["machineID", "model", "age"]], on="machineID", how="left")
    df["model"] = df["model"].str.extract(r"(\d+)").astype(int)
    return df.dropna()


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    exclude = {"datetime", "machineID", "label", "failure_type"}
    return [c for c in df.columns if c not in exclude]


def temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """80% train / 20% test — particion cronologica, sin shuffle."""
    split_date = pd.Timestamp("2015-10-01")
    train = df[df["datetime"] < split_date].copy()
    test  = df[df["datetime"] >= split_date].copy()
    print(f"Train: {len(train):,} filas | positivos: {train['label'].mean():.1%}")
    print(f"Test:  {len(test):,} filas  | positivos: {test['label'].mean():.1%}")
    return train, test
```

---

## F. src/train.py

```python
from __future__ import annotations
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    classification_report, roc_auc_score,
    average_precision_score, confusion_matrix,
)
from xgboost import XGBClassifier

from src.features import get_feature_columns

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def train_model() -> None:
    train = pd.read_parquet("data/processed/features_train.parquet")
    test  = pd.read_parquet("data/processed/features_test.parquet")

    feature_cols = get_feature_columns(train)
    X_train, y_train = train[feature_cols], train["label"]
    X_test,  y_test  = test[feature_cols],  test["label"]

    with open(MODELS_DIR / "feature_names.json", "w") as f:
        json.dump(feature_cols, f)

    scale_pos_weight = float((y_train == 0).sum() / (y_train == 1).sum())
    print(f"Desbalance — scale_pos_weight={scale_pos_weight:.1f}")

    model = XGBClassifier(
        n_estimators=500,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        early_stopping_rounds=30,
        random_state=42,
        tree_method="hist",
        n_jobs=-1,
    )

    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("\n--- Clasificacion ---")
    print(classification_report(y_test, y_pred, target_names=["Normal", "Falla proxima"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"PR-AUC:  {average_precision_score(y_test, y_proba):.4f}")
    print(f"\nMatriz de confusion:\n{confusion_matrix(y_test, y_pred)}")

    _compute_anticipation(test, y_proba)

    joblib.dump(model, MODELS_DIR / "predictive_model.pkl")
    print(f"\nModelo guardado.")


def _compute_anticipation(test_df: pd.DataFrame, y_proba, threshold: float = 0.5) -> None:
    import numpy as np
    failures = pd.read_csv("data/raw/PdM_failures.csv", parse_dates=["datetime"])
    df = test_df.copy()
    df["proba"] = y_proba
    df["alert"] = (df["proba"] >= threshold).astype(int)
    test_failures = failures[failures["datetime"] >= df["datetime"].min()]
    anticipations = []
    for _, row in test_failures.iterrows():
        mdf = df[df["machineID"] == row["machineID"]]
        before = mdf[mdf["datetime"] < row["datetime"]]
        alerts = before[before["alert"] == 1]
        if not alerts.empty:
            hours = (row["datetime"] - alerts["datetime"].min()).total_seconds() / 3600
            anticipations.append(hours)
    if anticipations:
        print(f"\n--- Metrica de negocio ---")
        print(f"Fallas anticipadas: {len(anticipations)}/{len(test_failures)} ({len(anticipations)/len(test_failures):.0%})")
        print(f"Anticipacion promedio: {np.mean(anticipations):.1f} horas  ← este numero va en el README")


if __name__ == "__main__":
    train_model()
```

---

## G. api/main.py

```python
from __future__ import annotations
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

model = joblib.load("models/predictive_model.pkl")
with open("models/feature_names.json") as f:
    FEATURE_NAMES: list[str] = json.load(f)

app = FastAPI(title="SAG Mill Predictive Maintenance API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])

SENSOR_COLS = ["volt", "rotate", "pressure", "vibration"]
WINDOWS     = [3, 24, 168]


class Reading(BaseModel):
    datetime: str
    machineID: int
    volt: float
    rotate: float
    pressure: float
    vibration: float


class PredictRequest(BaseModel):
    readings: list[Reading]
    machine_age: int = 10
    machine_model: int = 1


class PredictResponse(BaseModel):
    machine_id: int
    failure_probability: float
    risk_level: str
    alert: bool
    recommendation: str


def _build_features(readings: list[Reading], age: int, model_num: int) -> list[float]:
    df = pd.DataFrame([r.model_dump() for r in readings])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")
    features: dict = {}

    last = df.iloc[-1]
    for col in SENSOR_COLS:
        features[col] = float(last[col])

    for w in WINDOWS:
        wdf = df.tail(w)
        for col in SENSOR_COLS:
            features[f"{col}_mean_{w}h"] = float(wdf[col].mean())
            features[f"{col}_std_{w}h"]  = float(wdf[col].std() or 0)
            features[f"{col}_min_{w}h"]  = float(wdf[col].min())
            features[f"{col}_max_{w}h"]  = float(wdf[col].max())

    for col in SENSOR_COLS:
        features[f"{col}_delta_3h"]  = features[col] - features[f"{col}_mean_3h"]
        features[f"{col}_delta_24h"] = features[col] - features[f"{col}_mean_24h"]

    for i in range(1, 6):
        features[f"errors_error{i}_24h"] = 0
    for i in range(1, 5):
        features[f"hours_since_comp{i}"] = 500

    features["model"] = model_num
    features["age"]   = age

    return [features.get(f, 0) for f in FEATURE_NAMES]


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    if len(req.readings) < 3:
        raise HTTPException(400, "Se requieren al menos 3 lecturas")

    fv    = pd.DataFrame([_build_features(req.readings, req.machine_age, req.machine_model)], columns=FEATURE_NAMES)
    proba = float(model.predict_proba(fv)[0][1])

    if proba < 0.25:
        risk, rec = "low",      "Operacion normal. Continuar monitoreo de rutina."
    elif proba < 0.50:
        risk, rec = "medium",   "Incrementar frecuencia de monitoreo."
    elif proba < 0.75:
        risk, rec = "high",     "Programar inspeccion en las proximas horas."
    else:
        risk, rec = "critical", "ACCION INMEDIATA: alto riesgo de falla inminente."

    return PredictResponse(
        machine_id=req.readings[-1].machineID,
        failure_probability=round(proba, 4),
        risk_level=risk,
        alert=proba >= 0.5,
        recommendation=rec,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": "predictive_maintenance_v1", "features": len(FEATURE_NAMES)}
```

---

## H. Contenido de los notebooks

### 01_eda.ipynb — lo que debe tener

1. Carga de los 5 archivos y .describe() de cada uno
2. Distribucion temporal de fallas por tipo (barras)
3. Serie temporal de sensores para 3 maquinas representativas
4. Patron promedio de sensores en las N horas previas a una falla (grafico clave)
5. Heatmap de correlacion entre sensores
6. Distribucion de fallas por modelo de maquina y edad
7. Respuesta a las 4 hipotesis con graficos de soporte

### 02_feature_engineering.ipynb — lo que debe tener

1. Demostracion del rolling stats para una maquina
2. Visualizacion del label (ventana de 24h antes de falla en rojo)
3. Distribucion de clases en train y test (desbalance)
4. Muestra del DataFrame de features final (head + dtypes)
5. Guardar features_train.parquet y features_test.parquet

### 03_model_training.ipynb — lo que debe tener

1. Comparacion de 3 modelos: Logistic Regression, Random Forest, XGBoost
2. Curva de aprendizaje del XGBoost
3. Curva precision-recall para elegir threshold optimo
4. Tabla final de metricas de los 3 modelos comparados

### 04_evaluation.ipynb — lo que debe tener

1. Metricas finales en test (tabla completa)
2. Matriz de confusion con interpretacion en lenguaje operacional
3. Curva ROC y PR-AUC
4. SHAP summary plot (top 20 features) — exportar como imagen para README
5. SHAP waterfall para un caso de alta probabilidad y uno de baja
6. Metrica de negocio: anticipacion promedio en horas — exportar numero para README
7. Analisis de falsos negativos: que tienen en comun las fallas no detectadas

---

## I. Orden de trabajo (sprint intensivo)

### Dia 1 — Setup y datos
- Crear repositorio en GitHub
- Setup entorno virtual, instalar dependencias
- Descargar dataset de Kaggle
- Notebook 01_eda.ipynb completo

### Dia 2 — Feature engineering
- Implementar src/features.py
- Notebook 02_feature_engineering.ipynb
- Guardar parquet de train y test

### Dia 3 — Modelo y evaluacion
- Ejecutar src/train.py
- Notebook 03_model_training.ipynb
- Notebook 04_evaluation.ipynb
- Anotar los numeros reales: Recall, PR-AUC, horas de anticipacion

### Dia 4-5 — API y dashboard
- Implementar api/main.py y probar con curl
- Implementar dashboard/app.py con las 3 tabs
- Probar docker compose up --build

### Dia 6 — Documentacion
- Completar README con numeros reales
- Completar docs/model-card.md
- Revisar notebooks con ojo de portafolio

### Dia 7 — Deploy y portafolio
- Deploy API en Render
- Deploy dashboard en Streamlit Cloud
- Actualizar index.html del portafolio
- Postular al programa de graduados Codelco
