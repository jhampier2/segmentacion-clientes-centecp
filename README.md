# Dashboard de Segmentación de Clientes — CENTECP

Sistema de machine learning no supervisado que segmenta clientes de microfinanzas en tres perfiles de riesgo usando **K-Means**. Incluye API REST (Flask), dashboard interactivo (Chart.js) y motor de predicción para evaluar nuevos solicitantes de crédito en tiempo real.

---

## Índice

1. [¿Qué hace este sistema?](#qué-hace-este-sistema)
2. [Variables de entrada: qué significan y por qué se usan](#variables-de-entrada-qué-significan-y-por-qué-se-usan)
3. [Cómo funciona el modelo K-Means](#cómo-funciona-el-modelo-k-means)
4. [Perfiles de riesgo: interpretación detallada](#perfiles-de-riesgo-interpretación-detallada)
5. [Cómo interpretar los resultados](#cómo-interpretar-los-resultados)
6. [Guía de uso](#guía-de-uso)
7. [Endpoints API](#endpoints-api)
8. [Despliegue en Render](#despliegue-en-render)
9. [Desarrollo local con base de datos](#desarrollo-local-con-base-de-datos)
10. [Estructura del proyecto](#estructura-del-proyecto)
11. [Datos de prueba](#datos-de-prueba)

---

## ¿Qué hace este sistema?

Toma **1,500 clientes activos** de la cartera de créditos de CENTECP, los agrupa en 3 clusters mediante K-Means no supervisado, y expone:

- Un **dashboard web** con KPIs, gráficos de distribución y tabla filtrable de clientes.
- Un **modal de evaluación** donde ingresas los datos financieros de un nuevo solicitante y el modelo predice su cluster de riesgo al instante.
- Una **API REST** para integrar la segmentación en otros sistemas (CRM, core bancario, etc.).

---

## Variables de entrada: qué significan y por qué se usan

El modelo opera sobre **tres features** extraídos de la base de datos transaccional:

### 1. `ingresos_mensuales` — Ingresos mensuales declarados (USD)

| Aspecto | Detalle |
|---------|---------|
| **Origen** | Columna `ingresos_mensuales` de la tabla `tclie_general` |
| **Qué mide** | Capacidad de pago declarada por el cliente al momento de la afiliación |
| **Por qué se usa** | Es el predictor más fuerte de solvencia. K-Means encontró que esta variable por sí sola separa claramente los tres clusters: ingresos bajos (~5K), medios (~4.8K) y altos (~14K) definen pertenencia a cada grupo |

### 2. `linea_credito_utilizada` — Proporción de crédito consumido (0.0 a 1.0)

| Aspecto | Detalle |
|---------|---------|
| **Origen** | `SUM(d.saldo) / MAX(p.montoAprovado)` — saldo pendiente total entre monto aprobado del préstamo más grande |
| **Qué mide** | Qué porcentaje de su línea de crédito ya está comprometido. 0.0 = no debe nada, 1.0 = debe el 100% de lo aprobado |
| **Por qué se usa** | Un cliente con alta utilización tiene menos margen para absorber un nuevo préstamo. Es señal de sobreendeudamiento |

### 3. `dias_atraso_promedio` — Días de mora promedio

| Aspecto | Detalle |
|---------|---------|
| **Origen** | `AVG(DATEDIFF(fechaPago, expiration_at))` sobre todas las cuotas del cliente |
| **Qué mide** | Comportamiento de pago histórico. **Valores negativos** = paga antes del vencimiento (bueno). **Valores positivos** = paga tarde (malo). 0 = paga exactamente el día de vencimiento |
| **Por qué se usa** | Es el indicador directo de riesgo de impago. Un cliente que consistentemente paga 50 días antes (-50) es radicalmente distinto de uno que paga 20 días tarde (+20) |

> **Nota importante sobre días negativos:** La base de datos CENTECP tiene un patrón donde la mayoría de clientes paga antes del vencimiento. Por eso los centroides muestran valores como -54.5 (cluster 0) o -4.9 (cluster 1). Esto es normal en microfinanzas donde los oficiales de crédito visitan al cliente para cobrar antes de la fecha límite.

---

## Cómo funciona el modelo K-Means

### Pipeline de entrenamiento

```
Base de Datos (MySQL)
    │
    ▼
┌─────────────────────────────────────┐
│ consultas_ia.py                     │
│ SQL JOIN sobre 3 tablas:            │
│ tclie_general + tprestamo +         │
│ tpresta_detalle                     │
│ → 1,500 clientes activos            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ entrenar_inicial.py                 │
│                                     │
│ 1. StandardScaler                   │
│    Normaliza las 3 variables a      │
│    media=0, desviación=1            │
│                                     │
│ 2. K-Means (n_clusters=3,           │
│    random_state=42, n_init=10)      │
│    Agrupa clientes por similitud    │
│    en el espacio tridimensional     │
│                                     │
│ 3. Cálculo de umbrales              │
│    Percentil 95 de distancias       │
│    intra-cluster → control de       │
│    calidad de predicción            │
│                                     │
│ 4. Serialización (joblib)           │
│    motor_segmentacion.pkl           │
└─────────────────────────────────────┘
```

### ¿Por qué K-Means y no otro algoritmo?

- **No supervisado:** No necesitamos etiquetas predefinidas de "bueno" o "malo". El algoritmo descubre patrones naturales en los datos.
- **Interpretable:** Los centroides son directamente legibles: "el cliente promedio del cluster X gana Y, utiliza Z% de su crédito y paga con W días de anticipación".
- **3 clusters:** Elegido porque produce una segmentación accionable: bajo riesgo (ofertar), moderado (evaluar), alto (rechazar).

### ¿Por qué StandardScaler?

K-Means usa distancia euclidiana. Sin escalar, `ingresos_mensuales` (rango 800–49,000) dominaría completamente a `linea_credito_utilizada` (rango 0–1) y `dias_atraso_promedio` (rango -180 a +168). El scaler iguala la influencia de las tres variables.

---

## Perfiles de riesgo: interpretación detallada

### Cluster 0 — Bajo Riesgo (32.8% de la cartera — 492 clientes)

| Variable | Centroide | Interpretación |
|----------|-----------|----------------|
| `ingresos_mensuales` | **$5,080** | Ingresos moderados, estables |
| `linea_credito_utilizada` | **0.28 (28%)** | Usan activamente su crédito pero con holgura |
| `dias_atraso_promedio` | **-54.5 días** | Pagan casi 2 meses antes del vencimiento |
| Umbral de distancia | 2.502 | Cluster compacto, miembros muy similares entre sí |

**Perfil del cliente:** Usuario responsable que utiliza su línea de crédito de forma activa pero paga consistentemente con mucha anticipación. Tiene capacidad de pago comprobada y bajo riesgo de mora.

**Acción recomendada:** Ofrecer tasa preferencial del 12% con ampliación de línea de crédito. Son candidatos ideales para campañas de fidelización y venta cruzada.

---

### Cluster 1 — Riesgo Moderado (54.6% de la cartera — 819 clientes)

| Variable | Centroide | Interpretación |
|----------|-----------|----------------|
| `ingresos_mensuales` | **$4,775** | Ingresos más bajos que el cluster 0 |
| `linea_credito_utilizada` | **0.09 (9%)** | Apenas usan su crédito |
| `dias_atraso_promedio` | **-4.9 días** | Pagan cerca de la fecha de vencimiento |
| Umbral de distancia | 1.877 | Cluster más compacto, alta homogeneidad |

**Perfil del cliente:** Cliente conservador con baja utilización de crédito. Paga cerca del vencimiento (ni muy anticipado ni muy tarde). Sus ingresos son los más bajos de los tres grupos, lo que limita su capacidad de endeudamiento adicional, aunque no presenta morosidad significativa.

**Acción recomendada:** Evaluar historial crediticio completo para aprobación condicionada. Puede requerir garantías adicionales o un monto menor al solicitado.

---

### Cluster 2 — Riesgo Alto (12.6% de la cartera — 189 clientes)

| Variable | Centroide | Interpretación |
|----------|-----------|----------------|
| `ingresos_mensuales` | **$14,105** | Ingresos altos (casi 3× el cluster 0) |
| `linea_credito_utilizada` | **0.14 (14%)** | Baja utilización relativa |
| `dias_atraso_promedio` | **-17.4 días** | Pagan con anticipación moderada |
| Umbral de distancia | 2.798 | Cluster más disperso, miembros diversos |

**Perfil del cliente:** Este cluster es contraintuitivo a primera vista: son los clientes con mayores ingresos. Sin embargo, K-Means los separó porque su comportamiento financiero es **estadísticamente distinto** al resto de la cartera. La alta dispersión del cluster (umbral 2.798) sugiere que este grupo contiene tanto clientes excelentes como clientes con patrones atípicos que el algoritmo identifica como anomalías respecto al comportamiento mayoritario de la cartera.

> **Interpretación técnica:** En el espacio escalado tridimensional, estos clientes están lejos del centro de masa de la cartera (~$5,000 de ingreso). K-Means los aísla en su propio cluster porque son *outliers* por ingresos. La etiqueta "Riesgo Alto" refleja que su perfil no encaja en los patrones conocidos de buen comportamiento (clusters 0 y 1), no necesariamente que sean malos pagadores.

**Acción recomendada:** Rechazar crédito o requerir evaluación manual exhaustiva. Su atipicidad estadística justifica precaución.

---

## Cómo interpretar los resultados

Cuando evalúas un nuevo cliente, la API devuelve:

```json
{
  "cluster": 0,
  "nivel_riesgo": "Bajo Riesgo",
  "porcentaje_similitud": "90%",
  "recomendacion_accion": "Ofrecer tasa preferencial del 12% con línea de crédito adicional"
}
```

### `cluster` y `nivel_riesgo`

El identificador numérico (0, 1, 2) y su etiqueta humana. Indica a qué grupo pertenece el cliente según su similitud con los centroides.

### `porcentaje_similitud`

Es la métrica más importante. Se calcula como:

```
similitud = (1 - distancia_al_centroide / umbral_del_cluster) × 100
```

Donde:
- **distancia_al_centroide**: distancia euclidiana entre el cliente escalado y el centroide de su cluster asignado.
- **umbral_del_cluster**: percentil 95 de las distancias de todos los miembros de ese cluster a su centroide.

| Similitud | Interpretación |
|-----------|----------------|
| **90–100%** | El cliente es casi idéntico al perfil promedio del cluster. Alta confianza en la predicción |
| **70–89%** | El cliente pertenece claramente al cluster pero tiene algunas desviaciones menores |
| **40–69%** | Pertenece al cluster pero está en sus bordes. La predicción es válida pero con menor certeza |
| **0–39%** | El cliente está en el límite del cluster o es un caso atípico. Evaluar con criterio adicional |

> Si la similitud es **0%**, significa que el cliente está exactamente en el umbral del percentil 95 o más lejos. Es un valor extremo dentro de ese cluster.

### `recomendacion_accion`

Acción de negocio predefinida según el cluster. Son sugerencias basadas en reglas de negocio, no en el modelo ML.

---

## Guía de uso

### Dashboard web

1. Abrir `http://localhost:5000` en el navegador.
2. El panel superior muestra **4 KPIs**: total de clientes, ingreso promedio, días de atraso promedio y utilización promedio.
3. Los gráficos de dona y barras muestran la distribución de clientes por cluster.
4. La tabla inferior lista los clientes con paginación (20 por página). Usa los **filtros** (Cobranza, Evaluación, Mejores Tasas) para ver solo clientes de un cluster específico.
5. El botón **"Evaluar Nuevo Cliente"** abre un modal donde ingresas las 3 variables. El resultado aparece instantáneamente con el nivel de riesgo, porcentaje de similitud y recomendación.

### API (para integración)

```bash
# Evaluar un cliente nuevo
curl -X POST http://localhost:5000/api/segmentar \
  -H "Content-Type: application/json" \
  -d '{"ingresos_mensuales": 5000, "linea_credito_utilizada": 0.25, "dias_atraso_promedio": -50}'

# Obtener resumen del dashboard
curl http://localhost:5000/api/dashboard/resumen

# Listar clientes de un cluster específico
curl "http://localhost:5000/api/dashboard/clientes?cluster=0"

# Reentrenar modelo (requiere acceso a BD)
curl -X POST http://localhost:5000/api/dashboard/actualizar
```

---

## Endpoints API

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|:---:|
| `GET` | `/` | Dashboard SPA | No |
| `POST` | `/api/segmentar` | Predecir riesgo de un nuevo cliente | No |
| `GET` | `/api/dashboard/resumen` | KPIs y distribución de clusters | No |
| `GET` | `/api/dashboard/clientes?cluster={0,1,2}` | Clientes filtrados por cluster | No |
| `GET` | `/api/dashboard/clientes-riesgo` | Solo cluster 2 (compatibilidad) | No |
| `POST` | `/api/dashboard/actualizar` | Reentrenar modelo desde BD | No |

### POST `/api/segmentar` — Request

| Campo | Tipo | Requerido | Descripción | Ejemplo |
|-------|------|:---:|-------------|---------|
| `ingresos_mensuales` | number | Sí | Ingresos mensuales en USD | `5000` |
| `linea_credito_utilizada` | number | Sí | Proporción 0.0–1.0 | `0.25` |
| `dias_atraso_promedio` | number | Sí | Días de atraso (negativo = pago anticipado) | `-50` |

### POST `/api/segmentar` — Response

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `cluster` | int | ID del cluster asignado (0, 1, 2) |
| `nivel_riesgo` | string | Etiqueta legible |
| `porcentaje_similitud` | string | Qué tan cerca está del centroide (ej. `"90%"`) |
| `recomendacion_accion` | string | Acción de negocio sugerida |

---

## Despliegue en Render

El proyecto está listo para desplegar en [Render](https://render.com) sin base de datos:

### Configuración en Render

| Campo | Valor |
|-------|-------|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r backend_api/requirements.txt` |
| **Start Command** | `gunicorn backend_api.main:app --bind 0.0.0.0:$PORT` |
| **Root Directory** | (dejar vacío — usar raíz del repo) |

### Requisitos cumplidos

- `gunicorn>=21.0.0` incluido en `requirements.txt`.
- La app Flask se instancia como `app` en `backend_api/main.py:9`.
- El modelo se carga desde `motor_segmentacion.pkl` sin tocar la base de datos.
- Las importaciones de MySQL son perezosas (solo dentro del endpoint `/api/dashboard/actualizar`).
- La carpeta `database/` fue eliminada; el repositorio es ligero.

---

## Desarrollo local con base de datos

Si necesitas reentrenar el modelo con datos frescos:

1. Instalar MySQL/MariaDB e importar el dump SQL.
2. Instalar `mysql-connector-python`:
   ```bash
   pip install mysql-connector-python
   ```
3. Configurar credenciales en `backend_api/config/db_config.py`.
4. Llamar al endpoint de actualización:
   ```bash
   curl -X POST http://localhost:5000/api/dashboard/actualizar
   ```

---

## Estructura del proyecto

```
proyecto_segmentacion_dinamica/
├── backend_api/
│   ├── main.py                         # App Flask + endpoints REST
│   ├── requirements.txt                # Flask, pandas, scikit-learn, numpy, joblib, gunicorn
│   ├── config/
│   │   └── db_config.py                # Conexión MySQL (solo desarrollo local)
│   ├── models/
│   │   └── motor_segmentacion.pkl      # Modelo serializado (~1.2 MB, incluido en repo)
│   └── src/
│       ├── consultas_ia.py             # Query SQL que extrae los 3 features
│       └── entrenar_inicial.py         # Pipeline K-Means + StandardScaler
├── frontend_dashboard/
│   ├── index.html                      # SPA con modal de evaluación
│   ├── css/
│   │   └── dashboard.css               # Tema oscuro glassmorphism
│   └── js/
│       ├── api_client.js               # fetchResumen() / fetchClientes()
│       └── charts.js                   # Gráficos donut y barras (Chart.js 4.4)
├── .gitignore
├── README.md
└── test_*.py                           # Suite de pruebas
```

---

## Datos de prueba

Usa estos valores en el modal **"Evaluar Nuevo Cliente"** del dashboard o en `POST /api/segmentar`:

### Bajo Riesgo → Ofertar

| Ingresos | % Utilización | Días Atraso | Similitud esperada |
|----------|:---:|:---:|:---:|
| 5,000 | 0.25 | -50 | ~90% |
| 3,500 | 0.40 | -80 | ~51% |

### Riesgo Moderado → Evaluar

| Ingresos | % Utilización | Días Atraso | Similitud esperada |
|----------|:---:|:---:|:---:|
| 4,500 | 0.10 | 0 | ~91% |
| 6,000 | 0.05 | -10 | ~76% |

### Riesgo Alto → Rechazar

| Ingresos | % Utilización | Días Atraso | Similitud esperada |
|----------|:---:|:---:|:---:|
| 14,000 | 0.15 | -15 | ~96% |
| 30,000 | 0.30 | 20 | ~0% |

> **Tip:** Con 30,000 de ingresos y 0% de similitud, el cliente cae en Riesgo Alto pero en el borde extremo del cluster. El modelo dice "no se parece a nadie de la cartera conocida" → revisión manual obligatoria.

---

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.14, Flask, gunicorn |
| ML | scikit-learn (KMeans, StandardScaler), joblib |
| Datos | pandas, NumPy |
| Frontend | Vanilla JS ES6, Chart.js 4.4, CSS Glassmorphism |
| Base de datos (dev) | MySQL/MariaDB, mysql-connector-python |
