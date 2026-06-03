import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.consultas_ia import extraer_variables
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np

FEATURES = ["ingresos_mensuales", "linea_credito_utilizada", "dias_atraso_promedio"]
N_CLUSTERS = 3
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "motor_segmentacion.pkl")

def entrenar():
    os.makedirs(MODEL_DIR, exist_ok=True)
    df = extraer_variables()
    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    model.fit(X_scaled)
    labels = model.predict(X_scaled)
    df["cluster"] = labels

    centroids = model.cluster_centers_
    dist_thresholds = {}
    for c in range(N_CLUSTERS):
        mask = labels == c
        pts = X_scaled[mask]
        centroid = centroids[c]
        dists = np.linalg.norm(pts - centroid, axis=1)
        dist_thresholds[int(c)] = float(np.percentile(dists, 95)) if len(dists) > 0 else 1.0

    joblib.dump({
        "model": model,
        "scaler": scaler,
        "features": FEATURES,
        "dataframe": df,
        "dist_thresholds": dist_thresholds
    }, MODEL_PATH)
    print(f"Modelo entrenado con {len(df)} registros y exportado a {MODEL_PATH}")
    print(f"Umbrales de distancia por cluster: {dist_thresholds}")
    return df

if __name__ == "__main__":
    entrenar()
