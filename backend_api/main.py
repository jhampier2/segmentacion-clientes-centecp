from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "motor_segmentacion.pkl")

CLUSTER_LABELS = {
    0: "Bajo Riesgo",
    1: "Riesgo Moderado",
    2: "Riesgo Alto"
}

def cargar_modelo():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Modelo no encontrado en {MODEL_PATH}. "
            "Ejecuta el entrenamiento localmente con acceso a la base de datos antes de desplegar."
        )
    return joblib.load(MODEL_PATH)

artifact = cargar_modelo()
model = artifact["model"]
scaler = artifact["scaler"]
features = artifact["features"]
df_clientes = artifact["dataframe"]
dist_thresholds = artifact.get("dist_thresholds", {})

RECOMENDACIONES = {
    0: "Ofrecer tasa preferencial del 12% con línea de crédito adicional",
    1: "Evaluar historial crediticio para aprobación condicionada",
    2: "Rechazar crédito por alto riesgo de morosidad"
}

@app.route("/api/segmentar", methods=["POST"])
def segmentar():
    from flask import request
    data = request.get_json()
    vals = np.array([[data[f] for f in features]], dtype=float)
    scaled = scaler.transform(vals)

    similitudes_clusters = {}
    for c in range(3):
        c_centroid = model.cluster_centers_[c]
        c_dist = float(np.linalg.norm(scaled[0] - c_centroid))
        c_umbral = dist_thresholds.get(c, 1.0)
        c_sim = max(0, min(100, int((1 - c_dist / c_umbral) * 100)))
        similitudes_clusters[c] = {
            "nivel_riesgo": CLUSTER_LABELS[c],
            "porcentaje": c_sim
        }

    mejor_cluster = max(range(3), key=lambda c: similitudes_clusters[c]["porcentaje"])
    similitud = similitudes_clusters[mejor_cluster]["porcentaje"]
    cluster = mejor_cluster
    centroid = model.cluster_centers_[cluster]

    SIMILITUD_MINIMA = 20
    if similitud == 0:
        nivel_riesgo = "No Clasificable"
        recomendacion = "Cliente fuera de rango: no coincide con ningun perfil conocido de la cartera. Requiere evaluacion manual exhaustiva."
        cluster = -1
    elif similitud < SIMILITUD_MINIMA:
        nivel_riesgo = CLUSTER_LABELS[cluster] + " (Atipico)"
        recomendacion = "Cliente en zona gris: baja similitud con el perfil asignado. " + RECOMENDACIONES[cluster] + " con condiciones mas estrictas."
    else:
        nivel_riesgo = CLUSTER_LABELS[cluster]
        recomendacion = RECOMENDACIONES[cluster]

    raw_vals = vals[0]
    contribucion_variables = []
    for i, f in enumerate(features):
        centroid_raw = float(scaler.inverse_transform([centroid])[0][i])
        cliente_raw = float(raw_vals[i])
        contribucion_variables.append({
            "variable": f,
            "valor_cliente": round(cliente_raw, 2),
            "valor_centroide": round(centroid_raw, 2),
            "desviacion_pct": round(abs(cliente_raw - centroid_raw) / max(abs(centroid_raw), 1) * 100, 1)
        })

    return jsonify({
        "cluster": cluster,
        "nivel_riesgo": nivel_riesgo,
        "porcentaje_similitud": f"{similitud}%",
        "similitud_valor": similitud,
        "similitudes_clusters": similitudes_clusters,
        "contribucion_variables": contribucion_variables,
        "recomendacion_accion": recomendacion,
        "es_atipico": similitud < SIMILITUD_MINIMA
    })

@app.route("/api/dashboard/resumen", methods=["GET"])
def resumen():
    dist = df_clientes["cluster"].value_counts().sort_index()
    total = len(df_clientes)
    distribucion = [
        {"cluster": int(k), "nivel_riesgo": CLUSTER_LABELS[k], "cantidad": int(v), "porcentaje": round(v / total * 100, 1)}
        for k, v in dist.items()
    ]
    metricas = {
        "total_clientes": total,
        "ingreso_promedio": round(float(df_clientes["ingresos_mensuales"].mean()), 2),
        "dias_atraso_promedio": round(float(df_clientes["dias_atraso_promedio"].mean()), 1),
        "utilizacion_promedio": round(float(df_clientes["linea_credito_utilizada"].mean()), 4)
    }
    return jsonify({"distribucion": distribucion, "metricas": metricas})

CLIENTES_COLS = ["id_cliente", "nombre_completo", "dni", "ingresos_mensuales",
                 "linea_credito_utilizada", "dias_atraso_promedio", "cluster"]

def _filtrar_clientes(cluster=None):
    if cluster is not None and cluster in CLUSTER_LABELS:
        filtrado = df_clientes[df_clientes["cluster"] == cluster].copy()
    else:
        filtrado = df_clientes.copy()
    data = filtrado[CLIENTES_COLS].to_dict(orient="records")
    return cluster, len(filtrado), data

@app.route("/api/dashboard/clientes", methods=["GET"])
def clientes_por_cluster():
    from flask import request
    c = request.args.get("cluster", default=None, type=int)
    cluster, total, data = _filtrar_clientes(c)
    return jsonify({"cluster": cluster, "total": total, "clientes": data})

@app.route("/api/dashboard/clientes-riesgo", methods=["GET"])
def clientes_riesgo():
    cluster, total, data = _filtrar_clientes(2)
    return jsonify({"cluster": cluster, "total": total, "clientes": data})

@app.route("/api/dashboard/actualizar", methods=["POST"])
def actualizar():
    global df_clientes, model, scaler, features, dist_thresholds
    try:
        from src.entrenar_inicial import entrenar
    except ImportError as e:
        return jsonify({"error": f"No se puede reentrenar sin acceso a base de datos: {e}"}), 503
    try:
        df_clientes = entrenar()
        artifact = joblib.load(MODEL_PATH)
        model = artifact["model"]
        scaler = artifact["scaler"]
        features = artifact["features"]
        dist_thresholds = artifact.get("dist_thresholds", {})
        return jsonify({"mensaje": "Modelo reentrenado con datos actuales", "total": len(df_clientes)})
    except Exception as e:
        return jsonify({"error": f"Fallo al reentrenar: {e}"}), 500

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend_dashboard")

@app.route("/")
def servir_frontend():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/css/<path:filename>")
def servir_css(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "css"), filename)

@app.route("/js/<path:filename>")
def servir_js(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "js"), filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
