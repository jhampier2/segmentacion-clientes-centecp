# Dashboard de Segmentación de Clientes - CENTECP

Aplicación web full-stack para segmentación de clientes en tiempo real usando **K-Means (machine learning no supervisado)**. Clasifica clientes en tres niveles de riesgo basándose en ingresos, utilización de línea de crédito y días de atraso, con un dashboard interactivo para visualización y evaluación.

## Estructura del Proyecto

```
proyecto_segmentacion_dinamica/
├── backend_api/
│   ├── main.py                         # API Flask - servidor principal
│   ├── requirements.txt                # Dependencias Python
│   ├── config/
│   │   └── db_config.py                # Conexión a base de datos MySQL
│   ├── models/
│   │   └── motor_segmentacion.pkl      # Modelo ML serializado (joblib)
│   └── src/
│       ├── consultas_ia.py             # Consulta SQL - extracción de datos
│       └── entrenar_inicial.py         # Pipeline de entrenamiento K-Means
├── frontend_dashboard/
│   ├── index.html                      # Dashboard SPA
│   ├── css/
│   │   └── dashboard.css               # Estilos dark theme glassmorphism
│   └── js/
│       ├── api_client.js               # Cliente HTTP para la API
│       └── charts.js                   # Gráficos Chart.js (donut y barras)
├── database/
│   └── crediinversion_creditocentecp.sql  # Dump completo de la BD
└── test_*.py                           # Suite de pruebas
```

## Tecnologías

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend | Python + Flask | 3.14 / 3.1.1 |
| Machine Learning | scikit-learn (KMeans, StandardScaler) | 1.6.1 |
| Datos | Pandas, NumPy | 2.2.3 / 2.2.4 |
| Base de Datos | MariaDB / MySQL | 10.6 |
| Frontend | HTML5, CSS3, Vanilla JS (ES6) | — |
| Gráficos | Chart.js | 4.4.1 (CDN) |
| Estilos | Glassmorphism CSS personalizado | — |

## Requisitos Previos

- Python 3.10+
- Servidor MySQL/MariaDB corriendo
- Base de datos `crediinversion_creditocentecp` cargada

## Instalación

```bash
# 1. Clonar o navegar al proyecto
cd proyecto_segmentacion_dinamica

# 2. Instalar dependencias Python
pip install -r backend_api/requirements.txt

# 3. Importar la base de datos
mysql -u root < database/crediinversion_creditocentecp.sql
```

## Ejecución

```bash
# Iniciar el servidor (puerto 5000)
python backend_api/main.py

# Abrir en el navegador
# http://localhost:5000
```

Al primer inicio, si no existe `motor_segmentacion.pkl`, el sistema entrena automáticamente el modelo K-Means con los datos de la base de datos.

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/segmentar` | Predecir cluster de riesgo para un nuevo cliente |
| `GET` | `/api/dashboard/resumen` | Métricas agregadas y distribución de clusters |
| `GET` | `/api/dashboard/clientes?cluster={0,1,2}` | Lista de clientes filtrada por cluster |
| `GET` | `/api/dashboard/clientes-riesgo` | Solo clientes de alto riesgo (compatibilidad) |
| `POST` | `/api/dashboard/actualizar` | Reentrenar modelo con datos frescos de la BD |
| `GET` | `/` | Servir el dashboard frontend |

### POST `/api/segmentar`

```json
// Request
{
  "ingresos_mensuales": 2000,
  "linea_credito_utilizada": 65,
  "dias_atraso_promedio": 5
}

// Response
{
  "cluster": 2,
  "nivel_riesgo": "Riesgo Alto",
  "porcentaje_similitud": 87.5,
  "recomendacion_accion": "RECHAZAR crédito por alto riesgo de impago"
}
```

## Clusters de Riesgo

| Cluster | Etiqueta | Color | Recomendación |
|---------|----------|-------|---------------|
| 0 | Bajo Riesgo | Verde | Ofrecer tasa preferencial 12% y ampliar línea |
| 1 | Riesgo Moderado | Ámbar | Evaluar historial crediticio para aprobación condicional |
| 2 | Riesgo Alto | Rojo | Rechazar crédito por alto riesgo de impago |

## Pruebas

```bash
python test_completo.py      # Prueba integral de endpoints
python test_filtros.py       # Prueba de filtros por cluster
python test_clean.py         # Prueba con reinicio limpio del servidor
python test_inprocess.py     # Prueba en proceso (sin red)
```

## Funcionamiento

1. **Extracción de datos** — `consultas_ia.py` ejecuta una consulta SQL que une las tablas `tclie_general`, `tprestamo` y `tpresta_detalle` para obtener ingresos mensuales, % de utilización de crédito y días promedio de atraso.

2. **Entrenamiento** — `entrenar_inicial.py` escala las variables con `StandardScaler` y entrena K-Means con 3 clusters (random_state=42). Calcula umbrales de distancia al percentil 95. Serializa todo en `motor_segmentacion.pkl`.

3. **Predicción** — Un nuevo cliente se escala, se asigna al cluster más cercano y se calcula un porcentaje de similitud: `(1 - distancia/umbral) × 100`.

4. **Dashboard** — El frontend consume la API y renderiza tarjetas KPI, gráficos donut/barras (Chart.js) y una tabla paginada con filtros por cluster y un modal para evaluar clientes individuales.

## Configuración de Base de Datos

Editar `backend_api/config/db_config.py`:

```python
config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'crediinversion_creditocentecp',
    'port': 3306
}
```
